"""Example ComplianceRule definitions, in Netpicker's example-rule style.

A plain Python data module rather than a Django fixture or data migration: these rules
run user-supplied `rule_code` through `ComplianceRule.clean()` (see `validation.py`), and
a fixture loaded via `loaddata` bypasses model validation entirely (`raw=True`), which
would let unvalidated rule_code slip past the exact check this app exists to enforce. A
migration would apply this example content unconditionally to every install/upgrade,
which is wrong for optional example data. Consumed by the M6 seed-data Job, which is
expected to create these via `ComplianceRule.objects.get_or_create()` +
`validated_save()`, keeping the same validation path real user-authored rules go through.

Each entry's `rule_code` follows the M2 sandbox contract in `engine.py`/`validation.py`:
one top-level function, no imports, only `re` available beyond the builtins allowlist.
"""

from nautobot_pytest_compliance_rule_engine.models import ComplianceRuleSeverityChoices

EXAMPLE_COMPLIANCE_RULES = [
    {
        "name": "Login banner configured",
        "description": (
            "Checks that a login or MOTD banner is configured. Most acceptable-use and "
            "legal-notice policies require an unauthorized-access warning to be displayed "
            "before authentication; a missing banner can undermine a device's legal "
            "standing in an incident response."
        ),
        "severity": ComplianceRuleSeverityChoices.LOW,
        "rule_code": (
            "def check_login_banner_configured(configuration):\n"
            '    assert "banner login" in configuration or "banner motd" in configuration, (\n'
            '        "No login or MOTD banner configured"\n'
            "    )"
        ),
    },
    {
        "name": "NTP server configured",
        "description": (
            "Checks that at least one NTP server is configured. Accurate, synchronized "
            "clocks are a prerequisite for correlating logs across devices, for "
            "certificate validity checks, and for any time-ordered incident "
            "investigation -- an unsynchronized device undermines all of these."
        ),
        "severity": ComplianceRuleSeverityChoices.MEDIUM,
        "rule_code": (
            "def check_ntp_server_configured(configuration):\n"
            '    assert re.search(r"ntp server \\S+", configuration), "No NTP server configured"'
        ),
    },
    {
        "name": "SNMP community string is not default",
        "description": (
            "Checks that the SNMP community string is not left at the well-known "
            'default value of "public" or "private". These defaults are the first '
            "thing any automated scanner tries, and a device using one effectively "
            "has no SNMP access control at all."
        ),
        "severity": ComplianceRuleSeverityChoices.HIGH,
        "rule_code": (
            "def check_snmp_community_not_default(configuration):\n"
            '    match = re.search(r"snmp-server community (\\S+)", configuration, re.IGNORECASE)\n'
            '    assert match is None or match.group(1).lower() not in ("public", "private"), (\n'
            '        "SNMP community string uses a default value (public/private)"\n'
            "    )"
        ),
    },
    {
        "name": "SSH-only management access",
        "description": (
            "Checks that Telnet is not enabled for management access (`transport input "
            "telnet` or `transport input all`). Telnet sends credentials and session "
            "traffic in cleartext, so any device reachable over the network with Telnet "
            "enabled is one packet capture away from full compromise; SSH should be the "
            "only transport in use."
        ),
        "severity": ComplianceRuleSeverityChoices.MEDIUM,
        "rule_code": (
            "def check_ssh_only_management(configuration):\n"
            '    telnet_enabled = "transport input telnet" in configuration or "transport input all" in configuration\n'
            '    assert not telnet_enabled, "Telnet is enabled for management access; SSH-only is required"'
        ),
    },
    {
        "name": "Unencrypted HTTP management server disabled",
        "description": (
            "Checks that the device's built-in unencrypted HTTP management server is "
            "disabled. Plaintext web-based device management has repeatedly been the "
            "entry point for real-world vendor advisories and CVEs over the years -- "
            "credentials and session tokens travel in the clear, and the service is "
            "often reachable well beyond where an admin expects. This rule is an "
            "original example in that same spirit, not a reproduction of any specific "
            "advisory's text."
        ),
        "severity": ComplianceRuleSeverityChoices.HIGH,
        "rule_code": (
            "def check_insecure_http_server_disabled(configuration):\n"
            '    assert "no ip http server" in configuration or "ip http server" not in configuration, (\n'
            '        "Unencrypted HTTP management server is enabled; disable it in favor of HTTPS"\n'
            "    )"
        ),
    },
]
