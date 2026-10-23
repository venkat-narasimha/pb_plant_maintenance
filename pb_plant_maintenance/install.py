import frappe
from frappe import _


def after_install():
    """Run after app installation."""
    setup_roles()
    setup_workspace()
    frappe.db.commit()
    print(_("pb_plant_maintenance app installed successfully."))


def setup_roles():
    """Create default roles if they don't exist."""
    roles = ["PM Manager", "Maintenance Planner", "Technician", "Operator"]
    for role_name in roles:
        if not frappe.db.exists("Role", role_name):
            role = frappe.new_doc("Role")
            role.role_name = role_name
            role.desk_access = 1
            role.flags.ignore_permissions = True
            role.insert()


import json

MODULE   = "Plant Maintenance"     # must equal modules.txt / Module Def exactly
WS_LABEL = "Plant Maintenance"


def setup_workspace(force=False):
    """Create (or rebuild) the Plant Maintenance workspace with valid v15 content."""
    if frappe.db.exists("Workspace", WS_LABEL):
        if not force:
            return frappe.db.get_value("Workspace", WS_LABEL, "name")
        frappe.delete_doc("Workspace", WS_LABEL, force=True, ignore_permissions=True)

    ws = frappe.new_doc("Workspace")
    ws.label           = WS_LABEL
    ws.title           = "Plant Maintenance"
    ws.module          = MODULE
    ws.public          = 1
    ws.is_hidden       = 0
    ws.icon            = "tool"
    ws.indicator_color = "blue"
    ws.sequence_id     = 20.0

    def _ok(link_type, name):
        # link_type is literally "DocType" / "Report" / "Page" / "Dashboard"
        return bool(frappe.db.exists(link_type, name))

    # ---------- 1. Shortcuts (child table) ----------
    wanted_shortcuts = [
        ("Equipment",                "DocType", "Equipment"),
        ("Maintenance Notification", "DocType", "Maintenance Notification"),
        ("Maintenance Order",        "DocType", "Maintenance Order"),
        ("Maintenance Plan",         "DocType", "Maintenance Plan"),
        ("PM Settings",              "DocType", "PM Settings"),
    ]
    added_shortcuts = []
    for label, ltype, link_to in wanted_shortcuts:
        if not _ok(ltype, link_to):
            continue                                   # never point at a missing DocType
        ws.append("shortcuts", {
            "label": label, "type": ltype, "link_to": link_to,
            "color": "Grey", "doc_view": "List",
        })
        added_shortcuts.append(label)

    # ---------- 2. Cards = "Card Break" + "Link" rows ----------
    wanted_cards = [
        ("Master Data", [
            ("Equipment", "DocType"), ("Functional Location", "DocType"),
            ("Maintenance Task Operation", "DocType"), ("Measuring Point", "DocType"),
            ("Damage Code", "DocType"),
        ]),
        ("Transactions", [
            ("Maintenance Notification", "DocType"), ("Maintenance Order", "DocType"),
            ("Maintenance Confirmation", "DocType"), ("Measurement Document", "DocType"),
            ("Maintenance Plan", "DocType"),
        ]),
        ("Reports", [
            ("Equipment Register", "Report"), ("Maintenance Cost Analysis", "Report"),
            ("Equipment Downtime Report", "Report"),
        ]),
        ("Setup", [("PM Settings", "DocType")]),
    ]
    added_cards = []
    for card_name, items in wanted_cards:
        valid = [(l, t) for l, t in items if _ok(t, l)]
        if not valid:
            continue
        ws.append("links", {"type": "Card Break", "label": card_name})
        for l, t in valid:
            ws.append("links", {"type": "Link", "label": l, "link_to": l,
                                "link_type": t, "onboard": 0, "hidden": 0})
        added_cards.append(card_name)

    # ---------- 3. content — THE field v15 renders ----------
    content = [{"type": "header",
                "data": {"text": '<span class="h4"><b>Your Shortcuts</b></span>', "col": 12}}]
    content += [{"type": "shortcut", "data": {"shortcut_name": s, "col": 3}}
                for s in added_shortcuts]
    content.append({"type": "spacer", "data": {"col": 12}})
    content.append({"type": "header",
                    "data": {"text": '<span class="h4"><b>Reports &amp; Masters</b></span>', "col": 12}})
    content += [{"type": "card", "data": {"card_name": c, "col": 4}}
                for c in added_cards]

    ws.content = json.dumps(content)

    ws.flags.ignore_permissions = True
    ws.insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.clear_cache()
    return ws.name