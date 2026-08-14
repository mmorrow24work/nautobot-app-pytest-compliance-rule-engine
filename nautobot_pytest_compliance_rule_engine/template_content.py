"""Template content injections for nautobot_pytest_compliance_rule_engine app."""

from nautobot.apps.ui import ObjectsTablePanel, SectionChoices, Tab, TemplateExtension

from nautobot_pytest_compliance_rule_engine.tables import ComplianceTestResultTable

# How many of the device's most recent ComplianceTestResult rows to show in the tab.
RECENT_RESULTS_LIMIT = 20

# Rendered after Nautobot's own reserved tab weights (Tab.WEIGHT_MAIN_TAB=100 through
# Tab.WEIGHT_CHANGELOG_TAB=700), so this tab lands at the end of the tab bar.
COMPLIANCE_TAB_WEIGHT = 1000


class DeviceComplianceTab(TemplateExtension):
    """Add a "Compliance" tab to the Device detail page.

    Shows the device's most recent ComplianceTestResult rows, reusing the same table used by
    the standalone results list view (see tables.ComplianceTestResultTable).
    """

    model = "dcim.device"

    object_detail_tabs = [
        Tab(
            tab_id="compliance",
            label="Compliance",
            weight=COMPLIANCE_TAB_WEIGHT,
            panels=[
                ObjectsTablePanel(
                    weight=100,
                    section=SectionChoices.FULL_WIDTH,
                    table_class=ComplianceTestResultTable,
                    table_filter="device",
                    table_title="Compliance Results",
                    select_related_fields=["rule"],
                    max_display_count=RECENT_RESULTS_LIMIT,
                    add_button_route=None,
                ),
            ],
        ),
    ]


template_extensions = [DeviceComplianceTab]
