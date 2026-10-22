frappe.ui.form.on('Equipment', {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Create Notification'), () => {
                frappe.new_doc('Maintenance Notification', {
                    equipment: frm.doc.name,
                    functional_location: frm.doc.functional_location,
                    notification_type: 'Malfunction'
                });
            }, __('Create'));

            frm.add_custom_button(__('Create Maintenance Order'), () => {
                frappe.new_doc('Maintenance Order', {
                    equipment: frm.doc.name,
                    functional_location: frm.doc.functional_location,
                    order_type: 'Corrective'
                });
            }, __('Create'));

            frm.add_custom_button(__('Maintenance History'), () => {
                frappe.set_route('query-report', 'Maintenance Order List', {
                    equipment: frm.doc.name
                });
            }, __('View'));

            frm.add_custom_button(__('Measurement History'), () => {
                frappe.set_route('List', 'Measurement Document', {
                    equipment: frm.doc.name
                });
            }, __('View'));
        }
    },

    asset_reference(frm) {
        if (frm.doc.asset_reference) {
            frappe.db.get_doc('Asset', frm.doc.asset_reference).then(asset => {
                if (asset.company) frm.set_value('company', asset.company);
                if (asset.custodian) frm.set_value('custodian', asset.custodian);
            });
        }
    }
});