"""Align ComplianceRule's inherited base fields with what Nautobot 3.x's PrimaryModel declares.

Migration 0001 recorded these three fields as they were declared by the Nautobot version
current when it was written; 0003 (ComplianceRuleSet) already matches the newer
declarations. Under Nautobot 3.x, `makemigrations` reports ComplianceRule as drifted, so
this brings it back in line:

- `_custom_field_data` gains the `DjangoJSONEncoder` and drops `editable=False`
- `id` gains `unique=True`
- `tags` differs only in the capitalization of its `to=` label

Only `_custom_field_data` and `id` are real schema changes; the `tags` operation is a
state-only relabel.
"""

import uuid

import django.core.serializers.json
import nautobot.core.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    # `extras` is referenced only so that `Tag`/`TaggedItem` exist for the TagsField below.
    # Deliberately `__first__` rather than the concrete migration Django auto-selects: pinning
    # a specific `extras` migration name would tie this app to the exact Nautobot patch release
    # it was generated against and break loading on any release with a shorter `extras` history.
    dependencies = [
        ("extras", "__first__"),
        ("nautobot_pytest_compliance_rule_engine", "0003_complianceruleset"),
    ]

    operations = [
        migrations.AlterField(
            model_name="compliancerule",
            name="_custom_field_data",
            field=models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
        ),
        migrations.AlterField(
            model_name="compliancerule",
            name="id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True),
        ),
        migrations.AlterField(
            model_name="compliancerule",
            name="tags",
            field=nautobot.core.models.fields.TagsField(through="extras.TaggedItem", to="extras.Tag"),
        ),
    ]
