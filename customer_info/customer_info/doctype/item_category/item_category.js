frappe.ui.form.on("Item Category","validate",function(frm){	
	return frappe.call({
		method: "customer_info.customer_info.doctype.item_category.item_category.new_item_group",
		args: {
			"category_name":cur_frm.doc.category_name
		}
	})
})	

cur_frm.add_fetch('period', 'period', 'period_value');
cur_frm.add_fetch('ratio', 'ratio', 'ratio_value');