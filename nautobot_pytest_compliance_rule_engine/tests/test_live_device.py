"""Tests for live device data gathering via NAPALM.

No test here ever attempts a real network connection: NAPALM itself is
faked out via `sys.modules`, and the driver/connection it would return are
`MagicMock` objects with canned behaviour. This module must keep working in
CI, which has no network path to real network hardware.
"""

import sys
from unittest.mock import MagicMock, patch

from django.core.exceptions import ObjectDoesNotExist
from django.test import SimpleTestCase, override_settings

from nautobot_pytest_compliance_rule_engine.integrations.live_device import (
    LiveDeviceError,
    gather_command_output,
)

FAKE_SECRET_VALUES = {"username": "admin", "password": "s3cr3t", "secret": "en4ble"}


class _FakeModuleImportError(Exception):
    """Stand-in for napalm.base.exceptions.ModuleImportError."""


def _install_fake_napalm_module(get_network_driver):
    """Register a fake `napalm` package (with `napalm.base.exceptions`) in sys.modules.

    `get_network_driver` is used directly as `napalm.get_network_driver`.
    """
    fake_exceptions_module = MagicMock()
    fake_exceptions_module.ModuleImportError = _FakeModuleImportError

    fake_base_module = MagicMock()
    fake_base_module.exceptions = fake_exceptions_module

    fake_napalm_module = MagicMock()
    fake_napalm_module.get_network_driver = get_network_driver
    fake_napalm_module.base = fake_base_module

    return patch.dict(
        sys.modules,
        {
            "napalm": fake_napalm_module,
            "napalm.base": fake_base_module,
            "napalm.base.exceptions": fake_exceptions_module,
        },
    )


def _fake_get_secret_value(access_type, secret_type, obj=None, **kwargs):  # pylint: disable=unused-argument
    return FAKE_SECRET_VALUES[secret_type]


def _make_device(napalm_driver="ios", napalm_args=None, secrets_group=None, primary_ip="10.0.0.1", name="rtr1"):
    device = MagicMock(name="device")
    device.__str__.return_value = name
    device.name = name
    device.secrets_group = secrets_group

    if napalm_driver is None:
        device.platform = None
    else:
        device.platform = MagicMock(napalm_driver=napalm_driver, napalm_args=napalm_args)

    if primary_ip:
        device.primary_ip = MagicMock()
        device.primary_ip.address.ip = primary_ip
    else:
        device.primary_ip = None

    return device


class NoPlatformOrDriverTest(SimpleTestCase):
    """A device with no usable NAPALM driver fails before anything is imported or connected."""

    def test_raises_when_device_has_no_platform_at_all(self):
        device = _make_device(napalm_driver=None)
        with self.assertRaises(LiveDeviceError) as ctx:
            gather_command_output(device, ["show version"])
        self.assertIn("no platform configured", str(ctx.exception))

    def test_raises_when_platform_has_no_napalm_driver(self):
        device = _make_device(napalm_driver="")
        with self.assertRaises(LiveDeviceError) as ctx:
            gather_command_output(device, ["show version"])
        self.assertIn("no NAPALM driver configured", str(ctx.exception))


class NapalmNotInstalledTest(SimpleTestCase):
    """NAPALM missing from the environment is a clean LiveDeviceError, not an ImportError leaking out."""

    def test_raises_when_napalm_is_not_installed(self):
        device = _make_device()
        with patch.dict(sys.modules, {"napalm": None}):
            with self.assertRaises(LiveDeviceError) as ctx:
                gather_command_output(device, ["show version"])
        self.assertIn("NAPALM is not installed", str(ctx.exception))


class NoHostTest(SimpleTestCase):
    """A device with neither a primary IP nor a name has nowhere to connect."""

    def test_raises_when_device_has_no_primary_ip_or_name(self):
        device = _make_device(primary_ip=None, name="")
        with _install_fake_napalm_module(MagicMock()):
            with self.assertRaises(LiveDeviceError) as ctx:
                gather_command_output(device, ["show version"])
        self.assertIn("no primary IP address or name", str(ctx.exception))

    def test_falls_back_to_device_name_when_no_primary_ip(self):
        device = _make_device(primary_ip=None, name="rtr1.example.com")
        fake_connection = MagicMock()
        fake_connection.cli.return_value = {"show version": "output"}
        fake_driver_class = MagicMock(return_value=fake_connection)

        with _install_fake_napalm_module(MagicMock(return_value=fake_driver_class)):
            gather_command_output(device, ["show version"])

        self.assertEqual(fake_driver_class.call_args.kwargs["hostname"], "rtr1.example.com")


