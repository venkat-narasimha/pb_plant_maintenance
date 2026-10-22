import frappe
from frappe import _
from frappe.utils import flt, nowdate


def validate_order(doc, method=None):
    """Additional validation before order submission."""
    if doc.is_subcontracted and not doc.vendor:
        frappe.throw(_("Vendor is required for subcontracted orders."))


def post_maintenance_costs(doc, method=None):
    """Post labor and material costs on order completion."""
    if doc.status != "Completed":
        return
    create_labor_journal_entry(doc)
    # Material costs are posted via Stock Entry already


def reverse_maintenance_costs(doc, method=None):
    """Reverse journal entries on order cancellation."""
    jes = frappe.get_all(
        "Journal Entry",
        filters={
            "pm_maintenance_order": doc.name,
            "docstatus": 1,
        },
        pluck="name",
    )
    for je_name in jes:
        je = frappe.get_doc("Journal Entry", je_name)
        je.cancel()


def create_labor_journal_entry(doc):
    if flt(doc.total_labor_cost) <= 0:
        return
    if frappe.db.exists("Journal Entry", {"pm_maintenance_order": doc.name, "docstatus": 1}):
        return

    settings = frappe.get_single("PM Settings")
    expense_account = settings.default_expense_account_labor
    if not expense_account:
        frappe.log_error(
            f"No default labor expense account configured for order {doc.name}",
            "PM Order Posting"
        )
        return

    company = frappe.defaults.get_user_default("Company")
    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.company = company
    je.posting_date = nowdate()
    je.user_remark = _("Maintenance labor cost for order {0}").format(doc.name)
    je.pm_maintenance_order = doc.name

    # Debit expense
    je.append("accounts", {
        "account": expense_account,
        "debit_in_account_currency": flt(doc.total_labor_cost),
        "cost_center": doc.cost_center,
    })

    # Credit - use a clearing/suspense account from settings
    # (Assumes a labor absorption account exists)
    credit_account = frappe.db.get_value(
        "Company", company, "default_expense_account"
    ) or expense_account

    je.append("accounts", {
        "account": credit_account,
        "credit_in_account_currency": flt(doc.total_labor_cost),
        "cost_center": doc.cost_center,
    })

    je.flags.ignore_permissions = True
    je.insert()
    je.submit()


def handle_status_change(doc, method=None):
    """Handle status transitions for already-submitted orders."""
    if doc.status == "Completed":
        # Update linked notification
        if doc.notification:
            frappe.db.set_value(
                "Maintenance Notification", doc.notification, "status", "Closed"
            )
        # Update linked maintenance plan tasks
        update_plan_tasks(doc)


def update_plan_tasks(order):
    """Mark plan tasks as completed when order is completed."""
    if not order.equipment:
        return
    plans = frappe.get_all(
        "Maintenance Plan",
        filters={"equipment": order.equipment, "status": "Active"},
        pluck="name",
    )
    for plan_name in plans:
        plan = frappe.get_doc("Maintenance Plan", plan_name)
        modified = False
        for task in plan.tasks:
            if task.status in ("Scheduled", "Overdue", "In Progress"):
                task.last_completion_date = nowdate()
                task.next_due_date = plan.compute_next_due(
                    nowdate(), task.periodicity, task.periodicity_value
                )
                task.status = "Scheduled"
                modified = True
        if modified:
            plan.flags.ignore_permissions = True
            plan.save()


def update_order_from_confirmation(doc, method=None):
    """Update order when a confirmation is submitted."""
    order = frappe.get_doc("Maintenance Order", doc.maintenance_order)
    if doc.confirmation_type == "Final":
        order.status = "Completed"
        order.actual_end = doc.confirmation_date
    elif doc.confirmation_type == "Partial":
        if order.status not in ("In Progress", "Completed"):
            order.status = "In Progress"
        if not order.actual_start:
            order.actual_start = doc.confirmation_date
    order.flags.ignore_validate_update_after_submit = True
    order.save()


def reverse_confirmation(doc, method=None):
    """Reverse order state when confirmation is cancelled."""
    order = frappe.get_doc("Maintenance Order", doc.maintenance_order)
    order.status = "In Progress"
    order.flags.ignore_validate_update_after_submit = True
    order.save()