"""API serializers for nautobot_pytest_compliance_rule_engine."""

from nautobot.apps.api import BaseModelSerializer, NautobotModelSerializer, TaggedModelSerializerMixin

from nautobot_pytest_compliance_rule_engine.models import ComplianceRule, ComplianceRuleSet, ComplianceTestResult


class ComplianceRuleSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):
    """Serializer for ComplianceRule, exposing all model fields."""

    class Meta:
        model = ComplianceRule
        fields = "__all__"


class ComplianceRuleSetSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):
    """Serializer for ComplianceRuleSet, exposing all model fields."""

    class Meta:
        model = ComplianceRuleSet
        fields = "__all__"


class ComplianceTestResultSerializer(BaseModelSerializer):
    """Serializer for the read-only ComplianceTestResult API endpoint.

    Uses BaseModelSerializer rather than NautobotModelSerializer: ComplianceTestResult is a
    plain BaseModel (system-generated, not user-editable), so it has none of the custom
    field, relationship, or tag support that NautobotModelSerializer's extra mixins assume.
    """

    class Meta:
        model = ComplianceTestResult
        fields = "__all__"
