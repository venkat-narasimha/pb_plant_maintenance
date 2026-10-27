import frappe
from frappe import _


def resolve_company(doc):
    """Resolve a document's company from its linked records or site defaults."""
    if doc.company:
        return doc.company

    linked_sources = (
        ("equipment", "Equipment"),
        ("notification", "Maintenance Notification"),
        ("functional_location", "Functional Location"),
        ("cost_center", "Cost Center"),
        ("measuring_point", "Measuring Point"),
    )
    for fieldname, doctype in linked_sources:
        source_name = doc.get(fieldname)
        if source_name:
            company = frappe.db.get_value(doctype, source_name, "company")
            if company:
                return company

    return (
        frappe.defaults.get_user_default("Company")
        or frappe.db.get_single_value("Global Defaults", "default_company")
    )


def validate_company_consistency(doc):
    """Reject linked records that belong to a different company."""
    if not doc.company:
        return

    linked_records = (
        ("cost_center", "Cost Center"),
        ("equipment", "Equipment"),
        ("notification", "Maintenance Notification"),
        ("functional_location", "Functional Location"),
        ("asset_reference", "Asset"),
    )
    for fieldname, doctype in linked_records:
        record_name = doc.get(fieldname)
        if not record_name:
            continue

        linked_company = frappe.db.get_value(doctype, record_name, "company")
        if linked_company and linked_company != doc.company:
            frappe.throw(
                _("{0} {1} belongs to company {2}, but {3} belongs to company {4}. "
                  "Select records belonging to the same company.").format(
                    doctype,
                    record_name,
                    linked_company,
                    doc.doctype,
                    doc.company,
                )
            )
