import frappe
from frappe.model.document import Document


class PMSettings(Document):
    def validate(self):
        if self.capitalization_threshold and self.capitalization_threshold < 0:
            frappe.throw("Capitalization Threshold cannot be negative.")