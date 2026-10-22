import frappe
from frappe import _


def validate_plan_tasks(doc, method=None):
    """Validate tasks in a maintenance plan."""
    for task in doc.tasks:
        if task.periodicity in ("Daily", "Weekly", "Monthly", "Quarterly",
                                "Half-Yearly", "Yearly"):
            if not task.periodicity_value or task.periodicity_value < 1:
                frappe.throw(
                    _("Periodicity value must be >= 1 for task: {0}").format(
                        task.task_description
                    )
                )