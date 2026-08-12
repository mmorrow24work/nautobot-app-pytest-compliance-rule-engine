import uuid

import django.db.models.deletion
import nautobot.extras.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("dcim", "0001_initial"),
        ("extras", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ComplianceRule",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "_custom_field_data",
                    models.JSONField(blank=True, default=dict, editable=False),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True)),
                (
                    "severity",
                    models.CharField(
                        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")],
                        default="medium",
                        max_length=10,
                    ),
                ),
                (
                    "rule_code",
                    models.TextField(
                        help_text="Python/pytest function body executed by the compliance engine."
                    ),
                ),
                ("enabled", models.BooleanField(default=True)),
                (
                    "platform",
                    models.ForeignKey(
                        blank=True,
                        help_text="Platform this rule applies to; leave blank to apply to all platforms.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="compliance_rules",
                        to="dcim.platform",
                    ),
                ),
                (
                    "tags",
                    nautobot.extras.models.TagsField(through="extras.TaggedItem", to="extras.tag"),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
    ]
