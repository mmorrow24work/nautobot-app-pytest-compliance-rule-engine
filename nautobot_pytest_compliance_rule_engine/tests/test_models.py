"""Tests for the ComplianceRule, ComplianceTestResult, and ComplianceRuleSet models."""

from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from nautobot.dcim.models import Device, DeviceType, Location, LocationType, Manufacturer
from nautobot.extras.models import Role, Status

from nautobot_pytest_compliance_rule_engine.models import (
    ComplianceRule,
    ComplianceRuleSet,
    ComplianceRuleSeverityChoices,
    ComplianceTestResult,
    ComplianceTestResultStatusChoices,
)


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


class ComplianceTestResultModelTest(TestCase):
    """Tests for ComplianceTestResult model behavior."""

    @classmethod
    def setUpTestData(cls):
        """Build the minimal ComplianceRule and Device required to attach a ComplianceTestResult to."""
        device_ct = ContentType.objects.get_for_model(Device)
        location_ct = ContentType.objects.get_for_model(Location)

        manufacturer = Manufacturer.objects.create(name="Test Manufacturer")
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model="Test Device Type")

        location_type = LocationType.objects.create(name="Test Location Type")
        location_type.content_types.add(device_ct)

        location_status = Status.objects.create(name="Test Location Status")
        location_status.content_types.add(location_ct)
        location = Location.objects.create(
            name="Test Location",
            location_type=location_type,
            status=location_status,
        )

        device_role = Role.objects.create(name="Test Device Role")
        device_role.content_types.add(device_ct)

        device_status = Status.objects.create(name="Test Device Status")
        device_status.content_types.add(device_ct)

        cls.device = Device.objects.create(
            name="Test Device 1",
            device_type=device_type,
            role=device_role,
            location=location,
            status=device_status,
        )

        cls.rule = ComplianceRule.objects.create(
            name="Require NTP servers",
            rule_code="def test_ntp(device):\n    assert device.ntp_servers",
        )

    def test_create_compliance_test_result(self):
        """A ComplianceTestResult can be created with the expected field values and defaults."""
        result = ComplianceTestResult.objects.create(
            rule=self.rule,
            device=self.device,
            status=ComplianceTestResultStatusChoices.FAIL,
            output="AssertionError: device.ntp_servers is empty",
        )

        self.assertEqual(result.rule, self.rule)
        self.assertEqual(result.device, self.device)
        self.assertEqual(result.status, ComplianceTestResultStatusChoices.FAIL)
        self.assertEqual(result.output, "AssertionError: device.ntp_servers is empty")
        self.assertIsNotNone(result.run_datetime)
        self.assertIsNone(result.job_result)

    def test_output_and_job_result_are_optional(self):
        """A ComplianceTestResult can be created without output text or a linked JobResult."""
        result = ComplianceTestResult.objects.create(
            rule=self.rule,
            device=self.device,
            status=ComplianceTestResultStatusChoices.PASS,
        )

        self.assertEqual(result.output, "")
        self.assertIsNone(result.job_result)

    def test_status_choices_are_enforced(self):
        """An invalid status value fails model validation."""
        result = ComplianceTestResult(
            rule=self.rule,
            device=self.device,
            status="unknown",
        )

        with self.assertRaises(ValidationError):
            result.full_clean()

    def test_fk_relationships_resolve(self):
        """The rule and device foreign keys resolve, including their reverse relations."""
        result = ComplianceTestResult.objects.create(
            rule=self.rule,
            device=self.device,
            status=ComplianceTestResultStatusChoices.ERROR,
        )

        self.assertIn(result, self.rule.test_results.all())
        self.assertIn(result, self.device.compliance_test_results.all())

    def test_ordering_most_recent_run_first(self):
        """ComplianceTestResults are ordered by run_datetime, most recent first."""
        older = ComplianceTestResult.objects.create(
            rule=self.rule,
            device=self.device,
            status=ComplianceTestResultStatusChoices.PASS,
        )
        newer = ComplianceTestResult.objects.create(
            rule=self.rule,
            device=self.device,
            status=ComplianceTestResultStatusChoices.FAIL,
        )
        ComplianceTestResult.objects.filter(pk=older.pk).update(run_datetime=timezone.now() - timedelta(days=1))

        self.assertEqual(list(ComplianceTestResult.objects.all()), [newer, older])

    def test_deleting_rule_cascades_to_test_results(self):
        """Deleting a ComplianceRule deletes its ComplianceTestResults."""
        result = ComplianceTestResult.objects.create(
            rule=self.rule,
            device=self.device,
            status=ComplianceTestResultStatusChoices.PASS,
        )

        self.rule.delete()

        self.assertFalse(ComplianceTestResult.objects.filter(pk=result.pk).exists())

    def test_deleting_device_cascades_to_test_results(self):
        """Deleting a Device deletes its ComplianceTestResults."""
        result = ComplianceTestResult.objects.create(
            rule=self.rule,
            device=self.device,
            status=ComplianceTestResultStatusChoices.PASS,
        )

        self.device.delete()

        self.assertFalse(ComplianceTestResult.objects.filter(pk=result.pk).exists())

    def test_filter_by_rule_severity(self):
        """ComplianceTestResults can be queried by their rule's severity via the FK."""
        high_severity_rule = ComplianceRule.objects.create(
            name="Require SNMP community",
            severity=ComplianceRuleSeverityChoices.HIGH,
            rule_code="def test_snmp(device):\n    assert device.snmp_community",
        )
        low_severity_result = ComplianceTestResult.objects.create(
            rule=self.rule,
            device=self.device,
            status=ComplianceTestResultStatusChoices.PASS,
        )
        high_severity_result = ComplianceTestResult.objects.create(
            rule=high_severity_rule,
            device=self.device,
            status=ComplianceTestResultStatusChoices.FAIL,
        )

        high_severity_results = ComplianceTestResult.objects.filter(rule__severity=ComplianceRuleSeverityChoices.HIGH)

        self.assertIn(high_severity_result, high_severity_results)
        self.assertNotIn(low_severity_result, high_severity_results)


