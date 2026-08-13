"""API tests for ComplianceRule and ComplianceRuleSet.

Uses Nautobot's `APIViewTestCases.APIViewTestCase`, which exercises list/get/create/
update/delete both with and without the relevant object permission -- so each test
case below covers create/read/update/delete plus a permission-denied case for a user
without the right role, without hand-rolling that matrix.
"""

from django.urls import reverse
from nautobot.core.testing import APITestCase, APIViewTestCases

from nautobot_pytest_compliance_rule_engine.models import (
    ComplianceRule,
    ComplianceRuleSet,
    ComplianceRuleSeverityChoices,
)

VALID_RULE_CODE = "def test_ntp(configuration):\n    assert 'ntp' in configuration"


class AppTest(APITestCase):
    """The app's API root is reachable."""

    def test_root(self):
        url = reverse("plugins-api:nautobot_pytest_compliance_rule_engine-api:api-root")
        response = self.client.get(f"{url}?format=api", **self.header)

        self.assertEqual(response.status_code, 200)


class ComplianceRuleTest(APIViewTestCases.APIViewTestCase):
    """CRUD and permission tests for the ComplianceRule API endpoint."""

    model = ComplianceRule
    choices_fields = {"severity"}
    create_data = [
        {"name": "API Rule 4", "rule_code": VALID_RULE_CODE},
        {"name": "API Rule 5", "rule_code": VALID_RULE_CODE, "severity": ComplianceRuleSeverityChoices.HIGH},
        {"name": "API Rule 6", "rule_code": VALID_RULE_CODE, "description": "Created via the API"},
    ]
    update_data = {
        "description": "Updated via the API",
        "rule_code": VALID_RULE_CODE,
    }
    bulk_update_data = {
        "severity": ComplianceRuleSeverityChoices.LOW,
    }

    @classmethod
    def setUpTestData(cls):
        ComplianceRule.objects.create(name="API Rule 1", rule_code=VALID_RULE_CODE)
        ComplianceRule.objects.create(name="API Rule 2", rule_code=VALID_RULE_CODE)
        ComplianceRule.objects.create(name="API Rule 3", rule_code=VALID_RULE_CODE)


class ComplianceRuleSetTest(APIViewTestCases.APIViewTestCase):
    """CRUD and permission tests for the ComplianceRuleSet API endpoint."""

    model = ComplianceRuleSet
    create_data = [
        {"name": "API Rule Set 4"},
        {"name": "API Rule Set 5", "description": "Created via the API"},
        {"name": "API Rule Set 6"},
    ]
    update_data = {
        "description": "Updated via the API",
    }
    bulk_update_data = {
        "description": "Bulk updated via the API",
    }

    @classmethod
    def setUpTestData(cls):
        rule = ComplianceRule.objects.create(name="API Rule Set Member", rule_code=VALID_RULE_CODE)

        rule_set_1 = ComplianceRuleSet.objects.create(name="API Rule Set 1")
        rule_set_1.rules.add(rule)
        ComplianceRuleSet.objects.create(name="API Rule Set 2")
        ComplianceRuleSet.objects.create(name="API Rule Set 3")
