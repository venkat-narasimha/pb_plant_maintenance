import frappe
from frappe import _


def sync_equipment_from_asset(doc, method=None):
    """Sync Asset changes to linked Equipment records."""
    if not frappe.db.exists("Equipment", {"asset_reference": doc.name}):
        return
    equipments = frappe.get_all(
        "Equipment", filters={"asset_reference": doc.name}, pluck="name"
    )
    for eq_name in equipments:
        equipment = frappe.get_doc("Equipment", eq_name)
        if doc.status == "Scrapped" and equipment.status != "Scrapped":
            equipment.status = "Scrapped"
            equipment.flags.ignore_permissions = True
            equipment.save()


def prevent_asset_delete_if_equipment(doc, method=None):
    """Prevent asset deletion when linked equipment exists."""
    count = frappe.db.count("Equipment", {"asset_reference": doc.name})
    if count:
        frappe.throw(
            _("Cannot delete Asset {0}. {1} Equipment record(s) reference it.").format(
                doc.name, count
            )
        )