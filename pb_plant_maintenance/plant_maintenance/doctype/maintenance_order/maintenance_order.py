import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime, time_diff_in_hours

from pb_plant_maintenance.utils.company_utils import (
    resolve_company,
    validate_company_consistency,
)


class MaintenanceOrder(Document):
    def validate(self):
        self.company = resolve_company(self)
        self.validate_reference()
        validate_company_consistency(self)
        self.validate_schedule()
        self.calculate_costs()

    def validate_reference(self):
        if not self.equipment and not self.functional_location:
            frappe.throw(_("Either Equipment or Functional Location is required."))
        if self.equipment:
            status = frappe.db.get_value("Equipment", self.equipment, "status")
            if status == "Scrapped":
                frappe.throw(_("Cannot create order for scrapped equipment."))

    def validate_schedule(self):
        if self.planned_start and self.planned_end:
            if self.planned_end < self.planned_start:
                frappe.throw(_("Planned End must be after Planned Start."))
        if self.actual_start and self.actual_end:
            if self.actual_end < self.actual_start:
                frappe.throw(_("Actual End must be after Actual Start."))

    def calculate_costs(self):
        labor_cost = 0.0
        for op in self.operations or []:
            hours = flt(op.actual_duration) or flt(op.planned_duration)
            rate = 0.0
            if op.work_center:
                rate = flt(frappe.db.get_value(
                    "Workstation", op.work_center, "pm_hourly_rate"
                )) or 0.0
            op.labor_cost = hours * rate
            labor_cost += op.labor_cost

        material_cost = 0.0
        for part in self.required_parts or []:
            part.total_cost = flt(part.quantity_required) * flt(part.unit_cost)
            material_cost += part.total_cost

        self.total_labor_cost = labor_cost
        self.total_material_cost = material_cost
        self.total_cost = labor_cost + material_cost

        if self.actual_start and self.actual_end:
            self.downtime_hours = time_diff_in_hours(self.actual_end, self.actual_start)

    def on_submit(self):
        self.db_set("status", "Planned")
        self.status = "Planned"
        self.update_equipment_status("Under Maintenance")
        self.reserve_spare_parts()

    def on_cancel(self):
        self.status = "Cancelled"
        self.release_reserved_parts()
        self.update_equipment_status("Active")

    def on_update_after_submit(self):
        if self.status == "In Progress" and not self.actual_start:
            self.db_set("actual_start", now_datetime())
        if self.status == "Completed" and not self.actual_end:
            self.db_set("actual_end", now_datetime())
            self.update_equipment_status("Active")

    def update_equipment_status(self, new_status):
        if self.equipment:
            frappe.db.set_value("Equipment", self.equipment, "status", new_status)

    def reserve_spare_parts(self):
        """Reserve stock for required spare parts."""
        for part in self.required_parts or []:
            if not part.item_code or not part.quantity_required:
                continue
            try:
                from erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry import (
                    create_stock_reservation_entry,
                )
                create_stock_reservation_entry(
                    item_code=part.item_code,
                    warehouse=part.warehouse,
                    qty_to_reserve=part.quantity_required,
                    voucher_type=self.doctype,
                    voucher_no=self.name,
                )
            except Exception as e:
                frappe.log_error(
                    f"Failed to reserve {part.item_code}: {e}",
                    "PM Order Stock Reservation"
                )

    def release_reserved_parts(self):
        reservations = frappe.get_all(
            "Stock Reservation Entry",
            filters={
                "voucher_type": self.doctype,
                "voucher_no": self.name,
                "docstatus": 1,
            },
            pluck="name",
        )
        for res in reservations:
            doc = frappe.get_doc("Stock Reservation Entry", res)
            doc.cancel()