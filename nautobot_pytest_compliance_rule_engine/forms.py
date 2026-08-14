"""Forms for nautobot_pytest_compliance_rule_engine."""

from django import forms
from nautobot.apps.forms import (
    BootstrapMixin,
    DateTimePicker,
    DynamicModelMultipleChoiceField,
    NautobotFilterForm,
    NautobotModelForm,
    StaticSelect2,
    StaticSelect2Multiple,
    TagFilterField,
)
from nautobot.core.forms.constants import BOOLEAN_WITH_BLANK_CHOICES
from nautobot.dcim.models import Device, Platform

from nautobot_pytest_compliance_rule_engine.models import (
    ComplianceRule,
    ComplianceRuleSet,
    ComplianceRuleSeverityChoices,
    ComplianceTestResult,
    ComplianceTestResultStatusChoices,
)


class ComplianceRuleForm(NautobotModelForm):
    """Create/update form for ComplianceRule."""

    class Meta:
        model = ComplianceRule
        fields = "__all__"
        widgets = {
            "rule_code": forms.Textarea(attrs={"class": "text-monospace", "rows": 20}),
        }


class ComplianceRuleFilterForm(NautobotFilterForm):
    """Filter form for the ComplianceRule list view."""

    model = ComplianceRule
    q = forms.CharField(required=False, label="Search")
    severity = forms.MultipleChoiceField(
        choices=ComplianceRuleSeverityChoices.CHOICES, required=False, widget=StaticSelect2Multiple()
    )
    platform = DynamicModelMultipleChoiceField(queryset=Platform.objects.all(), to_field_name="name", required=False)
    enabled = forms.NullBooleanField(required=False, widget=StaticSelect2(choices=BOOLEAN_WITH_BLANK_CHOICES))
    tags = TagFilterField(ComplianceRule)


class ComplianceRuleSetForm(NautobotModelForm):
    """Create/update form for ComplianceRuleSet."""

    rules = DynamicModelMultipleChoiceField(queryset=ComplianceRule.objects.all(), required=False)

    class Meta:
        model = ComplianceRuleSet
        fields = "__all__"


class ComplianceRuleSetFilterForm(NautobotFilterForm):
    """Filter form for the ComplianceRuleSet list view."""

    model = ComplianceRuleSet
    q = forms.CharField(required=False, label="Search")
    rules = DynamicModelMultipleChoiceField(queryset=ComplianceRule.objects.all(), to_field_name="name", required=False)
    tags = TagFilterField(ComplianceRuleSet)


class ComplianceTestResultFilterForm(BootstrapMixin, forms.Form):
    """Filter form for the read-only ComplianceTestResult list view.

    Plain BootstrapMixin form rather than NautobotFilterForm: ComplianceTestResult is a
    system-generated BaseModel with no custom fields or relationships support to filter on.
    """

    model = ComplianceTestResult
    q = forms.CharField(required=False, label="Search")
    device = DynamicModelMultipleChoiceField(queryset=Device.objects.all(), to_field_name="name", required=False)
    rule = DynamicModelMultipleChoiceField(queryset=ComplianceRule.objects.all(), to_field_name="name", required=False)
    severity = forms.MultipleChoiceField(
        choices=ComplianceRuleSeverityChoices.CHOICES, required=False, widget=StaticSelect2Multiple()
    )
    status = forms.MultipleChoiceField(
        choices=ComplianceTestResultStatusChoices.CHOICES, required=False, widget=StaticSelect2Multiple()
    )
    run_datetime__gte = forms.DateTimeField(label="Run after", required=False, widget=DateTimePicker())
    run_datetime__lte = forms.DateTimeField(label="Run before", required=False, widget=DateTimePicker())
