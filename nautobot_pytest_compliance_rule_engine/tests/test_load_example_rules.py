"""Tests for the LoadExampleComplianceRules Job: idempotent seeding of the example rule set."""

from django.test import TestCase
from nautobot.extras.models import JobResult

from nautobot_pytest_compliance_rule_engine.jobs.example_rules import EXAMPLE_COMPLIANCE_RULES
from nautobot_pytest_compliance_rule_engine.jobs.load_example_rules import LoadExampleComplianceRules
from nautobot_pytest_compliance_rule_engine.models import ComplianceRule


class LoadExampleComplianceRulesJobTest(TestCase):
    """First run creates every example rule; a second run creates nothing new."""

    def build_job(self):
        """Return a Job instance wired to a real JobResult, as Celery would wire a real run."""
        job = LoadExampleComplianceRules()
        job.job_result = JobResult.objects.create(name="Load Example Compliance Rules")
        return job

    def test_labeled_as_optional_in_the_jobs_ui(self):
        self.assertEqual(LoadExampleComplianceRules.Meta.name, "Load Example Compliance Rules (optional)")

    def test_first_run_creates_every_example_rule(self):
        job = self.build_job()

        summary = job.run()

        self.assertEqual(summary, {"created": len(EXAMPLE_COMPLIANCE_RULES), "already_existed": 0})
        self.assertEqual(ComplianceRule.objects.count(), len(EXAMPLE_COMPLIANCE_RULES))
        for example in EXAMPLE_COMPLIANCE_RULES:
            rule = ComplianceRule.objects.get(name=example["name"])
            self.assertEqual(rule.description, example["description"])
            self.assertEqual(rule.severity, example["severity"])
            self.assertEqual(rule.rule_code, example["rule_code"])

    def test_second_run_does_not_duplicate_rules(self):
        job = self.build_job()
        job.run()

        second_summary = self.build_job().run()

        self.assertEqual(second_summary, {"created": 0, "already_existed": len(EXAMPLE_COMPLIANCE_RULES)})
        self.assertEqual(ComplianceRule.objects.count(), len(EXAMPLE_COMPLIANCE_RULES))

    def test_second_run_does_not_overwrite_a_user_edited_rule(self):
        """get_or_create only sets defaults on creation, so an edit a user made in between survives a rerun."""
        job = self.build_job()
        job.run()

        edited_name = EXAMPLE_COMPLIANCE_RULES[0]["name"]
        rule = ComplianceRule.objects.get(name=edited_name)
        rule.description = "Edited by a user after seeding"
        rule.save()

        self.build_job().run()

        rule.refresh_from_db()
        self.assertEqual(rule.description, "Edited by a user after seeding")
