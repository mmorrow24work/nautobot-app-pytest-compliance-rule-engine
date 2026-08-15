"""End-to-end integration test for the full M5 API surface.

Unlike `tests/test_api.py`, which exercises each endpoint in isolation, this drives the
whole flow through the REST API exactly as an external caller (e.g. a CI/CD pipeline)
would: create a ComplianceRule, create a ComplianceRuleSet containing it, trigger a run
via the job-trigger endpoint, poll the resulting JobResult, then confirm
ComplianceTestResult rows are retrievable via the read-only endpoint.

The job-trigger endpoint's own enqueue call (`JobResult.enqueue_job()`) defers Celery
dispatch to a `transaction.on_commit()` callback that calls `run_job.apply_async()`, which
in production is picked up by a live Celery worker. There is no worker in this test
environment (nor in CI's), so steps 1-3 below verify the trigger endpoint's real wiring
-- rule/rule-set creation, permission and validation, JobResult creation and shape -- and
stop at confirming the JobResult is queued (PENDING), the same boundary Nautobot's own
`JobViewSet.run()` API tests stop at. To then exercise the "poll -> confirm results
retrievable" half of the flow with real data, step 4 runs the Job to completion through
Nautobot's `create_job_result_and_run_job()` test utility -- the same synchronous,
worker-free execution path `test_job_integration.py` uses -- against the same
API-created rule set, so the read-only endpoint in step 5 is verified against real,
Job-produced rows rather than hand-inserted fixtures.

Device data gathering is mocked via the same integration point
`test_job_integration.py` uses (`get_latest_backup_config`); no live connections are made.
"""

from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from nautobot.apps.choices import JobResultStatusChoices
from nautobot.core.testing import create_job_result_and_run_job
from nautobot.core.testing.api import APITransactionTestCase
from nautobot.dcim.models import Device, DeviceType, Location, LocationType, Manufacturer
from nautobot.extras.models import Job as JobModel
from nautobot.extras.models import Role, Status
from rest_framework import status

from nautobot_pytest_compliance_rule_engine.jobs.run_compliance import RunComplianceRules

JOB_MODULE = "nautobot_pytest_compliance_rule_engine.jobs.run_compliance"
JOB_NAME = "RunComplianceRules"

NTP_RULE_CODE = "def check_ntp(configuration):\n    assert 'ntp server' in configuration, 'no NTP server configured'"
GOLDEN_CONFIG = "hostname r1\nntp server 10.0.0.1\n"


class APIIntegrationTest(APITransactionTestCase):
    """Full create-rule -> create-rule-set -> trigger-run -> poll -> read-results flow, via the API.

    `APITransactionTestCase`'s user is a superuser, so this exercises the full flow without
    also re-testing per-endpoint permission enforcement -- that's already covered in
    `test_api.py`.
    """

    databases = ("default", "job_logs")

    def setUp(self):
        super().setUp()

        device_ct = ContentType.objects.get_for_model(Device)
        location_ct = ContentType.objects.get_for_model(Location)

        manufacturer = Manufacturer.objects.create(name="Integration Manufacturer")
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model="Integration Device Type")

        location_type = LocationType.objects.create(name="Integration Location Type")
        location_type.content_types.add(device_ct)
        location_status = Status.objects.create(name="Integration Location Status")
        location_status.content_types.add(location_ct)
        location = Location.objects.create(
            name="Integration Location", location_type=location_type, status=location_status
        )

        role = Role.objects.create(name="Integration Role")
        role.content_types.add(device_ct)

        device_status = Status.objects.create(name="Integration Device Status")
        device_status.content_types.add(device_ct)

        self.device = Device.objects.create(
            name="r1",
            device_type=device_type,
            role=role,
            location=location,
            status=device_status,
        )

        # Nautobot ships every Job disabled until an admin opts it in; enable it here so
        # the trigger endpoint's "is this job enabled" guard doesn't block the run.
        job_model = JobModel.objects.get(
            module_name=RunComplianceRules.__module__,
            job_class_name=RunComplianceRules.__name__,
        )
        job_model.enabled = True
        job_model.save()

    def test_full_api_flow(self):
        # 1. Create a ComplianceRule via the API.
        create_rule_response = self.client.post(
            reverse("plugins-api:nautobot_pytest_compliance_rule_engine-api:compliancerule-list"),
            {"name": "NTP configured", "rule_code": NTP_RULE_CODE},
            format="json",
            **self.header,
        )
        self.assertHttpStatus(create_rule_response, status.HTTP_201_CREATED)
        rule_id = create_rule_response.data["id"]

        # 2. Create a ComplianceRuleSet containing it via the API.
        create_rule_set_response = self.client.post(
            reverse("plugins-api:nautobot_pytest_compliance_rule_engine-api:complianceruleset-list"),
            {"name": "Integration Rule Set", "rules": [rule_id]},
            format="json",
            **self.header,
        )
        self.assertHttpStatus(create_rule_set_response, status.HTTP_201_CREATED)
        rule_set_id = create_rule_set_response.data["id"]

        # 3. Trigger a run via the job-trigger endpoint and poll the resulting JobResult via
        # Nautobot's existing JobResult API. No Celery worker is running in this test
        # environment (or CI's), so -- like Nautobot's own JobViewSet.run() tests -- this
        # confirms the trigger endpoint's wiring and the JobResult's shape, not that a worker
        # picked it up; step 4 below exercises the Job actually producing results.
        with patch(f"{JOB_MODULE}.get_latest_backup_config", return_value=GOLDEN_CONFIG):
            run_response = self.client.post(
                reverse("plugins-api:nautobot_pytest_compliance_rule_engine-api:run-compliance-rules"),
                {"location": [], "role": [], "platform": [], "tag": [], "rule_set": rule_set_id},
                format="json",
                **self.header,
            )
        self.assertHttpStatus(run_response, status.HTTP_202_ACCEPTED)
        job_result_id = run_response.data["job_result"]["id"]

        job_result_response = self.client.get(
            reverse("extras-api:jobresult-detail", kwargs={"pk": job_result_id}), **self.header
        )
        self.assertHttpStatus(job_result_response, status.HTTP_200_OK)
        self.assertEqual(job_result_response.data["status"]["value"], JobResultStatusChoices.STATUS_PENDING)

        # 4. Run the same rule set to completion through Nautobot's synchronous job-testing
        # utility, so step 5 verifies the read-only endpoint against real Job output.
        with patch(f"{JOB_MODULE}.get_latest_backup_config", return_value=GOLDEN_CONFIG):
            executed_job_result = create_job_result_and_run_job(
                JOB_MODULE,
                JOB_NAME,
                location=[],
                role=[],
                platform=[],
                tag=[],
                rule_set=rule_set_id,
            )
        self.assertEqual(
            executed_job_result.status, JobResultStatusChoices.STATUS_SUCCESS, executed_job_result.traceback
        )

        # 5. Confirm the ComplianceTestResult it produced is retrievable via the read-only endpoint.
        results_response = self.client.get(
            f"{reverse('plugins-api:nautobot_pytest_compliance_rule_engine-api:compliancetestresult-list')}"
            f"?device={self.device.pk}",
            **self.header,
        )
        self.assertHttpStatus(results_response, status.HTTP_200_OK)
        self.assertEqual(results_response.data["count"], 1)
        result = results_response.data["results"][0]
        self.assertEqual(str(result["rule"]["id"]), rule_id)
        self.assertEqual(result["status"], "pass")
