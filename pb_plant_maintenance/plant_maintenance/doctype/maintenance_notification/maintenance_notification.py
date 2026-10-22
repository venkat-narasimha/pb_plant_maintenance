import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, time_diff_in_hours


class MaintenanceNotification(Document):
    def validate(self):
        self.validate_reference()
        self.validate_malfunction_dates()
        self.set_default_status()

    def validate_reference(self):
        if not self.equipment and not self.functional_location:
            frappe.throw(
                _("Either Equipment or Functional Location must be specified.")
            )
        if self.equipment and not frappe.db.exists("Equipment", self.equipment):
            frappe.throw(_("Equipment {0} does not exist.").format(self.equipment))
        if self.functional_location and not frappe.db.exists(
            "Functional Location", self.functional_location
        ):
            frappe.throw(
                _("Functional Location {0} does not exist.").format(self.functional_location)
            )

    def validate_malfunction_dates(self):
        if self.malfunction_start and self.malfunction_end:
            if self.malfunction_end < self.malfunction_start:
                frappe.throw(_("Malfunction End cannot be before Malfunction Start."))

    def set_default_status(self):
        if self.is_new() and self.status == "Draft":
            self.status = "Open"

    def on_submit(self):
        self.notify_stakeholders()
        self.update_equipment_status_if_breakdown()

    def on_update_after_submit(self):
        if self.status == "Closed":
            self.close_notification()

    def notify_stakeholders(self):
        """Send notifications for critical/high priority notifications."""
        if self.priority in ("Critical", "High"):
            self.send_critical_alert()

    def send_critical_alert(self):
        recipients = self.get_notification_recipients()
        if not recipients:
            return
        subject = _("Critical Maintenance Notification: {0}").format(self.name)
        message = self.build_notification_message()
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
            reference_doctype=self.doctype,
            reference_name=self.name,
        )

    def get_notification_recipients(self):
        recipients = set()
        if self.equipment:
            team = frappe.db.get_value("Equipment", self.equipment, "maintenance_team")
            if team:
                manager = frappe.db.get_value("Asset Maintenance Team", team, "manager")
                if manager:
                    user = frappe.db.get_value("Employee", manager, "user_id")
                    if user:
                        recipients.add(user)
        # Add role-based recipients
        role_users = frappe.get_all(
            "Has Role",
            filters={"role": "PM Manager", "parenttype": "User"},
            pluck="parent",
        )
        recipients.update(role_users)
        return list(recipients)

    def build_notification_message(self):
        return f"""
        <h3>Maintenance Notification: {self.name}</h3>
        <p><b>Type:</b> {self.notification_type}</p>
        <p><b>Priority:</b> {self.priority}</p>
        <p><b>Equipment:</b> {self.equipment or 'N/A'}</p>
        <p><b>Location:</b> {self.functional_location or 'N/A'}</p>
        <p><b>Description:</b> {self.short_description}</p>
        <p><b>Reported By:</b> {self.reported_by}</p>
        <p><b>Reported On:</b> {self.notification_date}</p>
        <p><a href="/app/maintenance-notification/{self.name}">Open Notification</a></p>
        """

    def update_equipment_status_if_breakdown(self):
        if self.breakdown and self.equipment:
            frappe.db.set_value(
                "Equipment", self.equipment, "status", "Under Maintenance"
            )

    def close_notification(self):
        if not self.maintenance_order:
            frappe.msgprint(
                _("Notification is being closed without a linked Maintenance Order."),
                indicator="orange", alert=True
            )

    def get_response_time_hours(self):
        if self.malfunction_start and self.notification_date:
            return time_diff_in_hours(self.notification_date, self.malfunction_start)
        return 0