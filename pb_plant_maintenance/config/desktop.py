from frappe import _

def get_data():
    return [
        {
            "module_name": "PM Custom",
            "color": "#3498db",
            "icon": "octicon octicon-tools",
            "type": "module",
            "label": _("Plant Maintenance"),
            "items": [
                {"type": "doctype", "name": "Equipment", "label": _("Equipment")},
                {"type": "doctype", "name": "Functional Location", "label": _("Functional Locations")},
                {"type": "doctype", "name": "Maintenance Notification", "label": _("Notifications")},
                {"type": "doctype", "name": "Maintenance Order", "label": _("Maintenance Orders")},
                {"type": "doctype", "name": "Maintenance Confirmation", "label": _("Confirmations")},
                {"type": "doctype", "name": "Maintenance Plan", "label": _("Maintenance Plans")},
                {"type": "doctype", "name": "Maintenance Task List", "label": _("Task Lists")},
                {"type": "doctype", "name": "Measuring Point", "label": _("Measuring Points")},
                {"type": "doctype", "name": "Measurement Document", "label": _("Measurements")},
                {"type": "doctype", "name": "Maintenance Strategy", "label": _("Strategies")},
                {"type": "doctype", "name": "Damage Code", "label": _("Damage Codes")},
                {"type": "doctype", "name": "Cause Code", "label": _("Cause Codes")},
                {"type": "doctype", "name": "PM Settings", "label": _("PM Settings")},
            ],
        },
        {
            "module_name": "PM Custom",
            "color": "#e74c3c",
            "icon": "octicon octicon-graph",
            "type": "module",
            "label": _("PM Reports"),
            "items": [
                {"type": "report", "name": "Equipment Register", "doctype": "Equipment", "is_query_report": True},
                {"type": "report", "name": "Maintenance Order List", "doctype": "Maintenance Order", "is_query_report": True},
                {"type": "report", "name": "Notification Analysis", "doctype": "Maintenance Notification", "is_query_report": True},
                {"type": "report", "name": "Cost Analysis", "doctype": "Maintenance Order", "is_query_report": True},
                {"type": "report", "name": "Downtime Analysis", "doctype": "Maintenance Order", "is_query_report": True},
                {"type": "report", "name": "Plan Compliance", "doctype": "Maintenance Plan", "is_query_report": True},
                {"type": "report", "name": "MTBF MTTR", "doctype": "Equipment", "is_query_report": True},
            ],
        },
    ]