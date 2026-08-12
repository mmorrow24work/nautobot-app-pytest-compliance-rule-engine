"""Django admin registration for nautobot_pytest_compliance_rule_engine."""

from django.contrib import admin
from nautobot.apps.admin import NautobotModelAdmin

from nautobot_pytest_compliance_rule_engine.models import ComplianceRule


@admin.register(ComplianceRule)
class ComplianceRuleAdmin(NautobotModelAdmin):
    """Admin configuration for ComplianceRule."""

    list_display = ("name", "severity", "platform", "enabled")
    list_filter = ("severity", "enabled", "platform")
    search_fields = ("name", "description")
