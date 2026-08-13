"""Tests for the optional Golden Config integration."""

import sys
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from nautobot_pytest_compliance_rule_engine.integrations.golden_config import (
    GOLDEN_CONFIG_APP_LABEL,
    get_latest_backup_config,
)


class _FakeDoesNotExist(Exception):
    """Stand-in for GoldenConfig.DoesNotExist."""


def _install_fake_golden_config_module(get_side_effect):
    """Register a fake nautobot_golden_config.models module in sys.modules.

    `get_side_effect` is used as the side_effect of GoldenConfig.objects.get(),
    so tests can make it return a record or raise DoesNotExist.
    """
    fake_golden_config_model = MagicMock()
    fake_golden_config_model.DoesNotExist = _FakeDoesNotExist
    fake_golden_config_model.objects.get.side_effect = get_side_effect

    fake_models_module = MagicMock()
    fake_models_module.GoldenConfig = fake_golden_config_model

    fake_package = MagicMock()

    return patch.dict(
        sys.modules,
        {
            "nautobot_golden_config": fake_package,
            "nautobot_golden_config.models": fake_models_module,
        },
    )


class GoldenConfigNotInstalledTest(SimpleTestCase):
    """When the Golden Config app is not installed, the helper returns None without importing it."""

    def test_returns_none_and_never_imports_the_app(self):
        """apps.is_installed() False short-circuits before nautobot_golden_config is touched."""
        device = MagicMock(name="device")
        with patch(
            "nautobot_pytest_compliance_rule_engine.integrations.golden_config.apps.is_installed",
            return_value=False,
        ) as mock_is_installed:
            result = get_latest_backup_config(device)

        self.assertIsNone(result)
        mock_is_installed.assert_called_once_with(GOLDEN_CONFIG_APP_LABEL)
        self.assertNotIn("nautobot_golden_config", sys.modules)


class GoldenConfigInstalledTest(SimpleTestCase):
    """When the Golden Config app is installed, the helper queries its GoldenConfig model."""

    def test_returns_backup_config_when_a_record_exists(self):
        """A GoldenConfig record with backup_config set returns that content."""
        device = MagicMock(name="device")
        fake_record = MagicMock(backup_config="hostname r1\nntp server 10.0.0.1\n")

        with (
            patch(
                "nautobot_pytest_compliance_rule_engine.integrations.golden_config.apps.is_installed",
                return_value=True,
            ),
            _install_fake_golden_config_module(get_side_effect=lambda device: fake_record),
        ):
            result = get_latest_backup_config(device)

        self.assertEqual(result, "hostname r1\nntp server 10.0.0.1\n")

    def test_returns_none_when_no_record_exists_for_the_device(self):
        """A device with no GoldenConfig record at all returns None."""
        device = MagicMock(name="device")

        with (
            patch(
                "nautobot_pytest_compliance_rule_engine.integrations.golden_config.apps.is_installed",
                return_value=True,
            ),
            _install_fake_golden_config_module(get_side_effect=_FakeDoesNotExist),
        ):
            result = get_latest_backup_config(device)

        self.assertIsNone(result)

    def test_returns_none_when_the_record_has_no_backup_yet(self):
        """A GoldenConfig record whose backup_config is still empty returns None."""
        device = MagicMock(name="device")
        fake_record = MagicMock(backup_config="")

        with (
            patch(
                "nautobot_pytest_compliance_rule_engine.integrations.golden_config.apps.is_installed",
                return_value=True,
            ),
            _install_fake_golden_config_module(get_side_effect=lambda device: fake_record),
        ):
            result = get_latest_backup_config(device)

        self.assertIsNone(result)
