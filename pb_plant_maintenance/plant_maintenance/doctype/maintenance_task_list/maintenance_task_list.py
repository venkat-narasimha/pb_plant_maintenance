import frappe
from frappe.model.document import Document

from pb_plant_maintenance.utils.company_utils import resolve_company


class MaintenanceTaskList(Document):
    def validate(self):
        self.company = resolve_company(self)
