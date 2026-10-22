import frappe
from frappe import _
from frappe.model.document import Document


class Equipment(Document):
    def validate(self):
        self.validate_asset_link()
        self.validate_dates()
        self.sync_asset_status()

    def validate_asset_link(self):
        """Ensure the linked asset exists and is not scrapped."""
        if self.asset_reference:
            asset_status = frappe.db.get_value(
                "Asset", self.asset_reference, "status"
            )
            if asset_status == "Scrapped":
                frappe.throw(
                    _("Cannot link equipment to a scrapped asset: {0}").format(
                        self.asset_reference
                    )
                )

    def validate_dates(self):
        if self.warranty_expiry and self.installation_date:
            if self.warranty_expiry < self.installation_date:
                frappe.throw(
                    _("Warranty Expiry cannot be before Installation Date")
                )

    def sync_asset_status(self):
        """Sync equipment status to the linked asset."""
        if not self.asset_reference:
            return
        status_map = {
            "Active": "Submitted",
            "Inactive": "Submitted",
            "Under Maintenance": "Submitted",
            "Scrapped": "Scrapped",
        }
        new_status = status_map.get(self.status)
        if new_status:
            frappe.db.set_value(
                "Asset", self.asset_reference, "status", new_status,
                update_modified=False
            )

    def on_trash(self):
        """Prevent deletion if there are open orders or notifications."""
        open_orders = frappe.db.count(
            "Maintenance Order",
            {"equipment": self.name, "status": ["not in", ["Closed", "Cancelled"]]},
        )
        if open_orders:
            frappe.throw(
                _("Cannot delete equipment with {0} open maintenance order(s)").format(
                    open_orders
                )
            )