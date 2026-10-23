import frappe
from frappe import _
from frappe.utils import date_diff, getdate, nowdate


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": _("Equipment"), "fieldname": "equipment", "fieldtype": "Link",
         "options": "Equipment", "width": 150},
        {"label": _("Equipment Name"), "fieldname": "equipment_name",
         "fieldtype": "Data", "width": 180},
        {"label": _("Breakdowns"), "fieldname": "breakdown_count",
         "fieldtype": "Int", "width": 110},
        {"label": _("Total Downtime (hrs)"), "fieldname": "total_downtime",
         "fieldtype": "Float", "width": 140},
        {"label": _("MTTR (hrs)"), "fieldname": "mttr",
         "fieldtype": "Float", "precision": 2, "width": 110},
        {"label": _("Operating Period (hrs)"), "fieldname": "operating_hours",
         "fieldtype": "Float", "width": 150},
        {"label": _("MTBF (hrs)"), "fieldname": "mtbf",
         "fieldtype": "Float", "precision": 2, "width": 110},
    ]


def get_data(filters):
    conditions = ["mo.docstatus = 1", "mo.order_type in ('Corrective', 'Emergency')"]
    values = {}

    if filters.get("from_date"):
        conditions.append("mo.actual_start >= %(from_date)s")
        values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions.append("mo.actual_end <= %(to_date)s")
        values["to_date"] = filters["to_date"]
    if filters.get("equipment"):
        conditions.append("mo.equipment = %(equipment)s")
        values["equipment"] = filters["equipment"]

    where = " AND ".join(conditions)

    data = frappe.db.sql(f"""
        SELECT
            mo.equipment,
            e.equipment_name,
            COUNT(*) as breakdown_count,
            COALESCE(SUM(mo.downtime_hours), 0) as total_downtime
        FROM `tabMaintenance Order` mo
        LEFT JOIN `tabEquipment` e ON e.name = mo.equipment
        WHERE {where} AND mo.equipment IS NOT NULL
        GROUP BY mo.equipment, e.equipment_name
        HAVING breakdown_count > 0
        ORDER BY breakdown_count DESC
    """, values, as_dict=True)

    from_date = getdate(filters.get("from_date") or "2020-01-01")
    to_date = getdate(filters.get("to_date") or nowdate())
    total_hours = date_diff(to_date, from_date) * 24

    for row in data:
        row["mttr"] = row.total_downtime / row.breakdown_count if row.breakdown_count else 0
        row["operating_hours"] = total_hours - row.total_downtime
        row["mtbf"] = row.operating_hours / row.breakdown_count if row.breakdown_count else 0

    return data