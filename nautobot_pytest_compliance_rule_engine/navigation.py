"""Navigation menu items for nautobot_pytest_compliance_rule_engine app."""

from nautobot.apps.ui import NavMenuAddButton, NavMenuGroup, NavMenuItem, NavMenuTab

menu_items = (
    NavMenuTab(
        name="Compliance",
        weight=1500,
        groups=(
            NavMenuGroup(
                name="Pytest Compliance Rule Engine",
                weight=100,
                items=(
                    NavMenuItem(
                        link="plugins:nautobot_pytest_compliance_rule_engine:compliancerule_list",
                        name="Compliance Rules",
                        weight=100,
                        permissions=["nautobot_pytest_compliance_rule_engine.view_compliancerule"],
                        buttons=(
                            NavMenuAddButton(
                                link="plugins:nautobot_pytest_compliance_rule_engine:compliancerule_add",
                                permissions=["nautobot_pytest_compliance_rule_engine.add_compliancerule"],
                            ),
                        ),
                    ),
                    NavMenuItem(
                        link="plugins:nautobot_pytest_compliance_rule_engine:complianceruleset_list",
                        name="Compliance Rule Sets",
                        weight=200,
                        permissions=["nautobot_pytest_compliance_rule_engine.view_complianceruleset"],
                        buttons=(
                            NavMenuAddButton(
                                link="plugins:nautobot_pytest_compliance_rule_engine:complianceruleset_add",
                                permissions=["nautobot_pytest_compliance_rule_engine.add_complianceruleset"],
                            ),
                        ),
                    ),
                    NavMenuItem(
                        link="plugins:nautobot_pytest_compliance_rule_engine:compliancetestresult_list",
                        name="Compliance Results",
                        weight=300,
                        permissions=["nautobot_pytest_compliance_rule_engine.view_compliancetestresult"],
                    ),
                ),
            ),
        ),
    ),
)
