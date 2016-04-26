cur_frm.add_fetch('product', 's90d_sac_price', 's90d_sac_price');
cur_frm.add_fetch('product', 'monthly_rental_payment', 'monthly_rental_payment');
cur_frm.add_fetch('product', 'period', 'agreement_period');
cur_frm.add_fetch('product', 'merchandise_status', 'merchandise_status');

frappe.ui.form.on("Customer Agreement",{
	payment_day:function(frm){
		if(cur_frm.doc.payment_day && cur_frm.doc.__islocal){
			cur_frm.doc.old_date = cur_frm.doc.payment_day
			refresh_field("old_date")
		}
        if(cur_frm.doc.payment_day){
            var a = parseInt(cur_frm.doc.payment_day)
            cur_frm.set_value("today_plus_payment_day",frappe.datetime.add_days(frappe.datetime.nowdate(),a))
            refresh_field("today_plus_payment_day") 
        }
	},
	customer: function(frm){
		if(cur_frm.doc.customer){
			frappe.call({
                method: "customer_info.customer_info.doctype.customer_agreement.customer_agreement.get_primary_address",
                args: {
                    "customer": cur_frm.doc.customer,
                },
             	callback: function(r){
                    if(r.message){
                        cur_frm.doc.address = r.message[0]["name"],                        
		          		cur_frm.doc.address_line1 = r.message[0]["address_line1"]
		          		cur_frm.doc.city = r.message[0]["city"]
		          		refresh_field(["address","address_line1","city"]);
                    }
                    if(r.message[0]['address_line2']){
                    	cur_frm.doc.full_address = r.message[0]["address_line1"] + "\n" + r.message[0]["address_line2"] + "\n" + r.message[0]["city"]
             			cur_frm.doc.address_line2 = r.message[0]["address_line2"]
             			refresh_field(['full_address','address_line2'])
             		}
             		if(!r.message[0]['address_line2']){
             			cur_frm.doc.address_line2 = ""
             			cur_frm.doc.full_address = r.message[0]["address_line1"] + "\n" + r.message[0]["city"]
             			refresh_field(["full_address","address_line2"])
             		}
             	}  	
            });			
		}
	},
	address: function(frm){
		if(cur_frm.doc.customer && cur_frm.doc.address){
			frappe.call({
                method: "customer_info.customer_info.doctype.customer_agreement.customer_agreement.get_address",
                args: {
                    "customer": cur_frm.doc.customer,
                	"address": cur_frm.doc.address
                },
             	callback: function(r){
                    if(r.message){     
		          		cur_frm.doc.address_line1 = r.message[0]["address_line1"]
		          		cur_frm.doc.city = r.message[0]["city"]
		          		refresh_field(["address","address_line1","city"]);
                    }
                    if(r.message[0]['address_line2']){
                    	cur_frm.doc.full_address = r.message[0]["address_line1"] + "\n" + r.message[0]["address_line2"] + "\n" + r.message[0]["city"]
             			cur_frm.doc.address_line2 = r.message[0]["address_line2"]
             			refresh_field(['full_address','address_line2'])
             		}
             		if(!r.message[0]['address_line2']){
             			cur_frm.doc.address_line2 = ""
             			cur_frm.doc.full_address = r.message[0]["address_line1"] + "\n" + r.message[0]["city"]
             			refresh_field(["full_address","address_line2"])
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
        if(cur_frm.doc.document_type == "Updated"){
            cur_frm.set_df_property("agreement_period","read_only",0)
            refresh_field("agreement_period")
        }
    },
    /*agreement_status:function(frm){
        if(cur_frm.doc.agreement_status && cur_frm.doc.__islocal){
            cur_frm.doc.old_agreement_status = cur_frm.doc.agreement_status
            refresh_field("old_agreement_status")
        }
    },*/
    validate:function(frm){
        if(cur_frm.doc.__islocal){
            cur_frm.doc.date = frappe.datetime.nowdate()
            refresh_field("date")
        }
        if(cur_frm.doc.agreement_status && cur_frm.doc.__islocal){
            cur_frm.doc.old_agreement_status = cur_frm.doc.agreement_status
            refresh_field("old_agreement_status")
        }
    },
    refresh:function(frm){
        if(!cur_frm.doc.__islocal){
            cur_frm.add_custom_button(__('Update Agreement'),function(){
                make_update_agreement();
            });
            cur_frm.set_df_property("agreement_no","hidden",0)
            refresh_field("agreement_no")
        }
    }    
})

make_update_agreement  = function() {
    frappe.model.open_mapped_doc({
        method: "customer_info.customer_info.doctype.customer_agreement.customer_agreement.make_update_agreement",
        frm: cur_frm
    })
}

cur_frm.fields_dict['address'].get_query=function(doc){
	return {
		filters:{
			'customer':doc.customer
		}
	}
}