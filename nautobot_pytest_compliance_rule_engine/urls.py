"""Django urlpatterns declaration for nautobot_pytest_compliance_rule_engine app."""

from nautobot.apps.urls import NautobotUIViewSetRouter

from nautobot_pytest_compliance_rule_engine import views

router = NautobotUIViewSetRouter()
router.register("compliance-rules", views.ComplianceRuleUIViewSet)
router.register("compliance-rule-sets", views.ComplianceRuleSetUIViewSet)
router.register("compliance-results", views.ComplianceTestResultUIViewSet)

urlpatterns = router.urls
