import uuid

import django.core.serializers.json
import nautobot.core.models.fields
import nautobot.extras.models.mixins
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("extras", "__first__"),
        ("nautobot_pytest_compliance_rule_engine", "0002_compliancetestresult"),
    ]

    operations = [
        migrations.CreateModel(
            name="ComplianceRuleSet",
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
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "_custom_field_data",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=django.core.serializers.json.DjangoJSONEncoder,
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True)),
                (
                    "rules",
                    models.ManyToManyField(
                        blank=True,
                        related_name="rule_sets",
                        to="nautobot_pytest_compliance_rule_engine.compliancerule",
                    ),
                ),
                (
                    "tags",
                    nautobot.core.models.fields.TagsField(through="extras.TaggedItem", to="extras.Tag"),
                ),
            ],
            options={
                "ordering": ["name"],
            },
            bases=(
                nautobot.extras.models.mixins.DynamicGroupMixin,
                nautobot.extras.models.mixins.NotesMixin,
                models.Model,
            ),
        ),
    ]
