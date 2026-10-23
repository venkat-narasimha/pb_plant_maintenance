import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate, today, flt
from frappe.utils.user import get_users_with_role


def schedule_preventive_maintenance():
    """Daily: Create maintenance orders for due plan tasks."""
    today_date = getdate(today())
    active_plans = frappe.get_all(
        "Maintenance Plan",
        filters={"status": "Active", "auto_create_orders": 1},
        pluck="name",
    )

    for plan_name in active_plans:
        try:
            plan = frappe.get_doc("Maintenance Plan", plan_name)
            if plan.end_date and getdate(plan.end_date) < today_date:
                continue
            due_tasks = plan.get_due_tasks(today_date)
            for task in due_tasks:
                create_order_for_task(plan, task)
        except Exception as e:
            frappe.log_error(
                f"Error scheduling plan {plan_name}: {e}",
                "PM Schedule Task"
            )


def create_order_for_task(plan, task):
    """Create a maintenance order for a due plan task."""
    # Check if order already exists
    existing = frappe.db.exists("Maintenance Order", {
        "equipment": plan.equipment,
        "description": ["like", f"%{task.task_description[:50]}%"],
        "status": ["not in", ["Closed", "Cancelled"]],
        "creation": [">", add_days(nowdate(), -7)],
    })
    if existing:
        return

    order = frappe.new_doc("Maintenance Order")
    order.order_type = "Preventive" if task.maintenance_type == "Preventive" else \
                       "Calibration" if task.maintenance_type == "Calibration" else "Inspection"
    order.equipment = plan.equipment
    order.functional_location = plan.functional_location
    order.maintenance_team = plan.maintenance_team
    order.priority = "Medium"
    order.description = _("Scheduled maintenance: {0}").format(task.task_description)
    order.planned_start = task.next_due_date
    order.planned_end = add_days(task.next_due_date, 1)
    order.status = "Planned"

    settings = frappe.get_single("PM Settings")
    order.cost_center = settings.default_cost_center

    # Copy task list if defined
    if task.task_list:
        copy_task_list_operations(task.task_list, order)

    order.flags.ignore_permissions = True
    order.insert()
    order.submit()

    # Update task
    task.status = "In Progress"
    plan.flags.ignore_permissions = True
    plan.save()

    # Notify team
    notify_maintenance_team(order)


def copy_task_list_operations(task_list_name, order):
    task_list = frappe.get_doc("Maintenance Task List", task_list_name)
    for op in task_list.operations:
        order.append("operations", {
            "operation_number": op.operation_number,
            "operation_description": op.operation_description,
            "work_center": op.work_center,
            "planned_duration": op.duration_hours,
            "status": "Pending",
        })


def send_maintenance_reminders():
    """Daily: Send reminders for upcoming maintenance tasks."""
    today_date = getdate(today())
    active_plans = frappe.get_all(
        "Maintenance Plan", filters={"status": "Active"}, pluck="name"
    )
    for plan_name in active_plans:
        plan = frappe.get_doc("Maintenance Plan", plan_name)
        lead_days = plan.lead_time_days or 3
        reminder_date = add_days(today_date, lead_days)
        for task in plan.tasks:
            if not task.next_due_date:
                continue
            due_date = getdate(task.next_due_date)
            if due_date == reminder_date:
                send_task_reminder(plan, task)


def send_task_reminder(plan, task):
    subject = _("Upcoming Maintenance: {0}").format(task.task_description)
    message = f"""
    <h3>Maintenance Reminder</h3>
    <p><b>Plan:</b> {plan.plan_name}</p>
    <p><b>Equipment:</b> {plan.equipment or plan.functional_location}</p>
    <p><b>Task:</b> {task.task_description}</p>
    <p><b>Due Date:</b> {task.next_due_date}</p>
    <p><b>Type:</b> {task.maintenance_type}</p>
    """
    recipients = get_maintenance_recipients(plan)
    if recipients:
        frappe.sendmail(
            recipients=recipients, subject=subject, message=message,
            reference_doctype="Maintenance Plan", reference_name=plan.name,
        )


def check_overdue_notifications():
    """Daily: Flag overdue notifications."""
    settings = frappe.get_single("PM Settings")
    overdue_days = settings.notify_overdue_days or 1
    cutoff = add_days(nowdate(), -overdue_days)
    overdue = frappe.get_all(
        "Maintenance Notification",
        filters={
            "status": ["in", ["Open", "In Progress"]],
            "docstatus": 1,
            "notification_date": ["<", cutoff],
        },
        pluck="name",
    )
    for notif_name in overdue:
        notification = frappe.get_doc("Maintenance Notification", notif_name)
        escalate_notification(notification)


