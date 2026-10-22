import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": _("Equipment"), "fieldname": "equipment", "fieldtype": "Link",
         "options": "Equipment", "width": 150},
        {"label": _("Order"), "fieldname": "order", "fieldtype": "Link",
         "options": "Maintenance Order", "width": 140},
        {"label": _("Order Type"), "fieldname": "order_type", "fieldtype": "Data", "width": 100},
        {"label": _("Actual Start"), "fieldname": "actual_start",
         "fieldtype": "Datetime", "width": 130},
        {"label": _("Actual End"), "fieldname": "actual_end",
         "fieldtype": "Datetime", "width": 130},
        {"label": _("Downtime (hrs)"), "fieldname": "downtime_hours",
         "fieldtype": "Float", "width": 110},
        {"label": _("Total Cost"), "fieldname": "total_cost",
         "fieldtype": "Currency", "width": 110},
    ]


def get_data(filters):
    conditions = ["docstatus = 1", "actual_start IS NOT NULL", "actual_end IS NOT NULL"]
    values = {}

    if filters.get("from_date"):
        conditions.append("actual_start >= %(from_date)s")
        values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions.append("actual_end <= %(to_date)s")
        values["to_date"] = filters["to_date"]
    if filters.get("equipment"):
        conditions.append("equipment = %(equipment)s")
        values["equipment"] = filters["equipment"]

    where = " AND ".join(conditions)
    return frappe.db.sql(f"""
        SELECT
            name as "order", equipment, order_type, actual_start, actual_end,
            downtime_hours, total_cost
        FROM `tabMaintenance Order`
        WHERE {where}
        ORDER BY downtime_hours DESC
    """, values, as_dict=True)