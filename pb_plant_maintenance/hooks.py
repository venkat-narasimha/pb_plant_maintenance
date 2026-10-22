app_name = "pb_plant_maintenance"
app_title = "Plant Maintenance"
app_publisher = "Processbricks"
app_description = "Custom Plant Maintenance module for ERPNext by Processbricks"
app_email = "venkatnarasimha@processbricks.com"
app_license = "MIT"
required_apps = ["frappe", "erpnext"]

# ---------- Document Events ----------
doc_events = {
    "Asset": {
        "on_update": "pb_plant_maintenance.utils.asset_sync.sync_equipment_from_asset",
        "on_trash": "pb_plant_maintenance.utils.asset_sync.prevent_asset_delete_if_equipment",
    },
    "Maintenance Order": {
        "validate": "pb_plant_maintenance.utils.order_posting.validate_order",
        "on_submit": "pb_plant_maintenance.utils.order_posting.post_maintenance_costs",
        "on_cancel": "pb_plant_maintenance.utils.order_posting.reverse_maintenance_costs",
        "on_update_after_submit": "pb_plant_maintenance.utils.order_posting.handle_status_change",
    },
    "Maintenance Confirmation": {
        "on_submit": "pb_plant_maintenance.utils.order_posting.update_order_from_confirmation",
        "on_cancel": "pb_plant_maintenance.utils.order_posting.reverse_confirmation",
    },
    "Measurement Document": {
        "on_submit": "pb_plant_maintenance.utils.measurement.process_measurement_document",
    },
    "Maintenance Plan": {
        "on_update": "pb_plant_maintenance.utils.plan.validate_plan_tasks",
    },
}

# ---------- Scheduled Tasks ----------
scheduler_events = {
    "daily": [
        "pb_plant_maintenance.tasks.schedule_preventive_maintenance",
        "pb_plant_maintenance.tasks.send_maintenance_reminders",
        "pb_plant_maintenance.tasks.check_overdue_notifications",
        "pb_plant_maintenance.tasks.check_overdue_orders",
    ],
    "hourly": [
        "pb_plant_maintenance.tasks.check_measurement_alerts",
    ],
    "weekly": [
        "pb_plant_maintenance.tasks.generate_maintenance_kpis",
        "pb_plant_maintenance.tasks.cleanup_old_logs",
    ],
    "monthly": [
        "pb_plant_maintenance.tasks.generate_monthly_reports",
    ],
}

# ---------- Permissions ----------
permission_query_conditions = {
    "Maintenance Order": "pb_plant_maintenance.utils.permissions.order_query_conditions",
    "Maintenance Notification": "pb_plant_maintenance.utils.permissions.notification_query_conditions",
}

has_permission = {
    "Maintenance Order": "pb_plant_maintenance.utils.permissions.order_has_permission",
}

# ---------- Fixtures ----------
fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "Pb Plant Maintenance"]]},
    {"dt": "Property Setter", "filters": [["module", "=", "Pb Plant Maintenance"]]},
    {"dt": "Notification", "filters": [["module", "=", "Pb Plant Maintenance"]]},
    {"dt": "Dashboard Chart", "filters": [["module", "=", "Pb Plant Maintenance"]]},
    {"dt": "Role", "filters": [["name", "in", [
        "PM Manager", "Maintenance Planner", "Technician", "Operator"
    ]]]},
]

# ---------- Website ----------
website_route_rules = [
    {"from_route": "/pm-dashboard", "to_route": "pm_dashboard"},
]

# ---------- Translations ----------
# translations via CSV in translations folder

# ---------- Jinja ----------
jinja = {
    "methods": [
        "pb_plant_maintenance.utils.helpers.get_equipment_criticality_color",
        "pb_plant_maintenance.utils.helpers.format_duration",
    ]
}

# Add to hooks.py
doctype_js = {
    "Equipment": "public/js/equipment.js",
    "Maintenance Order": "public/js/maintenance_order.js",
    "Maintenance Notification": "public/js/maintenance_notification.js",
}

after_install = "pb_plant_maintenance.install.after_install"