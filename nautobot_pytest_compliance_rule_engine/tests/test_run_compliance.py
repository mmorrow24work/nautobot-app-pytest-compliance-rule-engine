"""Tests for the RunComplianceRules Job: input form, device queryset resolution, and rule execution."""

from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from nautobot.dcim.models import Device, DeviceType, Location, LocationType, Manufacturer, Platform
from nautobot.extras.models import JobResult, Role, Status, Tag

from nautobot_pytest_compliance_rule_engine.integrations.live_device import LiveDeviceError
from nautobot_pytest_compliance_rule_engine.jobs.run_compliance import RunComplianceRules
from nautobot_pytest_compliance_rule_engine.models import (
    ComplianceRule,
    ComplianceRuleSet,
    ComplianceTestResult,
    ComplianceTestResultStatusChoices,
)

# The Job module is what patches target: it imports the two data-gathering
# helpers by name, so the names bound there are the ones a run() call reaches.
JOB_MODULE = "nautobot_pytest_compliance_rule_engine.jobs.run_compliance"


class RunComplianceRulesJobTest(TestCase):
    """Tests for the RunComplianceRules Job's input form and device queryset resolution."""

    @classmethod
    def setUpTestData(cls):
        """Build two Locations, two Roles, two Platforms, a Tag, and Devices that partially overlap the filters."""
        device_ct = ContentType.objects.get_for_model(Device)
        location_ct = ContentType.objects.get_for_model(Location)

        manufacturer = Manufacturer.objects.create(name="Test Manufacturer")
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model="Test Device Type")

        location_type = LocationType.objects.create(name="Test Location Type")
        location_type.content_types.add(device_ct)
        location_status = Status.objects.create(name="Test Location Status")
        location_status.content_types.add(location_ct)
        cls.location_1 = Location.objects.create(
            name="Test Location 1", location_type=location_type, status=location_status
        )
        cls.location_2 = Location.objects.create(
            name="Test Location 2", location_type=location_type, status=location_status
        )

        cls.role_1 = Role.objects.create(name="Test Role 1")
        cls.role_1.content_types.add(device_ct)
        cls.role_2 = Role.objects.create(name="Test Role 2")
        cls.role_2.content_types.add(device_ct)

        cls.platform_1 = Platform.objects.create(name="Test Platform 1")
        cls.platform_2 = Platform.objects.create(name="Test Platform 2")

        cls.tag = Tag.objects.create(name="Test Tag")
        cls.tag.content_types.add(device_ct)

        device_status = Status.objects.create(name="Test Device Status")
        device_status.content_types.add(device_ct)

        cls.matching_device = Device.objects.create(
            name="Matching Device",
            device_type=device_type,
            role=cls.role_1,
            platform=cls.platform_1,
            location=cls.location_1,
            status=device_status,
        )
        cls.matching_device.tags.add(cls.tag)

        cls.wrong_role_device = Device.objects.create(
            name="Wrong Role Device",
            device_type=device_type,
            role=cls.role_2,
            platform=cls.platform_1,
            location=cls.location_1,
            status=device_status,
        )

        cls.wrong_location_device = Device.objects.create(
            name="Wrong Location Device",
            device_type=device_type,
            role=cls.role_1,
            platform=cls.platform_1,
            location=cls.location_2,
            status=device_status,
        )

        cls.untagged_device = Device.objects.create(
            name="Untagged Device",
            device_type=device_type,
            role=cls.role_1,
            platform=cls.platform_1,
            location=cls.location_1,
            status=device_status,
        )

        cls.rule_set = ComplianceRuleSet.objects.create(name="Test Rule Set")

    def test_form_validates_with_sample_filter_inputs(self):
        """The Job's generated form accepts a full set of sample filter inputs."""
        form_class = RunComplianceRules.as_form_class()
        form = form_class(
            data={
                "location": [str(self.location_1.pk)],
                "role": [str(self.role_1.pk)],
                "platform": [str(self.platform_1.pk)],
                "tag": [str(self.tag.pk)],
                "rule_set": str(self.rule_set.pk),
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_form_validates_with_no_filters_selected(self):
        """The Job's form is valid when only the required rule_set is supplied and all filters are left blank."""
        form_class = RunComplianceRules.as_form_class()
        form = form_class(data={"rule_set": str(self.rule_set.pk)})

        self.assertTrue(form.is_valid(), form.errors)

    def test_form_requires_rule_set(self):
        """The Job's form rejects submissions missing the required rule_set."""
        form_class = RunComplianceRules.as_form_class()
        form = form_class(data={})

        self.assertFalse(form.is_valid())
        self.assertIn("rule_set", form.errors)

    def test_get_device_queryset_resolves_intersection_of_filters(self):
        """get_device_queryset filters devices by the intersection of location, role, platform, and tag."""
        job = RunComplianceRules()

        queryset = job.get_device_queryset(
            location=Location.objects.filter(pk=self.location_1.pk),
            role=Role.objects.filter(pk=self.role_1.pk),
            platform=Platform.objects.filter(pk=self.platform_1.pk),
            tag=Tag.objects.filter(pk=self.tag.pk),
        )

        self.assertEqual(list(queryset), [self.matching_device])

    def test_get_device_queryset_with_no_filters_returns_all_devices(self):
        """Leaving every filter blank (empty querysets) resolves to every Device."""
        job = RunComplianceRules()

        queryset = job.get_device_queryset(
            location=Location.objects.none(),
            role=Role.objects.none(),
            platform=Platform.objects.none(),
            tag=Tag.objects.none(),
        )

        self.assertEqual(queryset.count(), Device.objects.count())

    def test_get_device_queryset_filters_by_role_only(self):
        """Supplying only a role filter excludes devices with a different role."""
        job = RunComplianceRules()

        queryset = job.get_device_queryset(
            location=Location.objects.none(),
            role=Role.objects.filter(pk=self.role_1.pk),
            platform=Platform.objects.none(),
            tag=Tag.objects.none(),
        )

        self.assertIn(self.matching_device, queryset)
        self.assertIn(self.wrong_location_device, queryset)
        self.assertIn(self.untagged_device, queryset)
        self.assertNotIn(self.wrong_role_device, queryset)

    def test_run_with_an_empty_rule_set_records_nothing(self):
        """run() resolves the device queryset and, with no rules to run, records no results."""
        job = RunComplianceRules()

        summary = job.run(
            location=Location.objects.filter(pk=self.location_1.pk),
            role=Role.objects.filter(pk=self.role_1.pk),
            platform=Platform.objects.filter(pk=self.platform_1.pk),
            tag=Tag.objects.none(),
            rule_set=self.rule_set,
        )

        self.assertEqual(
            summary,
            {
                "rule_set": "Test Rule Set",
                "rules": 0,
                "devices_resolved": 2,
                "devices_evaluated": 0,
                "devices_skipped": 0,
                "results": 0,
                "pass": 0,
                "fail": 0,
                "error": 0,
            },
        )
        self.assertEqual(ComplianceTestResult.objects.count(), 0)


# Rules used by the execution tests. Each is the canonical shape the engine
# expects: one top-level function asserting on the data passed to it.
NTP_RULE_CODE = "def check_ntp(configuration):\n    assert 'ntp server' in configuration, 'no NTP server configured'"
SNMP_RULE_CODE = "def check_snmp(configuration):\n    assert 'snmp-server' in configuration, 'no SNMP community'"
VERSION_RULE_CODE = "def check_version(commands):\n    assert 'Version 17' in commands['show version']"

# Backup configurations the mocked Golden Config integration hands back, by device name.
GOLDEN_CONFIGS = {
    "r1": "hostname r1\nntp server 10.0.0.1\n",
    "r2": "hostname r2\nsnmp-server community public\n",
}


def golden_config_for(device):
    """Stand in for `get_latest_backup_config()`: a canned backup for some devices, None for the rest."""
    return GOLDEN_CONFIGS.get(device.name)


class RunComplianceRulesExecutionTest(TestCase):
    """Tests for the RunComplianceRules Job's data gathering, rule execution, and result recording."""

    @classmethod
    def setUpTestData(cls):
        """Build two IOS devices and one Junos device, a JobResult to attribute results to, and a rule set."""
        device_ct = ContentType.objects.get_for_model(Device)
        location_ct = ContentType.objects.get_for_model(Location)

        manufacturer = Manufacturer.objects.create(name="Test Manufacturer")
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model="Test Device Type")

        location_type = LocationType.objects.create(name="Test Location Type")
        location_type.content_types.add(device_ct)
        location_status = Status.objects.create(name="Test Location Status")
        location_status.content_types.add(location_ct)
        location = Location.objects.create(name="Test Location", location_type=location_type, status=location_status)

        role = Role.objects.create(name="Test Role")
        role.content_types.add(device_ct)

        device_status = Status.objects.create(name="Test Device Status")
        device_status.content_types.add(device_ct)

        cls.platform_ios = Platform.objects.create(name="Test IOS Platform", napalm_driver="ios")
        cls.platform_junos = Platform.objects.create(name="Test Junos Platform", napalm_driver="junos")

        def make_device(name, platform):
            return Device.objects.create(
                name=name,
                device_type=device_type,
                role=role,
                platform=platform,
                location=location,
                status=device_status,
            )

        cls.device_1 = make_device("r1", cls.platform_ios)
        cls.device_2 = make_device("r2", cls.platform_ios)
        cls.device_3 = make_device("r3", cls.platform_junos)

        cls.ntp_rule = ComplianceRule.objects.create(name="NTP configured", rule_code=NTP_RULE_CODE)
        cls.snmp_rule = ComplianceRule.objects.create(name="SNMP configured", rule_code=SNMP_RULE_CODE)
        cls.version_rule = ComplianceRule.objects.create(name="Version supported", rule_code=VERSION_RULE_CODE)
        cls.disabled_rule = ComplianceRule.objects.create(name="Disabled rule", rule_code=NTP_RULE_CODE, enabled=False)
        cls.junos_only_rule = ComplianceRule.objects.create(
            name="Junos only rule", rule_code=NTP_RULE_CODE, platform=cls.platform_junos
        )

        cls.rule_set = ComplianceRuleSet.objects.create(name="Test Rule Set")
        cls.rule_set.rules.set([cls.ntp_rule, cls.snmp_rule])

        cls.job_result = JobResult.objects.create(name="Run Compliance Rules")

    def build_job(self):
        """Return a Job instance wired to this test's JobResult, as Celery would wire a real run."""
        job = RunComplianceRules()
        job.job_result = self.job_result
        return job

    def run_job(self, job, rule_set=None, platform=None):
        """Run `job` over the devices on `platform` (all devices when omitted) and return its summary."""
        return job.run(
            location=Location.objects.none(),
            role=Role.objects.none(),
            platform=Platform.objects.filter(pk=platform.pk) if platform else Platform.objects.none(),
            tag=Tag.objects.none(),
            rule_set=rule_set or self.rule_set,
        )

    def recorded_statuses(self):
        """Return the recorded results as a `{(device name, rule name): status}` mapping."""
        return {(result.device.name, result.rule.name): result.status for result in ComplianceTestResult.objects.all()}

    def test_full_run_records_a_result_per_device_and_rule(self):
        """Two devices x two rules records four results with the mixed pass/fail outcomes of each pairing."""
        job = self.build_job()

        with (
            patch(f"{JOB_MODULE}.get_latest_backup_config", side_effect=golden_config_for),
            patch(f"{JOB_MODULE}.gather_command_output") as mock_gather,
        ):
            summary = self.run_job(job, platform=self.platform_ios)

        mock_gather.assert_not_called()  # Golden Config had a backup for both devices.
        self.assertEqual(
            self.recorded_statuses(),
            {
                ("r1", "NTP configured"): ComplianceTestResultStatusChoices.PASS,
                ("r1", "SNMP configured"): ComplianceTestResultStatusChoices.FAIL,
                ("r2", "NTP configured"): ComplianceTestResultStatusChoices.FAIL,
                ("r2", "SNMP configured"): ComplianceTestResultStatusChoices.PASS,
            },
        )
        self.assertEqual(
            summary,
            {
                "rule_set": "Test Rule Set",
                "rules": 2,
                "devices_resolved": 2,
                "devices_evaluated": 2,
                "devices_skipped": 0,
                "results": 4,
                "pass": 2,
                "fail": 2,
                "error": 0,
            },
        )

    def test_results_are_linked_to_the_running_job_result(self):
        """Every recorded result carries this run's JobResult and the failing assertion's message."""
        job = self.build_job()

        with (
            patch(f"{JOB_MODULE}.get_latest_backup_config", side_effect=golden_config_for),
            patch(f"{JOB_MODULE}.gather_command_output"),
        ):
            self.run_job(job, platform=self.platform_ios)

        results = ComplianceTestResult.objects.all()
        self.assertEqual(results.count(), 4)
        for result in results:
            self.assertEqual(result.job_result, self.job_result)

        failure = ComplianceTestResult.objects.get(device=self.device_1, rule=self.snmp_rule)
        self.assertEqual(failure.output, "no SNMP community")
        passing = ComplianceTestResult.objects.get(device=self.device_1, rule=self.ntp_rule)
        self.assertEqual(passing.output, "")

    def test_device_with_no_available_data_is_skipped_and_the_run_continues(self):
        """A device neither Golden Config nor the device itself can supply data for is skipped, not fatal."""
        job = self.build_job()

        with (
            patch(f"{JOB_MODULE}.get_latest_backup_config", return_value=None),
            patch(
                f"{JOB_MODULE}.gather_command_output",
                side_effect=[
                    LiveDeviceError("NAPALM is not installed."),
                    {"show running-config": GOLDEN_CONFIGS["r1"]},
                ],
            ),
            self.assertLogs(job.logger, level="WARNING") as logs,
        ):
            summary = self.run_job(job, platform=self.platform_ios)

        # r1 is unreachable and skipped; r2 falls back to live data and is still evaluated.
        self.assertEqual(summary["devices_skipped"], 1)
        self.assertEqual(summary["devices_evaluated"], 1)
        self.assertEqual(set(ComplianceTestResult.objects.values_list("device__name", flat=True)), {"r2"})
        self.assertTrue(
            any("Skipping device r1" in message for message in logs.output),
            logs.output,
        )
        self.assertTrue(
            any("NAPALM is not installed." in message for message in logs.output),
            logs.output,
        )

    def test_unexpected_data_gathering_failure_skips_only_that_device(self):
        """An unexpected exception while gathering one device's data is logged and the run carries on."""
        job = self.build_job()

        def explode_for_r1(device):
            if device.name == "r1":
                raise RuntimeError("golden config exploded")
            return golden_config_for(device)

        with (
            patch(f"{JOB_MODULE}.get_latest_backup_config", side_effect=explode_for_r1),
            patch(f"{JOB_MODULE}.gather_command_output"),
            self.assertLogs(job.logger, level="ERROR") as logs,
        ):
            summary = self.run_job(job, platform=self.platform_ios)

        self.assertEqual(summary["devices_skipped"], 1)
        self.assertEqual(summary["devices_evaluated"], 1)
        self.assertEqual(set(ComplianceTestResult.objects.values_list("device__name", flat=True)), {"r2"})
        self.assertTrue(
            any("RuntimeError" in message and "golden config exploded" in message for message in logs.output),
            logs.output,
        )

    def test_live_gathering_is_the_fallback_when_golden_config_has_nothing(self):
        """With no backup on record, the running configuration is gathered live and rules run against it."""
        job = self.build_job()
        rule_set = ComplianceRuleSet.objects.create(name="Live Rule Set")
        rule_set.rules.set([self.ntp_rule, self.version_rule])

        with (
            patch(f"{JOB_MODULE}.get_latest_backup_config", return_value=None),
            patch(
                f"{JOB_MODULE}.gather_command_output",
                return_value={
                    "show configuration": "hostname r3\nntp server 10.0.0.1\n",
                    "show version": "Version 17.9",
                },
            ) as mock_gather,
        ):
            summary = self.run_job(job, rule_set=rule_set, platform=self.platform_junos)

        # The Junos driver spells the running-config command differently.
        mock_gather.assert_called_once_with(self.device_3, ["show configuration"])
        self.assertEqual(summary["devices_evaluated"], 1)
        self.assertEqual(
            self.recorded_statuses(),
            {
                ("r3", "NTP configured"): ComplianceTestResultStatusChoices.PASS,
                ("r3", "Version supported"): ComplianceTestResultStatusChoices.PASS,
            },
        )

    def test_device_returning_no_running_config_output_is_skipped(self):
        """Live gathering that comes back without the running-config command's output is not usable data."""
        job = self.build_job()

        with (
            patch(f"{JOB_MODULE}.get_latest_backup_config", return_value=None),
            patch(f"{JOB_MODULE}.gather_command_output", return_value={}),
            self.assertLogs(job.logger, level="WARNING") as logs,
        ):
            summary = self.run_job(job, platform=self.platform_ios)

        self.assertEqual(summary["devices_skipped"], 2)
        self.assertEqual(summary["results"], 0)
        self.assertTrue(
            any("no output for 'show running-config'" in message for message in logs.output),
            logs.output,
        )

    def test_live_gathering_output_is_passed_to_rules_as_configuration_and_commands(self):
        """The running-config command's output becomes `configuration`; the whole dict becomes `commands`."""
        job = self.build_job()
        rule_set = ComplianceRuleSet.objects.create(name="IOS Rule Set")
        rule_set.rules.set([self.ntp_rule, self.version_rule])

        with (
            patch(f"{JOB_MODULE}.get_latest_backup_config", return_value=None),
            patch(
                f"{JOB_MODULE}.gather_command_output",
                return_value={
                    "show running-config": "hostname r1\nntp server 10.0.0.1\n",
                    "show version": "Version 17.9",
                },
            ) as mock_gather,
        ):
            self.run_job(job, rule_set=rule_set, platform=self.platform_ios)

        for device in (self.device_1, self.device_2):
            mock_gather.assert_any_call(device, ["show running-config"])
        self.assertEqual(
            self.recorded_statuses(),
            {
                ("r1", "NTP configured"): ComplianceTestResultStatusChoices.PASS,
                ("r1", "Version supported"): ComplianceTestResultStatusChoices.PASS,
                ("r2", "NTP configured"): ComplianceTestResultStatusChoices.PASS,
                ("r2", "Version supported"): ComplianceTestResultStatusChoices.PASS,
            },
        )

    def test_rule_asking_for_commands_errors_on_a_golden_config_sourced_device(self):
        """Golden Config supplies no command output, so a rule that needs it records an error, not a pass."""
        job = self.build_job()
        rule_set = ComplianceRuleSet.objects.create(name="Command Rule Set")
        rule_set.rules.set([self.version_rule])

        with (
            patch(f"{JOB_MODULE}.get_latest_backup_config", side_effect=golden_config_for),
            patch(f"{JOB_MODULE}.gather_command_output"),
        ):
            summary = self.run_job(job, platform=self.platform_ios)

        self.assertEqual(summary["error"], 2)
        result = ComplianceTestResult.objects.get(device=self.device_1, rule=self.version_rule)
        self.assertEqual(result.status, ComplianceTestResultStatusChoices.ERROR)
        self.assertIn("KeyError", result.output)

    def test_disabled_rules_are_not_run(self):
        """A rule in the set with enabled=False is left out of the run entirely."""
        job = self.build_job()
        rule_set = ComplianceRuleSet.objects.create(name="Partly Disabled Rule Set")
        rule_set.rules.set([self.ntp_rule, self.disabled_rule])

        with (
            patch(f"{JOB_MODULE}.get_latest_backup_config", side_effect=golden_config_for),
            patch(f"{JOB_MODULE}.gather_command_output"),
        ):
            summary = self.run_job(job, rule_set=rule_set, platform=self.platform_ios)

        self.assertEqual(summary["rules"], 1)
        self.assertEqual(summary["results"], 2)
        self.assertFalse(ComplianceTestResult.objects.filter(rule=self.disabled_rule).exists())

    def test_platform_bound_rules_only_run_against_their_own_platform(self):
        """A rule bound to a platform is skipped for devices on any other platform."""
        job = self.build_job()
        rule_set = ComplianceRuleSet.objects.create(name="Platform Rule Set")
        rule_set.rules.set([self.junos_only_rule])

        with (
            patch(f"{JOB_MODULE}.get_latest_backup_config", return_value="hostname x\nntp server 10.0.0.1\n"),
            patch(f"{JOB_MODULE}.gather_command_output"),
        ):
            summary = self.run_job(job, rule_set=rule_set)

        self.assertEqual(summary["devices_resolved"], 3)
        self.assertEqual(summary["devices_evaluated"], 1)
        self.assertEqual(
            self.recorded_statuses(),
            {("r3", "Junos only rule"): ComplianceTestResultStatusChoices.PASS},
        )

    def test_devices_with_no_applicable_rules_are_not_gathered_from(self):
        """A device no rule in the set applies to is left alone -- no data gathering, no results."""
        job = self.build_job()
        rule_set = ComplianceRuleSet.objects.create(name="Empty Rule Set")

        with (
            patch(f"{JOB_MODULE}.get_latest_backup_config") as mock_golden_config,
            patch(f"{JOB_MODULE}.gather_command_output") as mock_gather,
        ):
            summary = self.run_job(job, rule_set=rule_set)

        mock_golden_config.assert_not_called()
        mock_gather.assert_not_called()
        self.assertEqual(summary["results"], 0)
        self.assertEqual(ComplianceTestResult.objects.count(), 0)
