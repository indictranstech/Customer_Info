frappe.ui.form.on("Item","serial_number",function(frm){
	cur_frm.doc.item_code = cur_frm.doc.brand + "-" +cur_frm.doc.serial_number
	cur_frm.doc.item_name = cur_frm.doc.item_code
	cur_frm.doc.item_group = cur_frm.doc.product_category
	refresh_field(["item_code","item_name"])	
})


frappe.ui.form.on("Item","product_category",function(frm){
	cur_frm.doc.item_group = cur_frm.doc.product_category
	refresh_field("item_group")
})

cur_frm.fields_dict['brand'].get_query = function(doc) {
	return {
		filters: {
			'category': cur_frm.doc.product_category 
		}
	}
}