"""Django urlpatterns declaration for nautobot_pytest_compliance_rule_engine app.

No UI views are registered yet; the router is empty scaffolding for a later
milestone.
"""

from nautobot.apps.urls import NautobotUIViewSetRouter

router = NautobotUIViewSetRouter()

urlpatterns = router.urls
