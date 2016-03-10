cur_frm.add_fetch('product_category', 'period_value', 'period');
cur_frm.add_fetch('product_category', 'ratio_value', 'ratio');

frappe.ui.form.on("Item","serial_number",function(frm){
	cur_frm.doc.item_code = cur_frm.doc.brand + "-" +cur_frm.doc.serial_number
	cur_frm.doc.item_name = cur_frm.doc.item_code
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

frappe.ui.form.on("Item","purchase_price_with_vat",function(frm){
	var a = cur_frm.doc.purchase_price_with_vat * cur_frm.doc.ratio
	var b = a / cur_frm.doc.period
	var c = roundNumber(b,2)
	var n = c.toString();
	var n1 = n.slice(-2)
	var aa = parseInt(n1[0])
	if (aa >= 5){
		var five = Math.floor(b) + 0.99
		cur_frm.doc.monthly_rental_payment = five
		refresh_field("monthly_rental_payment")
	}
	else{
		var less = Math.floor(b) - 0.01
		cur_frm.doc.monthly_rental_payment = less
		refresh_field("monthly_rental_payment")
	}
})
