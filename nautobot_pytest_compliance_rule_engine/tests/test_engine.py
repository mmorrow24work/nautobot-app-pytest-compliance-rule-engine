"""Tests for the restricted-namespace execution of rule_code."""

import io
from contextlib import redirect_stdout

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from nautobot_pytest_compliance_rule_engine.engine import (
    ALLOWED_BUILTINS,
    build_rule_namespace,
    execute_rule,
    execute_rule_code,
)
from nautobot_pytest_compliance_rule_engine.models import ComplianceRule, ComplianceTestResultStatusChoices
from nautobot_pytest_compliance_rule_engine.validation import validate_rule_code

# The canonical rule shape: one top-level function asserting on device data.
NTP_RULE_CODE = "def check_ntp(configuration):\n    assert 'ntp server' in configuration, 'no NTP server configured'"


class RuleExecutionMixin:
    """Assertions shared by the engine test cases."""

    def assertPasses(self, rule_code, **kwargs):
        """Assert that rule_code runs cleanly, and return its result."""
        result = execute_rule_code(rule_code, **kwargs)
        self.assertEqual(result.status, ComplianceTestResultStatusChoices.PASS)
        self.assertEqual(result.output, "")
        return result

    def assertFails(self, rule_code, expected_output, **kwargs):
        """Assert that rule_code fails an assertion and reports the assertion message."""
        result = execute_rule_code(rule_code, **kwargs)
        self.assertEqual(result.status, ComplianceTestResultStatusChoices.FAIL)
        self.assertEqual(result.output, expected_output)
        return result

    def assertErrors(self, rule_code, expected_fragment, **kwargs):
        """Assert that rule_code errors and that the output names what went wrong."""
        result = execute_rule_code(rule_code, **kwargs)
        self.assertEqual(result.status, ComplianceTestResultStatusChoices.ERROR)
        self.assertIn(expected_fragment, result.output)
        return result


class RuleOutcomeTest(RuleExecutionMixin, SimpleTestCase):
    """A rule's outcome maps onto the status/output pair recorded as a ComplianceTestResult."""

    def test_rule_that_asserts_cleanly_passes(self):
        """A rule whose assertions hold is a pass with empty output."""
        self.assertPasses(NTP_RULE_CODE, configuration="hostname r1\nntp server 10.0.0.1\n")

    def test_failed_assertion_captures_the_assertion_message(self):
        """A failed assertion is a fail, with the assertion's message as the output."""
        self.assertFails(NTP_RULE_CODE, "no NTP server configured", configuration="hostname r1\n")

    def test_failed_assertion_without_a_message_has_empty_output(self):
        """An assertion written without a message fails with no output to report."""
        self.assertFails("def check(configuration):\n    assert 'ntp' in configuration", "", configuration="")

    def test_non_assertion_exception_is_an_error(self):
        """A KeyError from indexing missing command output is an error, not a fail."""
        result = self.assertErrors(
            "def check(commands):\n    assert commands['show ntp'].strip()",
            "KeyError",
            commands={},
        )
        self.assertEqual(result.output, "KeyError: 'show ntp'")

    def test_error_output_names_the_exception_type(self):
        """Error output is the exception type followed by its message."""
        self.assertErrors(
            "def check(configuration):\n    assert int(configuration) > 0",
            "ValueError: invalid literal for int()",
            configuration="not a number",
        )

    def test_result_is_a_status_output_pair(self):
        """The result unpacks as (status, output), the two fields a ComplianceTestResult records."""
        status, output = execute_rule_code(NTP_RULE_CODE, configuration="hostname r1\n")

        self.assertEqual(status, ComplianceTestResultStatusChoices.FAIL)
        self.assertEqual(output, "no NTP server configured")