@override_settings(NAPALM_USERNAME="legacy-user", NAPALM_PASSWORD="legacy-pass", NAPALM_ARGS={})
class GatherCommandOutputTest(SimpleTestCase):
    """The happy path: NAPALM is faked out, and the dict it returns from cli() is passed straight through."""

    def test_returns_command_output_dict_built_from_cli(self):
        secrets_group = MagicMock()
        secrets_group.get_secret_value.side_effect = _fake_get_secret_value
        device = _make_device(napalm_driver="ios", secrets_group=secrets_group)

        fake_connection = MagicMock()
        fake_connection.cli.return_value = {
            "show version": "Cisco IOS Software...",
            "show run": "hostname rtr1",
        }
        fake_driver_class = MagicMock(return_value=fake_connection)
        fake_get_network_driver = MagicMock(return_value=fake_driver_class)

        with _install_fake_napalm_module(fake_get_network_driver):
            result = gather_command_output(device, ["show version", "show run"])

        self.assertEqual(
            result,
            {"show version": "Cisco IOS Software...", "show run": "hostname rtr1"},
        )
        fake_get_network_driver.assert_called_once_with("ios")
        fake_connection.open.assert_called_once()
        fake_connection.cli.assert_called_once_with(["show version", "show run"])
        fake_connection.close.assert_called_once()

    def test_uses_secrets_group_credentials_and_enable_secret(self):
        secrets_group = MagicMock()
        secrets_group.get_secret_value.side_effect = _fake_get_secret_value
        device = _make_device(napalm_driver="ios", secrets_group=secrets_group)

        fake_connection = MagicMock()
        fake_connection.cli.return_value = {}
        fake_driver_class = MagicMock(return_value=fake_connection)

        with _install_fake_napalm_module(MagicMock(return_value=fake_driver_class)):
            gather_command_output(device, ["show version"])

        call_kwargs = fake_driver_class.call_args.kwargs
        self.assertEqual(call_kwargs["username"], "admin")
        self.assertEqual(call_kwargs["password"], "s3cr3t")
        self.assertEqual(call_kwargs["optional_args"]["secret"], "en4ble")

    def test_uses_enable_password_arg_name_for_eos(self):
        secrets_group = MagicMock()
        secrets_group.get_secret_value.side_effect = _fake_get_secret_value
        device = _make_device(napalm_driver="eos", secrets_group=secrets_group)

        fake_connection = MagicMock()
        fake_connection.cli.return_value = {}
        fake_driver_class = MagicMock(return_value=fake_connection)

        with _install_fake_napalm_module(MagicMock(return_value=fake_driver_class)):
            gather_command_output(device, ["show version"])

        call_kwargs = fake_driver_class.call_args.kwargs
        self.assertEqual(call_kwargs["optional_args"]["enable_password"], "en4ble")
        self.assertNotIn("secret", call_kwargs["optional_args"])

    def test_falls_back_to_napalm_settings_when_device_has_no_secrets_group(self):
        device = _make_device(napalm_driver="ios", secrets_group=None)

        fake_connection = MagicMock()
        fake_connection.cli.return_value = {}
        fake_driver_class = MagicMock(return_value=fake_connection)

        with _install_fake_napalm_module(MagicMock(return_value=fake_driver_class)):
            gather_command_output(device, ["show version"])

        call_kwargs = fake_driver_class.call_args.kwargs
        self.assertEqual(call_kwargs["username"], "legacy-user")
        self.assertEqual(call_kwargs["password"], "legacy-pass")
        self.assertNotIn("secret", call_kwargs["optional_args"])

    def test_falls_back_to_napalm_settings_when_secrets_group_defines_no_such_secret(self):
        secrets_group = MagicMock()
        secrets_group.get_secret_value.side_effect = ObjectDoesNotExist
        device = _make_device(napalm_driver="ios", secrets_group=secrets_group)

        fake_connection = MagicMock()
        fake_connection.cli.return_value = {}
        fake_driver_class = MagicMock(return_value=fake_connection)

        with _install_fake_napalm_module(MagicMock(return_value=fake_driver_class)):
            gather_command_output(device, ["show version"])

        call_kwargs = fake_driver_class.call_args.kwargs
        self.assertEqual(call_kwargs["username"], "legacy-user")
        self.assertEqual(call_kwargs["password"], "legacy-pass")
        self.assertNotIn("secret", call_kwargs["optional_args"])

    def test_merges_platform_napalm_args_with_the_napalm_args_setting(self):
        device = _make_device(napalm_driver="ios", napalm_args={"port": 2222})

        fake_connection = MagicMock()
        fake_connection.cli.return_value = {}
        fake_driver_class = MagicMock(return_value=fake_connection)

        with _install_fake_napalm_module(MagicMock(return_value=fake_driver_class)):
            gather_command_output(device, ["show version"])

        self.assertEqual(fake_driver_class.call_args.kwargs["optional_args"]["port"], 2222)

    def test_raises_when_connection_open_fails(self):
        device = _make_device(napalm_driver="ios")

        fake_connection = MagicMock()
        fake_connection.open.side_effect = OSError("no route to host")
        fake_driver_class = MagicMock(return_value=fake_connection)

        with _install_fake_napalm_module(MagicMock(return_value=fake_driver_class)):
            with self.assertRaises(LiveDeviceError) as ctx:
                gather_command_output(device, ["show version"])
        self.assertIn("Error connecting to device", str(ctx.exception))

    def test_raises_and_still_closes_when_cli_fails(self):
        device = _make_device(napalm_driver="ios")

        fake_connection = MagicMock()
        fake_connection.cli.side_effect = RuntimeError("command failed")
        fake_driver_class = MagicMock(return_value=fake_connection)

        with _install_fake_napalm_module(MagicMock(return_value=fake_driver_class)):
            with self.assertRaises(LiveDeviceError) as ctx:
                gather_command_output(device, ["show version"])
        self.assertIn("Error executing commands", str(ctx.exception))
        fake_connection.close.assert_called_once()
