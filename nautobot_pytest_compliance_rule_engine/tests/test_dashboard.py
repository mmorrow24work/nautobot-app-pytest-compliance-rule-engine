"""Tests for the fleet-wide Compliance Dashboard view.

Exercises the actual rendered page via the test client, rather than unit-testing
ComplianceDashboardView's aggregation methods directly, since what matters is what a
user sees -- consistent with test_template_content.py's approach for the Device tab.
"""

from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from nautobot.core.testing import TestCase, extract_page_body
from nautobot.dcim.models import Device, DeviceType, Location, LocationType, Manufacturer
from nautobot.extras.models import Role, Status

from nautobot_pytest_compliance_rule_engine.models import (
    ComplianceRule,
    ComplianceRuleSeverityChoices,
    ComplianceTestResult,
    ComplianceTestResultStatusChoices,
)
from nautobot_pytest_compliance_rule_engine.views import ComplianceDashboardView

VALID_RULE_CODE = "def test_ntp(configuration):\n    assert 'ntp' in configuration"


class ComplianceDashboardViewTest(TestCase):
    """Confirm the dashboard renders with no data, and summarizes results correctly once populated."""

    @classmethod
    def setUpTestData(cls):
        device_ct = ContentType.objects.get_for_model(Device)
        location_ct = ContentType.objects.get_for_model(Location)

        manufacturer = Manufacturer.objects.create(name="Dashboard Test Manufacturer")
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model="Dashboard Test Device Type")

        location_type = LocationType.objects.create(name="Dashboard Test Location Type")
        location_type.content_types.add(device_ct)

        location_status = Status.objects.create(name="Dashboard Test Location Status")
        location_status.content_types.add(location_ct)
        location = Location.objects.create(
            name="Dashboard Test Location",
            location_type=location_type,
            status=location_status,
        )

        device_role = Role.objects.create(name="Dashboard Test Device Role")
        device_role.content_types.add(device_ct)

        device_status = Status.objects.create(name="Dashboard Test Device Status")
        device_status.content_types.add(device_ct)

        cls.device_1 = Device.objects.create(
            name="Dashboard Test Device 1",
            device_type=device_type,
            role=device_role,
            location=location,
            status=device_status,
        )
        cls.device_2 = Device.objects.create(
            name="Dashboard Test Device 2",
            device_type=device_type,
            role=device_role,
            location=location,
            status=device_status,
        )

        cls.low_rule = ComplianceRule.objects.create(
            name="Dashboard Test Low Rule",
            severity=ComplianceRuleSeverityChoices.LOW,
            rule_code=VALID_RULE_CODE,
        )
        cls.high_rule = ComplianceRule.objects.create(
            name="Dashboard Test High Rule",
            severity=ComplianceRuleSeverityChoices.HIGH,
            rule_code=VALID_RULE_CODE,
        )

    def _url(self):
        return reverse("plugins:nautobot_pytest_compliance_rule_engine:dashboard")

    def test_dashboard_requires_permission(self):
        """A user without view_compliancetestresult is denied."""
        response = self.client.get(self._url())

        self.assertHttpStatus(response, [403, 302])

    def test_dashboard_renders_with_no_results(self):
        """With no ComplianceTestResults recorded, the dashboard still renders, showing an empty state."""
        self.add_permissions("nautobot_pytest_compliance_rule_engine.view_compliancetestresult")

        response = self.client.get(self._url())

        self.assertHttpStatus(response, 200)
        content = extract_page_body(response.content.decode(response.charset))
        self.assertIn("No compliance results have been recorded yet", content)
        self.assertIn("Low Severity", content)
        self.assertIn("High Severity", content)

    def test_dashboard_renders_with_results(self):
        """With results recorded, the dashboard shows severity-bucketed pass/fail/error counts."""
        self.add_permissions("nautobot_pytest_compliance_rule_engine.view_compliancetestresult")

        ComplianceTestResult.objects.create(
            rule=self.low_rule,
            device=self.device_1,
            status=ComplianceTestResultStatusChoices.PASS,
        )
        ComplianceTestResult.objects.create(
            rule=self.low_rule,
            device=self.device_2,
            status=ComplianceTestResultStatusChoices.FAIL,
            output="AssertionError: 'ntp' not in configuration",
        )
        ComplianceTestResult.objects.create(
            rule=self.high_rule,
            device=self.device_1,
            status=ComplianceTestResultStatusChoices.ERROR,
            output="KeyError: 'configuration'",
        )

        response = self.client.get(self._url())

        self.assertHttpStatus(response, 200)
        content = extract_page_body(response.content.decode(response.charset))
        self.assertNotIn("No compliance results have been recorded yet", content)
        self.assertIn("Low Severity", content)
        self.assertIn("High Severity", content)
        self.assertIn("30-Day Trend", content)

    def test_dashboard_current_snapshot_uses_latest_result_per_rule_and_device(self):
        """An older result for a (rule, device) pair is superseded by its newer result in the snapshot."""
        newer = ComplianceTestResult.objects.create(
            rule=self.low_rule,
            device=self.device_1,
            status=ComplianceTestResultStatusChoices.PASS,
        )
        older = ComplianceTestResult.objects.create(
            rule=self.low_rule,
            device=self.device_1,
            status=ComplianceTestResultStatusChoices.FAIL,
        )
        ComplianceTestResult.objects.filter(pk=older.pk).update(run_datetime=newer.run_datetime - timedelta(hours=1))

        severity_rows = ComplianceDashboardView()._severity_rows(ComplianceTestResult.objects.all())
        low_row = next(row for row in severity_rows if row["value"] == ComplianceRuleSeverityChoices.LOW)

        self.assertEqual(low_row["counts"]["pass"], 1)
        self.assertEqual(low_row["counts"]["fail"], 0)