class RuleSignatureTest(RuleExecutionMixin, SimpleTestCase):
    """The engine passes the subset of configuration/commands a rule's signature declares."""

    def test_rule_declaring_configuration_receives_it(self):
        """A rule declaring only `configuration` is called with the configuration."""
        self.assertPasses(
            "def check(configuration):\n    assert configuration == 'hostname r1'",
            configuration="hostname r1",
            commands={"show version": "irrelevant"},
        )

    def test_rule_declaring_commands_receives_it(self):
        """A rule declaring only `commands` is called with the command output."""
        self.assertPasses(
            "def check(commands):\n    assert commands['show version'] == 'v1'",
            configuration="hostname r1",
            commands={"show version": "v1"},
        )

    def test_rule_declaring_both_receives_both(self):
        """A rule declaring both arguments is called with both."""
        self.assertPasses(
            "def check(configuration, commands):\n    assert configuration and commands",
            configuration="hostname r1",
            commands={"show version": "v1"},
        )

    def test_rule_declaring_neither_is_called_with_no_arguments(self):
        """A rule declaring no arguments is called with none, even when data is available."""
        self.assertPasses("def check():\n    assert True", configuration="hostname r1", commands={"a": "b"})

    def test_keyword_only_argument_is_supported(self):
        """Arguments are passed by keyword, so a keyword-only parameter works."""
        self.assertPasses("def check(*, commands):\n    assert commands", commands={"show version": "v1"})

    def test_unsupported_argument_is_an_error(self):
        """A rule declaring an argument the engine does not supply errors rather than being skipped."""
        self.assertErrors(
            "def check(config):\n    assert config",
            "TypeError",
            configuration="hostname r1",
        )

    def test_missing_device_data_is_passed_through_as_none(self):
        """Device data the caller did not supply reaches the rule as None rather than being invented."""
        self.assertPasses("def check(configuration, commands):\n    assert configuration is None and commands is None")


class RuleNamespaceTest(RuleExecutionMixin, SimpleTestCase):
    """rule_code runs against an explicitly built namespace, not the real builtins."""

    def test_re_is_available(self):
        """The pre-injected `re` module is available without an import."""
        self.assertPasses(
            "def check(configuration):\n    assert re.search(r'^ntp server \\S+', configuration, re.MULTILINE)",
            configuration="hostname r1\nntp server 10.0.0.1\n",
        )

    def test_allowed_builtins_are_available(self):
        """A rule using builtins from the allowlist runs."""
        self.assertPasses(
            "def check(commands):\n"
            "    vlans = sorted(int(line) for line in commands['show vlan'].splitlines())\n"
            "    assert len(vlans) == 3 and max(vlans) < 4096",
            commands={"show vlan": "10\n20\n30"},
        )

    def test_namespace_carries_only_the_allowlist(self):
        """The namespace holds exactly the allowed builtins plus `re`, and nothing else."""
        namespace = build_rule_namespace()

        self.assertEqual(set(namespace), {"__builtins__", "re"})
        self.assertEqual(set(namespace["__builtins__"]), set(ALLOWED_BUILTINS))

    def test_builtins_omitted_from_the_allowlist_are_unavailable(self):
        """Builtins that are not on the allowlist are simply absent from the namespace."""
        for name in ["open", "eval", "exec", "compile", "getattr", "type", "input", "vars", "globals"]:
            with self.subTest(name=name):
                self.assertErrors(
                    f"def check():\n    {name}('x')",
                    f"NameError: name '{name}' is not defined",
                )

    def test_import_statement_fails_at_runtime(self):
        """An import that got past static validation still fails: __import__ is not in the namespace."""
        self.assertErrors("import os\n\ndef check():\n    assert True", "ImportError: __import__ not found")

    def test_import_inside_the_rule_function_fails_at_runtime(self):
        """An import nested in the rule's body fails for the same reason."""
        self.assertErrors("def check():\n    import subprocess\n    assert subprocess", "ImportError")

    def test_aliased_banned_callable_fails_at_runtime(self):
        """Aliasing `open` defeats the static call check but finds nothing to bind at run time.

        This is the bypass documented at the top of `validation.py`: the static
        pass matches on the name at the call site, so it accepts this rule. The
        namespace is what stops it.
        """
        rule_code = "def check(configuration):\n    reader = open\n    return reader('/etc/passwd').read()"
        validate_rule_code(rule_code)

        self.assertErrors(rule_code, "NameError: name 'open' is not defined", configuration="")

    def test_builtins_mapping_holds_nothing_dangerous(self):
        """Reaching into `__builtins__` by name finds only the allowlist."""
        self.assertErrors("def check():\n    __builtins__['__import__']('os')", "KeyError: '__import__'")

    def test_rule_cannot_see_the_engine_module_globals(self):
        """A rule's globals are the built namespace, not this module's or the engine's."""
        self.assertErrors(
            "def check():\n    assert ALLOWED_BUILTINS", "NameError: name 'ALLOWED_BUILTINS' is not defined"
        )

    def test_namespace_is_rebuilt_for_every_execution(self):
        """A rule that writes to `__builtins__` cannot affect the next rule to run."""
        self.assertPasses("def check():\n    __builtins__['len'] = None")

        self.assertPasses("def check():\n    assert len('ab') == 2")

    def test_dunder_attribute_escape_is_caught_statically_not_at_runtime(self):
        """The classic `__subclasses__` escape is rejected by layer 1; layer 2 does not catch it.

        Recorded as a test rather than left implicit: the runtime namespace does
        not filter attribute access, so this is exactly the incomplete
        containment that `docs/adr/0001-rule-sandboxing.md` describes. Static
        validation is what rejects this rule.
        """
        rule_code = "def check():\n    assert ().__class__.__bases__[0].__subclasses__()"

        with self.assertRaises(ValidationError):
            validate_rule_code(rule_code)

        self.assertPasses(rule_code)


