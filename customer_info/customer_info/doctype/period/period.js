frappe.ui.form.on("Period","period",function(frm){
	cur_frm.doc.period_name = cur_frm.doc.period + " " +"mėn"
	refresh_field("period_name")
})