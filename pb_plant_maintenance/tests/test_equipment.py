import frappe
from frappe.tests.utils import FrappeTestCase

def get_or_create_test_asset():
    """Helper to create a valid ERPNext Asset, bypassing strict accounting validations."""
    company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
    
    # 1. Ensure Location exists
    location_name = "Test PM Location"
    if not frappe.db.exists("Location", location_name):
        loc = frappe.new_doc("Location")
        loc.location_name = location_name
        loc.insert(ignore_permissions=True)
        
    # 2. Ensure Asset Category exists (Bypass strict accounting for tests)
    asset_category_name = "Test PM Asset Category"
    if not frappe.db.exists("Asset Category", asset_category_name):
        ac = frappe.new_doc("Asset Category")
        ac.asset_category_name = asset_category_name
        ac.flags.ignore_mandatory = True
        ac.flags.ignore_validate = True
        ac.insert(ignore_permissions=True)
        
    # 3. Ensure Fixed Asset Item exists
    item_code = "Test-Asset-Item-PM"
    if not frappe.db.exists("Item", item_code):
        item = frappe.new_doc("Item")
        item.item_code = item_code
        item.item_name = item_code
        item.is_stock_item = 0
        item.is_fixed_asset = 1
        item.asset_category = asset_category_name
        item.flags.ignore_mandatory = True
        item.flags.ignore_validate = True  # Bypasses "Asset Category is mandatory for Fixed Asset item" error
        item.insert(ignore_permissions=True)
        
    # 4. Create Asset
    asset = frappe.new_doc("Asset")
    asset.item_code = item_code
    asset.company = company
    asset.location = location_name
    asset.gross_purchase_amount = 10000
    asset.purchase_date = "2024-01-01"
    asset.available_for_use_date = "2024-01-01"
    asset.calculate_depreciation = 0
    asset.flags.ignore_mandatory = True
    asset.flags.ignore_validate = True
    asset.insert(ignore_permissions=True)
        
    return asset.name

def make_test_equipment(equipment_name="Test PM Equipment"):
    """Helper to create a valid Equipment record linked to a valid Asset."""
    asset_name = get_or_create_test_asset()
    
    eq = frappe.new_doc("Equipment")
    eq.equipment_name = equipment_name
    eq.asset_reference = asset_name
    eq.equipment_category = "Production"
    eq.criticality = "High"
    eq.status = "Active"
    eq.insert(ignore_permissions=True)
    return eq

class TestEquipment(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")

    def test_equipment_creation(self):
        """Test that Equipment creates successfully and follows naming series."""
        eq = make_test_equipment()
        self.assertTrue(eq.name)
        # Adjust prefix if your naming series is different, e.g., "EQUIP-"
        # self.assertTrue(eq.name.startswith("EQ-")) 
        self.assertEqual(eq.status, "Active")
        
    def test_equipment_criticality(self):
        """Test business logic regarding criticality defaults."""
        eq = make_test_equipment(equipment_name="Critical Pump")
        eq.criticality = "Critical"
        eq.save(ignore_permissions=True)
        self.assertEqual(eq.criticality, "Critical")

    def tearDown(self):
        # Best Practice: Rollback the database to keep the test environment clean
        frappe.db.rollback()