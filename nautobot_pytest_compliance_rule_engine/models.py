"""Models for nautobot_pytest_compliance_rule_engine."""

from django.db import models
from nautobot.apps.choices import ChoiceSet
from nautobot.apps.models import PrimaryModel
from nautobot.dcim.models import Platform
from nautobot.extras.models import TagsField


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
    tags = TagsField()

    class Meta:
        """Meta options for ComplianceRule."""

        ordering = ["name"]

    def __str__(self):
        """Return the rule's name."""
        return self.name
