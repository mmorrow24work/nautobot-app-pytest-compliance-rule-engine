"""Django urlpatterns declaration for nautobot_pytest_compliance_rule_engine app."""

from django.urls import path
from nautobot.apps.urls import NautobotUIViewSetRouter

from nautobot_pytest_compliance_rule_engine import views

router = NautobotUIViewSetRouter()
router.register("compliance-rules", views.ComplianceRuleUIViewSet)
router.register("compliance-rule-sets", views.ComplianceRuleSetUIViewSet)

urlpatterns = [
    path(
        "compliance-results/",
        views.ComplianceTestResultListView.as_view(),
        name="compliancetestresult_list",
    ),
] + router.urls
