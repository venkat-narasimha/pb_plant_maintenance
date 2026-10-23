import frappe
from frappe import _


def after_install():
    """Run after app installation."""
    setup_roles()
    setup_workspace()
    frappe.db.commit()
    print(_("PM Custom app installed successfully."))


def setup_roles():
    """Create default roles if they don't exist."""
    roles = ["PM Manager", "Maintenance Planner", "Technician", "Operator"]
    for role_name in roles:
        if not frappe.db.exists("Role", role_name):
            role = frappe.new_doc("Role")
            role.role_name = role_name
            role.desk_access = 1
            role.flags.ignore_permissions = True
            role.insert()


def setup_workspace():
    """Create a workspace for the PM module."""
    if frappe.db.exists("Workspace", "Plant Maintenance"):
        return
    workspace = frappe.new_doc("Workspace")
    workspace.label = "Plant Maintenance"
    workspace.title = "Plant Maintenance"
    workspace.module = "pb_plant_maintenance"
    workspace.public = 1
    workspace.is_hidden = 0
    workspace.icon = "tool"
    workspace.indicator_color = "blue"

    shortcuts = [
        ("Equipment", "Equipment", "Equity"),
        ("Maintenance Order", "Maintenance Order", "Tool"),
        ("Maintenance Notification", "Maintenance Notification", "Notification"),
        ("Maintenance Plan", "Maintenance Plan", "Calendar"),
    ]
    for label, link_to, icon in shortcuts:
        workspace.append("shortcuts", {
            "label": label, "link_to": link_to,
            "type": "DocType", "icon": icon,
        })

    workspace.flags.ignore_permissions = True
    workspace.insert()