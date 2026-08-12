"""API URL patterns for nautobot_pytest_compliance_rule_engine app.

No viewsets are registered yet; the router is empty scaffolding for a later
milestone.
"""

from nautobot.apps.api import OrderedDefaultRouter

router = OrderedDefaultRouter()

app_name = "nautobot_pytest_compliance_rule_engine-api"
urlpatterns = router.urls
