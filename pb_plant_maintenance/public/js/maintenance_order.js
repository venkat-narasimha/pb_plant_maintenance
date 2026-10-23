frappe.ui.form.on('Maintenance Order', {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.docstatus < 2) {
            if (frm.doc.status !== 'Completed' && frm.doc.status !== 'Closed') {
                frm.add_custom_button(__('Record Confirmation'), () => {
                    frappe.new_doc('Maintenance Confirmation', {
                        maintenance_order: frm.doc.name
                    });
                }, __('Actions'));

                frm.add_custom_button(__('Start Work'), () => {
                    frm.set_value('status', 'In Progress');
                    if (!frm.doc.actual_start) {
                        frm.set_value('actual_start', frappe.datetime.now_datetime());
                    }
                    frm.save();
                }, __('Actions'));

                frm.add_custom_button(__('Complete Order'), () => {
                    frappe.prompt({
                        fieldname: 'completion_notes',
                        fieldtype: 'Text Editor',
                        label: 'Completion Notes',
                        reqd: 0
                    }, (values) => {
                        frm.set_value('status', 'Completed');
                        frm.set_value('actual_end', frappe.datetime.now_datetime());
                        frm.set_value('completion_notes', values.completion_notes);
                        frm.save();
                    }, __('Complete Order'));
                }, __('Actions'));
            }

            frm.add_custom_button(__('Copy from Task List'), () => {
                frm.events.show_task_list_picker(frm);
            }, __('Actions'));
        }

        frm.set_query('work_center', 'operations', () => ({
            filters: { 'disabled': 0 }
        }));
    },

    show_task_list_picker(frm) {
        frappe.prompt({
            fieldname: 'task_list',
            fieldtype: 'Link',
            label: 'Task List',
            options: 'Maintenance Task List',
            reqd: 1,
            get_query: () => ({
                filters: {
                    status: 'Active',
                    task_list_type: frm.doc.equipment ? ['in', ['Equipment', 'General']] : ['in', ['Functional Location', 'General']]
                }
            })
        }, (values) => {
            frappe.call({
                method: 'pb_plant_maintenance.api.v1.copy_task_list_to_order',
                args: {
                    task_list: values.task_list,
                    order: frm.doc.name
                },
                callback: () => frm.reload_doc()
            });
        }, __('Select Task List'));
    },

    planned_start(frm) {
        if (frm.doc.planned_start && !frm.doc.planned_end) {
            frm.set_value('planned_end', frappe.datetime.add_hours(frm.doc.planned_start, 8));
        }
    },

    is_subcontracted(frm) {
        if (frm.doc.is_subcontracted) {
            frm.set_value('status', 'Planned');
        }
    }
});

frappe.ui.form.on('Order Operation', {
    planned_duration(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.work_center && row.planned_duration) {
            frappe.db.get_value('Workstation', row.work_center, 'pm_hourly_rate').then(r => {
                if (r.message && r.message.pm_hourly_rate) {
                    frappe.model.set_value(cdt, cdn, 'labor_cost',
                        row.planned_duration * r.message.pm_hourly_rate);
                }
            });
        }
    }
});

frappe.ui.form.on('Required Spare Part', {
    item_code(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code) {
            frappe.db.get_value('Item', row.item_code, 'last_purchase_rate').then(r => {
                if (r.message && r.message.last_purchase_rate) {
                    frappe.model.set_value(cdt, cdn, 'unit_cost', r.message.last_purchase_rate);
                }
            });
        }
    },
    quantity_required(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.quantity_required && row.unit_cost) {
            frappe.model.set_value(cdt, cdn, 'total_cost',
                row.quantity_required * row.unit_cost);
        }
    }
});