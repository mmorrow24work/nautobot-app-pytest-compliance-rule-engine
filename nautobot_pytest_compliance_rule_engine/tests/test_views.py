"""UI view tests for ComplianceRule and ComplianceRuleSet.

Uses Nautobot's `ViewTestCases`, which exercises get/create/edit/delete/list/bulk-delete
both with and without the relevant object permission -- so each test case below covers
a 200 for a superuser and a 403/404 for a permission-restricted user without hand-rolling
that matrix. Bulk-edit is intentionally not exercised here since no BulkEditForm is
defined for these models.
"""

from nautobot.core.testing import ViewTestCases

from nautobot_pytest_compliance_rule_engine.models import (
    ComplianceRule,
    ComplianceRuleSet,
    ComplianceRuleSeverityChoices,
)

VALID_RULE_CODE = "def test_ntp(configuration):\n    assert 'ntp' in configuration"


class ComplianceRuleViewTest(
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.GetObjectNotesViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    """CRUD and permission tests for the ComplianceRule UI views."""

    model = ComplianceRule

    @classmethod
    def setUpTestData(cls):
        ComplianceRule.objects.create(name="View Rule 1", rule_code=VALID_RULE_CODE)
        ComplianceRule.objects.create(name="View Rule 2", rule_code=VALID_RULE_CODE)
        ComplianceRule.objects.create(name="View Rule 3", rule_code=VALID_RULE_CODE)
        ComplianceRule.objects.create(name="View Rule 4", rule_code=VALID_RULE_CODE)

        cls.form_data = {
            "name": "View Rule 5",
            "description": "Created via the UI",
            "severity": ComplianceRuleSeverityChoices.HIGH,
            "rule_code": VALID_RULE_CODE,
            "enabled": True,
            "tags": [],
        }


class ComplianceRuleSetViewTest(
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.GetObjectNotesViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    """CRUD and permission tests for the ComplianceRuleSet UI views."""

    model = ComplianceRuleSet

    @classmethod
    def setUpTestData(cls):
        rule = ComplianceRule.objects.create(name="View Rule Set Member", rule_code=VALID_RULE_CODE)

        rule_set_1 = ComplianceRuleSet.objects.create(name="View Rule Set 1")
        rule_set_1.rules.add(rule)
        ComplianceRuleSet.objects.create(name="View Rule Set 2")
        ComplianceRuleSet.objects.create(name="View Rule Set 3")
        ComplianceRuleSet.objects.create(name="View Rule Set 4")

        cls.form_data = {
            "name": "View Rule Set 5",
            "description": "Created via the UI",
            "rules": [rule.pk],
            "tags": [],
        }
