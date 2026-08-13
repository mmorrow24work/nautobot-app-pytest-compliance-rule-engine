"""Live device data gathering via NAPALM.

NAPALM is not a dependency of this app -- it is not listed in
`pyproject.toml` and nothing here imports it at module load time.
`gather_command_output()` imports it lazily and raises `LiveDeviceError` with
an explanatory message if it is not installed, mirroring how Nautobot's own
`Device.napalm()` API view (`nautobot.dcim.api.views.DeviceViewSet.napalm`)
treats NAPALM as optional.

NAPALM is the convention Nautobot itself already uses for live device access:
`Platform.napalm_driver` / `Platform.napalm_args` select the driver, the
`NAPALM_USERNAME` / `NAPALM_PASSWORD` / `NAPALM_ARGS` / `NAPALM_TIMEOUT`
settings provide defaults, and a device's `SecretsGroup` (access type
`Generic`) supplies per-device credentials -- all read here the same way that
API view reads them. This module calls the driver's `cli()` method instead of
one of NAPALM's `get_*` methods, since rules ask for raw show-command output
rather than NAPALM's parsed getters.
"""

import logging
from typing import Dict, Iterable

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from nautobot.extras.choices import SecretsGroupAccessTypeChoices, SecretsGroupSecretTypeChoices
from nautobot.extras.secrets.exceptions import SecretError

logger = logging.getLogger(__name__)


class LiveDeviceError(Exception):
    """Raised when live command output cannot be gathered from a device."""


def _get_credentials(device):
    """Return the (username, password) NAPALM should authenticate with.

    Reads the `Generic` secrets from `device.secrets_group` when the device
    has one, falling back to the `NAPALM_USERNAME` / `NAPALM_PASSWORD`
    settings for whichever secret is undefined -- the same fallback order as
    `nautobot.dcim.api.views.DeviceViewSet.napalm`.
    """
    if not device.secrets_group:
        return settings.NAPALM_USERNAME, settings.NAPALM_PASSWORD

    try:
        try:
            username = device.secrets_group.get_secret_value(
                SecretsGroupAccessTypeChoices.TYPE_GENERIC,
                SecretsGroupSecretTypeChoices.TYPE_USERNAME,
                obj=device,
            )
        except ObjectDoesNotExist:
            username = settings.NAPALM_USERNAME
        try:
            password = device.secrets_group.get_secret_value(
                SecretsGroupAccessTypeChoices.TYPE_GENERIC,
                SecretsGroupSecretTypeChoices.TYPE_PASSWORD,
                obj=device,
            )
        except ObjectDoesNotExist:
            password = settings.NAPALM_PASSWORD
    except SecretError as exc:
        raise LiveDeviceError(f"Unable to retrieve credentials for device {device}: {exc}") from exc

    return username, password


def _get_optional_args(device):
    """Return NAPALM's `optional_args`, including the enable secret if the device has one."""
    optional_args = settings.NAPALM_ARGS.copy()
    if device.platform.napalm_args:
        optional_args.update(device.platform.napalm_args)

    if device.secrets_group:
        # NAPALM drivers spell the enable-secret optional_arg inconsistently.
        enable_password_arg = "enable_password" if device.platform.napalm_driver.lower() == "eos" else "secret"
        try:
            optional_args[enable_password_arg] = device.secrets_group.get_secret_value(
                SecretsGroupAccessTypeChoices.TYPE_GENERIC,
                SecretsGroupSecretTypeChoices.TYPE_SECRET,
                obj=device,
            )
        except ObjectDoesNotExist:
            pass  # No enable secret defined for this device; that's fine.
        except SecretError as exc:
            raise LiveDeviceError(f"Unable to retrieve enable secret for device {device}: {exc}") from exc

    return optional_args


def _get_host(device):
    """Return the address NAPALM should connect to: the device's primary IP, or else its name."""
    if device.primary_ip:
        return str(device.primary_ip.address.ip)
    if device.name:
        return device.name
    raise LiveDeviceError(f"Device {device} has no primary IP address or name to connect to.")


def gather_command_output(device, commands: Iterable[str]) -> Dict[str, str]:
    """Connect to `device` over NAPALM and return `{command: output_text}` for each of `commands`.

    `device` must have a `Platform` with a `napalm_driver` configured. Credentials
    are read from `device.secrets_group` (falling back to the `NAPALM_USERNAME` /
    `NAPALM_PASSWORD` settings for any secret it does not define), the same way
    Nautobot's own `Device.napalm()` API view reads them.

    Raises `LiveDeviceError` if the device has no usable platform/driver, no
    address to connect to, NAPALM is not installed, or the connection or
    command execution fails. Never attempts to connect in the absence of a
    real network path -- callers running in CI must mock this function or the
    NAPALM driver it imports.
    """
    if device.platform is None:
        raise LiveDeviceError(f"Device {device} has no platform configured; cannot determine a NAPALM driver.")
    if not device.platform.napalm_driver:
        raise LiveDeviceError(f"Platform {device.platform} has no NAPALM driver configured.")

    try:
        import napalm
        from napalm.base.exceptions import ModuleImportError as NapalmModuleImportError
    except ModuleNotFoundError as exc:
        if getattr(exc, "name", None) == "napalm":
            raise LiveDeviceError("NAPALM is not installed.") from exc
        raise

    try:
        driver = napalm.get_network_driver(device.platform.napalm_driver)
    except NapalmModuleImportError as exc:
        raise LiveDeviceError(
            f"NAPALM driver for platform {device.platform} not found: {device.platform.napalm_driver}."
        ) from exc

    host = _get_host(device)
    username, password = _get_credentials(device)
    optional_args = _get_optional_args(device)

    connection = driver(
        hostname=host,
        username=username,
        password=password,
        timeout=settings.NAPALM_TIMEOUT,
        optional_args=optional_args,
    )
    try:
        connection.open()
    except Exception as exc:
        raise LiveDeviceError(f"Error connecting to device {device} at {host}: {exc}") from exc

    try:
        return connection.cli(list(commands))
    except Exception as exc:
        raise LiveDeviceError(f"Error executing commands on device {device}: {exc}") from exc
    finally:
        connection.close()
