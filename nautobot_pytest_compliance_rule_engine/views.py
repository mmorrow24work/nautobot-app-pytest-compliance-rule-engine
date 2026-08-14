"""Views for nautobot_pytest_compliance_rule_engine."""

from nautobot.apps.views import NautobotUIViewSet

from nautobot_pytest_compliance_rule_engine import forms, tables
from nautobot_pytest_compliance_rule_engine.api.serializers import ComplianceRuleSerializer, ComplianceRuleSetSerializer
from nautobot_pytest_compliance_rule_engine.filters import ComplianceRuleFilterSet, ComplianceRuleSetFilterSet
from nautobot_pytest_compliance_rule_engine.models import ComplianceRule, ComplianceRuleSet


class ComplianceRuleUIViewSet(NautobotUIViewSet):
    """List/detail/edit/delete views for ComplianceRule."""

    queryset = ComplianceRule.objects.all()
    filterset_class = ComplianceRuleFilterSet
    filterset_form_class = forms.ComplianceRuleFilterForm
    form_class = forms.ComplianceRuleForm
    serializer_class = ComplianceRuleSerializer
    table_class = tables.ComplianceRuleTable


class ComplianceRuleSetUIViewSet(NautobotUIViewSet):
    """List/detail/edit/delete views for ComplianceRuleSet."""

    queryset = ComplianceRuleSet.objects.all()
    filterset_class = ComplianceRuleSetFilterSet
    filterset_form_class = forms.ComplianceRuleSetFilterForm
    form_class = forms.ComplianceRuleSetForm
    serializer_class = ComplianceRuleSetSerializer
    table_class = tables.ComplianceRuleSetTable
