"""Filters for nautobot_pytest_compliance_rule_engine."""

import django_filters
from nautobot.apps.filters import BaseFilterSet, NaturalKeyOrPKMultipleChoiceFilter, NautobotFilterSet, SearchFilter
from nautobot.dcim.models import Device, Platform

from nautobot_pytest_compliance_rule_engine.models import (
    ComplianceRule,
    ComplianceRuleSet,
    ComplianceRuleSeverityChoices,
    ComplianceTestResult,
)


class ComplianceRuleFilterSet(NautobotFilterSet):
    """API/UI filterset for ComplianceRule."""

    q = SearchFilter(
        filter_predicates={
            "name": "icontains",
            "description": "icontains",
        },
    )
    platform = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=Platform.objects.all(),
        to_field_name="name",
        label="Platform (name or ID)",
    )

    class Meta:
        model = ComplianceRule
        fields = [
            "id",
            "name",
            "description",
            "severity",
            "platform",
            "enabled",
            "tags",
        ]


class ComplianceRuleSetFilterSet(NautobotFilterSet):
    """API/UI filterset for ComplianceRuleSet."""

    q = SearchFilter(
        filter_predicates={
            "name": "icontains",
            "description": "icontains",
        },
    )
    rules = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=ComplianceRule.objects.all(),
        to_field_name="name",
        label="Rules (name or ID)",
    )

    class Meta:
        model = ComplianceRuleSet
        fields = [
            "id",
            "name",
            "description",
            "rules",
            "tags",
        ]


class ComplianceTestResultFilterSet(BaseFilterSet):
    """UI filterset for the read-only ComplianceTestResult list view.

    Uses BaseFilterSet rather than NautobotFilterSet: ComplianceTestResult is a plain
    BaseModel (system-generated, not user-editable), so it has none of the
    created/last_updated, custom field, or relationship support that NautobotFilterSet's
    extra mixins assume.
    """

    q = SearchFilter(
        filter_predicates={
            "rule__name": "icontains",
            "device__name": "icontains",
            "output": "icontains",
        },
    )
    device = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=Device.objects.all(),
        to_field_name="name",
        label="Device (name or ID)",
    )
    rule = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=ComplianceRule.objects.all(),
        to_field_name="name",
        label="Rule (name or ID)",
    )
    severity = django_filters.MultipleChoiceFilter(
        field_name="rule__severity",
        choices=ComplianceRuleSeverityChoices.CHOICES,
        label="Rule severity",
    )

    class Meta:
        model = ComplianceTestResult
        fields = ["id", "device", "rule", "status", "run_datetime"]
