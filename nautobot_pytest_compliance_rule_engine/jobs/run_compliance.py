"""RunComplianceRules Job: runs a ComplianceRuleSet against the devices its filters resolve to.

Nautobot 2.x has no ``Site`` model -- ``Location`` is its replacement -- so the
"site" filter called for by the design is implemented as a ``Location`` filter.

For each resolved device the Job gathers configuration/command data, runs every
applicable rule in the selected rule set through the execution engine
(``engine.execute_rule()``), and records one ``ComplianceTestResult`` per
device x rule, linked to this run's ``JobResult``.

Data gathering prefers the Golden Config app's latest backup for the device and
falls back to gathering live command output over NAPALM. A device neither
source can supply data for is skipped with a logged warning; the rest of the
run continues. The same is true of any unexpected failure while gathering one
device's data -- it is logged against that device and the remaining devices are
still evaluated.
"""

from typing import Dict, List, NamedTuple, Optional

from nautobot.apps.jobs import Job, MultiObjectVar, ObjectVar, register_jobs
from nautobot.dcim.models import Device, Location, Platform
from nautobot.extras.models import Role, Tag

from nautobot_pytest_compliance_rule_engine.engine import execute_rule
from nautobot_pytest_compliance_rule_engine.integrations.golden_config import get_latest_backup_config
from nautobot_pytest_compliance_rule_engine.integrations.live_device import LiveDeviceError, gather_command_output
from nautobot_pytest_compliance_rule_engine.models import (
    ComplianceRuleSet,
    ComplianceTestResult,
    ComplianceTestResultStatusChoices,
)

name = "Pytest Compliance Rule Engine"

# The show command whose output stands in for a device's configuration when
# Golden Config has no backup on record for it, keyed by the platform's NAPALM
# driver. Only drivers that spell it differently from the near-universal
# `show running-config` need an entry here.
RUNNING_CONFIG_COMMANDS = {
    "junos": "show configuration",
}

DEFAULT_RUNNING_CONFIG_COMMAND = "show running-config"


class DeviceData(NamedTuple):
    """The configuration and command output gathered for one device, and where they came from."""

    configuration: str
    commands: Dict[str, str]
    source: str


def running_config_command(device) -> str:
    """Return the show command that yields `device`'s running configuration."""
    driver = (device.platform.napalm_driver or "") if device.platform else ""
    return RUNNING_CONFIG_COMMANDS.get(driver.lower(), DEFAULT_RUNNING_CONFIG_COMMAND)


def rules_for_device(rules, device) -> List:
    """Return the subset of `rules` that applies to `device`.

    A rule with no platform set applies to every device; a rule bound to a
    platform applies only to devices on that platform.
    """
    return [rule for rule in rules if rule.platform_id is None or rule.platform_id == device.platform_id]


