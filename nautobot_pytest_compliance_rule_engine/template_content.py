"""Template content injections for nautobot_pytest_compliance_rule_engine app."""

from nautobot.apps.ui import DistinctViewTab, TemplateExtension

# Rendered after Nautobot's own reserved tab weights (Tab.WEIGHT_MAIN_TAB=100 through
# Tab.WEIGHT_CHANGELOG_TAB=700), so this tab lands at the end of the tab bar.
COMPLIANCE_TAB_WEIGHT = 1000


class DeviceComplianceTab(TemplateExtension):
    """Add a "Compliance" tab to the Device detail page.

    An inline `Tab` (rendered via its `panels`) can't be used here: Nautobot 2.4.5's
    `dcim/device.html` fully overrides `generic/object_retrieve.html`'s `content` block without
    including `{% plugin_object_detail_tab_content %}`, so a `Tab`'s panels never actually render
    on the Device detail page, even though the tab label itself still shows up (that comes from
    the untouched `header` block). A `DistinctViewTab` is used instead, linking to
    `views.DeviceComplianceTabView`, whose template extends `dcim/device/base.html` directly and
    so bypasses that override. That view shows the device's most recent ComplianceTestResult
    rows, reusing the same table used by the standalone results list view (see
    tables.ComplianceTestResultTable).
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
