import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class MaintenanceConfirmation(Document):
    def validate(self):
        self.validate_order_status()
        self.calculate_labor_cost()
        self.validate_materials()

    def validate_order_status(self):
        order_status = frappe.db.get_value(
            "Maintenance Order", self.maintenance_order, "status"
        )
        if order_status in ("Closed", "Cancelled"):
            frappe.throw(
                _("Cannot add confirmation to a {0} order.").format(order_status.lower())
            )

    def calculate_labor_cost(self):
        if not self.labor_rate and self.maintenance_order:
            work_center = frappe.db.get_value(
                "Maintenance Order", self.maintenance_order, "work_center"
            )
            if work_center:
                self.labor_rate = flt(frappe.db.get_value(
                    "Work Center", work_center, "pm_hourly_rate"
                )) or 0.0
        self.labor_cost = flt(self.labor_hours) * flt(self.labor_rate)

    def validate_materials(self):
        for mat in self.materials_used or []:
            if flt(mat.quantity) <= 0:
                frappe.throw(_("Quantity must be greater than zero for {0}").format(mat.item_code))

    def on_submit(self):
        self.update_order_operations()
        self.consume_materials()

    def on_cancel(self):
        self.reverse_materials()
        self.revert_order_status()

    def update_order_operations(self):
        order = frappe.get_doc("Maintenance Order", self.maintenance_order)
        if self.operation:
            for op in order.operations:
                if str(op.operation_number) == str(self.operation):
                    op.actual_duration = flt(op.actual_duration) + flt(self.labor_hours)
                    op.status = "Completed" if self.confirmation_type == "Final" else "In Progress"
                    op.completion_date = self.confirmation_date
                    op.confirmation_notes = self.work_performed
                    break
        order.flags.ignore_validate_update_after_submit = True
        order.save()

    def consume_materials(self):
        if not self.materials_used:
            return
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.purpose = "Material Issue"
        stock_entry.company = frappe.db.get_value(
            "Maintenance Order", self.maintenance_order, "company"
        ) or frappe.defaults.get_user_default("Company")
        stock_entry.posting_date = self.confirmation_date
        stock_entry.maintenance_order = self.maintenance_order
        stock_entry.maintenance_confirmation = self.name

        for mat in self.materials_used:
            stock_entry.append("items", {
                "item_code": mat.item_code,
                "qty": mat.quantity,
                "s_warehouse": mat.warehouse,
                "cost_center": frappe.db.get_value(
                    "Maintenance Order", self.maintenance_order, "cost_center"
                ),
            })

        stock_entry.flags.ignore_permissions = True
        stock_entry.insert()
        stock_entry.submit()
        self.db_set("stock_entry", stock_entry.name)

    def reverse_materials(self):
        stock_entry = frappe.db.get_value(
            "Maintenance Confirmation", self.name, "stock_entry"
        )
        if stock_entry:
            se = frappe.get_doc("Stock Entry", stock_entry)
            se.cancel()

    def revert_order_status(self):
        order = frappe.get_doc("Maintenance Order", self.maintenance_order)
        order.status = "In Progress"
        order.flags.ignore_validate_update_after_submit = True
        order.save()