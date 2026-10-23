import frappe
from frappe.model.document import Document


class MeasuringPoint(Document):
    def validate(self):
        if self.lower_limit and self.upper_limit:
            if self.lower_limit >= self.upper_limit:
                frappe.throw("Lower Limit must be less than Upper Limit.")

    def update_counter(self, reading_value, reading_date):
        self.db_set("counter_reading", reading_value)
        self.db_set("last_reading_date", reading_date)