"""Tests for the ComplianceRule model."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from nautobot_pytest_compliance_rule_engine.models import ComplianceRule, ComplianceRuleSeverityChoices


class ComplianceRuleModelTest(TestCase):
    """Tests for ComplianceRule model behavior."""

    def test_create_compliance_rule(self):
        """A ComplianceRule can be created with the expected field values and defaults."""
        rule = ComplianceRule.objects.create(
            name="Require NTP servers",
            description="Devices must have at least one NTP server configured.",
            severity=ComplianceRuleSeverityChoices.HIGH,
            rule_code="def test_ntp(device):\n    assert device.ntp_servers",
        )

        self.assertEqual(rule.name, "Require NTP servers")
        self.assertEqual(rule.severity, ComplianceRuleSeverityChoices.HIGH)
        self.assertTrue(rule.enabled)
        self.assertIsNone(rule.platform)

    def test_str_returns_name(self):
        """str(rule) returns the rule's name."""
        rule = ComplianceRule.objects.create(
            name="Require SNMP community",
            rule_code="def test_snmp(device):\n    assert device.snmp_community",
        )

        self.assertEqual(str(rule), "Require SNMP community")

    def test_severity_choices_are_enforced(self):
        """An invalid severity value fails model validation."""
        rule = ComplianceRule(
            name="Invalid severity rule",
            severity="critical",
            rule_code="def test_x(device):\n    assert True",
        )

        with self.assertRaises(ValidationError):
            rule.full_clean()

    def test_name_unique_constraint(self):
        """Two ComplianceRules cannot share the same name."""
        ComplianceRule.objects.create(
            name="Duplicate rule name",
            rule_code="def test_x(device):\n    assert True",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ComplianceRule.objects.create(
                    name="Duplicate rule name",
                    rule_code="def test_y(device):\n    assert True",
                )
