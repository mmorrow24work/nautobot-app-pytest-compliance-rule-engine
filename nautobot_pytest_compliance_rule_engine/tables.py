"""Tables for nautobot_pytest_compliance_rule_engine."""

import django_tables2 as tables
from nautobot.apps.tables import BaseTable, BooleanColumn, ButtonsColumn, TagColumn, ToggleColumn

from nautobot_pytest_compliance_rule_engine.models import ComplianceRule, ComplianceRuleSet


class ComplianceRuleTable(BaseTable):
    """Table for list view of ComplianceRule objects."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    severity = tables.Column()
    enabled = BooleanColumn()
    last_updated = tables.Column()
    tags = TagColumn(url_name="plugins:nautobot_pytest_compliance_rule_engine:compliancerule_list")
    actions = ButtonsColumn(ComplianceRule)

    class Meta(BaseTable.Meta):
        model = ComplianceRule
        fields = ("pk", "name", "description", "severity", "platform", "enabled", "last_updated", "tags")
        default_columns = ("pk", "name", "severity", "platform", "enabled", "last_updated", "tags", "actions")

    def render_severity(self, record):
        """Show the human-readable severity label rather than the raw choice value."""
        return record.get_severity_display()


class ComplianceRuleSetTable(BaseTable):
    """Table for list view of ComplianceRuleSet objects."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    rule_count = tables.Column(verbose_name="Rules", accessor="rules", orderable=False)
    last_updated = tables.Column()
    tags = TagColumn(url_name="plugins:nautobot_pytest_compliance_rule_engine:complianceruleset_list")
    actions = ButtonsColumn(ComplianceRuleSet)

    class Meta(BaseTable.Meta):
        model = ComplianceRuleSet
        fields = ("pk", "name", "description", "rule_count", "last_updated", "tags")
        default_columns = ("pk", "name", "rule_count", "last_updated", "tags", "actions")

    def render_rule_count(self, value):
        """Show the number of rules assigned to this set."""
        return value.count()
