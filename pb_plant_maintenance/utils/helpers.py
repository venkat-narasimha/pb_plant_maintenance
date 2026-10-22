import frappe
from frappe.utils import flt


def get_equipment_criticality_color(criticality):
    color_map = {
        "Critical": "#e74c3c",
        "High": "#e67e22",
        "Medium": "#f1c40f",
        "Low": "#27ae60",
    }
    return color_map.get(criticality, "#95a5a6")


def format_duration(hours):
    hours = flt(hours)
    if hours < 1:
        return f"{int(hours * 60)} min"
    if hours < 24:
        return f"{hours:.1f} hrs"
    return f"{hours / 24:.1f} days"


def get_pm_settings():
    return frappe.get_single("PM Settings")