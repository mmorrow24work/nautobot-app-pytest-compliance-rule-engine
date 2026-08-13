import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dcim", "__first__"),
        ("extras", "__first__"),
        ("nautobot_pytest_compliance_rule_engine", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ComplianceTestResult",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("pass", "Pass"), ("fail", "Fail"), ("error", "Error")],
                        max_length=10,
                    ),
                ),
                (
                    "output",
                    models.TextField(
                        blank=True,
                        help_text="Assertion message or error trace captured during the run.",
                    ),
                ),
                ("run_datetime", models.DateTimeField(auto_now_add=True)),
                (
                    "device",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="compliance_test_results",
                        to="dcim.device",
                    ),
                ),
                (
                    "job_result",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="compliance_test_results",
                        to="extras.jobresult",
                    ),
                ),
                (
                    "rule",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="test_results",
                        to="nautobot_pytest_compliance_rule_engine.compliancerule",
                    ),
                ),
            ],
            options={
                "ordering": ["-run_datetime"],
            },
        ),
    ]
