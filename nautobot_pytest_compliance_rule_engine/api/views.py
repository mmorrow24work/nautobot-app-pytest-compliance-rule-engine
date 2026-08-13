"""API views for nautobot_pytest_compliance_rule_engine."""

from nautobot.apps.api import NautobotModelViewSet

from nautobot_pytest_compliance_rule_engine.filters import ComplianceRuleFilterSet, ComplianceRuleSetFilterSet
from nautobot_pytest_compliance_rule_engine.models import ComplianceRule, ComplianceRuleSet

from . import serializers


class ComplianceRuleViewSet(NautobotModelViewSet):
    """CRUD API endpoint for ComplianceRule.

    Relies on NautobotModelViewSet's default queryset restriction, so the
    same object-level RBAC that gates the UI gates this endpoint too --
    no separate permission model is introduced here.
    """

    queryset = ComplianceRule.objects.all()
    serializer_class = serializers.ComplianceRuleSerializer
    filterset_class = ComplianceRuleFilterSet


class ComplianceRuleSetViewSet(NautobotModelViewSet):
    """CRUD API endpoint for ComplianceRuleSet.

    Relies on NautobotModelViewSet's default queryset restriction, so the
    same object-level RBAC that gates the UI gates this endpoint too --
    no separate permission model is introduced here.
    """

    queryset = ComplianceRuleSet.objects.all()
    serializer_class = serializers.ComplianceRuleSetSerializer
    filterset_class = ComplianceRuleSetFilterSet
