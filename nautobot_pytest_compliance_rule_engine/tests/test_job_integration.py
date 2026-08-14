"""End-to-end integration tests for the RunComplianceRules Job.

Unlike `tests/test_run_compliance.py`, which calls `Job.run()` directly,
these tests exercise the Job the way Nautobot itself runs it -- through
`create_job_result_and_run_job()` / `run_job_for_testing()`, Nautobot's
Job-testing utilities. That path resolves the Job's registered `Job` model,
deserializes the submitted `MultiObjectVar`/`ObjectVar` inputs back into
querysets and instances, invokes `Job.__call__()`, and records the outcome
on a real `JobResult` -- the same machinery a Celery worker uses.

Device data gathering is mocked throughout via the same two integration
points the Job imports by name (`get_latest_backup_config`,
`gather_command_output`); no live connections are made.
"""

from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from nautobot.apps.choices import JobResultStatusChoices, LogLevelChoices
from nautobot.core.testing import TransactionTestCase, create_job_result_and_run_job
from nautobot.dcim.models import Device, DeviceType, Location, LocationType, Manufacturer, Platform
from nautobot.extras.models import JobLogEntry, Role, Status

from nautobot_pytest_compliance_rule_engine.models import (
    ComplianceRule,
    ComplianceRuleSet,
    ComplianceRuleSeverityChoices,
    ComplianceTestResult,
    ComplianceTestResultStatusChoices,
)

# The Job module is what patches target: it imports the two data-gathering
# helpers by name, so the names bound there are the ones a run reaches
# regardless of whether it's invoked directly or through the Job runner.
JOB_MODULE = "nautobot_pytest_compliance_rule_engine.jobs.run_compliance"
JOB_NAME = "RunComplianceRules"

# Rules of mixed severity. Severity plays no role in pass/fail/error logic;
# these three are chosen so that, run against two devices, they produce one
# of each outcome per device.
NTP_RULE_CODE = "def check_ntp(configuration):\n    assert 'ntp server' in configuration, 'no NTP server configured'"
SNMP_RULE_CODE = "def check_snmp(configuration):\n    assert 'snmp-server' in configuration, 'no SNMP community'"
VERSION_RULE_CODE = "def check_version(commands):\n    assert 'Version 17' in commands['show version']"

# Golden Config backups: r1 has NTP but no SNMP; r2 has SNMP but no NTP.
# Neither carries command output, so the command-based rule errors for both.
GOLDEN_CONFIGS = {
    "r1": "hostname r1\nntp server 10.0.0.1\n",
    "r2": "hostname r2\nsnmp-server community public\n",
}


def golden_config_for(device):
    """Stand in for `get_latest_backup_config()`: a canned backup keyed by device name."""
    return GOLDEN_CONFIGS.get(device.name)


