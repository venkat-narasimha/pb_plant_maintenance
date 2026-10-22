import frappe
from frappe import _
from frappe.utils import flt, nowdate


@frappe.whitelist()
def convert_notification_to_order(notification, order_type="Corrective",
                                  planned_start=None, planned_end=None,
                                  maintenance_team=None):
    """Convert a notification to a maintenance order."""
    notif = frappe.get_doc("Maintenance Notification", notification)

    if notif.maintenance_order:
        frappe.throw(_("Notification already has a linked order: {0}").format(
            notif.maintenance_order))

    if notif.status == "Closed":
        frappe.throw(_("Cannot convert a closed notification."))

    settings = frappe.get_single("PM Settings")

    order = frappe.new_doc("Maintenance Order")
    order.order_type = order_type
    order.notification = notif.name
    order.equipment = notif.equipment
    order.functional_location = notif.functional_location
    order.priority = notif.priority
    order.description = notif.long_description or notif.short_description
    order.planned_start = planned_start or notif.notification_date
    order.planned_end = planned_end or order.planned_start
    order.maintenance_team = maintenance_team or (
        frappe.db.get_value("Equipment", notif.equipment, "maintenance_team")
        if notif.equipment else None
    )
    order.cost_center = settings.default_cost_center or frappe.db.get_value(
        "Company", frappe.defaults.get_user_default("Company"), "cost_center"
    )
    order.flags.ignore_permissions = True
    order.insert()
    order.submit()

    notif.status = "Converted to Order"
    notif.maintenance_order = order.name
    notif.converted_on = frappe.utils.now()
    notif.flags.ignore_permissions = True
    notif.save()

    return {"order": order.name, "status": "success"}


@frappe.whitelist()
def copy_task_list_to_order(task_list, order):
    """Copy operations from a task list to a maintenance order."""
    order_doc = frappe.get_doc("Maintenance Order", order)
    if order_doc.docstatus != 0:
        frappe.throw(_("Cannot modify a submitted order."))

    tl = frappe.get_doc("Maintenance Task List", task_list)
    if tl.status != "Active":
        frappe.throw(_("Task List {0} is not active.").format(task_list))

    existing_nums = {op.operation_number for op in order_doc.operations}
    for op in tl.operations:
        if op.operation_number in existing_nums:
            continue
        order_doc.append("operations", {
            "operation_number": op.operation_number,
            "operation_description": op.operation_description,
            "work_center": op.work_center,
            "planned_duration": op.duration_hours,
            "status": "Pending",
        })

    order_doc.flags.ignore_permissions = True
    order_doc.save()
    return {"added": len(tl.operations), "status": "success"}


@frappe.whitelist()
def record_measurement(measuring_point, reading_value, reading_date=None, remarks=None):
    """Record a measurement document via API."""
    if not frappe.has_permission("Measurement Document", "create"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    mp = frappe.get_doc("Measuring Point", measuring_point)
    doc = frappe.new_doc("Measurement Document")
    doc.measuring_point = measuring_point
    doc.equipment = mp.equipment
    doc.reading_value = flt(reading_value)
    doc.reading_date = reading_date or frappe.utils.now()
    doc.reading_by = frappe.session.user
    doc.remarks = remarks
    doc.flags.ignore_permissions = True
    doc.insert()
    doc.submit()
    return {"name": doc.name, "is_exception": doc.is_exception}


@frappe.whitelist()
def get_technician_dashboard():
    """Return dashboard data for the logged-in technician."""
    user = frappe.session.user
    orders = frappe.get_all(
        "Maintenance Order",
        filters={
            "docstatus": 1,
            "status": ["in", ["Planned", "In Progress"]],
        },
        or_filters=[
            ["owner", "=", user],
            ["maintenance_team", "in", _get_user_teams(user)],
        ],
        fields=["name", "equipment", "priority", "planned_start", "planned_end",
                "status", "order_type"],
        limit=50,
    )
    notifications = frappe.get_all(
        "Maintenance Notification",
        filters={"status": ["in", ["Open", "In Progress"]]},
        fields=["name", "short_description", "priority", "equipment", "notification_date"],
        limit=20,
    )
    return {
        "orders": orders,
        "notifications": notifications,
        "counts": {
            "open_orders": len(orders),
            "open_notifications": len(notifications),
        },
    }


def _get_user_teams(user):
    teams = frappe.get_all(
        "Asset Maintenance Team Member",
        filters={"user": user},
        pluck="parent",
    )
    return teams or [""]


@frappe.whitelist()
def schedule_plan_now(plan_name):
    """Manually trigger scheduling for a specific maintenance plan."""
    if not frappe.has_permission("Maintenance Plan", "write"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    from pb_plant_maintenance.tasks import create_order_for_task
    plan = frappe.get_doc("Maintenance Plan", plan_name)
    due_tasks = plan.get_due_tasks()
    created = []
    for task in due_tasks:
        create_order_for_task(plan, task)
        created.append(task.task_description)
    return {"scheduled_tasks": created}


@frappe.whitelist()
def get_kpis(from_date=None, to_date=None):
    """Return KPI data for dashboard."""
    from pb_plant_maintenance.tasks import compute_kpis
    cache_key = f"pm_kpis_{from_date}_{to_date}"
    kpis = frappe.cache().get_value(cache_key)
    if not kpis:
        kpis = compute_kpis()
        frappe.cache().set_value(cache_key, kpis, expires_in_sec=900)
    return kpis


@frappe.whitelist()
def get_equipment_history(equipment, limit=50):
    """Get complete maintenance history for an equipment."""
    orders = frappe.get_all(
        "Maintenance Order",
        filters={"equipment": equipment, "docstatus": 1},
        fields=["name", "order_type", "status", "planned_start", "actual_end",
                "total_cost", "downtime_hours"],
        order_by="planned_start desc",
        limit=limit,
    )
    notifications = frappe.get_all(
        "Maintenance Notification",
        filters={"equipment": equipment, "docstatus": 1},
        fields=["name", "notification_type", "priority", "short_description",
                "notification_date", "status"],
        order_by="notification_date desc",
        limit=limit,
    )
    return {"orders": orders, "notifications": notifications}