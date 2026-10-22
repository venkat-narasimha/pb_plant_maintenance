frappe.ui.form.on('Maintenance Notification', {
    refresh(frm) {
        if (frm.doc.docstatus === 1 && !frm.doc.maintenance_order
            && frm.doc.status !== 'Closed' && frm.doc.status !== 'Cancelled') {
            frm.add_custom_button(__('Convert to Maintenance Order'), () => {
                frappe.prompt([
                    {
                        fieldname: 'order_type',
                        fieldtype: 'Select',
                        label: 'Order Type',
                        options: 'Corrective\nEmergency\nPreventive',
                        default: 'Corrective',
                        reqd: 1
                    },
                    {
                        fieldname: 'planned_start',
                        fieldtype: 'Datetime',
                        label: 'Planned Start',
                        default: frappe.datetime.now_datetime(),
                        reqd: 1
                    },
                    {
                        fieldname: 'planned_end',
                        fieldtype: 'Datetime',
                        label: 'Planned End',
                        reqd: 1
                    }
                ], (values) => {
                    frappe.call({
                        method: 'pb_plant_maintenance.api.v1.convert_notification_to_order',
                        args: {
                            notification: frm.doc.name,
                            order_type: values.order_type,
                            planned_start: values.planned_start,
                            planned_end: values.planned_end
                        },
                        freeze: true,
                        callback: (r) => {
                            if (r.message && r.message.order) {
                                frappe.set_route('Form', 'Maintenance Order', r.message.order);
                            }
                        }
                    });
                }, __('Create Order'));
            });
        }

        if (frm.doc.status === 'Converted to Order' && frm.doc.maintenance_order) {
            frm.add_custom_button(__('View Order'), () => {
                frappe.set_route('Form', 'Maintenance Order', frm.doc.maintenance_order);
            });
        }
    },

    equipment(frm) {
        if (frm.doc.equipment) {
            frappe.db.get_value('Equipment', frm.doc.equipment,
                ['functional_location', 'maintenance_team', 'criticality']).then(r => {
                if (r.message) {
                    if (r.message.functional_location && !frm.doc.functional_location) {
                        frm.set_value('functional_location', r.message.functional_location);
                    }
                    if (r.message.criticality === 'Critical') {
                        frm.set_value('priority', 'Critical');
                    }
                }
            });
        }
    },

    breakdown(frm) {
        if (frm.doc.breakdown) {
            frm.set_value('priority', 'Critical');
            if (!frm.doc.malfunction_start) {
                frm.set_value('malfunction_start', frm.doc.notification_date);
            }
        }
    }
});