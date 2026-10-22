import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": _("Equipment"), "fieldname": "name", "fieldtype": "Link",
         "options": "Equipment", "width": 130},
        {"label": _("Equipment Name"), "fieldname": "equipment_name",
         "fieldtype": "Data", "width": 180},
        {"label": _("Category"), "fieldname": "equipment_category",
         "fieldtype": "Data", "width": 120},
        {"label": _("Criticality"), "fieldname": "criticality",
         "fieldtype": "Data", "width": 90},
        {"label": _("Status"), "fieldname": "status",
         "fieldtype": "Data", "width": 110},
        {"label": _("Location"), "fieldname": "functional_location",
         "fieldtype": "Link", "options": "Functional Location", "width": 130},
        {"label": _("Manufacturer"), "fieldname": "manufacturer",
         "fieldtype": "Data", "width": 130},
        {"label": _("Model"), "fieldname": "model_number",
         "fieldtype": "Data", "width": 120},
        {"label": _("Installation Date"), "fieldname": "installation_date",
         "fieldtype": "Date", "width": 110},
        {"label": _("Warranty Expiry"), "fieldname": "warranty_expiry",
         "fieldtype": "Date", "width": 110},
    ]


def get_data(filters):
    conditions = []
    values = {}

    if filters.get("equipment_category"):
        conditions.append("equipment_category = %(equipment_category)s")
        values["equipment_category"] = filters["equipment_category"]
    if filters.get("criticality"):
        conditions.append("criticality = %(criticality)s")
        values["criticality"] = filters["criticality"]
    if filters.get("status"):
        conditions.append("status = %(status)s")
        values["status"] = filters["status"]
    if filters.get("functional_location"):
        conditions.append("functional_location = %(functional_location)s")
        values["functional_location"] = filters["functional_location"]

    where = " AND ".join(conditions) if conditions else "1=1"

    return frappe.db.sql(f"""
        SELECT
            name, equipment_name, equipment_category, criticality, status,
            functional_location, manufacturer, model_number,
            installation_date, warranty_expiry
        FROM `tabEquipment`
        WHERE {where}
        ORDER BY criticality, equipment_name
    """, values, as_dict=True)