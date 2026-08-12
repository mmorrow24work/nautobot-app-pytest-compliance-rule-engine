"""Basic tests confirming the app is registered and installed correctly."""

from django.apps import apps
from django.test import TestCase


class NautobotPytestComplianceRuleEngineConfigTest(TestCase):
    """Tests for the app's Django/Nautobot registration."""

    def test_app_is_installed(self):
        """The app config should be discoverable via Django's app registry."""
        app_config = apps.get_app_config("nautobot_pytest_compliance_rule_engine")
        self.assertEqual(app_config.name, "nautobot_pytest_compliance_rule_engine")
        self.assertEqual(app_config.verbose_name, "Pytest Compliance Rule Engine")
