"""RunComplianceRules Job: resolves a device queryset and a ComplianceRuleSet selection.

Nautobot 2.x has no ``Site`` model -- ``Location`` is its replacement -- so the
"site" filter called for by the design is implemented as a ``Location`` filter.

The `run()` method is a stub for this issue: it logs the resolved device
queryset and the selected rule set. Executing the rule set's rules against
those devices is implemented in a later issue.
"""

from nautobot.apps.jobs import Job, MultiObjectVar, ObjectVar, register_jobs
from nautobot.dcim.models import Device, Location, Platform
from nautobot.extras.models import Role, Tag

from nautobot_pytest_compliance_rule_engine.models import ComplianceRuleSet

name = "Pytest Compliance Rule Engine"


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

    def run(self, location, role, platform, tag, rule_set):
        """Log the resolved device queryset and selected rule set. Actual rule execution comes in a later issue."""
        queryset = self.get_device_queryset(location, role, platform, tag)
        device_names = sorted(queryset.values_list("name", flat=True))

        self.logger.info(
            "Resolved %d device(s) for rule set '%s': %s",
            len(device_names),
            rule_set,
            ", ".join(device_names) or "(none)",
        )

        return {"device_count": len(device_names), "rule_set": str(rule_set)}


register_jobs(RunComplianceRules)
