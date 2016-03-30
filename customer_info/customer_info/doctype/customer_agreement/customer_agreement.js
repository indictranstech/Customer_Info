cur_frm.add_fetch('product', '90d_sac_price', '90d_sac_price');
cur_frm.add_fetch('product', 'monthly_rental_payment', 'monthly_rental_payment');
cur_frm.add_fetch('product', 'agreement_period', 'agreement_period');
cur_frm.add_fetch('address', 'address_line1', 'address_line1');
cur_frm.add_fetch('address', 'address_line2', 'address_line2');
cur_frm.add_fetch('address', 'city', 'city');


frappe.ui.form.on("Customer Agreement",{
	payment_day:function(frm){
		if(cur_frm.doc.payment_day && cur_frm.doc.__islocal){
			cur_frm.doc.old_date = cur_frm.doc.payment_day
			refresh_field("old_date")
		}
	},
	customer: function(frm){
		if(cur_frm.doc.customer){
			frappe.call({
                method: "customer_info.customer_info.doctype.customer_agreement.customer_agreement.get_address",
                args: {
                    "customer": cur_frm.doc.customer,
                },
             	callback: function(r){
                    if(r.message){
                        cur_frm.doc.address = r.message[0]["name"],
                        cur_frm.doc.address_line1 = r.message[0]["address_line1"],
		          		cur_frm.doc.address_line2 = r.message[0]["address_line2"],
		          		cur_frm.doc.city = r.message[0]["city"],
		          		refresh_field(["address","address_line1","address_line2","city"]);
                    }
             	}  	
            });			
		}
	},
	onload:function(frm){
		if(!cur_frm.doc.today_plus_90_days){
			cur_frm.set_value("today_plus_90_days", frappe.datetime.add_days(frappe.datetime.nowdate(),90));
			refresh_field("today_plus_90_days")
		}
	}
})


cur_frm.fields_dict['address'].get_query=function(doc){
	return {
		filters:{
			'customer':doc.customer
		}
	}
}