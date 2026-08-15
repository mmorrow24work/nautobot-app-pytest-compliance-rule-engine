"""LoadExampleComplianceRules Job: idempotently seeds the example ComplianceRule set.

Lets a user try the app out immediately after install rather than writing rules from
scratch. Safe to run more than once: each rule is looked up by its (unique) name via
`get_or_create`, so a second run creates nothing new and leaves existing rules
untouched -- including any a user has since edited.
"""

from nautobot.apps.jobs import Job, register_jobs

from nautobot_pytest_compliance_rule_engine.jobs.example_rules import EXAMPLE_COMPLIANCE_RULES
from nautobot_pytest_compliance_rule_engine.models import ComplianceRule

name = "Pytest Compliance Rule Engine"


class LoadExampleComplianceRules(Job):
    """Seed the database with the app's example ComplianceRule set."""

    class Meta:
        """Meta options for LoadExampleComplianceRules."""

        name = "Load Example Compliance Rules (optional)"
        description = "Load the app's example ComplianceRule set. Safe to run more than once."

    def run(self):
        """Create any example rules that don't already exist yet, keyed on name."""
        created_count = 0
        existing_count = 0

        for rule_data in EXAMPLE_COMPLIANCE_RULES:
            rule, created = ComplianceRule.objects.get_or_create(
                name=rule_data["name"],
                defaults={
                    "description": rule_data["description"],
                    "severity": rule_data["severity"],
                    "rule_code": rule_data["rule_code"],
                },
            )
            if created:
                created_count += 1
                self.logger.info("Created example rule '%s'.", rule.name, extra={"object": rule})
            else:
                existing_count += 1
                self.logger.info("Example rule '%s' already exists; left unchanged.", rule.name, extra={"object": rule})

        self.logger.info(
            "Loaded %d example rule(s): %d created, %d already existed.",
            len(EXAMPLE_COMPLIANCE_RULES),
            created_count,
            existing_count,
        )

        return {"created": created_count, "already_existed": existing_count}


register_jobs(LoadExampleComplianceRules)
