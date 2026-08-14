"""App declaration for nautobot_pytest_compliance_rule_engine."""

from importlib import metadata

from nautobot.apps import NautobotAppConfig

__version__ = metadata.version(__name__)


class NautobotPytestComplianceRuleEngineConfig(NautobotAppConfig):
    """App configuration for the nautobot_pytest_compliance_rule_engine app."""

    name = "nautobot_pytest_compliance_rule_engine"
    verbose_name = "Pytest Compliance Rule Engine"
    version = __version__
    author = "Mick Morrow"
    description = (
        "Define compliance rules as pytest-style Python snippets and run them against device data "
        "as a Nautobot Job, recording pass/fail results."
    )
    base_url = "pytest-compliance-rule-engine"
    required_settings = []
    min_version = "3.0.0"
    max_version = "3.9999"
    default_settings = {}
    caching_config = {}


config = NautobotPytestComplianceRuleEngineConfig
