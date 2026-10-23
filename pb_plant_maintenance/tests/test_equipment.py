import frappe
import unittest


class TestEquipment(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")

    def test_equipment_creation(self):
        if not frappe.db.exists("Asset", "TEST-ASSET-001"):
            asset = frappe.new_doc("Asset")
            asset.asset_name = "Test Asset"
            asset.company = frappe.defaults.get_user_default("Company")
            asset.item_code = frappe.db.get_value("Item", {}, "name") or "Test Item"
            asset.flags.ignore_permissions = True
        asset.gross_purchase_amount = 5000
        asset.purchase_date = '2024-01-01'
        asset.available_for_use_date = '2024-01-01'
        asset.calculate_depreciation = 0

            asset.insert(ignore_links=True)
            asset_name = asset.name
        else:
            asset_name = "TEST-ASSET-001"

        eq = frappe.new_doc("Equipment")
        eq.equipment_name = "Test Equipment"
        eq.asset_reference = asset_name
        eq.equipment_category = "Production"
        eq.criticality = "High"
        eq.flags.ignore_permissions = True
        eq.insert()
        self.assertTrue(eq.name)
        self.assertTrue(eq.name.startswith("EQ-"))

    def test_scrapped_asset_validation(self):
        # Test that equipment cannot be linked to scrapped asset
        pass

    def tearDown(self):
        frappe.db.rollback()