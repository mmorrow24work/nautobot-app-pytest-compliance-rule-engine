"""Align ComplianceRule's inherited PrimaryModel fields with their Nautobot 3.x definitions.

`ComplianceRuleSet` (added in 0003) already matches; only `ComplianceRule`, created back in
0001, still carried the older field definitions, so `makemigrations` reports it as pending
under Nautobot 3.x.

The `extras` dependency is deliberately `__first__` rather than the concrete migration name
`makemigrations` emitted. That name was the newest migration in the Nautobot release this was
generated against, and depending on it would refuse to migrate on any earlier 3.x -- including
the 3.1.7 deployment this app targets. `extras.Tag` and `extras.TaggedItem` both exist from
extras' first migration, which is all this needs, and it matches migrations 0001 and 0003.
"""

import uuid

import django.core.serializers.json
import nautobot.core.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

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
