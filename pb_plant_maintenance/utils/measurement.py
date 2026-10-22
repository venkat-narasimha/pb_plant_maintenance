import frappe


def process_measurement_document(doc, method=None):
    """Process a measurement document on submission."""
    # Trigger counter-based maintenance plan checks
    check_counter_based_plans(doc)


def check_counter_based_plans(doc):
    """Check if any counter-based plans need triggering."""
    plans = frappe.get_all(
        "Maintenance Plan",
        filters={
            "plan_type": "Counter-Based",
            "equipment": doc.equipment,
            "status": "Active",
        },
        pluck="name",
    )
    for plan_name in plans:
        plan = frappe.get_doc("Maintenance Plan", plan_name)
        for task in plan.tasks:
            if task.counter_limit and doc.reading_value >= task.counter_limit:
                if task.status == "Scheduled":
                    task.status = "Overdue"
                    plan.flags.ignore_permissions = True
                    plan.save()
                    frappe.publish_realtime(
                        "pm_counter_limit_reached",
                        {"plan": plan_name, "task": task.task_description},
                    )