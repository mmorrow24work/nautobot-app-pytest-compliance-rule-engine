"""Tests for the static rule_code validation that gates ComplianceRule saves."""

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from nautobot_pytest_compliance_rule_engine.models import ComplianceRule
from nautobot_pytest_compliance_rule_engine.validation import validate_rule_code

# A realistic rule of the shape the engine expects: one top-level function that
# asserts on the device data passed to it.
LEGITIMATE_RULE_CODE = "def check_keyword(configuration):\n    assert 'keyword' in configuration"


class ValidateRuleCodeRejectionTest(SimpleTestCase):
    """rule_code containing a banned construct is rejected."""

    def assertRejected(self, rule_code, expected_fragment):
        """Assert that rule_code is rejected and that the message names what was rejected."""
        with self.assertRaises(ValidationError) as context:
            validate_rule_code(rule_code)

        joined = " ".join(context.exception.messages)
        self.assertIn(expected_fragment, joined)

    def test_rejects_import_statement(self):
        """`import os` is rejected -- rules may not import anything."""
        self.assertRejected("import os", "'import os' is not allowed")

    def test_rejects_import_of_harmless_module(self):
        """Imports are banned outright, not only imports of dangerous modules."""
        self.assertRejected("import json", "'import json' is not allowed")

    def test_rejects_aliased_import(self):
        """An aliased import is rejected under the name being imported."""
        self.assertRejected("import subprocess as sp", "'import subprocess' is not allowed")

    def test_rejects_from_import(self):
        """`from x import y` is rejected."""
        self.assertRejected("from os import system", "'from os import ...' is not allowed")

    def test_rejects_relative_from_import(self):
        """A relative `from . import y` is rejected."""
        self.assertRejected("from . import models", "'from . import ...' is not allowed")

    def test_rejects_import_inside_function_body(self):
        """An import nested inside the rule's function is rejected, not just a top-level one."""
        self.assertRejected(
            "def check(configuration):\n    import os\n    assert configuration",
            "'import os' is not allowed",
        )

    def test_rejects_eval(self):
        """`eval('1+1')` is rejected."""
        self.assertRejected("eval('1+1')", "the call to 'eval()' is not allowed")

    def test_rejects_dunder_import_call(self):
        """`__import__('os').system('ls')` is rejected as a call to __import__."""
        self.assertRejected("__import__('os').system('ls')", "the call to '__import__()' is not allowed")

    def test_rejects_class_bases_escape(self):
        """`().__class__.__bases__[0]` is rejected as dunder attribute access."""
        self.assertRejected("().__class__.__bases__[0]", "access to the dunder attribute '.__class__'")

    def test_reports_every_dunder_in_an_escape_chain(self):
        """Each dunder attribute in an escape chain is named, not just the first one found."""
        with self.assertRaises(ValidationError) as context:
            validate_rule_code("().__class__.__bases__[0].__subclasses__()")

        joined = " ".join(context.exception.messages)
        self.assertIn("'.__class__'", joined)
        self.assertIn("'.__bases__'", joined)
        self.assertIn("'.__subclasses__'", joined)

    def test_rejects_globals_lookup(self):
        """A `__globals__` lookup on a function object is rejected."""
        self.assertRejected(
            "def check(configuration):\n    return check.__globals__",
            "access to the dunder attribute '.__globals__'",
        )

    def test_rejects_banned_call_via_attribute(self):
        """A banned callable reached as an attribute is rejected too."""
        self.assertRejected("configuration.open('/etc/passwd')", "the call to 'open()' is not allowed")

    def test_rejects_every_banned_call_name(self):
        """Each name on the banned-call list is rejected when called."""
        banned = [
            "eval",
            "exec",
            "compile",
            "__import__",
            "open",
            "globals",
            "locals",
            "vars",
            "getattr",
            "setattr",
            "delattr",
            "input",
            "breakpoint",
            "memoryview",
        ]
        for name in banned:
            with self.subTest(name=name):
                self.assertRejected(f"{name}()", f"the call to '{name}()' is not allowed")

    def test_rejects_every_banned_module_name(self):
        """Each name on the banned-module list is rejected when referenced at all."""
        banned = ["os", "sys", "subprocess", "shutil", "socket", "pathlib", "importlib", "builtins"]
        for name in banned:
            with self.subTest(name=name):
                self.assertRejected(f"x = {name}", f"the name '{name}' is not allowed")

    def test_rejects_banned_module_call(self):
        """A call through a banned module, such as `subprocess.run(...)`, is rejected."""
        self.assertRejected("subprocess.run(['ls'])", "the name 'subprocess' is not allowed")

    def test_rejects_banned_construct_in_comprehension(self):
        """A banned construct hidden inside a comprehension is still found."""
        self.assertRejected(
            "def check(configuration):\n    return [eval(line) for line in configuration]",
            "the call to 'eval()' is not allowed",
        )

    def test_rejects_banned_construct_in_lambda(self):
        """A banned construct hidden inside a lambda is still found."""
        self.assertRejected("f = lambda s: s.__class__", "access to the dunder attribute '.__class__'")

    def test_rejects_banned_construct_in_default_argument(self):
        """A banned construct in a default argument expression is still found."""
        self.assertRejected("def check(configuration, x=open('/etc/passwd')):\n    pass", "the call to 'open()'")

    def test_rejects_banned_construct_in_decorator(self):
        """A banned construct in a decorator expression is still found."""
        self.assertRejected(
            "@eval('str')\ndef check(configuration):\n    pass",
            "the call to 'eval()' is not allowed",
        )

    def test_reports_all_violations_at_once(self):
        """Several independent violations are reported together rather than one at a time."""
        with self.assertRaises(ValidationError) as context:
            validate_rule_code("import os\neval('1+1')\nx = ().__class__")

        joined = " ".join(context.exception.messages)
        self.assertIn("'import os'", joined)
        self.assertIn("the call to 'eval()'", joined)
        self.assertIn("'.__class__'", joined)

    def test_message_names_the_offending_line(self):
        """The rejection message points at the line the offending construct is on."""
        self.assertRejected("def check(configuration):\n    assert configuration\n    import os", "line 3")

    def test_rejects_unparseable_code(self):
        """rule_code that is not valid Python is rejected before anything else is checked."""
        with self.assertRaises(ValidationError) as context:
            validate_rule_code("def check(configuration:\n    assert True")

        self.assertIn("rule_code is not valid Python", " ".join(context.exception.messages))


