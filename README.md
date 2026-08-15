# nautobot-pytest-compliance-rule-engine

A Nautobot App that lets you define network compliance rules as small, pytest-style
Python snippets and run them against device data as a Nautobot Job, recording a
pass/fail/error result for every rule x device pairing.

Nautobot's [Golden Config](https://docs.nautobot.com/projects/golden-config/en/latest/)
app checks compliance by diffing a device's actual configuration against an
*intended* configuration built from a Jinja2 template -- it's very good at "does this
config match what it's supposed to look like." This app answers a different question:
"does this config (or command output) satisfy an arbitrary assertion," without needing
to author or maintain an intended-config template at all. A rule here is a Python
function containing one or more `assert` statements -- free-form checks like "an NTP
server is configured," "the SNMP community string isn't left at a default value," or
"Telnet is disabled" -- run directly against a device's backed-up configuration or live
command output. The two apps are complementary, not competing: Golden Config for
structured config drift, this app for arbitrary, code-expressed policy checks.

## Installation

Install the package into the same Python environment as your Nautobot instance:

```bash
pip install nautobot-pytest-compliance-rule-engine
```

Add the app to `PLUGINS` in your `nautobot_config.py`:

```python
PLUGINS = ["nautobot_pytest_compliance_rule_engine"]
```

Run migrations and restart Nautobot:

```bash
nautobot-server migrate
nautobot-server post_upgrade  # if you use it in your deployment
```

Once installed, an optional **Load Example Compliance Rules (optional)** Job is
available under Jobs, which seeds five example rules (banner check, NTP, SNMP
community string, SSH-only management, and an unencrypted-HTTP-management-server
check) so there's something to look at and run immediately.

## Configuration

No `PLUGINS_CONFIG` settings are required or currently read by this app -- adding it to
`PLUGINS` as shown above is sufficient.

## How to write a ComplianceRule

A `ComplianceRule` has a `name`, an optional `description`, a `severity`
(low/medium/high), an optional `platform` (leave blank to apply to every platform),
and a `rule_code` field: the Python that actually runs.

`rule_code` must define **exactly one top-level function**. That function's parameter
names tell the engine what to hand it -- declare `configuration` to receive the
device's configuration as a string, `commands` to receive a `dict` of command output
keyed by the command string, either, or neither. The function should `assert` whatever
the rule is checking; there's no return value to populate.

A worked example -- requiring an NTP server to be configured:

```python
def check_ntp_server_configured(configuration):
    assert "ntp server" in configuration, "No NTP server configured"
```

Running this rule against a device produces one of three outcomes, recorded as a
`ComplianceTestResult`:

| What happens in the rule | Result |
|---|---|
| No exception | `pass` |
| `AssertionError` (your `assert` failed) | `fail`, with the assertion message as the output |
| Any other exception | `error`, with the exception type and message as the output |

### What's off-limits

`rule_code` runs in a restricted namespace, not your full Python environment. This is
**defence in depth against mistakes and low-effort mischief by trusted rule authors,
not a security boundary** -- see
[`docs/adr/0001-rule-sandboxing.md`](docs/adr/0001-rule-sandboxing.md) for the full
threat model. In practice, a rule may not:

- **Import anything.** No `import` or `from ... import ...` statements at all --
  everything a rule needs arrives as a function argument, and the `re` module is
  already available without importing it.
- **Call `eval`, `exec`, `compile`, `__import__`, `open`, `globals`, `locals`, `vars`,
  `getattr`, `setattr`, `delattr`, `input`, `breakpoint`, or `memoryview`.**
- **Access any dunder attribute** (`__class__`, `__globals__`, `__subclasses__`, and
  so on) -- the usual route out of a restricted namespace.
- **Reference `os`, `sys`, `subprocess`, `shutil`, `socket`, `pathlib`, `importlib`, or
  `builtins` by name.**
- **Define more than one top-level function, or an `async def`.**

Beyond those, only a curated set of builtins is available: `len`, `str`, `int`,
`float`, `bool`, `isinstance`, `any`, `all`, `sorted`, `enumerate`, `zip`, `min`, `max`,
`sum`, `abs`, `round`, `list`, `dict`, `set`, `tuple`, `range`, and `print`.

A rule that breaks any of these rules is rejected with a validation error when you try
to save it, before it's ever persisted or run.

## Screenshots

TODO -- these need a live Nautobot instance to capture. Add screenshots here after
installing the app into a WSL Nautobot instance (see issue #28) of:

- The Compliance Rule list and detail views
- The Compliance tab on a Device's detail page
- The fleet-wide Compliance Dashboard widget

## License

No license is currently declared for this repository, matching the rest of this
account's repositories.
