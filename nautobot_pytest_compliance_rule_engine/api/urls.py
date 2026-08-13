"""API URL patterns for nautobot_pytest_compliance_rule_engine app."""

from nautobot.apps.api import OrderedDefaultRouter

from . import views

router = OrderedDefaultRouter()
router.register("compliance-rules", views.ComplianceRuleViewSet)
router.register("compliance-rule-sets", views.ComplianceRuleSetViewSet)

app_name = "nautobot_pytest_compliance_rule_engine-api"
urlpatterns = router.urls
