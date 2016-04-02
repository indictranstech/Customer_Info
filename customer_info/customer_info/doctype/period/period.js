frappe.ui.form.on("Period","period",function(frm){
	if(cur_frm.doc.period){
		cur_frm.doc.period_name = cur_frm.doc.period + " " +"mėn."
		cur_frm.set_df_property("period","read_only",1)
		refresh_field(["period_name","period"])
	}	
})