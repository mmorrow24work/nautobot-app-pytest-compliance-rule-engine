"""Tests for the M6 example ComplianceRule definitions.

Confirms each example both passes the same static validation and produces the same
pass/fail behavior a real user-authored rule would -- these are meant to be usable,
correct examples, not just well-formed strings.
"""

from nautobot.core.testing import TestCase

from nautobot_pytest_compliance_rule_engine.engine import execute_rule_code
from nautobot_pytest_compliance_rule_engine.jobs.example_rules import EXAMPLE_COMPLIANCE_RULES
from nautobot_pytest_compliance_rule_engine.models import (
    ComplianceRule,
    ComplianceRuleSeverityChoices,
    ComplianceTestResultStatusChoices,
)
from nautobot_pytest_compliance_rule_engine.validation import validate_rule_code

PASSING_CONFIGURATION = "\n".join(
    [
        "banner login ^ Unauthorized access is prohibited ^",
        "ntp server 10.0.0.1",
        "snmp-server community s3cr3t-string RO",
        "line vty 0 4",
        " transport input ssh",
        "no ip http server",
    ]
)

FAILING_CONFIGURATION = "\n".join(
    [
        "hostname r1",
        "line vty 0 4",
        " transport input telnet",
        "snmp-server community public RO",
        "ip http server",
    ]
)


class ExampleComplianceRulesTest(TestCase):
    """The example rules are well-formed, valid, and behave as their descriptions claim."""

    def test_exactly_five_examples(self):
        self.assertEqual(len(EXAMPLE_COMPLIANCE_RULES), 5)

    def test_names_are_unique(self):
        names = [example["name"] for example in EXAMPLE_COMPLIANCE_RULES]
        self.assertEqual(len(names), len(set(names)))

    def test_severities_are_valid_choices(self):
        valid_severities = {value for value, _ in ComplianceRuleSeverityChoices.CHOICES}
        for example in EXAMPLE_COMPLIANCE_RULES:
            self.assertIn(example["severity"], valid_severities)

    def test_each_example_has_a_description(self):
        for example in EXAMPLE_COMPLIANCE_RULES:
            self.assertTrue(example["description"].strip())

    def test_each_rule_code_passes_static_validation(self):
        for example in EXAMPLE_COMPLIANCE_RULES:
            validate_rule_code(example["rule_code"])  # raises ValidationError on failure

    def test_each_example_saves_as_a_valid_compliance_rule(self):
        for example in EXAMPLE_COMPLIANCE_RULES:
            rule = ComplianceRule(**example)
            rule.full_clean()
            rule.save()

    def test_each_rule_passes_against_a_compliant_configuration(self):
        for example in EXAMPLE_COMPLIANCE_RULES:
            result = execute_rule_code(example["rule_code"], configuration=PASSING_CONFIGURATION)
            self.assertEqual(
                result.status,
                ComplianceTestResultStatusChoices.PASS,
                f"{example['name']} unexpectedly failed against a compliant configuration: {result.output}",
            )

    def test_each_rule_fails_against_a_noncompliant_configuration(self):
        for example in EXAMPLE_COMPLIANCE_RULES:
            result = execute_rule_code(example["rule_code"], configuration=FAILING_CONFIGURATION)
            self.assertEqual(
                result.status,
                ComplianceTestResultStatusChoices.FAIL,
                f"{example['name']} unexpectedly did not fail against a noncompliant configuration: {result.output}",
            )
