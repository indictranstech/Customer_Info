

payoff_details = Class.extend({
	init:function(me){
		this.old_instance = me;
		this.init_for_render_dialog();
	},
	init_for_render_dialog:function(){
		var me = this;
		if(me.old_instance != "Process Payments"){
			me.click_on_pay_off_agreement();
			me.click_on_90_day_pay_Off();
		}
		else{
			me.show_dialog();
		}
	},
	click_on_pay_off_agreement:function(){
		var me = this;
		$(me.old_instance.dialog.fields_dict.payments_record.$wrapper).find(".pay_off_agreement").click(function() {
			me.old_dialog = me.old_instance.dialog;
			me.show_dialog();
		});
		/*if($("button[fieldname='pay_off_agreement']")){
		}
		$(me.old_instance.dialog.fields_dict.payments_record.$warpper).find("button[fieldname='pay_off_agreement']").click(function() {
			console.log("click of pay_off_agreement")
			me.old_dialog = me.old_instance.dialog;
			me.show_dialog();
		});*/
	},
	click_on_90_day_pay_Off: function(){
		var me = this;
		$(me.old_instance.dialog.fields_dict.payments_record.$wrapper).find(".s90_day_pay_Off").click(function() {
			me.old_dialog = me.old_instance.dialog;
			me.show_dialog();
		});
		/*me.old_instance.dialog.fields_dict.s90_day_pay_Off.$input.click(function() {
			me.old_dialog = me.old_instance.dialog;
			me.show_dialog();
		});*/
	},
	show_dialog:function(){
		var me = this;
		this.dialog = new frappe.ui.Dialog({
	        title: "Payments Detalis",
	            fields: [
		               	{"fieldtype": "Data" , "fieldname": "amount_paid_by_customer" , "label": "Cash","default":"0.0","reqd":"true"},
		               	{"fieldtype": "Data" , "fieldname": "bank_card" , "label": "Bank card","default":"0.0","reqd":"true"},
		               	{"fieldtype": "Data" , "fieldname": "bank_transfer" , "label": "Bank transfer","default":"0.0","reqd":"true"},
		               	{"fieldtype": "Column Break" , "fieldname": "column"},
		               	{"fieldtype": "Data" , "fieldname": "bonus" , "label": "Bonus","default":"0.0"},
		               	{"fieldtype": "Data" , "fieldname": "discount" , "label": "Discount","default":"0.0","reqd":"true"},
		               	{"fieldtype": "Data" , "fieldname": "balance" , "label": "Balance"},
		               	{"fieldtype": "Section Break" , "fieldname": "section"},
		               	{"fieldtype": "Button" , "fieldname": "process_payment" , "label": "Process payment"},
		               	{"fieldtype": "Button" , "fieldname": "add_in_receivables" , "label": "Add to receivables"},
		               	{"fieldtype": "Button" , "fieldname": "return_to_customer" , "label": "Give Change"},
		               	{"fieldtype": "Button" , "fieldname": "submit_payment" , "label": "Complete Payment"},
		               	{"fieldtype": "Column Break" , "fieldname": "column"},
		               	{"fieldtype": "HTML" , "fieldname": "msg"},
	            	],
	               	primary_action_label: "OK",
	               	primary_action: function(){
	                    me.dialog.hide()
	                }
	   	});
	    this.fd = this.dialog.fields_dict;
	    me.set_value_of_balance();
		$(this.dialog.body).parent().find('.btn-primary').hide()
	},
	set_value_of_balance:function(){
		var me = this;
		me.hide_button();
	    if(me.old_instance != "Process Payments"){
    		me.fd.bonus.df.hidden=1;
   			me.fd.bonus.refresh();
	       	if(me.old_instance.values['cond'] == "90 day pay Off"){
	       		this.val_balance = 0 - flt(me.old_instance.values['Total_payoff_amount'])
		       	me.dialog.fields_dict.balance.set_input(this.val_balance)
				me.dialog.show();
				me.init_for_trigger_of_amount_paid_by_customer();
				me.click_on_process_payment();
			}
			else if(me.old_instance.values['cond'] == "pay off agreement"){
				this.val_balance = 0 - flt(me.old_instance.values['s90_day_pay_Off'])
		       	me.dialog.fields_dict.balance.set_input(this.val_balance)
				me.dialog.show();
				me.init_for_trigger_of_amount_paid_by_customer();
				me.click_on_process_payment();
			}
	    }
	    else{
	    	me.dialog.set_value("balance",(flt(me.fd.amount_paid_by_customer.$input.val()) 
										- flt(cur_frm.doc.total_charges) 
										+ flt(me.fd.bank_card.$input.val())
										+ flt(me.fd.bank_transfer.$input.val())
										+ flt(me.fd.bonus.$input.val())
										+ flt(me.fd.discount.$input.val())).toFixed(2))
		   	me.fd.balance.df.read_only=1
		   	me.fd.balance.refresh();
		   	/*me.fd.bonus.df.hidden=0;
   			me.fd.bonus.refresh();*/
   			me.dialog.show();
			me.get_value_of_rental_payment_and_late_fees();
			me.init_for_trigger_of_amount_paid_by_customer();
			me.click_on_process_payment();
	    }
	    $("input").on("keydown", function(e) {
		    var code = e.which;
		    if(code == 13) {
		        e.preventDefault();
		    }
		});
		$("button[data-fieldname='process_payment']").on("keydown", function(e) {
		    var code = e.which;
		    if(code == 13) {
		        e.preventDefault();
		    }
		});   	
	},
	get_value_of_rental_payment_and_late_fees:function(){
		var me = this;
		var total_due = 0;
		var late_fees = 0;
		var flt_precision = frappe.defaults.get_default("float_precision")
		var agreements = [];
		var number_of_payments = 0;
		$.each($("#payments_grid").find(".slick-row"),function(i,d){
			if(flt($($(d).children()[3]).text()) > 0 ){
				late_fees += Number((flt($($(d).children()[9]).text())).toFixed(flt_precision))
				total_due += Number((flt($($(d).children()[10]).text())).toFixed(flt_precision))  
				
			}
			agreements.push($($(d).children()[0]).text())
			number_of_payments += flt($($(d).children()[3]).text())
		});
		this.rental_payment = total_due - late_fees;
       	this.late_fees = late_fees;
       	if(flt(this.late_fees) > 0 || flt(cur_frm.doc.receivables) < 0){
       		me.fd.bonus.df.hidden=1;
   			me.fd.bonus.refresh();
       	}
		this.agreements = agreements;
		this.number_of_payments = number_of_payments;
		me.get_amount_of_late_payment();
	},
	get_amount_of_late_payment:function(){
		var me = this;
		frappe.call({
	        method: "customer_info.customer_info.doctype.payments_management.payments_management.get_late_payment",
	       	args: {
	       		"agreements":me.agreements,
	       		"payment_date":cur_frm.doc.payment_date
	        },
	       	callback: function(r){
	    		if(r.message){
	    			me.late_payment = r.message["late_payment"]
	    			me.first_payment = r.message["first_payment"]
	    			me.payable_by_bonus = flt(me.late_payment) + flt(r.message["first_payment"])
	    			
	    			if(flt(me.payable_by_bonus) >= flt((me.rental_payment).toFixed(2))){
	    				me.payable_by_bonus = flt((me.rental_payment).toFixed(2)) - flt(me.late_payment) - flt(r.message["first_payment"])
	    			}
	    			else if(flt(me.payable_by_bonus) < flt((me.rental_payment).toFixed(2))){
	    				me.payable_by_bonus = cur_frm.doc.static_bonus
	    			}
	    		}
	    	}
	    });	
	},	
	setFocusToTextBox:function(){
	    $("input[data-fieldname='amount_paid_by_customer']").focus();
	},
	init_for_trigger_of_amount_paid_by_customer:function(){
		var me = this;	
		$(me.fd.amount_paid_by_customer.input).change(function(){
			if($(me.fd.amount_paid_by_customer.input).val() == ""){
				me.dialog.set_value("amount_paid_by_customer","0.0")	
			}
			me.init_for_commom_calculation();
		})
		$(me.fd.bank_card.input).change(function(){
			if($(me.fd.bank_card.input).val() == ""){
				me.dialog.set_value("bank_card","0.0")	
			}
			me.init_for_commom_calculation();
		})
		$(me.fd.bank_transfer.input).change(function(){
			if($(me.fd.bank_transfer.input).val() == ""){
				me.dialog.set_value("bank_transfer","0.0")	
			}
			me.init_for_commom_calculation();
		})
		$(me.fd.discount.input).change(function(){
			//me.setFocusToTextBox();
			if($(me.fd.discount.input).val() == ""){
				me.dialog.set_value("discount","0.0")	
			}
			me.init_for_commom_calculation();
		})
		$(me.fd.bonus.input).change(function(){
			if($(me.fd.bonus.input).val() == ""){
				me.dialog.set_value("bonus","0.0")	
			}
			/*if ((flt($(me.fd.bonus.input).val()) <= cur_frm.doc.static_bonus) 
				&& (flt($(me.fd.bonus.input).val()) <= flt(me.payable_by_bonus))) {
				if (flt($(me.fd.bonus.input).val()) > -flt($(me.fd.balance.input).val())) {
					me.dialog.set_value("bonus",-flt($(me.fd.balance.input).val()))	
					me.init_for_commom_calculation();
				}
				else{
					me.init_for_commom_calculation();
				}
			}*/
			if ((flt($(me.fd.bonus.input).val()) <= cur_frm.doc.static_bonus) 
				&& (flt($(me.fd.bonus.input).val()) <= flt(me.payable_by_bonus))) {
				if (flt($(me.fd.bonus.input).val()) > flt(cur_frm.doc.total_charges)  && flt(cur_frm.doc.total_charges) >= 0) {
					me.dialog.set_value("bonus",flt(cur_frm.doc.total_charges))	
					me.init_for_commom_calculation();
				}
				else{
					me.init_for_commom_calculation();
				}
			}
			if ((flt($(me.fd.bonus.input).val()) <= cur_frm.doc.static_bonus) && (flt($(me.fd.bonus.input).val())) > flt(me.payable_by_bonus)) {
				cur_dialog.fields_dict.bonus.set_input("0.0")		
				//msgprint(__("Bonus Is not Used For Late Payments \n Enter less then or Equal to {0} for bonus",[flt(me.payable_by_bonus).toFixed(2)]));
				me.init_for_commom_calculation();
				frappe.throw(__("Enter less then or Equal to {0} for bonus",[flt(me.payable_by_bonus).toFixed(2)]));
			}
			if(flt($(me.fd.bonus.input).val()) > cur_frm.doc.static_bonus){
				cur_dialog.fields_dict.bonus.set_input("0.0")		
				me.init_for_commom_calculation();
				frappe.throw(__("Please Enter less then or Equal to {0} for bonus", [cur_frm.doc.static_bonus]));
			}
		})		
	},
	init_for_commom_calculation:function(){
		var me = this;
		me.hide_button();
		if(me.old_instance != "Process Payments"){
			var val_of_balance = flt(me.fd.amount_paid_by_customer.$input.val()) + flt(cur_dialog.fields_dict.bank_card.$input.val())
																				  + flt(cur_dialog.fields_dict.bank_transfer.$input.val())
																				  + flt(cur_dialog.fields_dict.discount.$input.val())
																				  + flt(me.val_balance)
		}
		else{
			/*var val_of_balance = flt(me.fd.amount_paid_by_customer.$input.val()) - flt(cur_frm.doc.total_charges)
																			  + flt(cur_dialog.fields_dict.bank_card.$input.val())
																			  + flt(cur_dialog.fields_dict.bank_transfer.$input.val())
																			  + flt(cur_dialog.fields_dict.discount.$input.val())*/
			var val_of_balance = flt(me.fd.amount_paid_by_customer.$input.val()) - flt(cur_frm.doc.total_charges)
																			  + flt(cur_dialog.fields_dict.bank_card.$input.val())
																			  + flt(cur_dialog.fields_dict.bank_transfer.$input.val())
																			  + flt(cur_dialog.fields_dict.bonus.$input.val())
																			  + flt(cur_dialog.fields_dict.discount.$input.val())
		}
		cur_dialog.fields_dict.balance.set_input(val_of_balance.toFixed(2))
		me.dialog.fields_dict.msg.$wrapper.empty()
		$(me.dialog.body).find("[data-fieldname ='process_payment']").show();
	},
	hide_button:function(){
		$('button[data-fieldname="add_in_receivables"]').hide();
		$('button[data-fieldname="return_to_customer"]').hide();
		$('button[data-fieldname="submit_payment"]').hide();
	},
	click_on_process_payment:function(){
		var me = this;
		me.dialog.fields_dict.process_payment.$input.click(function() {
       		$(me.dialog.body).find("[data-fieldname ='process_payment']").hide();
			if(parseFloat(me.dialog.fields_dict.balance.$input.val()) >= 0){ 
				if(flt(me.fd.amount_paid_by_customer.$input.val()) == 0 
					&& flt(me.fd.bonus.$input.val()) > 0 && flt(me.fd.bank_transfer.$input.val()) == 0 && flt(me.fd.bank_card.$input.val()) == 0 && flt(me.fd.discount.$input.val()) == 0 ) {
       				html_msg = "<div class='row'>There Is "+0+" eur in balance Put It Into Receivables OR Give Change</div>"
       			}
       			else{
					html_msg = "<div class='row'>There Is "+ flt(me.dialog.fields_dict.balance.$input.val())+" eur in balance Put It Into Receivables OR Give Change</div>"       				
       			}
       			/*if(flt(me.dialog.fields_dict.balance.$input.val()) - flt(me.dialog.fields_dict.bonus.$input.val()) > 0){
       				html_msg = "<div class='row'>There Is "+ (flt(me.dialog.fields_dict.balance.$input.val()) - flt(me.dialog.fields_dict.bonus.$input.val()))+" eur in balance Put It Into Receivables OR Give Change</div>"	
       			}
       			else{
       				html_msg = "<div class='row'>There Is "+0+" eur in balance Put It Into Receivables OR Give Change</div>"
       			}*/
       			me.dialog.fields_dict.msg.$wrapper.empty()
       			me.dialog.fields_dict.msg.$wrapper.append(html_msg)
       			$('button[data-fieldname="process_payment"]').hide();
				$('button[data-fieldname="add_in_receivables"]').show();
			    $('button[data-fieldname="return_to_customer"]').show();
			    me.click_on_add_in_receivables();
			    me.click_on_return_to_customer();
       		}
       		if(parseFloat(me.dialog.fields_dict.balance.$input.val()) == 0 ){
       			$(me.dialog.body).find("[data-fieldname ='process_payment']").hide();
       			me.dialog.fields_dict.msg.$wrapper.empty()
       			$('button[data-fieldname="process_payment"]').hide();
       			me.hide_other_and_show_complete_payment();
       			me.add_in_receivables = 0
				me.click_on_submit();
       		}
       		if(parseFloat(me.dialog.fields_dict.balance.$input.val()) < 0 && me.old_instance == "Process Payments" && me.number_of_payments > 0){
       			me.calculate_underpayment();
       		}
       		if(parseFloat(me.dialog.fields_dict.balance.$input.val()) < 0 && me.old_instance == "Process Payments" && me.number_of_payments == 0){
       			me.check_value_of_cash_card_transfer_discount();
       		}
       		else if (parseFloat(me.dialog.fields_dict.balance.$input.val()) < 0){
       			html = "<div class='row' style='margin-left: -160px;color: red;'>Error Message Balance Is Negative</div>"
       			$('button[data-fieldname="add_in_receivables"]').hide();
			    $('button[data-fieldname="return_to_customer"]').hide();
       			me.dialog.fields_dict.msg.$wrapper.empty()
       			me.dialog.fields_dict.msg.$wrapper.append(html)
       		}
		});
	},
	check_value_of_cash_card_transfer_discount:function(){
		var me = this;
		value = me.dialog.get_values();
		if(flt(value.amount_paid_by_customer) > 0 || flt(value.bank_transfer) > 0 || flt(value.bank_card) > 0 || flt(value.discount) > 0){
			$('button[data-fieldname="add_in_receivables"]').show();
			$('button[data-fieldname="return_to_customer"]').show();
			me.click_on_add_in_receivables();
			me.click_on_return_to_customer();
		}
		else{
			html = "<div class='row' style='margin-left: -160px;color: red;'>Enter amount in Cash or Bank Card or Bank Transfer or Discount </div>"
			me.dialog.fields_dict.msg.$wrapper.empty()
       		me.dialog.fields_dict.msg.$wrapper.append(html)			
		}
	},
	calculate_underpayment:function(){
		var me = this;
		value = me.dialog.get_values();
		if (flt(value.bonus) > 0){
			frappe.throw(__("No Bonus For Partial Payment"));
		}
		else{
			frappe.call({
		        method: "customer_info.customer_info.doctype.payments_management.payments_management.calculate_underpayment",
		       	args: {
		       		"agreements":me.agreements,
		        	"payment_date":cur_frm.doc.payment_date,
		        	"amount_paid_by_customer":value.amount_paid_by_customer,
		        	"receivables":cur_frm.doc.receivables,
		        	"late_fees":me.late_fees
		        },
		       	callback: function(r){
					r.message = Number((flt(r.message)).toFixed(2))
		       		me.sum_of_cash_card_transfer = flt(me.dialog.fields_dict.bank_transfer.$input.val()) + flt(me.dialog.fields_dict.bank_card.$input.val()) + flt(me.dialog.fields_dict.amount_paid_by_customer.$input.val())
		       		if(r.message && (parseFloat(me.dialog.fields_dict.balance.$input.val()) < 0) && me.sum_of_cash_card_transfer >= parseFloat(r.message)){
			       		$('button[data-fieldname="process_payment"]').hide();
					    $('button[data-fieldname="return_to_customer"]').hide();
						$('button[data-fieldname="add_in_receivables"]').show();
						//html = "<div class='row' style='margin-left: -88px;color: green;'>Cash amount >= "+" "+(flt(r.message) - flt(value.bonus))+" so "+flt(value.balance)+" "+"add in receivables</div>"
					    html = "<div class='row' style='margin-left: -88px;color: green;'>Add "+flt(value.balance)+" "+" in receivables</div>"
					    me.dialog.fields_dict.msg.$wrapper.empty()
					    me.dialog.fields_dict.msg.$wrapper.append(html)
					    me.click_on_add_in_receivables();
					    me.click_on_return_to_customer();
					}
			       	if(r.message && (parseFloat(me.dialog.fields_dict.balance.$input.val()) < 0) && me.sum_of_cash_card_transfer < parseFloat(r.message)){
			       		html = "<div class='row' style='margin-left: -160px;color: red;'>Error Message Balance Is Negative Cash should be >= "+" "+r.message+"</div>"
		       			$('button[data-fieldname="add_in_receivables"]').hide();
					    $('button[data-fieldname="return_to_customer"]').hide();
		       			me.dialog.fields_dict.msg.$wrapper.empty()
		       			me.dialog.fields_dict.msg.$wrapper.append(html)
			       	}	
		    	}
		    });
		}
	},
	click_on_add_in_receivables:function(){
		var me = this;
		me.dialog.fields_dict.add_in_receivables.$input.click(function() {
			value = me.dialog.get_values();
			me.add_in_receivables = value.balance// - value.bonus;
			/*if(flt(me.add_in_receivables) + flt(value.bonus) >= 0 && flt(value.bonus) > 0){
				me.add_in_receivables = 0	
			}*/
			me.hide_other_and_show_complete_payment();
			me.click_on_submit();
		})
	},
	click_on_return_to_customer:function(){
		var me =this;
		me.dialog.fields_dict.return_to_customer.$input.click(function() {
			var val_of_cash = flt($(me.fd.amount_paid_by_customer.input).val()) - flt($(me.fd.balance.input).val())
			//cur_dialog.fields_dict.amount_paid_by_customer.set_input(val_of_cash.toFixed(2))
			me.add_in_receivables = 0
    		me.hide_other_and_show_complete_payment();
    		me.click_on_submit();
		})
	},
	hide_other_and_show_complete_payment:function(){
		$('button[data-fieldname="return_to_customer"]').hide();
		$('button[data-fieldname="add_in_receivables"]').hide();
		$('[data-fieldname="msg"]').hide();
		$('button[data-fieldname="submit_payment"]').show();
	},
	click_on_submit:function(){
		var me = this;
		/*console.log(me.old_instance)
		console.log(me.old_instance['values']['s90d_SAC_price'],"old_dialog")
		console.log(me.old_instance['values']['s90_day_pay_Off'],"old_dialog")*/
		me.dialog.fields_dict.submit_payment.$input.click(function(){
			if(me.old_instance == "Process Payments" && me.number_of_payments > 0){
				me.update_payments_records();
			}
			else if(me.old_instance == "Process Payments" && me.number_of_payments == 0){
				//frappe.throw("Please Add Any Payment")
				me.update_payments_records();
			}
			else{
				me.payoff_submit();	
			}
		});
	},
	payoff_submit:function(){
		var me = this;
		frappe.call({
	        method: "customer_info.customer_info.doctype.payments_management.payments_management.update_payments_records_on_payoff_submit",
	       	args: {
	       		"customer_agreement":me.old_instance.item['id'],
	        	"payment_date":cur_frm.doc.payment_date,
	        },
	       	callback: function(r){
	    		if(r.message){
	    			me.update_on_payoff(r.message)
	    		}
	    	}
	    });	
	},
	update_on_payoff:function(data){
		var me = this;
		value = me.dialog.get_values();
		frappe.call({
	        method: "customer_info.customer_info.doctype.payments_management.payments_management.payoff_submit",
	       	args:{"args": {
							"customer_agreement":me.old_instance.item['id'],
							"agreement_status":"Closed",
							"condition": me.old_instance.values['cond'],
							"customer":cur_frm.doc.customer,
							"receivables":cur_frm.doc.receivables,
							"add_in_receivables":me.add_in_receivables,
							"values":value,//JSON.stringify(value),
							"payment_date":cur_frm.doc.payment_date,
							//"total_charges":cur_frm.doc.total_charges,
							"data":data,
							"rental_payment":me.old_instance['values']['s90d_SAC_price'] ? me.old_instance['values']['s90d_SAC_price'] : me.old_instance['values']['Discounted_payment_amount'],
							"total_amount":me.old_instance['values']['s90_day_pay_Off'] ? me.old_instance['values']['s90_day_pay_Off'] : me.old_instance['values']['Total_payoff_amount']
	       		        }
	       		},
	        	//"receivables":me.add_in_receivables,
	       	callback: function(r){
	       		// remove all bonus when agreements status closed for payoff
				if(r.message && r.message == "True"){
					cur_frm.set_value("bonus",0)
					cur_frm.set_value("static_bonus",0)
				}
	       		get_bonus_link();
	       		me.dialog.hide();
				me.old_dialog.hide();
				calculate_total_charges("Payoff");
	    		render_agreements();
	    		msgprint("Agreement paid off successfully")
	    	}
	    });
	},
	update_payments_records:function(){
		var me = this;
		value = me.dialog.get_values();
		frappe.call({
			async:false,    
	        method: "customer_info.customer_info.doctype.payments_management.payments_management.update_on_submit",
	       	args:{
	       		"args": {
					"values":value,//JSON.stringify(value),
					"rental_payment":me.rental_payment,
					"late_fees":me.late_fees,
					"payment_date":cur_frm.doc.payment_date,
					"customer":cur_frm.doc.customer,
					"bonus":cur_frm.doc.bonus - flt(value.bonus),
					"manual_bonus":cur_frm.doc.assign_manual_bonus,
					"used_bonus":flt(value.bonus),
					"new_bonus":flt(cur_frm.doc.bonus) - flt(cur_frm.doc.static_bonus),
					"add_in_receivables":me.add_in_receivables,
					"receivables":cur_frm.doc.receivables,
					"total_charges":cur_frm.doc.total_charges,
					//"receivables":me.add_in_receivables,
   		        },
   		        "flag":"from_payoff"
	       	},
	       	callback: function(r){
	       		/*if(flt(value.bonus) >= cur_frm.doc.total_charges && flt(value.amount_paid_by_customer) == 0 
	       			&& flt(value.bank_card) == 0 && flt(value.bank_transfer) == 0 && flt(value.discount) == 0){
	       			console.log("insided 1")
	       			var bonus_value = flt(cur_frm.doc.static_bonus) - flt(value.bonus) //+ flt(value.balance)
	       			cur_frm.set_value("bonus",bonus_value)
	       			cur_frm.set_value("static_bonus",bonus_value)
	       		}*/
	       		if(flt(value.bonus) >= cur_frm.doc.amount_of_due_payments && flt(value.amount_paid_by_customer) == 0 
	       			&& flt(value.bank_card) == 0 && flt(value.bank_transfer) == 0 && flt(value.discount) == 0){
	       			var bonus_value = flt(cur_frm.doc.static_bonus) - flt(value.bonus) //+ flt(value.balance)
	       			cur_frm.set_value("bonus",bonus_value)
	       			cur_frm.set_value("static_bonus",bonus_value)
	       		}
	       		else if(flt(me.late_fees) > 0 || flt(cur_frm.doc.receivables) < 0 || flt(me.add_in_receivables) < 0){
	       			var bonus_val = flt(cur_frm.doc.static_bonus) - flt(value.bonus)
	       			cur_frm.set_value("bonus",bonus_val)
	       			cur_frm.set_value("static_bonus",bonus_val)
	       		}
	       		else{
	       			var bonus_value = flt(cur_frm.doc.bonus) - flt(value.bonus)
	       			cur_frm.set_value("bonus",bonus_value)
		       		cur_frm.set_value("static_bonus",bonus_value)
	       		}

	       		if(r.message && r.message['remove_bonus'] == "True"){
	       			var bonus_value = 0
	       			cur_frm.set_value("bonus",bonus_value)
		       		cur_frm.set_value("static_bonus",bonus_value)
	       		}
	       		

	            if(r.message){ 
	            	if(r.message["completed_agreement_list"]){
	            		msgprint(r.message["completed_agreement_list"]+"\n"+"Agreement Payoff successfully")
	            	}
	            	if(r.message["used_bonus_of_customer"]){	
	       				cur_frm.set_value("used_bonus",flt(r.message['used_bonus_of_customer']))
	        	    }
	        	}    

	            if(flt(me.add_in_receivables) == 0){
	            	cur_frm.set_value("receivables","0")
	            }

	            if(flt(me.add_in_receivables) > 0){
	            	cur_frm.set_value("receivables",flt(me.add_in_receivables))	
	            }
	            get_bonus_link();
	        	render_agreements();
	        	calculate_total_charges("Process Payment");
	    		me.dialog.hide();
	    	}
	    })
	}
});	