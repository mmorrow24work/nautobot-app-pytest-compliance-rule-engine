"""Views for nautobot_pytest_compliance_rule_engine."""

from nautobot.apps.views import NautobotUIViewSet, ObjectListView

from nautobot_pytest_compliance_rule_engine import forms, tables
from nautobot_pytest_compliance_rule_engine.api.serializers import ComplianceRuleSerializer, ComplianceRuleSetSerializer
from nautobot_pytest_compliance_rule_engine.filters import (
    ComplianceRuleFilterSet,
    ComplianceRuleSetFilterSet,
    ComplianceTestResultFilterSet,
)
from nautobot_pytest_compliance_rule_engine.models import ComplianceRule, ComplianceRuleSet, ComplianceTestResult


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


class ComplianceTestResultListView(ObjectListView):
    """Read-only list view for ComplianceTestResult; results are system-generated, so no add/edit/delete."""

    queryset = ComplianceTestResult.objects.select_related("rule", "device")
    filterset = ComplianceTestResultFilterSet
    filterset_form = forms.ComplianceTestResultFilterForm
    table = tables.ComplianceTestResultTable
    action_buttons = ("export",)
