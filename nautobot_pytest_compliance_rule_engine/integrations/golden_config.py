"""Optional integration with the Golden Config app (nautobot-plugin-golden-config).

Golden Config is not a dependency of this app -- it is not listed in
`pyproject.toml` and nothing here imports `nautobot_golden_config` at module
load time. `get_latest_backup_config()` checks at runtime whether it is
installed and returns `None`, with a log message explaining why, whenever it
is not installed, has no record for the device, or has no successful backup
on record. Callers should treat `None` as "fall back to live device data
gathering", not as an error.
"""

import logging

from django.apps import apps

logger = logging.getLogger(__name__)

# The Django app label nautobot-plugin-golden-config registers itself under
# (`nautobot_golden_config.apps.GoldenConfig.name`), used both to detect
# whether it is installed and to import its models only when it is.
GOLDEN_CONFIG_APP_LABEL = "nautobot_golden_config"


def get_latest_backup_config(device):
    """Return `device`'s latest backed-up configuration from Golden Config, or `None`.

    Returns `None` when the Golden Config app is not installed, when it has no
    `GoldenConfig` record for `device`, or when that record has no backup
    config recorded yet -- each case is logged so the reason is visible.
    """
    if not apps.is_installed(GOLDEN_CONFIG_APP_LABEL):
        logger.info("Golden Config app is not installed; no backup config available for device %s.", device)
        return None

    from nautobot_golden_config.models import GoldenConfig  # pylint: disable=import-outside-toplevel

    try:
        golden_config = GoldenConfig.objects.get(device=device)
    except GoldenConfig.DoesNotExist:
        logger.info("No Golden Config record found for device %s; no backup config available.", device)
        return None

    if not golden_config.backup_config:
        logger.info("Golden Config record for device %s has no backup config recorded yet.", device)
        return None

    return golden_config.backup_config
