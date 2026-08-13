"""API serializers for nautobot_pytest_compliance_rule_engine."""

from nautobot.apps.api import NautobotModelSerializer, TaggedModelSerializerMixin

from nautobot_pytest_compliance_rule_engine.models import ComplianceRule, ComplianceRuleSet


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
