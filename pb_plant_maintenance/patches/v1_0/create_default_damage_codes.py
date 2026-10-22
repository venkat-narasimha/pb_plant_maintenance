import frappe


DEFAULT_DAMAGE_CODES = [
    ("D001", "Bearing Failure", "Mechanical"),
    ("D002", "Seal Leak", "Mechanical"),
    ("D003", "Motor Burnout", "Electrical"),
    ("D004", "Wiring Fault", "Electrical"),
    ("D005", "Sensor Failure", "Instrumentation"),
    ("D006", "Calibration Drift", "Instrumentation"),
    ("D007", "Corrosion", "Structural"),
    ("D008", "Software Error", "Software"),
    ("D009", "Vibration Excess", "Mechanical"),
    ("D010", "Overheating", "Mechanical"),
]


def execute():
    for code, description, category in DEFAULT_DAMAGE_CODES:
        if not frappe.db.exists("Damage Code", code):
            doc = frappe.new_doc("Damage Code")
            doc.code = code
            doc.description = description
            doc.category = category
            doc.flags.ignore_permissions = True
            doc.insert()