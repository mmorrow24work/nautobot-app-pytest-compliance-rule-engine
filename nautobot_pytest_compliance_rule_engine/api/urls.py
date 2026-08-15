"""API URL patterns for nautobot_pytest_compliance_rule_engine app."""

from django.urls import path
from nautobot.apps.api import OrderedDefaultRouter

from . import views

router = OrderedDefaultRouter()
router.register("compliance-rules", views.ComplianceRuleViewSet)
router.register("compliance-rule-sets", views.ComplianceRuleSetViewSet)
router.register("compliance-test-results", views.ComplianceTestResultViewSet)

app_name = "nautobot_pytest_compliance_rule_engine-api"
urlpatterns = router.urls + [
    path("run-compliance-rules/", views.RunComplianceRulesAPIView.as_view(), name="run-compliance-rules"),
]
