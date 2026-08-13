"""Models for nautobot_pytest_compliance_rule_engine."""

from django.core.exceptions import ValidationError
from django.db import models
from nautobot.apps.choices import ChoiceSet
from nautobot.apps.models import BaseModel, PrimaryModel
from nautobot.dcim.models import Device, Platform
from nautobot.extras.models import JobResult

from nautobot_pytest_compliance_rule_engine.validation import validate_rule_code


class ComplianceRuleSeverityChoices(ChoiceSet):
    """Severity levels for a ComplianceRule, mirroring Netpicker's @low/@medium/@high pattern."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    CHOICES = (
        (LOW, "Low"),
        (MEDIUM, "Medium"),
        (HIGH, "High"),
    )


class ComplianceRule(PrimaryModel):
    """A single compliance rule: a pytest-style Python snippet run against device data."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    severity = models.CharField(
        max_length=10,
        choices=ComplianceRuleSeverityChoices.CHOICES,
        default=ComplianceRuleSeverityChoices.MEDIUM,
    )
    platform = models.ForeignKey(
        to=Platform,
        on_delete=models.SET_NULL,
        related_name="compliance_rules",
        null=True,
        blank=True,
        help_text="Platform this rule applies to; leave blank to apply to all platforms.",
    )
    rule_code = models.TextField(help_text="Python/pytest function body executed by the compliance engine.")
    enabled = models.BooleanField(default=True)

    class Meta:
        """Meta options for ComplianceRule."""

        ordering = ["name"]

    def clean(self):
        """Statically reject unsafe rule_code before the rule can be saved.

        Runs wherever `full_clean()` runs -- forms, API serializers, and
        `validated_save()`. A direct `objects.create()` bypasses it; see the
        limitations documented in `validation.py`.
        """
        super().clean()
        try:
            validate_rule_code(self.rule_code)
        except ValidationError as exc:
            # Re-key onto the field so forms and serializers show the error against rule_code.
            raise ValidationError({"rule_code": exc.messages}) from exc

    def __str__(self):
        """Return the rule's name."""
        return self.name


class ComplianceTestResultStatusChoices(ChoiceSet):
    """Outcome of running a ComplianceRule against a Device."""

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"

    CHOICES = (
        (PASS, "Pass"),
        (FAIL, "Fail"),
        (ERROR, "Error"),
    )


class ComplianceTestResult(BaseModel):
    """The recorded outcome of running a single ComplianceRule against a single Device.

    Created by the RunComplianceRules Job (M3); not intended to be created or edited via UI forms.
    """

    rule = models.ForeignKey(
        to=ComplianceRule,
        on_delete=models.CASCADE,
        related_name="test_results",
    )
    device = models.ForeignKey(
        to=Device,
        on_delete=models.CASCADE,
        related_name="compliance_test_results",
    )
    status = models.CharField(
        max_length=10,
        choices=ComplianceTestResultStatusChoices.CHOICES,
    )
    output = models.TextField(blank=True, help_text="Assertion message or error trace captured during the run.")
    run_datetime = models.DateTimeField(auto_now_add=True)
    job_result = models.ForeignKey(
        to=JobResult,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="compliance_test_results",
    )

    class Meta:
        """Meta options for ComplianceTestResult."""

        ordering = ["-run_datetime"]

    def __str__(self):
        """Return a summary of the rule, device, and status."""
        return f"{self.rule} - {self.device} - {self.status}"


class ComplianceRuleSet(PrimaryModel):
    """A named group of ComplianceRules that can be assigned to a Job run as a unit."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    rules = models.ManyToManyField(
        to=ComplianceRule,
        related_name="rule_sets",
        blank=True,
    )

    class Meta:
        """Meta options for ComplianceRuleSet."""

        ordering = ["name"]

    def __str__(self):
        """Return the rule set's name."""
        return self.name
