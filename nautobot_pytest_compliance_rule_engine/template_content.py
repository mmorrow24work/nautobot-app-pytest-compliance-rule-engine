"""Template content injections for nautobot_pytest_compliance_rule_engine app."""

from nautobot.apps.ui import DistinctViewTab, TemplateExtension

# Rendered after Nautobot's own reserved tab weights (Tab.WEIGHT_MAIN_TAB=100 through
# Tab.WEIGHT_CHANGELOG_TAB=700), so this tab lands at the end of the tab bar.
COMPLIANCE_TAB_WEIGHT = 1000


class DeviceComplianceTab(TemplateExtension):
    """Add a "Compliance" tab to the Device detail page.

    This is a `DistinctViewTab` linking to `views.DeviceComplianceTabView`, rather than an
    inline `Tab` rendered via its `panels`. Under Nautobot 2.x that was forced: `dcim/device.html`
    fully overrode `generic/object_retrieve.html`'s `content` block without including
    `{% plugin_object_detail_tab_content %}`, so an inline `Tab`'s panels never rendered. Nautobot
    3.x no longer overrides that block -- `dcim/device.html` now only extends
    `generic/object_retrieve.html` and adds a `javascript` block -- so an inline `Tab` would work
    here today.

    The distinct view is kept regardless: it is the pattern Nautobot core itself uses for the
    Device "Config", "Status", and "LLDP Neighbors" tabs, it keeps the result rows off the main
    device page's query path, and it gives the tab its own URL. `plugin_object_detail_tabs.html`
    links it as `{{ tab.url }}?tab={{ tab_id }}`, and `ObjectView.get_extra_context()` reads that
    `?tab=` back into `active_tab`, so the tab highlights as active without extra wiring.

    The view shows the device's most recent ComplianceTestResult rows, reusing the same table
    used by the standalone results list view (see tables.ComplianceTestResultTable).
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
