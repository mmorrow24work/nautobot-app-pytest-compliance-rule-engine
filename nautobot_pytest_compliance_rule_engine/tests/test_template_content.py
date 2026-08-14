"""Tests for the "Compliance" tab injected onto the Device detail page.

See template_content.py -- this exercises the actual rendered Device detail page HTML
via the test client, rather than unit-testing the TemplateExtension class directly, since
what matters is what a user sees.
"""

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from nautobot.core.testing import TestCase, extract_page_body
from nautobot.dcim.models import Device, DeviceType, Location, LocationType, Manufacturer
from nautobot.extras.models import Role, Status

from nautobot_pytest_compliance_rule_engine.models import (
    ComplianceRule,
    ComplianceTestResult,
    ComplianceTestResultStatusChoices,
)

VALID_RULE_CODE = "def test_ntp(configuration):\n    assert 'ntp' in configuration"


class DeviceComplianceTabTest(TestCase):
    """Confirm the Compliance tab renders on the Device detail page, with and without results."""

    @classmethod
    def setUpTestData(cls):
        device_ct = ContentType.objects.get_for_model(Device)
        location_ct = ContentType.objects.get_for_model(Location)

        manufacturer = Manufacturer.objects.create(name="Tab Test Manufacturer")
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model="Tab Test Device Type")

        location_type = LocationType.objects.create(name="Tab Test Location Type")
        location_type.content_types.add(device_ct)

        location_status = Status.objects.create(name="Tab Test Location Status")
        location_status.content_types.add(location_ct)
        location = Location.objects.create(
            name="Tab Test Location",
            location_type=location_type,
            status=location_status,
        )

        device_role = Role.objects.create(name="Tab Test Device Role")
        device_role.content_types.add(device_ct)

        device_status = Status.objects.create(name="Tab Test Device Status")
        device_status.content_types.add(device_ct)

        cls.device_with_results = Device.objects.create(
            name="Tab Test Device With Results",
            device_type=device_type,
            role=device_role,
            location=location,
            status=device_status,
        )
        cls.device_without_results = Device.objects.create(
            name="Tab Test Device Without Results",
            device_type=device_type,
            role=device_role,
            location=location,
            status=device_status,
        )

        cls.rule = ComplianceRule.objects.create(
            name="Tab Test Rule",
            rule_code=VALID_RULE_CODE,
        )

        ComplianceTestResult.objects.create(
            rule=cls.rule,
            device=cls.device_with_results,
            status=ComplianceTestResultStatusChoices.FAIL,
            output="ntp is not configured",
        )

    def test_device_page_shows_compliance_tab_link(self):
        """The Device detail page itself shows a link to the Compliance tab.

        The tab's content is *not* checked here: it renders on its own page (see
        DeviceComplianceTabView), not inline on the Device detail page -- this is a
        DistinctViewTab, so the Device page carries only the link (see template_content.py
        for why a distinct view is used).
        """
        self.add_permissions("dcim.view_device")

        url = reverse("dcim:device", kwargs={"pk": self.device_with_results.pk})
        response = self.client.get(url)

        self.assertHttpStatus(response, 200)
        content = extract_page_body(response.content.decode(response.charset))
        self.assertIn("Compliance", content)
        expected_tab_url = reverse(
            "plugins:nautobot_pytest_compliance_rule_engine:device_compliance_tab",
            kwargs={"pk": self.device_with_results.pk},
        )
        self.assertIn(expected_tab_url, content)

    def test_device_with_results_tab_shows_content(self):
        """A device with ComplianceTestResults shows those results on its Compliance tab page."""
        self.add_permissions("dcim.view_device")
        self.add_permissions("nautobot_pytest_compliance_rule_engine.view_compliancetestresult")

        url = reverse(
            "plugins:nautobot_pytest_compliance_rule_engine:device_compliance_tab",
            kwargs={"pk": self.device_with_results.pk},
        )
        response = self.client.get(url)

        self.assertHttpStatus(response, 200)
        content = extract_page_body(response.content.decode(response.charset))
        self.assertIn("Tab Test Rule", content)
        self.assertIn("ntp is not configured", content)

    def test_device_without_results_tab_shows_empty_state(self):
        """A device with no ComplianceTestResults still shows its Compliance tab page, with no error."""
        self.add_permissions("dcim.view_device")
        self.add_permissions("nautobot_pytest_compliance_rule_engine.view_compliancetestresult")

        url = reverse(
            "plugins:nautobot_pytest_compliance_rule_engine:device_compliance_tab",
            kwargs={"pk": self.device_without_results.pk},
        )
        response = self.client.get(url)

        self.assertHttpStatus(response, 200)
        content = extract_page_body(response.content.decode(response.charset))
        self.assertNotIn("Tab Test Rule", content)
