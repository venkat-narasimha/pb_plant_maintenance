import os

BASE_DIR = "pb_plant_maintenance"

# 1. Fix permissions.py
perms_file = os.path.join(BASE_DIR, "utils/permissions.py")
if os.path.exists(perms_file):
    with open(perms_file, "r") as f: content = f.read()
    content = content.replace('"Asset Maintenance Team Member"', '"Maintenance Team Member"')
    content = content.replace('filters={"user": user}', 'filters={"team_member": user}')
    content = content.replace('filters={"user": user, "parent": doc.maintenance_team}', 'filters={"team_member": user, "parent": doc.maintenance_team}')
    with open(perms_file, "w") as f: f.write(content)
    print("✅ Fixed permissions.py")

# 2. Fix tasks.py
tasks_file = os.path.join(BASE_DIR, "tasks.py")
if os.path.exists(tasks_file):
    with open(tasks_file, "r") as f: content = f.read()
    content = content.replace('"Asset Maintenance Team Member"', '"Maintenance Team Member"')
    content = content.replace('fields=["user"]', 'fields=["team_member"]')
    content = content.replace('m.user for m in members if m.user', 'm.team_member for m in members if m.team_member')
    with open(tasks_file, "w") as f: f.write(content)
    print("✅ Fixed tasks.py")

# 3. Fix api/v1.py
api_file = os.path.join(BASE_DIR, "api/v1.py")
if os.path.exists(api_file):
    with open(api_file, "r") as f: content = f.read()
    content = content.replace('"Asset Maintenance Team Member"', '"Maintenance Team Member"')
    content = content.replace('filters={"user": user}', 'filters={"team_member": user}')
    with open(api_file, "w") as f: f.write(content)
    print("✅ Fixed api/v1.py")

# 4. Fix maintenance_notification.py
notif_file = os.path.join(BASE_DIR, "doctype/maintenance_notification/maintenance_notification.py")
if os.path.exists(notif_file):
    with open(notif_file, "r") as f: content = f.read()
    old_block = '''        if team:
            manager = frappe.db.get_value("Asset Maintenance Team", team, "manager")
            if manager:
                user = frappe.db.get_value("Employee", manager, "user_id")
                if user:
                    recipients.add(user)'''
    new_block = '''        if team:
            manager_user = frappe.db.get_value("Asset Maintenance Team", team, "maintenance_manager")
            if manager_user:
                recipients.add(manager_user)'''
    if old_block in content:
        content = content.replace(old_block, new_block)
        with open(notif_file, "w") as f: f.write(content)
        print("✅ Fixed maintenance_notification.py")
    else:
        print("⚠️ Could not find exact block in maintenance_notification.py, please check manually.")