class RunComplianceRulesJobIntegrationTest(TransactionTestCase):
    """Run RunComplianceRules through Nautobot's Job execution machinery, end to end."""

    # JobLogEntry rows are written to a dedicated "job_logs" database; both must be declared.
    databases = ("default", "job_logs")

    def setUp(self):
        """Build two IOS devices, one Junos device, and rules of mixed severity."""
        super().setUp()

        device_ct = ContentType.objects.get_for_model(Device)
        location_ct = ContentType.objects.get_for_model(Location)

        manufacturer = Manufacturer.objects.create(name="Test Manufacturer")
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model="Test Device Type")

        location_type = LocationType.objects.create(name="Test Location Type")
        location_type.content_types.add(device_ct)
        location_status = Status.objects.create(name="Test Location Status")
        location_status.content_types.add(location_ct)
        location = Location.objects.create(name="Test Location", location_type=location_type, status=location_status)

        role = Role.objects.create(name="Test Role")
        role.content_types.add(device_ct)

        device_status = Status.objects.create(name="Test Device Status")
        device_status.content_types.add(device_ct)

        self.platform_ios = Platform.objects.create(name="Test IOS Platform", napalm_driver="ios")
        self.platform_junos = Platform.objects.create(name="Test Junos Platform", napalm_driver="junos")

        def make_device(name, platform):
            return Device.objects.create(
                name=name,
                device_type=device_type,
                role=role,
                platform=platform,
                location=location,
                status=device_status,
            )

        self.device_1 = make_device("r1", self.platform_ios)
        self.device_2 = make_device("r2", self.platform_ios)
        self.device_3 = make_device("r3", self.platform_junos)

        self.ntp_rule = ComplianceRule.objects.create(
            name="NTP configured", rule_code=NTP_RULE_CODE, severity=ComplianceRuleSeverityChoices.LOW
        )
        self.snmp_rule = ComplianceRule.objects.create(
            name="SNMP configured", rule_code=SNMP_RULE_CODE, severity=ComplianceRuleSeverityChoices.MEDIUM
        )
        self.version_rule = ComplianceRule.objects.create(
            name="Version supported", rule_code=VERSION_RULE_CODE, severity=ComplianceRuleSeverityChoices.HIGH
        )

    def run_compliance_job(self, rule_set, platform=None):
        """Run RunComplianceRules through Nautobot's Job runner and return its JobResult.

        Every job variable is passed explicitly: the Job runner deserializes
        submitted data strictly from what's given, so an omitted key -- even
        for an optional filter -- reaches `Job.run()` as a missing argument.
        """
        return create_job_result_and_run_job(
            JOB_MODULE,
            JOB_NAME,
            location=[],
            role=[],
            platform=[str(platform.pk)] if platform else [],
            tag=[],
            rule_set=str(rule_set.pk),
        )

    def recorded_statuses(self):
        """Return the recorded results as a `{(device name, rule name): status}` mapping."""
        return {(result.device.name, result.rule.name): result.status for result in ComplianceTestResult.objects.all()}

    def test_mixed_severity_rules_across_multiple_devices_record_correct_counts(self):
        """A rule set of mixed severity run across two devices records the expected pass/fail/error counts."""
        rule_set = ComplianceRuleSet.objects.create(name="Mixed Severity Rule Set")
        rule_set.rules.set([self.ntp_rule, self.snmp_rule, self.version_rule])

        with (
            patch(f"{JOB_MODULE}.get_latest_backup_config", side_effect=golden_config_for),
            patch(f"{JOB_MODULE}.gather_command_output") as mock_gather,
        ):
            job_result = self.run_compliance_job(rule_set, platform=self.platform_ios)

        self.assertEqual(job_result.status, JobResultStatusChoices.STATUS_SUCCESS, job_result.traceback)
        mock_gather.assert_not_called()  # Golden Config had a backup for both devices.

        self.assertEqual(
            job_result.result,
            {
                "rule_set": "Mixed Severity Rule Set",
                "rules": 3,
                "devices_resolved": 2,
                "devices_evaluated": 2,
                "devices_skipped": 0,
                "results": 6,
                "pass": 2,
                "fail": 2,
                "error": 2,
            },
        )
        self.assertEqual(
            self.recorded_statuses(),
            {
                ("r1", "NTP configured"): ComplianceTestResultStatusChoices.PASS,
                ("r1", "SNMP configured"): ComplianceTestResultStatusChoices.FAIL,
                ("r1", "Version supported"): ComplianceTestResultStatusChoices.ERROR,
                ("r2", "NTP configured"): ComplianceTestResultStatusChoices.FAIL,
                ("r2", "SNMP configured"): ComplianceTestResultStatusChoices.PASS,
                ("r2", "Version supported"): ComplianceTestResultStatusChoices.ERROR,
            },
        )
        for result in ComplianceTestResult.objects.all():
            self.assertEqual(result.job_result, job_result)

        self.assertFalse(
            JobLogEntry.objects.filter(job_result=job_result, log_level=LogLevelChoices.LOG_ERROR).exists()
        )

    def test_device_matching_zero_rules_in_the_set_is_left_alone(self):
        """A device no rule in the set applies to is resolved but records no results; the run still succeeds."""
        rule_set = ComplianceRuleSet.objects.create(name="IOS Only Rule Set")
        ios_only_rule = ComplianceRule.objects.create(
            name="IOS only rule", rule_code=NTP_RULE_CODE, platform=self.platform_ios
        )
        rule_set.rules.set([ios_only_rule])

        with (
            patch(f"{JOB_MODULE}.get_latest_backup_config", side_effect=golden_config_for) as mock_golden_config,
            patch(f"{JOB_MODULE}.gather_command_output"),
        ):
            # No platform filter: both the matching IOS devices and the non-matching Junos device are resolved.
            job_result = self.run_compliance_job(rule_set)

        self.assertEqual(job_result.status, JobResultStatusChoices.STATUS_SUCCESS, job_result.traceback)
        self.assertEqual(job_result.result["devices_resolved"], 3)
        self.assertEqual(job_result.result["devices_evaluated"], 2)
        self.assertEqual(job_result.result["results"], 2)

        # r3 (Junos) matches no rule in the set, so its data was never even gathered.
        gathered_devices = {call.args[0] for call in mock_golden_config.call_args_list}
        self.assertNotIn(self.device_3, gathered_devices)
        self.assertEqual(
            set(ComplianceTestResult.objects.values_list("device__name", flat=True)),
            {"r1", "r2"},
        )

    def test_empty_rule_set_completes_with_zero_results(self):
        """A rule set with zero rules completes successfully and records nothing -- it does not error."""
        rule_set = ComplianceRuleSet.objects.create(name="Empty Rule Set")

        with (
            patch(f"{JOB_MODULE}.get_latest_backup_config") as mock_golden_config,
            patch(f"{JOB_MODULE}.gather_command_output") as mock_gather,
        ):
            job_result = self.run_compliance_job(rule_set)

        self.assertEqual(job_result.status, JobResultStatusChoices.STATUS_SUCCESS, job_result.traceback)
        mock_golden_config.assert_not_called()
        mock_gather.assert_not_called()

        self.assertEqual(
            job_result.result,
            {
                "rule_set": "Empty Rule Set",
                "rules": 0,
                "devices_resolved": 3,
                "devices_evaluated": 0,
                "devices_skipped": 0,
                "results": 0,
                "pass": 0,
                "fail": 0,
                "error": 0,
            },
        )
        self.assertEqual(ComplianceTestResult.objects.count(), 0)
        self.assertFalse(
            JobLogEntry.objects.filter(job_result=job_result, log_level=LogLevelChoices.LOG_ERROR).exists()
        )