class RuleStructureTest(RuleExecutionMixin, SimpleTestCase):
    """rule_code that is not one top-level function is reported as an error, not raised at the caller."""

    def test_rule_code_defining_no_function_is_an_error(self):
        """A bare snippet with no function definition is an error naming the convention.

        Static validation accepts a bare `assert` -- it only rejects unsafe
        constructs -- so the engine is where the one-function convention is
        enforced.
        """
        rule_code = "assert 'ntp server' in configuration"
        validate_rule_code(rule_code)

        self.assertErrors(rule_code, "rule_code must define exactly one top-level function; it defines none")

    def test_rule_code_defining_two_functions_is_an_error(self):
        """Two top-level functions are ambiguous, so the engine refuses to pick one."""
        result = self.assertErrors(
            "def helper(line):\n    return line.strip()\n\n\ndef check(configuration):\n    assert configuration",
            "rule_code must define exactly one top-level function; it defines 2",
        )
        self.assertIn("helper, check", result.output)

    def test_async_rule_is_an_error(self):
        """An `async def` rule is rejected rather than passing without ever running."""
        self.assertErrors("async def check(configuration):\n    assert False", "must define a plain function")

    def test_structurally_invalid_rule_code_never_executes(self):
        """The shape is checked on the parse tree, so a rejected rule's top-level statements do not run."""
        printed = io.StringIO()

        with redirect_stdout(printed):
            self.assertErrors("print('should not run')\nx = 1", "it defines none")

        self.assertEqual(printed.getvalue(), "")

    def test_unparseable_rule_code_is_an_error(self):
        """rule_code that never passed static validation and does not compile is an error."""
        self.assertErrors("def check(configuration:\n    assert True", "SyntaxError")

    def test_exception_from_a_top_level_statement_is_an_error(self):
        """A rule whose module-level statements raise is an error rather than propagating."""
        self.assertErrors("x = 1 / 0\n\ndef check():\n    assert True", "ZeroDivisionError")


class ExecuteRuleTest(TestCase):
    """execute_rule() runs the rule_code held by a ComplianceRule instance."""

    def test_executes_the_rules_code(self):
        """A stored rule passes or fails against the device data it is given."""
        rule = ComplianceRule.objects.create(name="Require NTP", rule_code=NTP_RULE_CODE)

        passing = execute_rule(rule, configuration="ntp server 10.0.0.1\n")
        failing = execute_rule(rule, configuration="hostname r1\n")

        self.assertEqual(passing.status, ComplianceTestResultStatusChoices.PASS)
        self.assertEqual(failing.status, ComplianceTestResultStatusChoices.FAIL)
        self.assertEqual(failing.output, "no NTP server configured")

    def test_result_can_be_recorded_as_a_compliance_test_result(self):
        """The status and output map straight onto the ComplianceTestResult fields."""
        rule = ComplianceRule.objects.create(name="Require NTP", rule_code=NTP_RULE_CODE)
        result = execute_rule(rule, configuration="hostname r1\n")

        self.assertIn(result.status, dict(ComplianceTestResultStatusChoices.CHOICES))
        self.assertIsInstance(result.output, str)
