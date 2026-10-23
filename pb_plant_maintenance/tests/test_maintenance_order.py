import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime, add_to_date
from pb_plant_maintenance.tests.test_equipment import make_test_equipment

def make_test_maintenance_order(equipment=None):
    """Helper to create a valid Maintenance Order with mandatory ERPNext dependencies."""
    if not equipment:
        eq = make_test_equipment()
        equipment = eq.name
        
    company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
    
    # Fetch a valid, non-group Cost Center
    cost_center = frappe.db.get_value("Cost Center", {"company": company, "is_group": 0}, "name")
    if not cost_center:
        cost_center = frappe.db.get_value("Cost Center", {"is_group": 0}, "name")

    order = frappe.new_doc("Maintenance Order")
    order.order_type = "Corrective"
    order.priority = "Medium"
    order.description = "Test maintenance order"
    order.equipment = equipment
    order.planned_start = now_datetime()
    order.planned_end = add_to_date(now_datetime(), hours=8)
    order.cost_center = cost_center
    order.company = company
    
    # Add a test operation
    order.append("operations", {
        "operation_number": 1,
        "operation_description": "Test operation",
        "planned_duration": 4.0,
    })
    
    order.insert(ignore_permissions=True)
    return order

class TestMaintenanceOrder(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")

    def test_order_creation_and_validation(self):
        """Test basic creation and default status."""
        order = make_test_maintenance_order()
        self.assertTrue(order.name)
        self.assertTrue(order.name.startswith("MO-"))
        self.assertEqual(order.status, "Draft")
        
    def test_order_cost_calculation(self):
        """Test the actual Python controller logic that calculates material costs."""
        order = make_test_maintenance_order()
        
        # 1. Setup a valid stock Item
        item_code = "Test-Spare-Part-PM"
        if not frappe.db.exists("Item", item_code):
            item = frappe.new_doc("Item")
            item.item_code = item_code
            item.item_name = item_code
            item.is_stock_item = 1
            item.insert(ignore_permissions=True)
            
        # 2. Setup a valid Warehouse
        warehouse = frappe.db.get_value("Warehouse", {"company": order.company, "is_group": 0}, "name")
        if not warehouse:
            warehouse = frappe.db.get_value("Warehouse", {"is_group": 0}, "name")
            
        # 3. Add required spare part to the order
        order.append("required_parts", {
            "item_code": item_code,
            "quantity_required": 2.0,
            "unit_cost": 100.0,
            "warehouse": warehouse
        })
        
        # Saving triggers the validate() method, which calls calculate_costs()
        order.save(ignore_permissions=True)
        
        # Assert that the custom controller logic correctly calculated the totals
        self.assertEqual(order.total_material_cost, 200.0)
        self.assertEqual(order.total_cost, 200.0) 

    def tearDown(self):
        frappe.db.rollback()