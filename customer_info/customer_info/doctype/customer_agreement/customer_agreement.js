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
    onload:function(frm){
        if(!cur_frm.doc.today_plus_90_days){
            cur_frm.set_value("today_plus_90_days", frappe.datetime.add_days(frappe.datetime.nowdate(),90));
            refresh_field("today_plus_90_days")
        }
        if(cur_frm.doc.document_type == "Updated"){
            cur_frm.set_df_property("agreement_period","read_only",0)
            cur_frm.set_df_property("agreement_status","read_only",1)
            refresh_field("agreement_period","agreement_status")
        }    
    },
    validate:function(frm){
        if(cur_frm.doc.__islocal){
            cur_frm.doc.date = frappe.datetime.nowdate()
            refresh_field("date")
        }
        if(cur_frm.doc.agreement_status && cur_frm.doc.__islocal){
            cur_frm.doc.old_agreement_status = cur_frm.doc.agreement_status
            refresh_field("old_agreement_status")
        }
        if(cur_frm.doc.payment_day && cur_frm.doc.date){
            var date_after_one_month = frappe.datetime.add_months(cur_frm.doc.date,1)
            var newDate = new Date(date_after_one_month)
            var a = parseInt(cur_frm.doc.date.substr(-2))
            var b = parseInt(cur_frm.doc.payment_day)
            if(a > b){
                var c = a - b
                cur_frm.doc.due_date_of_next_month = new Date(newDate.setDate(newDate.getDate()-c))
                refresh_field("due_date_of_next_month")
            }
            if(a < b){
                var c = b - a
                cur_frm.doc.due_date_of_next_month = new Date(newDate.setDate(newDate.getDate() + c))
                refresh_field("due_date_of_next_month")
            }
            if(a == b){
                cur_frm.doc.due_date_of_next_month = newDate
                refresh_field("due_date_of_next_month")    
            }
        }
        if(cur_frm.doc.agreement_period && cur_frm.doc.__islocal){
            cur_frm.doc.payments_left = cur_frm.doc.agreement_period
            refresh_field("payments_left")
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
    },
    /*address: function(frm){
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
    },*/    
})

cur_frm.fields_dict['product'].get_query = function(doc) {
    return {
        query: "customer_info.customer_info.doctype.customer_agreement.customer_agreement.get_product"
    }
}

make_update_agreement  = function() {
    frappe.model.open_mapped_doc({
        method: "customer_info.customer_info.doctype.customer_agreement.customer_agreement.make_update_agreement",
        frm: cur_frm
    })
}

/*cur_frm.fields_dict['address'].get_query=function(doc){
	return {
		filters:{
			'customer':doc.customer
		}
	}
}*/