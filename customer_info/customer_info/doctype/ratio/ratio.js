frappe.ui.form.on("Ratio","ratio",function(frm){
	cur_frm.doc.ratio_name = cur_frm.doc.ratio.toString()
	refresh_field("ratio_name")
})