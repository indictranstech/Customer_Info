
{% include 'customer_info/customer_info/doctype/payments_management/payoff_details.js' %};

Payments_Details = Class.extend({
	init:function(item, index, flag){
		console.log(flag,"flag")
		this.item = item;
		this.index = index;
		this.flag = flag
		this.init_for_render_dialog();
	},
	init_for_render_dialog:function(){
		var me = this;
		this.dialog = new frappe.ui.Dialog({
            title: "Payments And Summary Detalis",
                fields: [
                   	{"fieldtype": "HTML" , "fieldname": "payments_record" , "label": "Relative Items"},
                   	{"fieldtype": "Button" , "fieldname": "s90_day_pay_Off" , "label": "Pay Off Agreement"},
                   	{"fieldtype": "Button" , "fieldname": "pay_off_agreement" , "label": "90 day pay Off"}
                   	],
                   	primary_action_label: "Add",
                   	primary_action: function(){
                        me.make_list_of_payments_checked()
                    }
       	});
       	this.dialog.$wrapper.find('.modal-dialog').css("width", "1000px");
       	this.dialog.$wrapper.find('.modal-dialog').css("height", "1000px");
       	this.payments_record_list = []
       	this.fd = this.dialog.fields_dict;
       	this.initial_amount = cur_frm.doc.remaining_amount;
       	this.render_payment_management();
	},
	hide_dialog:function(){
		this.dialog.hide();
	},
	render_payment_management:function(){
		var me = this;
		console.log("item",me.item,this.item,"eeeeeee")
		var counter = 0
		$('button[data-fieldname="pay_off_agreement"]').hide();
		$('button[data-fieldname="s90_day_pay_Off"]').hide();
		if(this.item['id']){
			me.template_name = "common_template"
			this.common_function_for_render_templates()	
			me.dialog.show();
		}
	},
	common_function_for_render_templates:function(){
		var me = this;
		frappe.call({
			method:"customer_info.customer_info.doctype.payments_management.payments_management.get_payments_record",
			args:{
				"customer_agreement":me.item['id'],
				"receivable":cur_frm.doc.receivables,
				"late_fees":me.item['late_fees'],
				"payment_date":cur_frm.doc.payment_date
			},
			freeze: true,
			freeze_message: __("Please Wait..."),
			callback:function(r){
				if(r.message && me.template_name == "common_template"){
					console.log(r.message,"aaaaaaaaaaaaa")
					me.rendering_data = r.message
					me.check_pre_select = "Yes"
					html = $(frappe.render_template("common_template",{
            	   				"post":me.check_payment_record_for_pre_select(),
            	   				"payment_date":cur_frm.doc.payment_date,
            	   				"summary":r.message['summary_records'],
            	   				"history":r.message['history_record'],
            	   				"index":me.index
            	   			})).appendTo(me.fd.payments_record.wrapper);
					me.add_date_on_check();
					me.increase_decrease_total_charges_and_due_payment();
					me.init_trigger_for_nav_tabs();
				}
				else if(r.message && me.template_name == "payments_details"){
					me.remove_id_of_nav_tab_and_hide_primary_button()
					$('#history'+ me.index).hide();
					me.rendering_data = r.message
					me.check_pre_select = "No"
					html = $(frappe.render_template("payments_details",{
        	   				"post":me.check_payment_record_for_pre_select(),
        	   				"payment_date":cur_frm.doc.payment_date,
        	   				"index":me.index
        	   			})).appendTo(me.fd.payments_record.wrapper);
					$(me.dialog.body).parent().find('.btn-primary').show();
					$(me.dialog.body).find('#home'+ me.index).removeClass("tab-pane fade");
					me.add_date_on_check();
					me.increase_decrease_total_charges_and_due_payment();
				}
				else if(r.message && me.template_name == "summary_record"){
					me.remove_id_of_nav_tab_and_hide_primary_button();
					$('#history'+ me.index).hide();
					$(me.dialog.body).parent().find('.btn-primary').hide();
			
					if(r.message['summary_records']['cond'] == "pay off agreement"){
						if(me.flag == "Open Agreement"){
							$('button[data-fieldname="pay_off_agreement"]').show();
							me.values = r.message["summary_records"];
							new payoff_details(me);	
						}
					}
					else if(r.message['summary_records']['cond'] == "90 day pay Off"){
						if(me.flag == "Open Agreement"){
							$('button[data-fieldname="s90_day_pay_Off"]').show();
							me.values = r.message["summary_records"];
							new payoff_details(me);
						}
					}
					html = $(frappe.render_template("summary_record",{
        	   				"summary":r.message['summary_records'],
        	   				"index":me.index
        	   			})).appendTo(me.fd.payments_record.wrapper);
					$(me.dialog.body).find('#menu'+ me.index).removeClass("tab-pane fade");
				}
				else if(r.message && me.template_name == "payment_history"){
					me.remove_id_of_nav_tab_and_hide_primary_button();
					html = $(frappe.render_template("payment_history",{
        	   				"index":me.index,
        	   				"history":r.message['history_record']
        	   			})).appendTo(me.fd.payments_record.wrapper);
					$(me.dialog.body).find('#history'+ me.index).removeClass("tab-pane fade");
					$(me.dialog.body).parent().find('.btn-primary').hide();
				}
			}	
		});
	},
	remove_id_of_nav_tab_and_hide_primary_button:function(){
		var me = this;
		$(me.dialog.body).parent().find('.btn-primary').show()
		$(me.dialog.body).find('#home'+ me.index).remove()
		$(me.dialog.body).find('#menu'+ me.index).remove()
		$(me.dialog.body).find('#history'+ me.index).remove()	
	},
	init_trigger_for_nav_tabs:function(){
		var me = this;		
		$(me.dialog.body).find(".payment-li").click(function(){
			$('button[data-fieldname="pay_off_agreement"]').hide();
			$('button[data-fieldname="s90_day_pay_Off"]').hide();
			//me.template_name = "payments_management"
			me.template_name = "payments_details"
			me.common_function_for_render_templates()
		});		
		$(me.dialog.body).find(".summary-li").click(function(){
			me.template_name = "summary_record"
			me.common_function_for_render_templates()
		});
		$(me.dialog.body).find(".history-li").click(function(){
			$('button[data-fieldname="pay_off_agreement"]').hide();
			$('button[data-fieldname="s90_day_pay_Off"]').hide();
			me.template_name = "payment_history"
			me.common_function_for_render_templates()
		});
	},
	check_payment_record_for_pre_select:function(){
		var me = this;
		if(me.check_pre_select == "No"){
			me.payments_record_list = []
		}
		$.each(me.rendering_data, function(i, d) {
			me.payments_record_list.push(d)
		});
   		var date = new Date();
		var firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
		var lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);
		//var today = new Date(frappe.datetime.add_days(frappe.datetime.nowdate(),-1));
		var today = new Date();
		var lastDay_pluse_one = new Date(date.getFullYear(), date.getMonth() + 1, 1);

	   	for(i=0;i < me.payments_record_list[0].length; i++){
	   		//var date_diff_first = frappe.datetime.get_diff(me.payments_record_list[0][i]['due_date'],firstDay)
	   		//var date_diff_last = frappe.datetime.get_diff(lastDay,me.payments_record_list[0][i]['due_date'])
	   		due_date_dateformat = new Date(me.payments_record_list[0][i]['due_date'])
	   		due_date_dateformat.setHours(00)
	   		due_date_dateformat.setSeconds(00)
	   		due_date_dateformat.setMinutes(00)
	   		today.setHours(00)
	   		today.setSeconds(00)
	   		today.setMinutes(00)
	   		if(me.payments_record_list[0][i]['check_box_of_submit'] == 0 && me.payments_record_list[0][i]['check_box'] == 1 && me.payments_record_list[0][i]['payment_date']){
	   			me.payments_record_list[0][i]['paid'] = "Yes"	
	   		}
	   		else{
	   			me.payments_record_list[0][i]['paid'] = "No"		
	   		}
	   		console.log(due_date_dateformat,today)
	   		
	   		if((me.payments_record_list[0][i]['check_box_of_submit'] == 0 && (due_date_dateformat <= today && due_date_dateformat >= firstDay) && me.payments_record_list[0][i]['pre_select_uncheck'] == 0) || (me.payments_record_list[0][i]['check_box_of_submit'] == 0 && due_date_dateformat < firstDay && me.payments_record_list[0][i]['pre_select_uncheck'] == 0)){
	   			me.payments_record_list[0][i]['check_box'] = 1
	   			me.payments_record_list[0][i]['pre_select'] = "Yes"
	   			me.payments_record_list[0][i]['payment_date'] = cur_frm.doc.payment_date
	   			me.payments_record_list[0][i]['is_late_payment'] = "Yes"	   			
	   		}
	   		else{
	   			me.payments_record_list[0][i]['pre_select'] = "No"
	   			me.payments_record_list[0][i]['is_late_payment'] = "No"
	   		}
	   	}
	   	return me.payments_record_list
	},
	make_list_of_payments_checked:function(){
		this.row_to_update = []
		this.row_to_check = []
		this.row_to_uncheck = []
		this.row_to_pre_select_uncheck = []
		var me = this;
        
        $.each($(this.fd.payments_record.wrapper).find(".select"), function(name, item){
        	if($(this).is(':checked') && ($(this).attr("data-from") == "")){	
        		me.row_to_update.push($(item).val());
        	}
        	if($(this).is(':not(:checked)') && ($(this).attr("pre-select") == "Yes")){
                me.row_to_pre_select_uncheck.push($(item).val());
    		}
    		if($(this).hasClass("new-entry") && $(this).is(':checked')){
                me.row_to_check.push($(item).val());
    		}
    		if($(this).hasClass("new-entry") && $(this).is(':not(:checked)')){
                me.row_to_uncheck.push($(item).val());
    		}
        });
        
        //console.log(me.row_to_pre_select_uncheck,"me.row_to_pre_select_uncheck")
        console.log(me.row_to_update,"row_to_update")
        //console.log(me.row_to_uncheck,"row_to_uncheck")
        console.log(me.row_to_check,"row_to_check")
	    //console.log(cur_frm.doc.bonus,"bonus")
	    var add_list = []
	    console.log((me.dialog.$wrapper).find(".select"),"me 12321132111")
	    $.each((me.dialog.$wrapper).find(".select"),function(i,d){
	    	if ($(d).is(':checked')){
	    		add_list.push($(d).attr("value").split(" ")[1])
	    	}
	    });
	    var checking_sequence = ""
	    console.log(add_list,"add_list")
	    if(add_list.length > 1){
	    	for(i=0;i<add_list.length-1;i++){
		    	console.log(add_list[i+1],add_list[i])
		    	if(flt(add_list[i+1]) - flt(add_list[i]) != 1){
		    		frappe.throw("Error Please Add Payment In sequence")
		    		checking_sequence = "false"
		    		break;
		    	}
	    	}
	    }
	    console.log("checking_sequence",checking_sequence)
	    /*if(checking_sequence == ""){
	    	me.common_function_for_add_checkbox();
	    }*/
	    if(add_list.length >= 1 && add_list[0] == "1"){
		    me.common_function_for_add_checkbox();
	    }
	    if(add_list.length >= 1 && add_list[0] != "1"){
	    	frappe.throw("Error Please Add Payment In sequence")
	    }
	    /*if(me.row_to_check.concat(me.row_to_update).length == 0){
	    	frappe.throw("Please Any Payment")
	    }*/
	},
	common_function_for_add_checkbox:function(){
		var me = this;
		if(me.row_to_update.length > 0 || me.row_to_uncheck.length > 0 || me.row_to_check.length > 0){
			var me = this
	   		frappe.call({    
		        method: "customer_info.customer_info.doctype.payments_management.payments_management.temporary_payments_update_to_child_table_of_customer_agreement",
		        async: false,
	           	args: {
	           		"row_to_update":me.row_to_update,
	           		"row_to_uncheck":me.row_to_uncheck,
	           		"row_to_check":me.row_to_check,
	           		"row_to_pre_select_uncheck":me.row_to_pre_select_uncheck,
	           		"parent":this.item['id'],
	           		"payment_date":cur_frm.doc.payment_date
	            },
	           	callback: function(res){
	        	}
	        });
	        frappe.call({
		        method: "customer_info.customer_info.doctype.payments_management.payments_management.set_values_in_agreement_temporary",
		        async: false,
	           	args: {
	           		"customer_agreement":this.item['id'],
	            	"frm_bonus":cur_frm.doc.bonus,
	            	//"flag":"Payment Details",
	            	"row_to_uncheck":me.row_to_uncheck
	            },
	           	callback: function(r){
	        		cur_frm.set_value("bonus",r.message)
	        		render_agreements()
	            	me.update_total_charges_and_due_payments()
	        		me.dialog.hide();
	        	}
	        });	
	    }
	    else{
	    	me.dialog.hide();
	    }
	},
	add_date_on_check:function(){
		var me = this;
		if(me.flag == "Suspended Agreement"){
			$(me.dialog.body).find('input[type="checkbox"]').prop( "disabled", true );
			$(me.dialog.body).parent().find('.btn-primary').hide();
		}
		$('.select').change(function() {  
		    var value = '"'+$(this).attr("value")+'"' 
		    if ($(this).is(':checked')){
		    	$('[payment-id= '+value+']').text(cur_frm.doc.payment_date)
		    }
		    else{
		    	$('[payment-id= '+value+']').empty()
		    }	
		});
	},
	increase_decrease_total_charges_and_due_payment:function(){
		var me = this;
	    var factor = me.payments_record_list[0][1].monthly_rental_amount;		
		$(me.fd.payments_record.wrapper).find('div.due_payments').append(flt((cur_frm.doc.amount_of_due_payments)).toFixed(2))
		$(me.fd.payments_record.wrapper).find('div.total_charges').append(flt((cur_frm.doc.total_charges)).toFixed(2))
		$(me.dialog.wrapper).find('input[data-from=""]').change(function() {  
		    if ($(this).is(':checked')) {
		    	me.add = "Yes"
		    	me.late_fee = $(this).attr("late-fee")
				me.add_and_subtract_from_total_and_due_charges();
			} 
			else {
				me.add = "No"
				me.late_fee = $(this).attr("late-fee")
				me.add_and_subtract_from_total_and_due_charges();
			}
		});
		$(me.dialog.wrapper).find('input[data-from="from_child_table"]').change(function() {  
		    if ($(this).is(':checked')){
		    	me.add = "Yes"
		    	me.late_fee = $(this).attr("late-fee")
				me.add_and_subtract_from_total_and_due_charges();
			} 
			else {
				me.add = "No"
				me.late_fee = $(this).attr("late-fee")
				me.add_and_subtract_from_total_and_due_charges();
			}
		});
	},
	add_and_subtract_from_total_and_due_charges:function(){
		var me = this;
		console.log(me.late_fee,"late_fee")
		var factor = me.payments_record_list[0][1].monthly_rental_amount;
		if(me.add == "Yes"){
			me.total_charges = parseFloat($(me.dialog.body).find('div.total_charges').text()) + parseFloat(factor) + flt(me.late_fee)
			me.due_payments = parseFloat($(me.dialog.body).find('div.due_payments').text()) + parseFloat(factor) + flt(me.late_fee)
			me.set_total_due_and_total_charges()
		}
		if(me.add == "No"){
			me.due_payments = parseFloat($(me.dialog.body).find('div.due_payments').text()) - parseFloat(factor) - flt(me.late_fee)
			me.total_charges = parseFloat($(me.dialog.body).find('div.total_charges').text()) - parseFloat(factor) - flt(me.late_fee)
			me.set_total_due_and_total_charges()
		}
	},
	set_total_due_and_total_charges:function(){
		var me = this;
		$(me.dialog.body).find('div.due_payments').empty()
		$(me.dialog.body).find('div.due_payments').append(me.due_payments.toFixed(2))
		$(me.dialog.body).find('div.total_charges').empty()
		$(me.dialog.body).find('div.total_charges').append(me.total_charges.toFixed(2))
	},
	update_total_charges_and_due_payments : function(frm){
		var me = this;
		var factor = me.payments_record_list[0][1].monthly_rental_amount;
		var payments_cheked = me.row_to_check.length + me.row_to_update.length
		cur_frm.set_value("total_charges",parseFloat($(cur_dialog.body).find('div.total_charges').text()) == 0 ? "0":parseFloat($(cur_dialog.body).find('div.total_charges').text()))
		cur_frm.set_value("amount_of_due_payments",parseFloat($(cur_dialog.body).find('div.due_payments').text()) == 0 ? "0":parseFloat($(cur_dialog.body).find('div.due_payments').text()))
	}
});