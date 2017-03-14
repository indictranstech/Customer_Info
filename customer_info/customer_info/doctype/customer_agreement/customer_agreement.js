cur_frm.add_fetch('product', 's90d_sac_price', 's90d_sac_price');
cur_frm.add_fetch('product', 's90d_sac_price', 'duplicate_s90d_sac_price');
cur_frm.add_fetch('product', 'monthly_rental_payment', 'monthly_rental_payment');
cur_frm.add_fetch('product', 'period', 'agreement_period');
cur_frm.add_fetch('product', 'product_category', 'product_category');
cur_frm.add_fetch('product', 'merchandise_status', 'merchandise_status');
cur_frm.add_fetch('customer','customer_group','customer_group')


var print_format_mapper = {
                "Perdavimo-priėmimo aktas":"Delivery - receive note 1",
                "Grąžinimo aktas":"Delivery - receive note 2",
                "Sutarties sustabdymo aktas":"Delivery - receive note 3",
                "Prekės keitimo aktas":"Delivery - receive note 4"
            }


frappe.ui.form.on("Customer Agreement",{
	payment_day:function(frm){
		if(cur_frm.doc.payment_day && cur_frm.doc.__islocal){
            console.log("in payment_day")
			cur_frm.doc.old_date = cur_frm.doc.payment_day
			refresh_field("old_date")
		}
        if(cur_frm.doc.payment_day && !cur_frm.doc.__islocal && cur_frm.doc.payments_record){
            date_of_next_month_according_to_payment_day()
            frappe.call({
                method: "change_due_dates_in_child_table",
                doc: frm.doc,
                callback: function(r){
                    console.log(r.message)
                }   
            });
        }
	},
    update_due_date:function(frm){
        if(cur_frm.doc.payment_day && !cur_frm.doc.__islocal && cur_frm.doc.payments_record && cur_frm.doc.update_due_date){
            cur_frm.doc.due_date_of_next_month = cur_frm.doc.update_due_date
            refresh_field("due_date_of_next_month")
            console.log(cur_frm.doc.due_date_of_next_month,"due_date_of_next_month")
            frappe.call({
                method: "customer_info.customer_info.doctype.customer_agreement.customer_agreement.update_due_dates_of_payments",
                args:{
                    "update_date":cur_frm.doc.update_due_date,
                    "name":cur_frm.doc.name
                },
                freeze: true,
                freeze_message: __("Please Wait..."),
                callback: function(r){
                    $.each(cur_frm.doc.payments_record,function(index,row){
                        if(Object.keys(r.message).indexOf(row.payment_id) != -1){
                            row.due_date = r.message[row.payment_id]        
                        }
                    })
                    refresh_field("payments_record")
                    cur_frm.set_value("current_due_date",cur_frm.doc.update_due_date)
                    cur_frm.set_value("next_due_date",frappe.datetime.add_months(cur_frm.doc.update_due_date,1))
                    cur_frm.doc.payment_day = String((cur_frm.doc.update_due_date).split("-")[2])
                    refresh_field("payment_day")
                }   
            });
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
                        //cur_frm.set_value("address",r.message[0]['name'])
                        cur_frm.set_value("address_line1",r.message[0]['address_line1'])
                        cur_frm.set_value("city",r.message[0]['city'])
                        if(r.message[0]['address_line2']){
                            cur_frm.set_value("address_line2",r.message[0]["address_line2"])
                        }
                        else{
                            cur_frm.set_value("address_line2","")
                        }
                    }
                    else{
                        //cur_frm.set_value("address","")
                        cur_frm.set_value("city","")
                        cur_frm.set_value("address_line1","")
                        cur_frm.set_value("address_line2","")   
                    }
             	}  	
            });			
		}
	},
    onload:function(frm){
        $('.page-icon-group').hide()
        if(cur_frm.doc.agreement_status != "Updated"){
            cur_frm.set_df_property("agreement_status","options",["","Open","Closed","Suspended"])
            cur_frm.set_df_property("agreement_update_date","hidden",1)
        }
        if(cur_frm.doc.agreement_status == "Updated"){
            cur_frm.set_df_property("agreement_status","options",["","Open","Closed","Suspended","Updated"])
            cur_frm.set_df_property("agreement_update_date","hidden",0)
        }
        if(cur_frm.doc.__islocal){
            cur_frm.doc.agreement_status = "Open"
            refresh_field("agreement_status")
        }
        if(cur_frm.doc.product && !cur_frm.doc.__islocal){
            cur_frm.set_df_property("product","read_only",1)
        }
        if(cur_frm.doc.document_type == "Updated" && cur_frm.doc.__islocal){
            cur_frm.set_df_property("agreement_period","read_only",0)
        }
    },
    today_plus_90_days:function(frm){
        if(cur_frm.doc.today_plus_90_days){
            cur_frm.set_value("duplicate_today_plus_90_days",cur_frm.doc.today_plus_90_days)
        }
    },
    validate:function(frm){
        if(cur_frm.doc.__islocal && cur_frm.doc.document_type == "New"){
            cur_frm.set_value("date",cur_frm.doc.date ? cur_frm.doc.date:frappe.datetime.nowdate())
            cur_frm.set_value("today_plus_90_days", frappe.datetime.add_days(frappe.datetime.nowdate(),90));
            cur_frm.set_value("duplicate_today_plus_90_days",frappe.datetime.add_days(frappe.datetime.nowdate(),90));    
        }
        if(cur_frm.doc.payment_day && cur_frm.doc.date && cur_frm.doc.__islocal){
            date_of_next_month_according_to_payment_day()
        }
        if(cur_frm.doc.agreement_status && cur_frm.doc.__islocal){
            cur_frm.doc.old_agreement_status = cur_frm.doc.agreement_status
            refresh_field("old_agreement_status")
        }
        if(cur_frm.doc.merchandise_status && cur_frm.doc.__islocal){
            cur_frm.doc.old_merchandise_status = cur_frm.doc.merchandise_status
            refresh_field("old_merchandise_status")
        }
        /*if(cur_frm.doc.agreement_period && cur_frm.doc.__islocal){
            cur_frm.doc.payments_left = cur_frm.doc.agreement_period
            refresh_field("payments_left")
            cur_frm.set_value("discounted_payments_left",cur_frm.doc.agreement_period)
            cur_frm.set_value("balance",cur_frm.doc.monthly_rental_payment * flt(cur_frm.doc.agreement_period))
        }*/
        if(cur_frm.doc.product){
            cur_frm.set_df_property("product","read_only",1)
        }
        if(cur_frm.doc.document_type == "Updated"){
            cur_frm.set_df_property("agreement_period","read_only",1)
        }
        if(cur_frm.doc.agreement_status != "Updated"){
            cur_frm.set_df_property("agreement_update_date","hidden",1)    
        }
        /*if(cur_frm.doc.product_category && cur_frm.doc.product){
            cur_frm.set_value("concade_product_name_and_category",cur_frm.doc.product_category + " " + cur_frm.doc.product)
        }*/
        /*if(cur_frm.doc.__islocal){ //add bonus of new agreement
            if(cur_frm.doc.customer_group == "Individual"){    
                frappe.call({
                    async:false,
                    method: "frappe.client.get_value",
                    args: {
                        doctype: "Customer Agreement",
                        fieldname: "name",
                        filters: { customer: cur_frm.doc.customer },
                    },
                    callback: function(res){
                        if (res && res.message){
                            cur_frm.set_value("bonus",20)
                            cur_frm.set_value("new_agreement_bonus",20)
                        }
                    }   
                });
                frappe.call({
                    async:false,
                    method: "customer_info.customer_info.doctype.customer_agreement.customer_agreement.set_bonus_in_customer",
                    args: {
                        "customer": cur_frm.doc.customer,
                        "bonus":cur_frm.doc.bonus
                    },
                    callback: function(res){
                    }   
                });
            }
        }*/         
    },
    refresh:function(frm){
        $('.page-icon-group').hide();
        if(!cur_frm.doc.__islocal){
            cur_frm.add_custom_button(__('Update Agreement'),function(){
                //make_update_agreement();
                make_new_child_agreement(frm);
            });
            cur_frm.set_df_property("agreement_no","hidden",0)
            refresh_field("agreement_no")
            if(cur_frm.doc.agreement_status == "Open"){
                cur_frm.add_custom_button(__('Payments Management'),function(){
                    get_payments_management_from_agreement();
                });
            }    
        }
        if(cur_frm.doc.duplicate_today_plus_90_days && !cur_frm.doc.__islocal){
            console.log("in if cond")
            var today_date = frappe.datetime.nowdate()
            var date_diff = frappe.datetime.get_diff(today_date,cur_frm.doc.duplicate_today_plus_90_days)
            console.log(date_diff,"date_diff")
            console.log((date_diff >= 0),"if")
            if(date_diff >= 0){
                console.log("in date_diff")
                cur_frm.set_value('duplicate_s90d_sac_price',0)
                cur_frm.set_value('duplicate_today_plus_90_days','')
                cur_frm.save();
            }
        }
        if(!cur_frm.doc.__islocal){
            cur_frm.set_df_property("update_due_date","hidden",0)
            frm.add_custom_button(__('Customer Agreement'), 
            frm.events.respond_with_customer_agreement, __("Generate PDF"));
            
            $.each(print_format_mapper,function(index,data){
                frm.add_custom_button(__(index),
                frm.events.respond_with_customer_agreement, __("Generate PDF"));                 
            })
            /*for(i=1;i<=print_format_mapper;i++){
                frm.add_custom_button(__('Delivery - receive note '+i),
                frm.events.respond_with_customer_agreement, __("Generate PDF"));
            }*/
        }

    },
    respond_with_customer_agreement:function(frm){
        var url_to_generate_pdf = frappe.urllib.get_base_url()+"/api/method/frappe.templates.pages.print.download_pdf?doctype=Customer%20Agreement&name="+cur_frm.doc.name+"&format="+print_format_mapper[$(this).text()]+"&no_letterhead=0"
        window.open(url_to_generate_pdf)
    },
    agreement_status:function(frm){
        if(cur_frm.doc.agreement_status == "Closed" && !cur_frm.doc.__islocal){
            cur_frm.doc.agreement_close_date = frappe.datetime.nowdate()
            refresh_field("agreement_close_date")
        }
        if(cur_frm.doc.agreement_status == "Updated" && cur_frm.doc.agreement_update_date){
            cur_frm.set_df_property("agreement_update_date","hidden",0)
        }
        if(cur_frm.doc.agreement_status != "Updated"){
            cur_frm.set_df_property("agreement_update_date","hidden",1)    
        }
        if(cur_frm.doc.agreement_status == "Suspended" && !cur_frm.doc.__islocal){
            cur_frm.set_value("suspended_from",frappe.datetime.nowdate())
        }
    },
    agreement_closing_suspending_reason:function(frm){
        if(cur_frm.doc.agreement_closing_suspending_reason  == "Fraud/Stolen"){
            cur_frm.set_value("merchandise_status","Stolen")
        }
    }

})