class ValidateRuleCodeAcceptanceTest(SimpleTestCase):
    """Legitimate rule_code is accepted."""

    def assertAccepted(self, rule_code):
        """Assert that rule_code passes static validation."""
        validate_rule_code(rule_code)

    def test_accepts_simple_assertion(self):
        """The canonical `assert 'keyword' in configuration` rule is accepted."""
        self.assertAccepted("assert 'keyword' in configuration")

    def test_accepts_function_wrapped_rule(self):
        """A rule written as a single top-level function is accepted."""
        self.assertAccepted(LEGITIMATE_RULE_CODE)

    def test_accepts_regex_rule(self):
        """A rule using the pre-injected `re` module is accepted."""
        self.assertAccepted(
            "def check_ntp(configuration):\n"
            "    assert re.search(r'^ntp server \\S+', configuration, re.MULTILINE), 'no NTP server configured'"
        )

    def test_accepts_allowed_builtins(self):
        """A rule using builtins from the engine's allowlist is accepted."""
        self.assertAccepted(
            "def check_vlans(commands):\n"
            "    vlans = sorted(int(line.split()[0]) for line in commands['show vlan'].splitlines())\n"
            "    assert len(vlans) > 0 and all(v < 4096 for v in vlans)"
        )

    def test_accepts_non_dunder_attribute_access(self):
        """Ordinary attribute access on the data passed to a rule is accepted."""
        self.assertAccepted("def check(configuration):\n    assert configuration.strip().startswith('!')")

    def test_accepts_single_underscore_attributes(self):
        """Only attributes that both start and end with a double underscore are rejected."""
        self.assertAccepted("def check(configuration):\n    assert configuration._private")
        self.assertAccepted("def check(configuration):\n    assert configuration.__private")
        self.assertAccepted("def check(configuration):\n    assert configuration.value__")

    def test_accepts_control_flow_and_loops(self):
        """A rule using loops and conditionals is accepted."""
        self.assertAccepted(
            "def check(configuration):\n"
            "    for line in configuration.splitlines():\n"
            "        if line.startswith('snmp-server community'):\n"
            "            assert 'public' not in line\n"
            "    else:\n"
            "        pass"
        )

    def test_accepts_empty_rule_code(self):
        """Empty rule_code parses cleanly; the field's own blank check is what rejects it."""
        self.assertAccepted("")

    def test_accepts_banned_names_as_string_content(self):
        """A banned name appearing inside a string literal is not a reference to it."""
        self.assertAccepted("def check(configuration):\n    assert 'import os' not in configuration")
        self.assertAccepted("def check(configuration):\n    assert '__class__' not in configuration")


class ComplianceRuleCleanTest(TestCase):
    """ComplianceRule.clean() runs the static validation and keys errors onto rule_code."""

    def test_full_clean_rejects_unsafe_rule_code(self):
        """full_clean() on a rule with unsafe rule_code raises, keyed to the rule_code field."""
        rule = ComplianceRule(name="Unsafe rule", rule_code="__import__('os').system('ls')")

        with self.assertRaises(ValidationError) as context:
            rule.full_clean()

        self.assertIn("rule_code", context.exception.message_dict)
        self.assertIn(
            "the call to '__import__()' is not allowed",
            " ".join(context.exception.message_dict["rule_code"]),
        )

    def test_validated_save_rejects_unsafe_rule_code(self):
        """validated_save() does not persist a rule whose rule_code is rejected."""
        rule = ComplianceRule(name="Unsafe rule", rule_code="import os")

        with self.assertRaises(ValidationError):
            rule.validated_save()

        self.assertFalse(ComplianceRule.objects.filter(name="Unsafe rule").exists())

    def test_full_clean_accepts_legitimate_rule_code(self):
        """A rule with legitimate rule_code passes full_clean() and saves."""
        rule = ComplianceRule(name="Require keyword", rule_code=LEGITIMATE_RULE_CODE)
        rule.full_clean()
        rule.save()

        self.assertTrue(ComplianceRule.objects.filter(name="Require keyword").exists())

    def test_editing_a_rule_to_unsafe_code_is_rejected(self):
        """An existing rule cannot be edited to hold unsafe rule_code."""
        rule = ComplianceRule.objects.create(name="Require keyword", rule_code=LEGITIMATE_RULE_CODE)

        rule.rule_code = "().__class__.__bases__[0]"

        with self.assertRaises(ValidationError):
            rule.full_clean()