class ComplianceRuleSetModelTest(TestCase):
    """Tests for ComplianceRuleSet model behavior."""

    @classmethod
    def setUpTestData(cls):
        """Build the ComplianceRules used to exercise the rule_set M2M relationship."""
        cls.rule_1 = ComplianceRule.objects.create(
            name="Require NTP servers",
            rule_code="def test_ntp(device):\n    assert device.ntp_servers",
        )
        cls.rule_2 = ComplianceRule.objects.create(
            name="Require SNMP community",
            rule_code="def test_snmp(device):\n    assert device.snmp_community",
        )

    def test_create_compliance_rule_set(self):
        """A ComplianceRuleSet can be created with the expected field values."""
        rule_set = ComplianceRuleSet.objects.create(
            name="CIS Cisco IOS Hardening",
            description="Rules enforcing CIS benchmarks for Cisco IOS devices.",
        )

        self.assertEqual(rule_set.name, "CIS Cisco IOS Hardening")
        self.assertEqual(rule_set.description, "Rules enforcing CIS benchmarks for Cisco IOS devices.")
        self.assertEqual(rule_set.rules.count(), 0)

    def test_rule_set_with_zero_rules_is_valid(self):
        """A ComplianceRuleSet with no rules passes full_clean and can be saved."""
        rule_set = ComplianceRuleSet(name="Empty rule set")
        rule_set.full_clean()
        rule_set.save()

        self.assertEqual(rule_set.rules.count(), 0)

    def test_str_returns_name(self):
        """str(rule_set) returns the rule set's name."""
        rule_set = ComplianceRuleSet.objects.create(name="CIS Cisco IOS Hardening")

        self.assertEqual(str(rule_set), "CIS Cisco IOS Hardening")

    def test_name_unique_constraint(self):
        """Two ComplianceRuleSets cannot share the same name."""
        ComplianceRuleSet.objects.create(name="Duplicate rule set name")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ComplianceRuleSet.objects.create(name="Duplicate rule set name")

    def test_add_and_remove_rules(self):
        """Rules can be added to and removed from a ComplianceRuleSet."""
        rule_set = ComplianceRuleSet.objects.create(name="CIS Cisco IOS Hardening")

        rule_set.rules.add(self.rule_1, self.rule_2)

        self.assertEqual(rule_set.rules.count(), 2)
        self.assertIn(self.rule_1, rule_set.rules.all())
        self.assertIn(self.rule_2, rule_set.rules.all())
        self.assertIn(rule_set, self.rule_1.rule_sets.all())

        rule_set.rules.remove(self.rule_1)

        self.assertEqual(rule_set.rules.count(), 1)
        self.assertNotIn(self.rule_1, rule_set.rules.all())
        self.assertIn(self.rule_2, rule_set.rules.all())
        self.assertNotIn(rule_set, self.rule_1.rule_sets.all())