class RunComplianceRules(Job):
    """Run a ComplianceRuleSet's rules against devices matching the selected filters."""

    location = MultiObjectVar(
        model=Location,
        required=False,
        label="Locations",
        description="Limit devices to these locations. Leave blank to include all locations.",
    )
    role = MultiObjectVar(
        model=Role,
        required=False,
        label="Roles",
        description="Limit devices to these roles. Leave blank to include all roles.",
    )
    platform = MultiObjectVar(
        model=Platform,
        required=False,
        label="Platforms",
        description="Limit devices to these platforms. Leave blank to include all platforms.",
    )
    tag = MultiObjectVar(
        model=Tag,
        required=False,
        label="Tags",
        description="Limit devices to those with any of these tags. Leave blank to skip tag filtering.",
    )
    rule_set = ObjectVar(
        model=ComplianceRuleSet,
        label="Rule set",
        description="The ComplianceRuleSet whose rules will be run against the resolved devices.",
    )

    class Meta:
        """Meta options for RunComplianceRules."""

        name = "Run Compliance Rules"
        description = "Run a ComplianceRuleSet's rules against devices matching the selected filters."

    def get_device_queryset(self, location, role, platform, tag):
        """Resolve the Device queryset for the given filter selections."""
        queryset = Device.objects.all()
        if location:
            queryset = queryset.filter(location__in=location)
        if role:
            queryset = queryset.filter(role__in=role)
        if platform:
            queryset = queryset.filter(platform__in=platform)
        if tag:
            queryset = queryset.filter(tags__in=tag).distinct()
        return queryset

    def gather_device_data(self, device) -> Optional[DeviceData]:
        """Return the data to run rules against for `device`, or None if there is none to be had.

        Golden Config's latest backup is preferred: it needs no connection to
        the device and is what the rules are normally written against. When it
        has nothing on record -- no Golden Config app installed, no record for
        the device, no backup taken yet -- the device's running configuration
        is gathered live over NAPALM instead.

        Returns None, having logged why, when the live fallback cannot reach
        the device either. Callers should treat that as "skip this device".

        Golden Config only ever supplies a configuration, so `commands` is
        empty for a device sourced from it; a rule asking for command output
        records an error for that device rather than a pass.
        """
        configuration = get_latest_backup_config(device)
        if configuration is not None:
            return DeviceData(configuration=configuration, commands={}, source="Golden Config")

        command = running_config_command(device)
        try:
            commands = gather_command_output(device, [command])
        except LiveDeviceError as exc:
            self.logger.warning("Live data gathering failed for device %s: %s", device, exc, extra={"object": device})
            return None

        if command not in commands:
            self.logger.warning(
                "Live data gathering for device %s returned no output for '%s'.",
                device,
                command,
                extra={"object": device},
            )
            return None

        return DeviceData(configuration=commands[command], commands=commands, source="live device")

    def record_result(self, rule, device, execution) -> ComplianceTestResult:
        """Persist one rule execution against one device, linked to this run's JobResult."""
        result = ComplianceTestResult(
            rule=rule,
            device=device,
            status=execution.status,
            output=execution.output,
            job_result=self.job_result,
        )
        result.validated_save()
        return result

    def run(self, location, role, platform, tag, rule_set):
        """Run the rule set's enabled rules against every resolved device and record the outcomes."""
        devices = list(self.get_device_queryset(location, role, platform, tag))
        rules = list(rule_set.rules.filter(enabled=True))

        self.logger.info(
            "Running %d enabled rule(s) from rule set '%s' against %d device(s).",
            len(rules),
            rule_set,
            len(devices),
        )

        counts = {status: 0 for status, _ in ComplianceTestResultStatusChoices.CHOICES}
        devices_evaluated = 0
        devices_skipped = 0

        for device in devices:
            applicable_rules = rules_for_device(rules, device)
            if not applicable_rules:
                self.logger.info(
                    "No rules in rule set '%s' apply to device %s; nothing to run.",
                    rule_set,
                    device,
                    extra={"object": device},
                )
                continue

            # One device's data gathering must not take the whole run down with it.
            try:
                device_data = self.gather_device_data(device)
            except Exception as exc:
                self.logger.error(
                    "Skipping device %s: gathering its data raised %s: %s",
                    device,
                    type(exc).__name__,
                    exc,
                    extra={"object": device},
                )
                devices_skipped += 1
                continue

            if device_data is None:
                self.logger.warning(
                    "Skipping device %s: no configuration is available from Golden Config or the device itself.",
                    device,
                    extra={"object": device},
                )
                devices_skipped += 1
                continue

            self.logger.info(
                "Running %d rule(s) against device %s using data from %s.",
                len(applicable_rules),
                device,
                device_data.source,
                extra={"object": device},
            )

            for rule in applicable_rules:
                execution = execute_rule(
                    rule,
                    configuration=device_data.configuration,
                    commands=device_data.commands,
                )
                self.record_result(rule, device, execution)
                counts[execution.status] += 1

            devices_evaluated += 1

        self.logger.info(
            "Recorded %d result(s): %d passed, %d failed, %d errored. %d device(s) evaluated, %d skipped.",
            sum(counts.values()),
            counts[ComplianceTestResultStatusChoices.PASS],
            counts[ComplianceTestResultStatusChoices.FAIL],
            counts[ComplianceTestResultStatusChoices.ERROR],
            devices_evaluated,
            devices_skipped,
        )

        # The per-status keys are the ComplianceTestResultStatusChoices values themselves.
        return {
            "rule_set": str(rule_set),
            "rules": len(rules),
            "devices_resolved": len(devices),
            "devices_evaluated": devices_evaluated,
            "devices_skipped": devices_skipped,
            "results": sum(counts.values()),
            **counts,
        }


register_jobs(RunComplianceRules)