cur_frm.fields_dict['product'].get_query = function(doc) {
    return {
        query: "customer_info.customer_info.doctype.customer_agreement.customer_agreement.get_product"
    }
}

make_update_agreement = function() {
    frappe.model.open_mapped_doc({
        method: "customer_info.customer_info.doctype.customer_agreement.customer_agreement.make_update_agreement",
        frm: cur_frm
    })
}


function make_new_child_agreement(frm){
    tn = frappe.model.make_new_doc_and_get_name('Customer Agreement');
    locals['Customer Agreement'][tn].today_plus_90_days = cur_frm.doc.today_plus_90_days
    locals['Customer Agreement'][tn].duplicate_today_plus_90_days = cur_frm.doc.today_plus_90_days
    locals['Customer Agreement'][tn].document_type = "Updated"
    locals['Customer Agreement'][tn].agreement_status = "Open"
    locals['Customer Agreement'][tn].parent_name = cur_frm.doc.name
    locals['Customer Agreement'][tn].agreement_no = cur_frm.doc.name
    locals['Customer Agreement'][tn].date = frappe.datetime.nowdate()
    frappe.set_route('Form', 'Customer Agreement', tn);
}

//date_of_next_month_according_to_payment_day
/*date_of_next_month_according_to_payment_day = function(frm){
    var date_after_one_month = frappe.datetime.add_months(cur_frm.doc.date,1)
    var newDate = new Date(date_after_one_month)
    var a = parseInt(cur_frm.doc.date.substr(-2))
    var b = parseInt(cur_frm.doc.payment_day)
    if(a > b){
        var c = a - b
        cur_frm.doc.due_date_of_next_month = new Date(newDate.setDate(newDate.getDate()-c))
        refresh_field("due_date_of_next_month")
        cur_frm.set_value("current_due_date",cur_frm.doc.due_date_of_next_month)
        cur_frm.set_value("next_due_date",cur_frm.doc.due_date_of_next_month)    
    }
    if(a < b){
        var c = b - a
        cur_frm.doc.due_date_of_next_month = new Date(newDate.setDate(newDate.getDate() + c))
        refresh_field("due_date_of_next_month")
        cur_frm.set_value("current_due_date",cur_frm.doc.due_date_of_next_month)
        cur_frm.set_value("next_due_date",cur_frm.doc.due_date_of_next_month)    
    }
    if(a == b){
        cur_frm.doc.due_date_of_next_month = newDate
        refresh_field("due_date_of_next_month")
        cur_frm.set_value("current_due_date",cur_frm.doc.due_date_of_next_month)
        cur_frm.set_value("next_due_date",cur_frm.doc.due_date_of_next_month)    
    }
}*/
date_of_next_month_according_to_payment_day = function(frm){
    var date_after_one_month = frappe.datetime.add_months(cur_frm.doc.date,1)
    var newDate = new Date(date_after_one_month)
    var a = parseInt(cur_frm.doc.date.substr(-2))
    var b = parseInt(cur_frm.doc.payment_day)
    if(a > b){
        var c = a - b
        //cur_frm.doc.due_date_of_next_month = new Date(newDate.setDate(newDate.getDate()-c))
        cur_frm.doc.due_date_of_next_month = new Date(frappe.datetime.add_days(newDate,-c))
        refresh_field("due_date_of_next_month")
        cur_frm.set_value("current_due_date",cur_frm.doc.date)
        cur_frm.set_value("next_due_date",cur_frm.doc.due_date_of_next_month)    
    }
    if(a < b){
        var c = b - a
        //cur_frm.doc.due_date_of_next_month = new Date(newDate.setDate(newDate.getDate() + c))
        cur_frm.doc.due_date_of_next_month = new Date(frappe.datetime.add_days(newDate,+c))
        refresh_field("due_date_of_next_month")
        cur_frm.set_value("current_due_date",cur_frm.doc.date)
        cur_frm.set_value("next_due_date",cur_frm.doc.due_date_of_next_month)    
    }
    if(a == b){
        cur_frm.doc.due_date_of_next_month = newDate
        refresh_field("due_date_of_next_month")
        cur_frm.set_value("current_due_date",cur_frm.doc.date)
        cur_frm.set_value("next_due_date",cur_frm.doc.due_date_of_next_month)    
    }
    if(cur_frm.doc.__islocal){
        cur_frm.set_value("current_due_date",cur_frm.doc.date)
        cur_frm.set_value("next_due_date",cur_frm.doc.due_date_of_next_month)
    }
}



//update_due_date_in_payments_records_according_to_payment_day
get_update_due_date = function(due_date_of_next_month,i){
    var CurrentDate = new Date(due_date_of_next_month);
    console.log(((new Date(CurrentDate.setMonth(CurrentDate.getMonth() + i))) instanceof Date),"dates")
    return new Date(CurrentDate.setMonth(CurrentDate.getMonth() + i));
}


get_payments_management_from_agreement = function(frm){
    frappe.model.open_mapped_doc({
        method: "customer_info.customer_info.doctype.payments_management.payments_management.get_payments_management_from_agreement",
        frm: cur_frm
    })
}
