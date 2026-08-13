"""Tests for the RunComplianceRules Job's input form and device queryset resolution."""

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from nautobot.dcim.models import Device, DeviceType, Location, LocationType, Manufacturer, Platform
from nautobot.extras.models import Role, Status, Tag

from nautobot_pytest_compliance_rule_engine.jobs.run_compliance import RunComplianceRules
from nautobot_pytest_compliance_rule_engine.models import ComplianceRuleSet


class RunComplianceRulesJobTest(TestCase):
    """Tests for the RunComplianceRules Job's input form and device queryset resolution."""

    @classmethod
    def setUpTestData(cls):
        """Build two Locations, two Roles, two Platforms, a Tag, and Devices that partially overlap the filters."""
        device_ct = ContentType.objects.get_for_model(Device)
        location_ct = ContentType.objects.get_for_model(Location)

        manufacturer = Manufacturer.objects.create(name="Test Manufacturer")
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model="Test Device Type")

        location_type = LocationType.objects.create(name="Test Location Type")
        location_type.content_types.add(device_ct)
        location_status = Status.objects.create(name="Test Location Status")
        location_status.content_types.add(location_ct)
        cls.location_1 = Location.objects.create(
            name="Test Location 1", location_type=location_type, status=location_status
        )
        cls.location_2 = Location.objects.create(
            name="Test Location 2", location_type=location_type, status=location_status
        )

        cls.role_1 = Role.objects.create(name="Test Role 1")
        cls.role_1.content_types.add(device_ct)
        cls.role_2 = Role.objects.create(name="Test Role 2")
        cls.role_2.content_types.add(device_ct)

        cls.platform_1 = Platform.objects.create(name="Test Platform 1")
        cls.platform_2 = Platform.objects.create(name="Test Platform 2")

        cls.tag = Tag.objects.create(name="Test Tag")
        cls.tag.content_types.add(device_ct)

        device_status = Status.objects.create(name="Test Device Status")
        device_status.content_types.add(device_ct)

        cls.matching_device = Device.objects.create(
            name="Matching Device",
            device_type=device_type,
            role=cls.role_1,
            platform=cls.platform_1,
            location=cls.location_1,
            status=device_status,
        )
        cls.matching_device.tags.add(cls.tag)

        cls.wrong_role_device = Device.objects.create(
            name="Wrong Role Device",
            device_type=device_type,
            role=cls.role_2,
            platform=cls.platform_1,
            location=cls.location_1,
            status=device_status,
        )

        cls.wrong_location_device = Device.objects.create(
            name="Wrong Location Device",
            device_type=device_type,
            role=cls.role_1,
            platform=cls.platform_1,
            location=cls.location_2,
            status=device_status,
        )

        cls.untagged_device = Device.objects.create(
            name="Untagged Device",
            device_type=device_type,
            role=cls.role_1,
            platform=cls.platform_1,
            location=cls.location_1,
            status=device_status,
        )

        cls.rule_set = ComplianceRuleSet.objects.create(name="Test Rule Set")

    def test_form_validates_with_sample_filter_inputs(self):
        """The Job's generated form accepts a full set of sample filter inputs."""
        form_class = RunComplianceRules.as_form_class()
        form = form_class(
            data={
                "location": [str(self.location_1.pk)],
                "role": [str(self.role_1.pk)],
                "platform": [str(self.platform_1.pk)],
                "tag": [str(self.tag.pk)],
                "rule_set": str(self.rule_set.pk),
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_form_validates_with_no_filters_selected(self):
        """The Job's form is valid when only the required rule_set is supplied and all filters are left blank."""
        form_class = RunComplianceRules.as_form_class()
        form = form_class(data={"rule_set": str(self.rule_set.pk)})

        self.assertTrue(form.is_valid(), form.errors)

    def test_form_requires_rule_set(self):
        """The Job's form rejects submissions missing the required rule_set."""
        form_class = RunComplianceRules.as_form_class()
        form = form_class(data={})

        self.assertFalse(form.is_valid())
        self.assertIn("rule_set", form.errors)

    def test_get_device_queryset_resolves_intersection_of_filters(self):
        """get_device_queryset filters devices by the intersection of location, role, platform, and tag."""
        job = RunComplianceRules()

        queryset = job.get_device_queryset(
            location=Location.objects.filter(pk=self.location_1.pk),
            role=Role.objects.filter(pk=self.role_1.pk),
            platform=Platform.objects.filter(pk=self.platform_1.pk),
            tag=Tag.objects.filter(pk=self.tag.pk),
        )

        self.assertEqual(list(queryset), [self.matching_device])

    def test_get_device_queryset_with_no_filters_returns_all_devices(self):
        """Leaving every filter blank (empty querysets) resolves to every Device."""
        job = RunComplianceRules()

        queryset = job.get_device_queryset(
            location=Location.objects.none(),
            role=Role.objects.none(),
            platform=Platform.objects.none(),
            tag=Tag.objects.none(),
        )

        self.assertEqual(queryset.count(), Device.objects.count())

    def test_get_device_queryset_filters_by_role_only(self):
        """Supplying only a role filter excludes devices with a different role."""
        job = RunComplianceRules()

        queryset = job.get_device_queryset(
            location=Location.objects.none(),
            role=Role.objects.filter(pk=self.role_1.pk),
            platform=Platform.objects.none(),
            tag=Tag.objects.none(),
        )

        self.assertIn(self.matching_device, queryset)
        self.assertIn(self.wrong_location_device, queryset)
        self.assertIn(self.untagged_device, queryset)
        self.assertNotIn(self.wrong_role_device, queryset)

    def test_run_logs_and_returns_resolved_device_count(self):
        """run() resolves the device queryset for the given filters and returns a summary."""
        job = RunComplianceRules()

        result = job.run(
            location=Location.objects.filter(pk=self.location_1.pk),
            role=Role.objects.filter(pk=self.role_1.pk),
            platform=Platform.objects.filter(pk=self.platform_1.pk),
            tag=Tag.objects.none(),
            rule_set=self.rule_set,
        )

        self.assertEqual(result, {"device_count": 2, "rule_set": "Test Rule Set"})
