import frappe
from frappe import _
from frappe.model.document import Document


class MeasurementDocument(Document):
    def validate(self):
        self.check_limits()

    def check_limits(self):
        mp = frappe.get_doc("Measuring Point", self.measuring_point)
        self.is_exception = 0
        if mp.lower_limit and self.reading_value < mp.lower_limit:
            self.is_exception = 1
        if mp.upper_limit and self.reading_value > mp.upper_limit:
            self.is_exception = 1

    def on_submit(self):
        self.update_measuring_point()
        if self.is_exception:
            self.create_exception_notification()

    def update_measuring_point(self):
        mp = frappe.get_doc("Measuring Point", self.measuring_point)
        mp.update_counter(self.reading_value, self.reading_date)

    def create_exception_notification(self):
        """Auto-create a maintenance notification for out-of-limit readings."""
        mp = frappe.get_doc("Measuring Point", self.measuring_point)
        notification = frappe.new_doc("Maintenance Notification")
        notification.notification_type = "Malfunction"
        notification.priority = "High"
        notification.equipment = mp.equipment
        notification.short_description = _(
            "Out-of-limit reading on {0}: {1} {2}"
        ).format(mp.measuring_point_name, self.reading_value, mp.unit_of_measure)
        notification.long_description = _(
            "Reading value {0} is outside limits ({1} to {2})."
        ).format(self.reading_value, mp.lower_limit, mp.upper_limit)
        notification.flags.ignore_permissions = True
        notification.insert()
        notification.submit()
        self.db_set("generated_notification", notification.name)