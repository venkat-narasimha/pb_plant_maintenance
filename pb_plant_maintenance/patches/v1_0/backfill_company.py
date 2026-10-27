import frappe
from frappe import _


def execute():
    default_company = frappe.db.get_single_value("Global Defaults", "default_company")
    unresolved = []

    mappings = {
        "Equipment": ("name", "company", "asset_reference"),
        "Maintenance Notification": ("name", "company", "equipment"),
        "Maintenance Order": ("name", "company", "cost_center", "equipment"),
        "Maintenance Confirmation": ("name", "company", "maintenance_order"),
        "Maintenance Plan": ("name", "company"),
        "Maintenance Task List": ("name", "company"),
        "Measuring Point": ("name", "company"),
        "Measurement Document": ("name", "company"),
    }

    for doctype, fields in mappings.items():
        for record in frappe.get_all(doctype, fields=list(fields)):
            if record.company:
                continue

            company = None
            if doctype == "Equipment" and record.asset_reference:
                company = frappe.db.get_value("Asset", record.asset_reference, "company")
            elif doctype == "Maintenance Notification" and record.equipment:
                company = frappe.db.get_value("Equipment", record.equipment, "company")
            elif doctype == "Maintenance Order":
                if record.cost_center:
                    company = frappe.db.get_value("Cost Center", record.cost_center, "company")
                if not company and record.equipment:
                    company = frappe.db.get_value("Equipment", record.equipment, "company")
            elif doctype == "Maintenance Confirmation" and record.maintenance_order:
                company = frappe.db.get_value(
                    "Maintenance Order", record.maintenance_order, "company"
                )
            else:
                company = default_company

            company = company or default_company
            if not company:
                unresolved.append(f"{doctype} {record.name}")
                continue

            frappe.db.set_value(
                doctype,
                record.name,
                "company",
                company,
                update_modified=False,
            )

    if unresolved:
        frappe.throw(
            _("Could not backfill Company for these records: {0}. "
              "Set Global Defaults.default_company or repair their linked records, then retry.")
            .format(", ".join(unresolved[:20]))
        )
