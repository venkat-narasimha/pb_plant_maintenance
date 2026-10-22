import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_months, getdate, today


class MaintenancePlan(Document):
    def validate(self):
        self.validate_reference()
        self.validate_dates()
        self.calculate_next_due_dates()

    def validate_reference(self):
        if not self.equipment and not self.functional_location:
            frappe.throw(_("Either Equipment or Functional Location is required."))

    def validate_dates(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            frappe.throw(_("End Date must be after Start Date."))

    def calculate_next_due_dates(self):
        for task in self.tasks:
            if not task.next_due_date and self.start_date:
                task.next_due_date = self.start_date
            elif task.last_completion_date and task.periodicity:
                task.next_due_date = self.compute_next_due(
                    task.last_completion_date, task.periodicity, task.periodicity_value
                )

    @staticmethod
    def compute_next_due(base_date, periodicity, periodicity_value=1):
        base_date = getdate(base_date)
        periodicity_value = int(periodicity_value or 1)
        if periodicity == "Daily":
            return add_days(base_date, periodicity_value)
        if periodicity == "Weekly":
            return add_days(base_date, 7 * periodicity_value)
        if periodicity == "Monthly":
            return add_months(base_date, periodicity_value)
        if periodicity == "Quarterly":
            return add_months(base_date, 3 * periodicity_value)
        if periodicity == "Half-Yearly":
            return add_months(base_date, 6 * periodicity_value)
        if periodicity == "Yearly":
            return add_months(base_date, 12 * periodicity_value)
        return base_date

    def get_due_tasks(self, as_on_date=None):
        as_on_date = getdate(as_on_date or today())
        due_tasks = []
        for task in self.tasks:
            if task.next_due_date and getdate(task.next_due_date) <= as_on_date:
                due_tasks.append(task)
        return due_tasks