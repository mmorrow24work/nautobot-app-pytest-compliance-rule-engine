"""Tables for nautobot_pytest_compliance_rule_engine."""

import django_tables2 as tables
from django.utils.html import format_html
from nautobot.apps.tables import BaseTable, BooleanColumn, ButtonsColumn, TagColumn, ToggleColumn

from nautobot_pytest_compliance_rule_engine.models import (
    ComplianceRule,
    ComplianceRuleSet,
    ComplianceRuleSeverityChoices,
    ComplianceTestResult,
    ComplianceTestResultStatusChoices,
)


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


SEVERITY_LABEL_CSS_CLASSES = {
    ComplianceRuleSeverityChoices.LOW: "default",
    ComplianceRuleSeverityChoices.MEDIUM: "warning",
    ComplianceRuleSeverityChoices.HIGH: "danger",
}

STATUS_LABEL_CSS_CLASSES = {
    ComplianceTestResultStatusChoices.PASS: "success",
    ComplianceTestResultStatusChoices.FAIL: "danger",
    ComplianceTestResultStatusChoices.ERROR: "warning",
}

OUTPUT_TRUNCATE_LENGTH = 80


class ComplianceTestResultTable(BaseTable):
    """Read-only table for the ComplianceTestResult list view; results are system-generated, so no bulk actions."""

    device = tables.Column(linkify=True)
    rule = tables.Column(verbose_name="Rule")
    status = tables.Column()
    run_datetime = tables.Column(verbose_name="Run Time")
    output = tables.Column(orderable=False)

    class Meta(BaseTable.Meta):
        model = ComplianceTestResult
        fields = ("device", "rule", "status", "run_datetime", "output")
        default_columns = ("device", "rule", "status", "run_datetime", "output")

    def render_rule(self, record):
        """Show the rule name, linked to its detail page, with a severity badge."""
        css_class = SEVERITY_LABEL_CSS_CLASSES.get(record.rule.severity, "default")
        return format_html(
            '<a href="{}">{}</a> <span class="label label-{}">{}</span>',
            record.rule.get_absolute_url(),
            record.rule.name,
            css_class,
            record.rule.get_severity_display(),
        )

    def render_status(self, record):
        """Show the status as a color-coded badge: green=pass, red=fail, orange=error."""
        css_class = STATUS_LABEL_CSS_CLASSES.get(record.status, "default")
        return format_html('<span class="label label-{}">{}</span>', css_class, record.get_status_display())

    def render_output(self, value):
        """Truncate long output, with a native expand/collapse control to view the full text."""
        if not value:
            return "—"
        if len(value) <= OUTPUT_TRUNCATE_LENGTH:
            return value
        return format_html(
            "{}&hellip; <details><summary>view full</summary><pre>{}</pre></details>",
            value[:OUTPUT_TRUNCATE_LENGTH],
            value,
        )
