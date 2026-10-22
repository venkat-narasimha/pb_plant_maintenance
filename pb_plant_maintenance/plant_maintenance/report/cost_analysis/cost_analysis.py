import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    return columns, data, None, chart


def get_columns():
    return [
        {"label": _("Equipment"), "fieldname": "equipment", "fieldtype": "Link",
         "options": "Equipment", "width": 150},
        {"label": _("Total Orders"), "fieldname": "order_count",
         "fieldtype": "Int", "width": 100},
        {"label": _("Labor Cost"), "fieldname": "total_labor_cost",
         "fieldtype": "Currency", "width": 120},
        {"label": _("Material Cost"), "fieldname": "total_material_cost",
         "fieldtype": "Currency", "width": 120},
        {"label": _("Total Cost"), "fieldname": "total_cost",
         "fieldtype": "Currency", "width": 120},
        {"label": _("Avg Cost/Order"), "fieldname": "avg_cost",
         "fieldtype": "Currency", "width": 120},
        {"label": _("Total Downtime (hrs)"), "fieldname": "total_downtime",
         "fieldtype": "Float", "width": 130},
    ]


def get_data(filters):
    conditions = ["docstatus = 1", "status = 'Completed'"]
    values = {}

    if filters.get("from_date"):
        conditions.append("actual_end >= %(from_date)s")
        values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions.append("actual_end <= %(to_date)s")
        values["to_date"] = filters["to_date"]
    if filters.get("equipment"):
        conditions.append("equipment = %(equipment)s")
        values["equipment"] = filters["equipment"]
    if filters.get("cost_center"):
        conditions.append("cost_center = %(cost_center)s")
        values["cost_center"] = filters["cost_center"]

    where = " AND ".join(conditions)

    return frappe.db.sql(f"""
        SELECT
            equipment,
            COUNT(*) as order_count,
            SUM(total_labor_cost) as total_labor_cost,
            SUM(total_material_cost) as total_material_cost,
            SUM(total_cost) as total_cost,
            AVG(total_cost) as avg_cost,
            SUM(downtime_hours) as total_downtime
        FROM `tabMaintenance Order`
        WHERE {where}
        GROUP BY equipment
        ORDER BY total_cost DESC
    """, values, as_dict=True)


def get_chart(data):
    if not data:
        return None
    return {
        "data": {
            "labels": [d.equipment or "Unknown" for d in data[:10]],
            "datasets": [
                {"name": "Labor Cost", "values": [d.total_labor_cost for d in data[:10]]},
                {"name": "Material Cost", "values": [d.total_material_cost for d in data[:10]]},
            ],
        },
        "type": "bar",
        "colors": ["#3498db", "#e74c3c"],
    }