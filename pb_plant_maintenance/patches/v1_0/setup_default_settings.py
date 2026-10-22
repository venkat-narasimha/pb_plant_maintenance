import frappe


def execute():
    settings = frappe.get_single("PM Settings")
    if not settings.capitalization_threshold:
        settings.capitalization_threshold = 50000
    if not settings.notify_overdue_days:
        settings.notify_overdue_days = 1
    settings.notify_critical = 1
    settings.auto_sync_asset_status = 1
    settings.flags.ignore_permissions = True
    settings.save()