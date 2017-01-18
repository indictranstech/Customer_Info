frappe.ui.form.on("Brand","model",function(frm){
	cur_frm.doc.brand = cur_frm.doc.brand_name + "-" + cur_frm.doc.model
	refresh_field("brand")	
})