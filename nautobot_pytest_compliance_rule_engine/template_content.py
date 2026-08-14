"""Template content injections for nautobot_pytest_compliance_rule_engine app."""

from nautobot.apps.ui import DistinctViewTab, TemplateExtension

# Rendered after Nautobot's own reserved tab weights (Tab.WEIGHT_MAIN_TAB=100 through
# Tab.WEIGHT_CHANGELOG_TAB=700), so this tab lands at the end of the tab bar.
COMPLIANCE_TAB_WEIGHT = 1000


class DeviceComplianceTab(TemplateExtension):
    """Add a "Compliance" tab to the Device detail page.

    A `DistinctViewTab` linking to `views.DeviceComplianceTabView`, rather than an inline `Tab`
    rendered via its `panels`. Under Nautobot 2.4.5 that was forced: `dcim/device.html` fully
    overrode `generic/object_retrieve.html`'s `content` block without including
    `{% plugin_object_detail_tab_content %}`, so an inline `Tab`'s panels never rendered. Nautobot
    3.x removed that override -- `dcim/device.html` now only adds a `javascript` block -- so an
    inline `Tab` would work today.

    The distinct view is kept regardless: it is what Nautobot 3.x core itself uses for the
    Device's own config/status/LLDP tabs, and it keeps the results on their own URL rather than
    loading them with every Device detail page view. That view shows the device's most recent
    ComplianceTestResult rows, reusing the same table used by the standalone results list view
    (see tables.ComplianceTestResultTable).
    """

    model = "dcim.device"

    object_detail_tabs = [
        DistinctViewTab(
            tab_id="compliance",
            label="Compliance",
            weight=COMPLIANCE_TAB_WEIGHT,
            url_name="plugins:nautobot_pytest_compliance_rule_engine:device_compliance_tab",
        ),
    ]


template_extensions = [DeviceComplianceTab]
