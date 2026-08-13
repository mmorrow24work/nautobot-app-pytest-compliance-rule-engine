"""Restricted-namespace execution of ComplianceRule.rule_code.

This is layer 2 of the two-layer approach described in
``docs/adr/0001-rule-sandboxing.md``: ``rule_code`` is executed with ``exec()``
against an explicitly built namespace that never contains the real
``__builtins__``. Layer 1 (``validation.py``) rejects the obvious escape
mechanisms statically, at save time.

This module assumes layer 1 already ran, but does not depend on it: a
``rule_code`` value that reached the engine without static validation (a
fixture, a direct ``objects.create()``, a data migration) is still executed
against the same restricted namespace.

This is **not a sandbox** and does not contain hostile code. Rule authorship is
restricted to trusted users holding the relevant Nautobot RBAC permission; this
module is defence in depth against mistakes and low-effort mischief by those
users, not a security boundary against a determined attacker who already holds
rule-authoring rights. In particular, and beyond the bypasses listed in
``validation.py``:

- Nothing here bounds CPU time, memory, or recursion depth. A rule containing
  `while True: pass` hangs the process running the Job.
- A curated builtins mapping is a well-known incomplete containment. Gadgets
  reachable through allowed pure-Python constructs alone have historically been
  used to escape namespaces built this way.
- A rule runs in the Job's own process, so an escape has the Job's reach --
  the ORM included.

One deliberate side effect of the builtins allowlist is that `class` statements
inside a rule fail with a `NameError` on `__build_class__`, which the allowlist
does not carry. Rules are single assertion functions; they do not need classes.
"""

import ast
import inspect
import re
from types import FunctionType
from typing import Any, Dict, NamedTuple, Optional

from nautobot_pytest_compliance_rule_engine.models import ComplianceTestResultStatusChoices

# The only builtins a rule may use. Spelled out as an explicit mapping rather
# than filtered out of the `builtins` module, so that the whole set a rule can
# reach is auditable in one place.
ALLOWED_BUILTINS = {
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "isinstance": isinstance,
    "any": any,
    "all": all,
    "sorted": sorted,
    "enumerate": enumerate,
    "zip": zip,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "round": round,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "range": range,
    "print": print,
}

# The only module injected into a rule's namespace. Real compliance rules need
# pattern matching and imports are banned outright, so `re` is provided
# directly. Nothing else is injected.
INJECTED_MODULES = {"re": re}

# The arguments a rule's function may declare. The engine passes the subset the
# signature asks for; a rule declaring neither is called with no arguments.
SUPPORTED_RULE_ARGUMENTS = ("configuration", "commands")

# Stands in for a filename in tracebacks and error messages raised out of a rule.
RULE_FILENAME = "<compliance rule>"


class RuleExecutionResult(NamedTuple):
    """The outcome of executing one rule, ready to be recorded as a ComplianceTestResult."""

    status: str
    output: str


class _RuleStructureError(Exception):
    """rule_code does not have the shape the engine requires (exactly one top-level function)."""


def build_rule_namespace() -> Dict[str, Any]:
    """Return a fresh globals mapping for executing rule_code.

    The mapping carries the allowed builtins and the injected `re` module and
    nothing else -- notably not this module's own globals. It is rebuilt per
    execution because a rule can reach `__builtins__` by name and write to it;
    a fresh copy keeps that from carrying over into the next rule.
    """
    namespace = {"__builtins__": dict(ALLOWED_BUILTINS)}
    namespace.update(INJECTED_MODULES)
    return namespace


def _load_rule_function(rule_code: str, namespace: Dict[str, Any]) -> FunctionType:
    """Execute rule_code in namespace and return the single top-level function it defines.

    The shape is checked on the parse tree before anything runs, so rule_code
    that is not one top-level function never executes at all. Raises
    `_RuleStructureError` if it defines no function, more than one, or an
    `async def`. Anything raised by rule_code's own top-level statements
    propagates to the caller.
    """
    tree = ast.parse(rule_code, filename=RULE_FILENAME)
    defined_functions = [node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]

    if not defined_functions:
        raise _RuleStructureError(
            "rule_code must define exactly one top-level function; it defines none. A rule is a single "
            "function that asserts on the device data passed to it, for example: "
            "'def check_ntp(configuration): assert \"ntp server\" in configuration'."
        )
    if len(defined_functions) > 1:
        raise _RuleStructureError(
            f"rule_code must define exactly one top-level function; it defines {len(defined_functions)} "
            f"({', '.join(defined_functions)}). Move any helper logic inside the rule's own function."
        )

    exec(compile(tree, RULE_FILENAME, "exec"), namespace)  # The namespace is the containment.

    rule_function = namespace[defined_functions[0]]
    if inspect.iscoroutinefunction(rule_function):
        # Calling one would hand back a coroutine that never runs, so every such rule would "pass".
        raise _RuleStructureError(
            f"rule_code must define a plain function; '{defined_functions[0]}' is declared with 'async def'."
        )

    return rule_function


def _rule_arguments(rule_function: FunctionType, configuration, commands) -> Dict[str, Any]:
    """Return the subset of configuration/commands the rule's signature declares, as keyword arguments."""
    parameters = inspect.signature(rule_function).parameters
    available = {"configuration": configuration, "commands": commands}
    return {name: available[name] for name in SUPPORTED_RULE_ARGUMENTS if name in parameters}


def _error_result(exc: BaseException) -> RuleExecutionResult:
    """Map an exception that is not an AssertionError onto an error result."""
    return RuleExecutionResult(
        status=ComplianceTestResultStatusChoices.ERROR,
        output=f"{type(exc).__name__}: {exc}",
    )


def execute_rule_code(
    rule_code: str,
    configuration: Optional[str] = None,
    commands: Optional[Dict[str, str]] = None,
) -> RuleExecutionResult:
    """Execute rule_code against the given device data and return its result.

    `rule_code` is expected to have passed `validation.validate_rule_code()`
    already, but nothing here relies on that. It is executed in the namespace
    built by `build_rule_namespace()`, and the single top-level function it
    defines is called with whichever of `configuration` and `commands` its
    signature declares. Both are passed through as given, `None` included.

    Returns a `RuleExecutionResult`: a clean run is a pass, an `AssertionError`
    is a fail carrying the assertion message, and anything else -- including
    rule_code that fails to compile or does not define exactly one function --
    is an error carrying the exception type and message.
    """
    namespace = build_rule_namespace()

    try:
        rule_function = _load_rule_function(rule_code, namespace)
    except _RuleStructureError as exc:
        return RuleExecutionResult(status=ComplianceTestResultStatusChoices.ERROR, output=str(exc))
    except Exception as exc:  # A syntax error, or rule_code's top-level statements raising.
        return _error_result(exc)

    try:
        rule_function(**_rule_arguments(rule_function, configuration, commands))
    except AssertionError as exc:
        return RuleExecutionResult(status=ComplianceTestResultStatusChoices.FAIL, output=str(exc))
    except Exception as exc:
        return _error_result(exc)

    return RuleExecutionResult(status=ComplianceTestResultStatusChoices.PASS, output="")


def execute_rule(
    rule,
    configuration: Optional[str] = None,
    commands: Optional[Dict[str, str]] = None,
) -> RuleExecutionResult:
    """Execute a ComplianceRule against the given device data and return its result.

    Thin wrapper over `execute_rule_code()` for callers holding a
    `ComplianceRule` instance, which is how the RunComplianceRules Job (M3)
    will reach the engine.
    """
    return execute_rule_code(rule.rule_code, configuration=configuration, commands=commands)
