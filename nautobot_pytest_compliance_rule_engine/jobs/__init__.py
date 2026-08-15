"""Jobs for nautobot_pytest_compliance_rule_engine.

`NautobotAppConfig.ready()` imports this module and looks up the `jobs`
attribute below; importing each Job module here also registers its Job with
Celery via `register_jobs()`, which is what actually makes it runnable.
"""

from nautobot_pytest_compliance_rule_engine.jobs.load_example_rules import LoadExampleComplianceRules
from nautobot_pytest_compliance_rule_engine.jobs.run_compliance import RunComplianceRules

jobs = [RunComplianceRules, LoadExampleComplianceRules]

__all__ = ["LoadExampleComplianceRules", "RunComplianceRules", "jobs"]
