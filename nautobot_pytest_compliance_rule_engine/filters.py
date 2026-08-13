"""Filters for nautobot_pytest_compliance_rule_engine."""

from nautobot.apps.filters import NaturalKeyOrPKMultipleChoiceFilter, NautobotFilterSet, SearchFilter
from nautobot.dcim.models import Platform

from nautobot_pytest_compliance_rule_engine.models import ComplianceRule, ComplianceRuleSet


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
