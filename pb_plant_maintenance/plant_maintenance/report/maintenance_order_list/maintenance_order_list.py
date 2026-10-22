import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": _("Order"), "fieldname": "name", "fieldtype": "Link",
         "options": "Maintenance Order", "width": 140},
        {"label": _("Type"), "fieldname": "order_type", "fieldtype": "Data", "width": 100},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": _("Priority"), "fieldname": "priority", "fieldtype": "Data", "width": 80},
        {"label": _("Equipment"), "fieldname": "equipment", "fieldtype": "Link",
         "options": "Equipment", "width": 130},
        {"label": _("Location"), "fieldname": "functional_location", "fieldtype": "Link",
         "options": "Functional Location", "width": 120},
        {"label": _("Planned Start"), "fieldname": "planned_start",
         "fieldtype": "Datetime", "width": 130},
        {"label": _("Planned End"), "fieldname": "planned_end",
         "fieldtype": "Datetime", "width": 130},
        {"label": _("Actual End"), "fieldname": "actual_end",
         "fieldtype": "Datetime", "width": 130},
        {"label": _("Downtime (hrs)"), "fieldname": "downtime_hours",
         "fieldtype": "Float", "width": 100},
        {"label": _("Labor Cost"), "fieldname": "total_labor_cost",
         "fieldtype": "Currency", "width": 100},
        {"label": _("Material Cost"), "fieldname": "total_material_cost",
         "fieldtype": "Currency", "width": 100},
        {"label": _("Total Cost"), "fieldname": "total_cost",
         "fieldtype": "Currency", "width": 100},
    ]


def get_data(filters):
    conditions = ["docstatus = 1"]
    values = {}

    if filters.get("from_date"):
        conditions.append("planned_start >= %(from_date)s")
        values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions.append("planned_start <= %(to_date)s")
        values["to_date"] = filters["to_date"]
    if filters.get("order_type"):
        conditions.append("order_type = %(order_type)s")
        values["order_type"] = filters["order_type"]
    if filters.get("status"):
        conditions.append("status = %(status)s")
        values["status"] = filters["status"]
    if filters.get("equipment"):
        conditions.append("equipment = %(equipment)s")
        values["equipment"] = filters["equipment"]
    if filters.get("priority"):
        conditions.append("priority = %(priority)s")
        values["priority"] = filters["priority"]

    where = " AND ".join(conditions)
    return frappe.db.sql(f"""
        SELECT
            name, order_type, status, priority, equipment, functional_location,
            planned_start, planned_end, actual_end, downtime_hours,
            total_labor_cost, total_material_cost, total_cost
        FROM `tabMaintenance Order`
        WHERE {where}
        ORDER BY planned_start DESC
    """, values, as_dict=True)