def escalate_notification(notification):
    recipients = get_users_with_role("PM Manager")
    if not recipients:
        return
    subject = _("Overdue Notification: {0}").format(notification.name)
    message = f"""
    <p>Notification <b>{notification.name}</b> is overdue.</p>
    <p>Equipment: {notification.equipment}</p>
    <p>Priority: {notification.priority}</p>
    <p>Reported: {notification.notification_date}</p>
    """
    frappe.sendmail(
        recipients=recipients, subject=subject, message=message,
        reference_doctype="Maintenance Notification", reference_name=notification.name,
    )


def check_overdue_orders():
    """Daily: Flag orders past planned end date."""
    overdue = frappe.get_all(
        "Maintenance Order",
        filters={
            "status": ["in", ["Planned", "In Progress"]],
            "docstatus": 1,
            "planned_end": ["<", nowdate()],
        },
        pluck="name",
    )
    for order_name in overdue:
        order = frappe.get_doc("Maintenance Order", order_name)
        if order.maintenance_team:
            notify_maintenance_team(order, overdue=True)


def check_measurement_alerts():
    """Hourly: Check for overdue measurements."""
    points = frappe.get_all(
        "Measuring Point",
        filters={"reading_frequency": ["is", "set"]},
        fields=["name", "reading_frequency", "last_reading_date", "equipment"],
    )
    today_date = getdate(today())
    for mp in points:
        if not mp.last_reading_date:
            continue
        freq_days = {
            "Daily": 1, "Weekly": 7, "Monthly": 30, "Quarterly": 90,
        }.get(mp.reading_frequency, 30)
        next_due = add_days(mp.last_reading_date, freq_days)
        if getdate(next_due) <= today_date:
            create_measurement_todo(mp)


def create_measurement_todo(mp):
    existing = frappe.db.exists("ToDo", {
        "reference_type": "Measuring Point",
        "reference_name": mp.name,
        "status": "Open",
    })
    if existing:
        return
    todo = frappe.new_doc("ToDo")
    todo.description = _("Record measurement for {0}").format(mp.name)
    todo.reference_type = "Measuring Point"
    todo.reference_name = mp.name
    todo.owner = "Administrator"
    todo.flags.ignore_permissions = True
    todo.insert()


def generate_maintenance_kpis():
    """Weekly: Pre-compute KPI data for dashboard."""
    from pb_plant_maintenance.utils.helpers import get_pm_settings
    kpis = compute_kpis()
    frappe.cache().set_value("pm_weekly_kpis", kpis, expires_in_sec=7 * 24 * 3600)


def compute_kpis():
    from frappe.utils import add_days
    last_30 = add_days(nowdate(), -30)

    total_orders = frappe.db.count(
        "Maintenance Order",
        {"docstatus": 1, "creation": [">=", last_30]},
    )
    completed_orders = frappe.db.count(
        "Maintenance Order",
        {"docstatus": 1, "status": "Completed", "creation": [">=", last_30]},
    )
    total_cost = frappe.db.sql("""
        SELECT COALESCE(SUM(total_cost), 0) FROM `tabMaintenance Order`
        WHERE docstatus = 1 AND creation >= %s
    """, last_30)[0][0]

    return {
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "completion_rate": (completed_orders / total_orders * 100) if total_orders else 0,
        "total_cost": flt(total_cost),
    }


def cleanup_old_logs():
    """Weekly: Remove old error logs related to PM."""
    frappe.db.sql("""
        DELETE FROM `tabError Log`
        WHERE method LIKE 'pb_plant_maintenance%'
        AND creation < DATE_SUB(NOW(), INTERVAL 90 DAY)
    """)


def generate_monthly_reports():
    """Monthly: Generate compliance and cost reports."""
    # Placeholder for automated report generation and emailing
    pass


def notify_maintenance_team(order, overdue=False):
    """Send notification to the maintenance team."""
    recipients = get_maintenance_recipients(order)
    if not recipients:
        return
    subject = _("Overdue Maintenance Order: {0}") if overdue else _("New Maintenance Order: {0}")
    subject = subject.format(order.name)
    message = f"""
    <h3>Maintenance Order {order.name}</h3>
    <p><b>Type:</b> {order.order_type}</p>
    <p><b>Priority:</b> {order.priority}</p>
    <p><b>Equipment:</b> {order.equipment or 'N/A'}</p>
    <p><b>Planned:</b> {order.planned_start} to {order.planned_end}</p>
    <p><a href="/app/maintenance-order/{order.name}">Open Order</a></p>
    """
    frappe.sendmail(
        recipients=recipients, subject=subject, message=message,
        reference_doctype="Maintenance Order", reference_name=order.name,
    )


def get_maintenance_recipients(doc):
    recipients = set()
    if doc.maintenance_team:
        members = frappe.get_all(
            "Maintenance Team Member",
            filters={"parent": doc.maintenance_team},
            fields=["team_member"],
        )
        recipients.update(m.team_member for m in members if m.team_member)
    return list(recipients)