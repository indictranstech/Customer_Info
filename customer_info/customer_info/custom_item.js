/*cur_frm.add_fetch('product_category', 'period_value', 'period');
cur_frm.add_fetch('product_category', 'ratio_value', 'ratio');*/

/*frappe.ui.form.on("Item","product_category",function(frm){
	cur_frm.add_fetch('product_category', 'period_value', 'period');
	cur_frm.add_fetch('product_category', 'ratio_value', 'ratio');
	refresh_field("period")	
})*/

frappe.ui.form.on("Item", "product_category", function(frm){
    if(cur_frm.doc.product_category){
          frappe.call({
                  method: "frappe.client.get_value",
                  args: {
                        doctype: "Item Category",
                        fieldname: ["period_value","ratio_value","period"],
                        filters: { name: cur_frm.doc.product_category },
                  },
             	callback: function(res){
                	      if (res && res.message){
                		      cur_frm.doc.period = res.message['period_value']
                              cur_frm.doc.ratio = res.message['ratio_value']
                		      cur_frm.doc.agreement_period = res.message['period']
                              refresh_field(["period","ratio","agreement_period"]);
                 	      }
             	}  	
          });
      }    
});


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
      if(cur_frm.doc.purchase_price_with_vat >= 1 && cur_frm.doc.purchase_price_with_vat <= 430.99){
            var mul = cur_frm.doc.purchase_price_with_vat * 15
            var div = mul / 100
            var de = cur_frm.doc.purchase_price_with_vat - div
            calculation_for_90d_sac(de)
      }            
      if(cur_frm.doc.purchase_price_with_vat >= 431 && cur_frm.doc.purchase_price_with_vat <= 580.99){
            var mul = cur_frm.doc.purchase_price_with_vat * 12
            var div = mul / 100
            var de = cur_frm.doc.purchase_price_with_vat - div
            calculation_for_90d_sac(de)                  
      }
      if(cur_frm.doc.purchase_price_with_vat >= 581){
            var mul = cur_frm.doc.purchase_price_with_vat * 10
            var div = mul / 100
            var de = cur_frm.doc.purchase_price_with_vat - div
            calculation_for_90d_sac(de)      
      }
})            

calculation_for_90d_sac = function(de){
      var deduc = de.toFixed(2)
      var str_deduc = deduc.toString()
      var slice_str_deduc = str_deduc.slice(-1)
      var int_slice_str_deduc = parseInt(slice_str_deduc[0])

      var floor = Math.floor(deduc)
      var str_floor = floor.toString();
      var slice_str_floor = str_floor.slice(-1)
      var int_str_floor = parseInt(slice_str_floor[0])
      
      if (int_str_floor >= 5 && int_slice_str_deduc >= 0) {
            var minus = 9 - int_str_floor
            cur_frm.set_value("90d_sac_price",(floor + minus))
            refresh_field("90d_sac_price")
      }
      if(int_str_floor <= 5 && int_slice_str_deduc == 0){
            var minus = 5 - int_str_floor
            cur_frm.set_value("90d_sac_price",(floor + minus))
            refresh_field("90d_sac_price")     
      }      
}