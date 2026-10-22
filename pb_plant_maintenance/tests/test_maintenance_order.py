import frappe
import unittest
from frappe.utils import now_datetime, add_hours


class TestMaintenanceOrder(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")

    def test_order_cost_calculation(self):
        order = frappe.new_doc("Maintenance Order")
        order.order_type = "Corrective"
        order.priority = "Medium"
        order.description = "Test order"
        order.planned_start = now_datetime()
        order.planned_end = add_hours(now_datetime(), 8)
        order.cost_center = frappe.db.get_value("Cost Center", {}, "name")
        order.append("operations", {
            "operation_number": 1,
            "operation_description": "Test op",
            "planned_duration": 4,
        })
        order.append("required_parts", {
            "item_code": frappe.db.get_value("Item", {}, "name"),
            "quantity_required": 2,
            "unit_cost": 100,
            "warehouse": frappe.db.get_value("Warehouse", {}, "name"),
        })
        order.flags.ignore_permissions = True
        order.insert()
        self.assertEqual(order.total_material_cost, 200)

    def tearDown(self):
        frappe.db.rollback()