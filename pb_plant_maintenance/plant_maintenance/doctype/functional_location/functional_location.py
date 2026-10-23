import frappe
from frappe import _
from frappe.utils.nestedset import NestedSet


class FunctionalLocation(NestedSet):
    nsm_parent_field = "parent_functional_location"

    def validate(self):
        self.validate_parent()
        self.validate_company_consistency()

    def validate_parent(self):
        if self.parent_functional_location:
            if self.parent_functional_location == self.name:
                frappe.throw(_("A Functional Location cannot be its own parent."))
            parent = frappe.get_doc("Functional Location", self.parent_functional_location)
            if not parent.is_group:
                frappe.throw(
                    _("Parent Location {0} is not marked as a Group.").format(parent.name)
                )
            if parent.company != self.company:
                frappe.throw(
                    _("Parent Location belongs to a different company.")
                )

    def validate_company_consistency(self):
        if self.is_group and self.parent_functional_location:
            parent_company = frappe.db.get_value(
                "Functional Location", self.parent_functional_location, "company"
            )
            if parent_company and parent_company != self.company:
                frappe.throw(_("Company must match parent location's company."))

    def on_update(self):
        super().on_update()

    def on_trash(self):
        equipment_count = frappe.db.count("Equipment", {"functional_location": self.name})
        if equipment_count:
            frappe.throw(
                _("Cannot delete Functional Location with {0} linked equipment.").format(
                    equipment_count
                )
            )
        super().on_trash()