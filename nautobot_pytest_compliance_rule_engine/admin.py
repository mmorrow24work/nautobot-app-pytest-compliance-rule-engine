"""Django admin definitions for nautobot_pytest_compliance_rule_engine."""

from django.contrib import admin

from nautobot_pytest_compliance_rule_engine.models import ComplianceTestResult


@admin.register(ComplianceTestResult)
class ComplianceTestResultAdmin(admin.ModelAdmin):
    """Read-only admin for ComplianceTestResult: records are created by the compliance Job, not edited by hand."""

    list_display = ["rule", "device", "status", "run_datetime", "job_result"]
    list_filter = ["status"]

    def has_add_permission(self, request):
        """Disallow creating ComplianceTestResults via the admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disallow editing ComplianceTestResults via the admin."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disallow deleting ComplianceTestResults via the admin."""
        return False
