import frappe


def order_query_conditions(user):
    """Row-level filter for Maintenance Orders."""
    if not user:
        user = frappe.session.user
    if "PM Manager" in frappe.get_roles(user) or "Maintenance Planner" in frappe.get_roles(user):
        return ""
    # Technicians see only orders assigned to their team or themselves
    teams = frappe.get_all(
        "Maintenance Team Member",
        filters={"team_member": user},
        pluck="parent",
    )
    if not teams:
        return "1=0"  # no teams, no orders

    teams_str = ", ".join(f"'{t}'" for t in teams)
    return f"(`tabMaintenance Order`.maintenance_team in ({teams_str}) or `tabMaintenance Order`.owner = '{user}')"


def notification_query_conditions(user):
    """Operators see only their own notifications; others see all."""
    if not user:
        user = frappe.session.user
    if any(r in frappe.get_roles(user) for r in ["PM Manager", "Maintenance Planner", "Technician"]):
        return ""
    return f"`tabMaintenance Notification`.reported_by = '{user}'"


def order_has_permission(doc, user=None, permission_type=None):
    """Additional permission check for Maintenance Orders."""
    if not user:
        user = frappe.session.user
    if any(r in frappe.get_roles(user) for r in ["PM Manager", "Maintenance Planner"]):
        return True
    if doc.owner == user:
        return True
    if doc.maintenance_team:
        teams = frappe.get_all(
            "Maintenance Team Member",
            filters={"team_member": user, "parent": doc.maintenance_team},
        )
        if teams:
            return True
    return False