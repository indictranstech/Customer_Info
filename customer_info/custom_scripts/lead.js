frappe.ui.form.on("Lead", {
	refresh:function() {
		// body...
		setTimeout(function() { cur_frm.set_df_property("naming_series", "hidden", true); }, 100);
	}
})