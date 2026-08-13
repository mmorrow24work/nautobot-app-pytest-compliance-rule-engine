"""Static rejection of unsafe ComplianceRule.rule_code.

This is layer 1 of the two-layer approach described in
``docs/adr/0001-rule-sandboxing.md``: ``rule_code`` is parsed with ``ast.parse()``
at save time and rejected before it is ever persisted or executed. Layer 2
(``engine.py``) executes whatever survives against an explicitly built namespace.

This is **not a sandbox** and does not contain hostile code. Rule authorship is
restricted to trusted users holding the relevant Nautobot RBAC permission; this
module is defence in depth against mistakes and low-effort mischief by those
users, not a security boundary against a determined attacker who already holds
rule-authoring rights.

# ---------------------------------------------------------------------------
# Known bypasses this module does NOT catch
# ---------------------------------------------------------------------------
#
# The checks below match on *syntax*, not on runtime values, so all of the
# following get past this layer. They are listed so that nobody reads a clean
# pass here as a proof of safety:
#
# 1. Aliasing a banned callable. The call check matches the name at the call
#    site, so `f = open` followed by `f("/etc/passwd")` is not rejected -- the
#    `Call.func` is `f`, not `open`. Only `engine.py` withholding `open` from
#    the builtins allowlist stops that rule at run time.
# 2. Format-string attribute access. `"{0.__class__}".format(obj)` and
#    f-string conversions reach attributes through the string formatter rather
#    than through an `Attribute` node, so the dunder-attribute check never
#    sees them. This is a well-known route to `object.__subclasses__()`.
# 3. Names resolved at run time. Nothing here knows what any identifier
#    actually refers to. A name that is harmless at parse time may be bound to
#    something dangerous by the calling code, and a banned module name reached
#    other than as a bare `Name` (via a container lookup, say) is invisible.
# 4. Resource exhaustion. `while True: pass`, unbounded recursion, a
#    catastrophically backtracking regex, or allocating a huge list all parse
#    cleanly. Neither layer imposes a CPU, memory, or wall-clock limit, and a
#    rule shares the process running the Job.
# 5. Anything that skips `full_clean()`. This runs from
#    `ComplianceRule.clean()`, so it covers forms, API serializers, and
#    `validated_save()` -- but a direct `objects.create()`, a `queryset
#    .update()`, a fixture load, or a data migration writes `rule_code`
#    unvalidated.
# 6. Rules stored before a rule changed. Existing rows are not re-validated
#    when the lists below are tightened; only the next save of that rule is.
#
# When in doubt, reject: a false rejection is a support ticket, a false
# acceptance is an incident.
"""

import ast

from django.core.exceptions import ValidationError

# Callables that can reach code or resources outside the engine's namespace.
# A call is rejected whether it is written `eval(...)` or `something.eval(...)`.
BANNED_CALL_NAMES = frozenset(
    {
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
    }
)

# Modules a rule has no business naming. `re` is the only module the engine
# injects, and imports are banned outright, so any of these appearing as a bare
# name is either a mistake or an attempt to reach the host process.
BANNED_MODULE_NAMES = frozenset(
    {
        "os",
        "sys",
        "subprocess",
        "shutil",
        "socket",
        "pathlib",
        "importlib",
        "builtins",
    }
)


def _is_dunder(attr):
    """Return True if an attribute name both starts and ends with a double underscore."""
    return attr.startswith("__") and attr.endswith("__")


class _RuleCodeVisitor(ast.NodeVisitor):
    """Collect every construct in a parsed rule_code tree that the sandbox contract rejects.

    Every violation in the tree is collected rather than raising on the first
    one, so a rule author sees all of the problems with a snippet at once.
    """

    def __init__(self):
        """Start with an empty violation list."""
        self.violations = []

    def _reject(self, node, message):
        """Record a violation, keyed by source position so the report reads in source order."""
        self.violations.append((node.lineno, node.col_offset, f"line {node.lineno}: {message}"))

    def visit_Import(self, node):
        """Reject `import x` -- rules may not import anything."""
        names = ", ".join(alias.name for alias in node.names)
        self._reject(
            node,
            f"'import {names}' is not allowed. Rules may not import anything; everything a rule "
            "needs is passed to it as a function argument, and the 're' module is provided already.",
        )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Reject `from x import y` -- rules may not import anything."""
        module = "." * node.level + (node.module or "")
        self._reject(
            node,
            f"'from {module} import ...' is not allowed. Rules may not import anything; everything a rule "
            "needs is passed to it as a function argument, and the 're' module is provided already.",
        )
        self.generic_visit(node)

    def visit_Call(self, node):
        """Reject calls to any banned callable, whether called by bare name or as an attribute."""
        func = node.func
        if isinstance(func, ast.Name):
            called = func.id
        elif isinstance(func, ast.Attribute):
            called = func.attr
        else:
            called = None

        if called in BANNED_CALL_NAMES:
            self._reject(
                node,
                f"the call to '{called}()' is not allowed. It can execute new code or reach "
                "resources outside the compliance engine's restricted namespace.",
            )
        self.generic_visit(node)

    def visit_Attribute(self, node):
        """Reject dunder attribute access -- the usual route out of a restricted namespace."""
        if _is_dunder(node.attr):
            self._reject(
                node,
                f"access to the dunder attribute '.{node.attr}' is not allowed. Dunder attributes "
                "(such as __class__, __globals__, and __subclasses__) are the standard way to reach "
                "objects outside the compliance engine's restricted namespace.",
            )
        self.generic_visit(node)

    def visit_Name(self, node):
        """Reject references to modules that give access to the host process."""
        if node.id in BANNED_MODULE_NAMES:
            self._reject(
                node,
                f"the name '{node.id}' is not allowed. Rules have no access to the '{node.id}' module, "
                "and 're' is the only module available to them.",
            )
        self.generic_visit(node)


def validate_rule_code(rule_code):
    """Statically reject rule_code that a ComplianceRule must not store or execute.

    Parses `rule_code` and raises `django.core.exceptions.ValidationError` if it
    fails to parse, or if it contains an import, a call to a banned callable,
    dunder attribute access, or a reference to a banned module. A clean return
    means only that none of those constructs are present -- see the bypasses
    listed at the top of this module.
    """
    try:
        tree = ast.parse(rule_code)
    except SyntaxError as exc:
        # Offset/line can be None for some SyntaxErrors, so report what we have.
        location = f" (line {exc.lineno})" if exc.lineno else ""
        raise ValidationError(f"rule_code is not valid Python{location}: {exc.msg}.") from exc

    visitor = _RuleCodeVisitor()
    visitor.visit(tree)

    if visitor.violations:
        messages = [message for _, _, message in sorted(visitor.violations)]
        raise ValidationError(["rule_code was rejected by static validation:"] + messages)
