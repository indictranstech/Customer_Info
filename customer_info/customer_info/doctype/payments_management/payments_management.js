cur_frm.add_fetch('customer', 'first_name', 'first_name');
cur_frm.add_fetch('customer', 'last_name', 'last_name');
cur_frm.add_fetch('customer', 'company_phone_1', 'company_phone_1');
cur_frm.add_fetch('customer', 'company_phone_2', 'company_phone_2');
cur_frm.add_fetch('customer', 'prersonal_code', 'prersonal_code');
cur_frm.add_fetch('customer', 'summary_of_notes', 'summary_of_notes');
cur_frm.add_fetch('customer','bonus','bonus')

var list_of_row_to_update_on_submit = [];
var index = 0
frappe.ui.form.on("Payments Management", {
	refresh: function(frm) {
		frm.disable_save();
		$($(".indicator")[0]).hide()
	},
	onload:function(frm){
		$(cur_frm.fields_dict.call_commitment.wrapper).css("margin-left","406px")
		$(cur_frm.fields_dict.payments_grid.wrapper).empty()
		$(cur_frm.fields_dict.payments_grid.wrapper).append("<table width='100%>\
  		<tr>\
		    <td valign='top' width='100%'>\
		      <div id='payments_grid' style='width:100%;height:200px;''></div>\
		    	</td>\
  			</tr>\
		</table>");
		if(cur_frm.doc.customer){
			render_agreements();
			update_payments_record_by_due_date();
			calculate_total_charges();
			get_address_of_customer()
		}
	},
	customer:function(){
		if(cur_frm.doc.customer){
			remove_all_not_submitted();
			render_agreements();
			update_payments_record_by_due_date();
			calculate_total_charges();
			get_address_of_customer();			
		}
	},
	submit:function(){
		if(cur_frm.doc.customer){	
			var me = this;
			new process_payment()
		}
		else{
			msgprint("Select Customer First")
		}
	},
	call_commitment:function(frm){
		if(cur_frm.doc.customer){
			new call_commit()	
	    }
	    else{
			msgprint("Select Customer First")
		}    
	},
	add_notes:function(frm){
		if(cur_frm.doc.notes_on_customer_payments){
			frappe.call({
	            method: "customer_info.customer_info.doctype.payments_management.payments_management.add_notes_in_customer",
	            args: {
	            	"customer":cur_frm.doc.customer,
	            	"notes_on_customer_payments":cur_frm.doc.notes_on_customer_payments,
	            	"summary_of_notes":cur_frm.doc.summary_of_notes
	            },
	            callback: function(r) {
	            	if(r.message){
	            		cur_frm.set_value("summary_of_notes",r.message)
	            	}
	            	cur_frm.set_value("notes_on_customer_payments","")
	            	msgprint("Comment Added Successfully");
	            }
	        });
		}
	}
})


get_address_of_customer = function(){
	console.log("in get_address_of_customer")
	cur_frm.set_value("full_address","")
	frappe.call({
        method: "customer_info.customer_info.doctype.customer_agreement.customer_agreement.get_primary_address",
        args: {
            "customer": cur_frm.doc.customer,
        },
     	callback: function(r){
            console.log(r.message)
            if(r.message[0]['address_line1'] && !r.message[0]['address_line2']){
            	cur_frm.doc.full_address = r.message[0]["address_line1"] + "\n" + r.message[0]["city"]
     			refresh_field('full_address')
     		}
     		else if(r.message[0]['address_line2']){
     			cur_frm.doc.full_address = r.message[0]["address_line1"] + "\n" + r.message[0]["address_line2"] + "\n" + r.message[0]["city"]
     			refresh_field("full_address")
     		}
     	}  	
    });
}

update_payments_record_by_due_date = function(frm){
	frappe.call({
			async:false,
            method: "customer_info.customer_info.doctype.payments_management.payments_management.update_payments_record_by_due_date",
            args: {
              "customer": cur_frm.doc.customer
            },
            callback: function(r){
        		
        	}
    });
}

remove_all_not_submitted =function(frm){
	frappe.call({
			async:false,
            method: "customer_info.customer_info.doctype.payments_management.payments_management.remove_all_not_submitted",
            args: {
              "customer": cur_frm.doc.customer
            },
            callback: function(r){
        		
        	}
    });	
}


calculate_total_charges = function(frm){
	frappe.call({
			async:false,
            method: "customer_info.customer_info.doctype.payments_management.payments_management.calculate_total_charges",
            args: {
              "customer": cur_frm.doc.customer
            },
            callback: function(r){
            if(r.message){
              	console.log(r.message)
              	cur_frm.doc.amount_of_due_payments = r.message['amount_of_due_payments'] > 0 ? r.message['amount_of_due_payments']:"0";
	           	cur_frm.doc.receivables = r.message['receivables'] > 0 ? r.message['receivables']:"0";
	           	cur_frm.doc.total_charges = (r.message['amount_of_due_payments'] - r.message['receivables']) == 0 ? "0": (r.message['amount_of_due_payments'] - r.message['receivables'])
	           	/*if((r.message['amount_of_due_payments'] - cur_frm.doc.receivables) == 0){
	           		cur_frm.doc.total_charges = "0"
	           	}
	           	else{
	           		cur_frm.doc.total_charges = (r.message['amount_of_due_payments'] - cur_frm.doc.receivables)
	           	}*/
	           	cur_frm.refresh_fields()
            }
            else{
            	cur_frm.doc.total_charges = 0.0
	           	refresh_field('total_charges')	
            }
        }
    });
}

render_agreements = function(){
	list_of_row_to_update_on_submit = [];
	var grid;

	var buttonFormat_detail = function (row, cell, value, columnDef, dataContext) {
		return "<input type='button' value='Detail' class='detail' style='height:20px;padding: 0px;width: 70px;'; />";    
	}

	var buttonFormat_suspension = function (row, cell, value, columnDef, dataContext) {
		console.log(dataContext['suspenison'],"dataContext")
		var id = "mybutton" + String(row);
			if(dataContext['suspenison']){
				return "<input type='button' value = "+dataContext['suspenison']+" id= "+id+" class='suspenison' style='height:20px;padding: 0px;width: 70px;'; />";		    
			}
			else{
				return "<input type='button' value = 'Call/Commitment' id= "+id+" class='suspenison' style='height:20px;padding: 0px;width: 100px;'; />";		
			}
	}


	var columns = [
	    /*{id: "serial", name: "#", field: "serial", cssClass: "cell-selection", width: 20, resizable: false, selectable: false, focusable: false },*/
	    {id: "agreement_no", name: "Agreement No", field: "agreement_no",width: 80},
	    {id: "agreement_period", name: "Agreement Period", field: "agreement_period",width: 80},
	    {id: "product", name: "Product", field: "product",width: 120},
	    {id: "number_of_payments", name: "# of Payments", field: "number_of_payments",width: 70},
	    {id: "monthly_rental_payment", name: "Rental Payments", field: "monthly_rental_payment",width: 90},
	    {id: "current_due_date", name: "Current Due Date", field: "current_due_date",width: 90},
	    {id: "next_due_date", name: "Next Due Date", field: "next_due_date",width: 90},
	    {id: "payments_left", name: "Payments left", field: "payments_left",width: 70},
	    {id: "balance", name: "Balance", field: "balance",width: 70},
	    {id: "late_fees", name: "Late Fees", field: "late_fees",width: 50},
	    {id: "total_dues", name: "Total Dues", field: "total_dues",width: 50},
	    {id: "payments_made", name: "Payments Made", field: "payments_made",width: 50},
	    {id: "detail", name: "Detail", field: "detail",formatter: buttonFormat_detail},
	    {id: "suspenison", name: "Call/Commitment", field: "suspenison",formatter: buttonFormat_suspension}
  	];
  	var options = {
    	enableCellNavigation: true,
    	enableColumnReorder: false,
  		/*editable: true,*/
  	};
  	var data = [];
  	frappe.call({
            method: "customer_info.customer_info.doctype.payments_management.payments_management.get_customer_agreement",
            type: "GET",
            /*async: false,*/
            args: {
              "customer": cur_frm.doc.customer
            },
            callback: function(r){
              if(r.message){
              	console.log(r.message,"customer_agreementss")
                this.data = r.message;
                make_grid(r.message,columns,options)
            }
        }
    });
}

make_grid= function(data1,columns,options){
	var data = [];
	var me = this;
	/*var index = 0;*/
	for (var i = 0; i<data1.list_of_agreement.length; i++) {
          	data[i] = {
          	id : data1.list_of_agreement[i][0],	
          	/*serial:i,*/	
            agreement_no: data1.list_of_agreement[i][0],
            agreement_period: data1.list_of_agreement[i][1],
            product: data1.list_of_agreement[i][2],
            number_of_payments: data1.list_of_agreement[i][3],
            monthly_rental_payment: data1.list_of_agreement[i][4],
            current_due_date: data1.list_of_agreement[i][5],
            next_due_date: data1.list_of_agreement[i][6],
            payments_left: data1.list_of_agreement[i][7],
            balance: data1.list_of_agreement[i][8],
            late_fees: data1.list_of_agreement[i][9],
            total_dues: data1.list_of_agreement[i][10],
            payments_made: data1.list_of_agreement[i][11],
            suspenison: data1.list_of_agreement[i][12]
        };
    }

    dataView = new Slick.Data.DataView();    
    dataView.beginUpdate();
    dataView.setItems(data);
    dataView.endUpdate();

	grid = new Slick.Grid("#payments_grid", dataView, columns, options);
	grid.onClick.subscribe(function (e, args) {
        var item = dataView.getItem(args.row);
        console.log(dataView,"dataView")
        if($(e.target).hasClass("detail")) {
            index = parseInt(index) + 1;
            console.log(index, "in clcikc_____________")            
        	new Payments_Details(item, index)
        }
        if($(e.target).hasClass("suspenison")) {
        	console.log("in mybutton",$(e.target).attr('id'))
        	var id = $(e.target).attr('id')
        	new manage_suspenison(id,item)
        }
    });
}



call_commit = Class.extend({
	init:function(){
		this.get_contact_result()
	},
	get_contact_result:function(){
		var me  = this;
		this.dialog = new frappe.ui.Dialog({
            		title: "Contact result",
                	fields: [
                   		{"fieldtype": "Button" , "fieldname": "reset" , "label": "Reset"},
                   		{"fieldtype": "Select" , "fieldname": "contact_result" , "label": "Contact Result","options":["","WBI","Sent SMS/Email"]},
                   		{"fieldtype": "Date" , "fieldname": "date_picker" , "label": "Date"},
                   		{"fieldtype": "Currency" , "fieldname": "amount" , "label": "Amount"}
                   	],
                   	primary_action_label: "Save",
                   	primary_action: function(){
                        me.change_name_of_buttons()
                    }
	       		});
       	this.fd = this.dialog.fields_dict;
       	this.dialog.$wrapper.find('.modal-dialog').css("width", "350px");
       	this.dialog.$wrapper.find('.modal-dialog').css("height", "300px");
       	this.dialog.$wrapper.find('.hidden-xs').css("margin-left","-2px");
       	this.dialog.show();
       	this.get_customer_agreement();
		this.before_select_contact_result()
		this.select_contact_result()
		this.click_on_reset()
	},
	get_customer_agreement:function(){
		this.agreements = [];
		var me = this;
		frappe.call({    
			method: "frappe.client.get_list",
		   	args: {
		    	doctype: "Customer Agreement",
		       	fields: ["name","call_commitment"],
		       	filters: { "agreement_status" : "Open","customer":cur_frm.doc.customer},
			},
			callback: function(r){
				if(r && r.message){
					console.log(r.message,"result result")
					for(i=0;i<r.message.length;i++){
						me.agreements.push({"name":r.message[i]['name'],
											"call_commitment":r.message[i]['call_commitment']})
					}
					console.log(me.agreements,"me.agreements 123123")
					me.get_fields_values();	
				}
			}
		});
	},
	get_fields_values:function(){
		var me = this;
		this.common_agreement_of_call_commit = [] 
		console.log(me,"me in side get_fields_values")
		console.log(me.agreements,"nameeeeeeeeeeeeeeeeee")
		for(i=0;i < me.agreements.length;i++){
			if(me.agreements[i]['call_commitment'] == "All"){
				console.log(me.agreements[i]['call_commitment'])
				me.common_agreement_of_call_commit.push(me.agreements[i]['name'])
				console.log(me.agreements[i]['name'])
			}
		}
		frappe.call({    
			method: "frappe.client.get_list",
		   	args: {
		    	doctype: "Customer Agreement",
		       	fields: ["contact_result","suspension_date","amount_of_contact_result","call_commitment"],
		       	filters: { "name" : me.common_agreement_of_call_commit[0],
		        			"customer":cur_frm.doc.customer,
		        			"agreement_status":"Open"
		        	},
			},
			callback: function(r){
				console.log(r.message,"r.message of call_commit")
				if(r && r.message[0]['contact_result'] == "WBI" 
					&& r.message[0]['amount_of_contact_result'] 
					&& r.message[0]["call_commitment"] == "All"){
					console.log(r.message,"contact_result contact_result")
					$(me.dialog.body).find("[data-fieldname ='date_picker']").show();
					$(me.dialog.body).find("[data-fieldname ='amount']").show();
					me.dialog.fields_dict.contact_result.set_input(r.message[0]['contact_result'])
					me.dialog.fields_dict.date_picker.set_input(r.message[0]['suspension_date'])
					me.dialog.fields_dict.amount.set_input(r.message[0]['amount_of_contact_result'])
				}
				else if(r && r.message[0]['contact_result'] == "Sent SMS/Email" && r.message[0]["call_commitment"] == "All"){
					console.log(r.message,"contact_result contact_result")
					me.dialog.fields_dict.contact_result.set_input(r.message[0]['contact_result'])
				}
			}
		});
	},
	before_select_contact_result:function(){
		var me = this;
		$(me.dialog.body).find("[data-fieldname ='date_picker']").hide();
		$(me.dialog.body).find("[data-fieldname ='amount']").hide();
	},
	select_contact_result:function(){
		var me = this;
		$(me.fd.contact_result.input).change(function(){
			if(me.fd.contact_result.$input.val() == "WBI"){
				$(me.dialog.body).find("[data-fieldname ='date_picker']").show();
				$(me.dialog.body).find("[data-fieldname ='amount']").show();					
			}
			else{
				me.dialog.fields_dict.date_picker.set_input("")
				me.dialog.fields_dict.amount.set_input("")
				$(me.dialog.body).find("[data-fieldname ='date_picker']").hide();
				$(me.dialog.body).find("[data-fieldname ='amount']").hide();			
			}
		})
	},
	click_on_reset:function(){
		var me = this;
		me.dialog.fields_dict.contact_result.set_input("")
		me.dialog.fields_dict.date_picker.set_input("")
		me.dialog.fields_dict.amount.set_input("")
		me.dialog.fields_dict.reset.$input.click(function() {
			frappe.call({
	            method: "customer_info.customer_info.doctype.payments_management.payments_management.set_or_reset_call_commitment",
	            args: {
	            	"customer":cur_frm.doc.customer
	            },
	            callback: function(r) {
	            	me.dialog.hide();
	            	render_agreements();
	            	msgprint("All Call/Commitment Reset");
	            }
	        });
		})
	},
	change_name_of_buttons:function(){
		var me = this;
		console.log(me,"me in side change_name_of_buttons")
		date = me.fd.date_picker.$input.val()
		if(date){
			me.update_call_commitment_data_in_agreement(date)
			me.dialog.hide();
		}
		else if (me.fd.contact_result.$input.val() == "Sent SMS/Email"){
			date = ""
			me.update_call_commitment_data_in_agreement(date)
			me.dialog.hide();
		}
	},
	update_call_commitment_data_in_agreement:function(date){
		var me  = this;
		console.log(me,"me in side of update_call_commitment_data_in_agreement")
		if(date == ""){	
			console.log("in first frappe.call")
			frappe.call({
	            method: "customer_info.customer_info.doctype.payments_management.payments_management.update_call_commitment_data_in_agreement",
	            args: {
	              "customer_agreement": me.agreements,
	              "date": "",
	              "contact_result": me.fd.contact_result.$input.val(),
	              "amount": 0,
	              "all_or_individual":"all"		
	            },
	            callback: function(r){
	        		render_agreements();
	        		msgprint("All Call/Commitment Save");
	        	}
		    });
		}
		else{
			console.log("in second frappe.call")
			frappe.call({
	            method: "customer_info.customer_info.doctype.payments_management.payments_management.update_call_commitment_data_in_agreement",
	            args: {
	              "customer_agreement": me.agreements,
	              "date": date,
	              "contact_result": me.fd.contact_result.$input.val(),
	              "amount": me.fd.amount.$input.val(),
	              "all_or_individual":"all"		
	            },
	            callback: function(r){
	        		render_agreements();
	        		msgprint("All Call/Commitment Save");
	        	}
		    });	
		}    
	}
})


manage_suspenison = Class.extend({
	init:function(id,item){
		this.item = item;
		this.id = id;
		this.get_contact_result()
	},
	get_contact_result:function(){
		var me  = this;
		this.dialog = new frappe.ui.Dialog({
            		title: "Contact result",
                	fields: [
                   		{"fieldtype": "Button" , "fieldname": "reset" , "label": "Reset"},
                   		{"fieldtype": "Select" , "fieldname": "contact_result" , "label": "Contact Result","options":["","WBI","Sent SMS/Email"]},
                   		{"fieldtype": "Date" , "fieldname": "date_picker" , "label": "Date"},
                   		{"fieldtype": "Currency" , "fieldname": "amount" , "label": "Amount"}
                   	],
                   	primary_action_label: "Save",
                   	primary_action: function(){
                        me.change_name_of_button()
                    }
	       		});
       	this.fd = this.dialog.fields_dict;
       	this.dialog.$wrapper.find('.modal-dialog').css("width", "350px");
       	this.dialog.$wrapper.find('.modal-dialog').css("height", "300px");
       	this.dialog.$wrapper.find('.hidden-xs').css("margin-left","-2px");
       	this.dialog.show();
       	this.get_fields_values();	
		this.before_select_contact_result()
		this.select_contact_result()
		this.click_on_reset()
	},
	get_fields_values:function(){
		var me = this;
		frappe.call({    
			method: "frappe.client.get_list",
		   	args: {
		    	doctype: "Customer Agreement",
		       	fields: ["contact_result","suspension_date","amount_of_contact_result","call_commitment"],
		       	filters: { "name" : me.item['id']
		        	},
			},
			callback: function(r){
				console.log(r.message)
				console.log(r && r.message[0]['contact_result'] == "WBI")
				if(r && r.message[0]['contact_result'] == "WBI"){
					console.log(r.message,"contact_result contact_result")
					$(me.dialog.body).find("[data-fieldname ='date_picker']").show();
					$(me.dialog.body).find("[data-fieldname ='amount']").show();
					me.dialog.fields_dict.contact_result.set_input(r.message[0]['contact_result'])
					me.dialog.fields_dict.date_picker.set_input(r.message[0]['suspension_date'])
					me.dialog.fields_dict.amount.set_input(r.message[0]['amount_of_contact_result'])
				}
				else if(r && r.message[0]['contact_result'] == "Sent SMS/Email"){
					console.log(r.message,"contact_result contact_result")
					me.dialog.fields_dict.contact_result.set_input(r.message[0]['contact_result'])
				}
			}
		});
	},
	before_select_contact_result:function(){
		var me = this;
		$(me.dialog.body).find("[data-fieldname ='date_picker']").hide();
		$(me.dialog.body).find("[data-fieldname ='amount']").hide();
	},
	select_contact_result:function(){
		var me = this;
		$(me.fd.contact_result.input).change(function(){
			if(me.fd.contact_result.$input.val() == "WBI"){
				$(me.dialog.body).find("[data-fieldname ='date_picker']").show();
				$(me.dialog.body).find("[data-fieldname ='amount']").show();					
			}
			else{
				me.dialog.fields_dict.date_picker.set_input("")
				me.dialog.fields_dict.amount.set_input("")
				$(me.dialog.body).find("[data-fieldname ='date_picker']").hide();
				$(me.dialog.body).find("[data-fieldname ='amount']").hide();			
			}
		})
	},
	click_on_reset:function(){
		var me = this;
		me.dialog.fields_dict.reset.$input.click(function() {
			me.dialog.fields_dict.contact_result.set_input("")
			me.dialog.fields_dict.date_picker.set_input("")
			me.dialog.fields_dict.amount.set_input("")
       		var date = frappe.datetime.nowdate()
       		id = "#" + me.id
       		$(id).attr('value','Call/Commitment');
			$(me.dialog.body).find("[data-fieldname ='date_picker']").hide();
			$(me.dialog.body).find("[data-fieldname ='amount']").hide();
			/*me.update_call_commitment_data_in_agreement(date)*/
			frappe.call({
	            method: "customer_info.customer_info.doctype.payments_management.payments_management.set_or_reset_call_commitment",
	            args: {
	            	"customer":cur_frm.doc.customer,
	            	"agreement_name":me.item['id']
	            },
	            callback: function(r) {
	            	me.dialog.hide();
	            	/*render_agreements();
	            	msgprint("All Call/Commitment Reset");*/
	            }
	        });
			me.dialog.hide();
		});
	},
	change_name_of_button:function(){
		var me = this;
		console.log(me,"me in side change_name_of_button")
		id = "#" + this.id
		date = me.fd.date_picker.$input.val()
		if(date){
			$(id).attr('value', date);
			me.update_call_commitment_data_in_agreement(date)
			me.dialog.hide();
		}
		else if (me.fd.contact_result.$input.val() == "Sent SMS/Email"){
			date = ""
			$(id).attr('value', "SMS/Email");
			me.update_call_commitment_data_in_agreement(date)
			me.dialog.hide();
		}
	},
	update_call_commitment_data_in_agreement:function(date){
		var me  = this;
		console.log(me,"me in side of update_call_commitment_data_in_agreement")
		if(date == ""){	
			console.log("in first frappe.call")
			frappe.call({
	            method: "customer_info.customer_info.doctype.payments_management.payments_management.update_call_commitment_data_in_agreement",
	            args: {
	              "customer_agreement": me.item['id'],
	              "date": "",
	              "contact_result": me.fd.contact_result.$input.val(),
	              "amount": 0,
	              "all_or_individual":"individual"		
	            },
	            callback: function(r){
	        	}
		    });
		}
		else{	
			frappe.call({
	            method: "customer_info.customer_info.doctype.payments_management.payments_management.update_call_commitment_data_in_agreement",
	            args: {
	              "customer_agreement": me.item['id'],
	              "date": date,
	              "contact_result": me.fd.contact_result.$input.val(),
	              "amount": me.fd.amount.$input.val(),
	              "all_or_individual":"individual"
	            },
	            callback: function(r){
	        	}
		    });
		}
	}
})


process_payment = Class.extend({
	init:function(){
		this.init_for_render_dialog()
	},
	init_for_render_dialog:function(){
		var me = this;
		this.dialog = new frappe.ui.Dialog({
	        title: "Payments Detalis",
	            fields: [
	               	{"fieldtype": "Data" , "fieldname": "rental_payment" , "label": "Rental Payment","default":"0.0","reqd":"true"},
	               	{"fieldtype": "Data" , "fieldname": "amount_paid_by_customer" , "label": "Cash","default":"0.0","reqd":"true"},
	               	{"fieldtype": "Data" , "fieldname": "bank_card" , "label": "Bank card","default":"0.0","reqd":"true"},
	               	{"fieldtype": "Data" , "fieldname": "bank_transfer" , "label": "Bank transfer","default":"0.0","reqd":"true"},
	               	{"fieldtype": "Column Break" , "fieldname": "column"},
	               	{"fieldtype": "Data" , "fieldname": "late_fees" , "label": "Late Fees","default":"0.0","reqd":"true"},
	               	{"fieldtype": "Data" , "fieldname": "bonus" , "label": "Bonus","default":"0.0"},
	               	{"fieldtype": "Data" , "fieldname": "discount" , "label": "Discount","default":"0.0","reqd":"true"},
	               	{"fieldtype": "Data" , "fieldname": "balance" , "label": "Balance"},
	               	{"fieldtype": "Section Break" , "fieldname": "section"},
	               	{"fieldtype": "Button" , "fieldname": "process_payment" , "label": "Process payment"},
	               	{"fieldtype": "Button" , "fieldname": "add_in_receivables" , "label": "Add to receivables"},
	               	{"fieldtype": "Column Break" , "fieldname": "column"},
	               	{"fieldtype": "Button" , "fieldname": "return_to_customer" , "label": "Give Change"},
	               	{"fieldtype": "Column Break" , "fieldname": "column"},	
	               	{"fieldtype": "HTML" , "fieldname": "msg"},
	               	{"fieldtype": "Section Break" , "fieldname": "section"},
	               	{"fieldtype": "Button" , "fieldname": "submit_payment" , "label": "SUBMIT"},
	               	],
	               	primary_action_label: "OK",
	               	primary_action: function(){
	               		msgprint("for submit click on SUBMIT")
	               		/*console.log(this,me,"in primary_action 123423123")
	                    me.click_on_make_entry()
	                    me.update_payments_records()
	                    me.dialog.hide()*/
	                }
	   	});
	    this.fd = this.dialog.fields_dict;
	    this.show_dialog()
	},
	show_dialog:function(){
		var me = this;
		/*$('button[data-fieldname="process_payment"]').css("margin-top","-506px");
		$('button[data-fieldname="process_payment"]').css("margin-left","399px");*/
       	$('button[data-fieldname="submit_payment"]').css("display","none");
		$('button[data-fieldname="add_in_receivables"]').css("display","none");
	    $('button[data-fieldname="return_to_customer"]').css("display","none");
		this.dialog.show();
       	$(this.dialog.body).parent().find('.btn-primary').hide();
		/*this.dialog.set_value("bonus",flt(cur_frm.doc.bonus).toFixed(2))
		this.fd.bonus.df.read_only=1;
		this.fd.bonus.refresh();*/
       	this.dialog.set_value("balance",(flt(me.fd.amount_paid_by_customer.$input.val()) 
										- flt(cur_frm.doc.total_charges) 
										+ flt(me.fd.bank_card.$input.val())
										+ flt(me.fd.bank_transfer.$input.val())
										+ flt(me.fd.bonus.$input.val())
										+ flt(me.fd.discount.$input.val())).toFixed(2))
       	this.fd.balance.df.read_only=1
       	this.fd.balance.refresh();
       	this.fd.rental_payment.df.hidden=1
       	this.fd.rental_payment.refresh();
       	this.fd.late_fees.df.hidden=1
       	this.fd.late_fees.refresh();
		this.get_value_of_rental_payment_and_late_fees();
		this.init_for_trigger_of_amount_paid_by_customer()
		this.click_on_process_payment()
		this.click_on_add_in_receivables()
		this.click_on_return_to_customer()
	},
	get_value_of_rental_payment_and_late_fees:function(){
		var me = this;
		var total_due = 0
		var late_fees = 0
		frappe.call({
            method: "frappe.client.get_list",
		   	args: {
		    	doctype: "Customer Agreement",
		       	fields: ["late_fees","total_due"],
		       	filters: { "customer" : cur_frm.doc.customer,"agreement_status":"Open"
		        },
			},
            callback: function(r){
            	console.log(r.message,"get_value_of_rental_payment_and_late_fees")
        		for(i=0;i<r.message.length;i++){
        			total_due += r.message[i]['total_due']
					late_fees += r.message[i]['late_fees']        			
        		}
        		console.log(late_fees,total_due,"result of total_due and ")
        		me.dialog.set_value("rental_payment",total_due - late_fees)
        		me.dialog.set_value("late_fees",late_fees)
        	}
	    });	
	},
	init_for_trigger_of_amount_paid_by_customer:function(){
		var me = this;
		$(me.fd.amount_paid_by_customer.input).change(function(){
			me.init_for_commom_calculation()
		})
		$(me.fd.bank_card.input).change(function(){
			me.init_for_commom_calculation()
		})
		$(me.fd.bank_transfer.input).change(function(){
			me.init_for_commom_calculation()
		})
		$(me.fd.discount.input).change(function(){
			me.init_for_commom_calculation()
			me.setFocusToTextBox()
		})
		$(me.fd.bonus.input).change(function(){
			if(flt($(me.fd.bonus.input).val()) <= cur_frm.doc.bonus){
				me.init_for_commom_calculation()
			}
			else{
				cur_dialog.fields_dict.bonus.set_input(0.0)		
				msgprint (__("Please Enter less then or Equal to {0} for bonus", [cur_frm.doc.bonus]));
			}
		})	
	},
	init_for_commom_calculation:function(){
		var me = this;
		var val_of_balance = flt(me.fd.amount_paid_by_customer.$input.val()) - flt(cur_frm.doc.total_charges)
																			  + flt(cur_dialog.fields_dict.bank_card.$input.val())
																			  + flt(cur_dialog.fields_dict.bank_transfer.$input.val())
																			  + flt(cur_dialog.fields_dict.bonus.$input.val())
																			  + flt(cur_dialog.fields_dict.discount.$input.val())
		console.log(val_of_balance,"val_of_balance")
		cur_dialog.fields_dict.balance.set_input(val_of_balance.toFixed(2))
		me.dialog.fields_dict.msg.$wrapper.empty()
		$(me.dialog.body).parent().find('.btn-primary').hide()
		$('button[data-fieldname="add_in_receivables"]').css("display","none");
		$('button[data-fieldname="return_to_customer"]').css("display","none");
		$(me.dialog.body).find("[data-fieldname ='process_payment']").show();
	},
	setFocusToTextBox:function(){
	    $("input[data-fieldname='amount_paid_by_customer']").focus();
	},
	click_on_process_payment:function(){
		var me = this;	
		me.dialog.fields_dict.process_payment.$input.click(function() {
       		console.log(cur_dialog.fields_dict.balance.$input.val(),"balanceeeeee123")
       		console.log(parseFloat(cur_dialog.fields_dict.balance.$input.val()) > 0 )
       		console.log("onclick of process_payment")
       		if(parseFloat(me.dialog.fields_dict.balance.$input.val()) > 0 ){
       			console.log("in if")
       			$('button[data-fieldname="add_in_receivables"]').removeAttr("style");
       			$('button[data-fieldname="return_to_customer"]').removeAttr("style");
       			$(me.dialog.body).find("[data-fieldname ='process_payment']").hide();
       			html = "<div class='row' style='margin-left: -88px;'>There Is "+me.dialog.fields_dict.balance.$input.val()+" eur in balance Put It Into Receivables OR Give Change</div>"
       			me.dialog.fields_dict.msg.$wrapper.empty()
       			me.dialog.fields_dict.msg.$wrapper.append(html)
       		}
       		if(parseFloat(me.dialog.fields_dict.balance.$input.val()) < 0 ){
       			html = "<div class='row' style='margin-left: -88px;color: red;'>Error Message Balance Is Negative</div>"
       			$(me.dialog.body).parent().find('.btn-primary').hide()
       			me.dialog.fields_dict.msg.$wrapper.empty()
       			me.dialog.fields_dict.msg.$wrapper.append(html)
       		}
	    });
	    /*me.dialog.fields_dict.process_payment.$input.keypress(function(){
       		console.log("keypress of process_payment")
	    	$(me.dialog.body).find("[data-fieldname ='process_payment']").show();
			$(me.dialog.body).find("[data-fieldname ='add_in_receivables']").hide();
			$(me.dialog.body).find("[data-fieldname ='return_to_customer']").hide();
	    	$(me.dialog.body).find("[data-fieldname ='msg']").hide();
	    });	*/
	},
	click_on_add_in_receivables:function(){
		var me = this;
		me.dialog.fields_dict.add_in_receivables.$input.click(function() {
			value = me.dialog.get_values();
			frappe.call({
	            method: "customer_info.customer_info.doctype.payments_management.payments_management.add_receivables_in_customer",
	            async:false,
	            args: {
	              "customer": cur_frm.doc.customer,
	              "receivables":value.balance
	            },
	            callback: function(r){
	              if(r.message){
	            		cur_frm.doc.receivables = value.balance
	            		refresh_field("receivables")
	            		/*msgprint("Receivables Added In Customer Record")*/
	            		/*$(me.dialog.body).parent().find('.btn-primary').show()*/
	            		$('button[data-fieldname="return_to_customer"]').css("display","none");
	            		$('button[data-fieldname="submit_payment"]').css("display","");
	            		me.click_on_submit();
	            	}
	        	}
		    });	
		})
	},
	click_on_return_to_customer:function(){
		var me =this;
		me.dialog.fields_dict.return_to_customer.$input.click(function() {
			frappe.call({
	            method: "customer_info.customer_info.doctype.payments_management.payments_management.add_receivables_in_customer",
	            async:false,
	            args: {
	              "customer": cur_frm.doc.customer,
	              "receivables":0
	            },
	            callback: function(r){
	              if(r.message){
	            		cur_frm.doc.receivables = "0"
	            		refresh_field("receivables")
	            		/*msgprint("Return To Customer")*/
	            		/*$(me.dialog.body).parent().find('.btn-primary').show()*/
	            		$('button[data-fieldname="add_in_receivables"]').css("display","none");
	            		$('button[data-fieldname="submit_payment"]').css("display","");
	            		me.click_on_submit();
	            	}
	        	}
		    });
		})
	},
	click_on_submit:function(){
		var me =this;
		me.dialog.fields_dict.submit_payment.$input.click(function() {
			console.log(this,me,"in primary_action 123423123")
            me.click_on_make_entry();
            me.update_payments_records();
            me.dialog.hide();	
		});
	},
	click_on_make_entry:function(){
		var me =this;
		value = me.dialog.get_values();
		frappe.call({
            method: "customer_info.customer_info.doctype.payments_management.payments_management.make_payment_history",
            async:false,
            args: {
              "cash":value.amount_paid_by_customer,
              "bank_card":value.bank_card,
              "bank_transfer":value.bank_transfer,
              "bonus":value.bonus,
              "discount":value.discount,
              "balance":value.balance,
              "payment_date":cur_frm.doc.payment_date,
              "customer":cur_frm.doc.customer,
              "receivables":flt(cur_frm.doc.receivables),
              "rental_payment":value.rental_payment,
              "late_fees":value.late_fees,
            },
            callback: function(r){
             	
        	}
	    });
	},
	update_payments_records:function(){
		var me = this;
		frappe.call({
			async:false,    
	        method: "customer_info.customer_info.doctype.payments_management.payments_management.update_on_submit",
	       	args: {
	        	"payment_date":cur_frm.doc.payment_date,
	        	"customer":cur_frm.doc.customer,
	        	"bonus":cur_frm.doc.bonus
	        },
	       	callback: function(r){
	       		console.log(r.message)
	       		cur_frm.set_value("total_charges","0")
	       		cur_frm.set_value("amount_of_due_payments","0")
	       		/*cur_frm.set_value("receivables","0")*/
	        	render_agreements()
	        	/*me.click_on_make_entry*/
	        	/*msgprint(__("Payments Summary Successfully Updated Against All Above Customer Agreement\n Entry Made For this Payment"))*/
	    	}
	    })
	}	
})


Payments_Details = Class.extend({
	init:function(item, index){
		this.item = item;
		this.index = index;
		this.init_for_render_dialog();
		console.log(this.index, "in clcikc87687678678687_____________")       
	},
	init_for_render_dialog:function(){
		console.log(this.item)
		console.log(this,"in init_for_render_dialog")
		var me = this;
		this.dialog = new frappe.ui.Dialog({
            title: "Payments And Summary Detalis",
                fields: [
                   	{"fieldtype": "HTML" , "fieldname": "payments_record" , "label": "Relative Items"},
                   	{"fieldtype": "Button" , "fieldname": "s90_day_pay_Off" , "label": "90 day pay Off"},
                   	{"fieldtype": "Button" , "fieldname": "pay_off_agreement" , "label": " Pay Off Agreement"}
                   	],
                   	primary_action_label: "Add",
                   	primary_action: function(){
                   		console.log(this,me,"in primary_action")
                        me.make_list_of_payments_checked()
                    }
       	});
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
		var counter = 0
		$('button[data-fieldname="pay_off_agreement"]').css("display","none");
		$('button[data-fieldname="s90_day_pay_Off"]').css("display","none");
		if(this.item['id']){
			this.common_function_for_render_templates("common_template")	
			me.dialog.show();
		}
	},
	common_function_for_render_templates:function(template_name){
		var me = this;
		frappe.call({
			method:"customer_info.customer_info.doctype.payments_management.payments_management.get_payments_record",
			args:{
				"customer_agreement":me.item['id'],
				"receivable":cur_frm.doc.receivables
			},
			callback:function(r){
				if(r.message && template_name == "common_template"){
					html = $(frappe.render_template("common_template",{
            	   				"post":me.check_payment_record_for_pre_select(r.message,"Yes"),
            	   				"payment_date":cur_frm.doc.payment_date,
            	   				"summary":r.message['summary_records'],
            	   				"index":me.index
            	   			})).appendTo(me.fd.payments_record.wrapper);
					me.increase_decrease_total_charges_and_due_payment();
					me.init_trigger_for_nav_tabs();
				}
				else if(r.message && template_name == "payments_management"){
					$(me.dialog.body).parent().find('.btn-primary').show()
					$(me.dialog.body).find('#home'+ me.index).remove()
					$(me.dialog.body).find('#menu'+ me.index).remove()
					html = $(frappe.render_template("payments_management",{
        	   				"post":me.check_payment_record_for_pre_select(r.message,"No"),
        	   				"payment_date":cur_frm.doc.payment_date,
        	   				"index":me.index
        	   			})).appendTo(me.fd.payments_record.wrapper);
					$(me.dialog.body).find('#home'+ me.index).removeClass("tab-pane fade");	
					me.increase_decrease_total_charges_and_due_payment();
				}
				else if(r.message && template_name == "summary_record"){
					console.log(r.message['summary_records']['cond'],"summary-li summary-li")
					$(me.dialog.body).parent().find('.btn-primary').hide()
					$(me.dialog.body).find('#home'+ me.index).remove()
					$(me.dialog.body).find('#menu'+ me.index).remove()
					if(r.message['summary_records']['cond'] == 1){
						$('button[data-fieldname="pay_off_agreement"]').removeAttr("style");
						me.click_on_pay_off_agreement(r.message["summary_records"]);
					}
					else if(r.message['summary_records']['cond'] == 2){
						$('button[data-fieldname="s90_day_pay_Off"]').removeAttr("style");
						me.click_on_90_day_pay_Off(r.message["summary_records"]);
					}
					html = $(frappe.render_template("summary_record",{
        	   				"summary":r.message['summary_records'],
        	   				"index":me.index
        	   			})).appendTo(me.fd.payments_record.wrapper);
					$(me.dialog.body).find('#menu'+ me.index).removeClass("tab-pane fade");
				}
			}	
		});
	},
	init_trigger_for_nav_tabs:function(){
		var me = this;
		console.log($(me.dialog.body).find(".summary-li"), $(me.dialog.body).find(".nav-tabs"),"summary onClick")
		
		$(me.dialog.body).find(".payment-li").click(function(){
			$('button[data-fieldname="pay_off_agreement"]').css("display","none");
			$('button[data-fieldname="s90_day_pay_Off"]').css("display","none");
			me.common_function_for_render_templates("payments_management")
		});

		
		$(me.dialog.body).find(".summary-li").click(function(){
			me.common_function_for_render_templates("summary_record")
		});
	},
	check_payment_record_for_pre_select:function(payments_records,first_time){
		var me = this;

		if(first_time == "No"){
			me.payments_record_list = []
		}
		
		$.each(payments_records, function(i, d) {
			me.payments_record_list.push(d)
		});

   		var date = new Date();
		var firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
		var lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);
		var lastDay_pluse_one = new Date(date.getFullYear(), date.getMonth() + 1, 1);

	   	for(i=0;i < me.payments_record_list[0].length; i++){
	   		var date_diff_first = frappe.datetime.get_diff(me.payments_record_list[0][i]['due_date'],firstDay)
	   		var date_diff_last = frappe.datetime.get_diff(lastDay,me.payments_record_list[0][i]['due_date'])
	   		due_date_dateformat = new Date(me.payments_record_list[0][i]['due_date'])
	   		due_date_dateformat.setHours(00)
	   		due_date_dateformat.setSeconds(00)
	   		due_date_dateformat.setMinutes(00)
	   		if((me.payments_record_list[0][i]['check_box_of_submit'] == 0 && (due_date_dateformat <= lastDay && due_date_dateformat >= firstDay) && me.payments_record_list[0][i]['pre_select_uncheck'] == 0) || (me.payments_record_list[0][i]['check_box_of_submit'] == 0 && due_date_dateformat < firstDay && me.payments_record_list[0][i]['pre_select_uncheck'] == 0)){
	   			console.log("in if first")
	   			console.log(due_date_dateformat,"due_date after slice")
	   			me.payments_record_list[0][i]['check_box'] = 1
	   			me.payments_record_list[0][i]['pre_select'] = "Yes"
	   		}
	   		else{
	   			me.payments_record_list[0][i]['pre_select'] = "No"
	   		}
	   		if(me.payments_record_list[0][i]['check_box_of_submit'] == 0 && me.payments_record_list[0][i]['check_box'] == 1 && me.payments_record_list[0][i]['payment_date']){
	   			me.payments_record_list[0][i]['paid'] = "Yes"	
	   		}
	   		else{
	   			me.payments_record_list[0][i]['paid'] = "No"		
	   		}
	   	}
	   	console.log(me.payments_record_list,"return by check_payment_record_for_pre_select")
	   	return me.payments_record_list
	},
	make_list_of_payments_checked:function(){
		this.row_to_update = []
		this.row_to_check = []
		this.row_to_uncheck = []
		this.row_to_pre_select_uncheck = []
		var me = this;
        $.each($(this.fd.payments_record.wrapper).find('.select:checked[data-from=""]'), function(name, item){
                me.row_to_update.push($(item).val());
        });
        console.log($(this.fd.payments_record.wrapper).find('[pre-select="Yes"]'),"pre-select row")
        $.each($(this.fd.payments_record.wrapper).find('[pre-select="Yes"]'), function(name, item){
            if($(this).is(':not(:checked)')){
                me.row_to_pre_select_uncheck.push($(item).val());
    		}
        });
        $.each($(this.fd.payments_record.wrapper).find('.new-entry'), function(name, item){
    		if($(this).is(':checked')){
    			me.row_to_check.push($(item).val())
    		}
    		if($(this).is(':not(:checked)')){
    			me.row_to_uncheck.push($(item).val())
    		}
        });
        console.log(me.row_to_pre_select_uncheck,"me.row_to_pre_select_uncheck")
        console.log(me.row_to_update,"row_to_update")
        console.log(me.row_to_uncheck,"row_to_uncheck")
        console.log(me.row_to_check,"row_to_check")
	    console.log(cur_frm.doc.bonus,"bonus")    
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
	        		/*render_agreements()
	            	me.update_total_charges_and_due_payments()
	        		me.hide_dialog()*/
	        	}
	        });
	        frappe.call({
		        method: "customer_info.customer_info.doctype.payments_management.payments_management.set_values_in_agreement_temporary",
		        async: false,
	           	args: {
	           		"customer_agreement":this.item['id'],
	            	"frm_bonus":cur_frm.doc.bonus,
	            	"row_to_uncheck":me.row_to_uncheck
	            },
	           	callback: function(r){
	           		console.log(r.message,"message of bonus")
	        		cur_frm.set_value("bonus",r.message)
	        		render_agreements()
	            	me.update_total_charges_and_due_payments()
	        		/*msgprint("Changes Added")*/
	        		/*me.hide_dialog()*/
	        	}
	        });
	    }
	},
	increase_decrease_total_charges_and_due_payment:function(){
		var me = this
		console.log(me.payments_record_list,"me in side increase_decrease_total_charges_and_due_payment")
        var factor = me.payments_record_list[0][1].monthly_rental_amount;		
		$(this.fd.payments_record.wrapper).find('div.due_payments').append(flt((cur_frm.doc.amount_of_due_payments)).toFixed(2))
		$(this.fd.payments_record.wrapper).find('div.total_charges').append(flt((cur_frm.doc.total_charges)).toFixed(2))
		$('input[data-from=""]').change(function() {  
		    if ($(this).is(':checked')){
				var add_in_total_charges = parseFloat($(cur_dialog.body).find('div.total_charges').text()) + parseFloat(factor)
				var add_in_due_payments = parseFloat($(cur_dialog.body).find('div.due_payments').text()) + parseFloat(factor)
				$(cur_dialog.body).find('div.due_payments').empty()
				$(cur_dialog.body).find('div.due_payments').append(add_in_due_payments.toFixed(2))
				$(cur_dialog.body).find('div.total_charges').empty()
				$(cur_dialog.body).find('div.total_charges').append(add_in_total_charges.toFixed(2))
    		} 
    		else {
				var subtract_from_due_payments = parseFloat($(cur_dialog.body).find('div.due_payments').text()) - parseFloat(factor)
				var subtract_from_total_charges = parseFloat($(cur_dialog.body).find('div.total_charges').text()) - parseFloat(factor)
				console.log(subtract_from_total_charges.toFixed(2),"subtract_from_total_charges")
				$(cur_dialog.body).find('div.due_payments').empty()
				$(cur_dialog.body).find('div.due_payments').append(subtract_from_due_payments.toFixed(2))
				$(cur_dialog.body).find('div.total_charges').empty()
				$(cur_dialog.body).find('div.total_charges').append(subtract_from_total_charges.toFixed(2))
    		}
		});
		$('input[data-from="from_child_table"]').change(function() {  
		    if ($(this).is(':checked')){
				var add_in_total_charges = parseFloat($(cur_dialog.body).find('div.total_charges').text()) + parseFloat(factor)
				var add_in_due_payments = parseFloat($(cur_dialog.body).find('div.due_payments').text()) + parseFloat(factor)
				$(cur_dialog.body).find('div.due_payments').empty()
				$(cur_dialog.body).find('div.due_payments').append(add_in_due_payments.toFixed(2))
				$(cur_dialog.body).find('div.total_charges').empty()
				$(cur_dialog.body).find('div.total_charges').append(add_in_total_charges.toFixed(2))
    		} 
    		else {
				var subtract_from_due_payments = parseFloat($(cur_dialog.body).find('div.due_payments').text()) - parseFloat(factor)
				var subtract_from_total_charges = parseFloat($(cur_dialog.body).find('div.total_charges').text()) - parseFloat(factor)
				$(cur_dialog.body).find('div.due_payments').empty()
				$(cur_dialog.body).find('div.due_payments').append(subtract_from_due_payments.toFixed(2))
				$(cur_dialog.body).find('div.total_charges').empty()
				$(cur_dialog.body).find('div.total_charges').append(subtract_from_total_charges.toFixed(2))
    		}
		});
	},
	update_total_charges_and_due_payments : function(frm){
		var me = this;
		var factor = me.payments_record_list[0][1].monthly_rental_amount;
		var payments_cheked = me.row_to_check.length + me.row_to_update.length
		console.log(me,"me me me")
		console.log(me.row_to_check.length + me.row_to_update.length,"length")
		/*cur_frm.set_value("total_charges",(cur_frm.doc.total_charges - flt(payments_cheked*factor))==0?"0":cur_frm.doc.total_charges - flt(payments_cheked*factor))
		cur_frm.set_value("amount_of_due_payments",(cur_frm.doc.amount_of_due_payments - flt(payments_cheked*factor))==0?"0":cur_frm.doc.amount_of_due_payments - flt(payments_cheked*factor))*/
		cur_frm.set_value("total_charges",parseFloat($(cur_dialog.body).find('div.total_charges').text()) == 0 ? "0":parseFloat($(cur_dialog.body).find('div.total_charges').text()))
		cur_frm.set_value("amount_of_due_payments",parseFloat($(cur_dialog.body).find('div.due_payments').text()) == 0 ? "0":parseFloat($(cur_dialog.body).find('div.due_payments').text()))
	},
	click_on_pay_off_agreement:function(values){
		var me = this;
		this.values = values;
		me.dialog.fields_dict.pay_off_agreement.$input.click(function() {
			me.show_inner_dialog()
		});
	},
	click_on_90_day_pay_Off: function(values){
		var me = this;
		console.log("in s90_day_pay_Off")
		this.values = values;
		me.dialog.fields_dict.s90_day_pay_Off.$input.click(function() {
			me.show_inner_dialog()
		});
	},
	show_inner_dialog:function(){
		var me = this;
		this.inner_dialog = new frappe.ui.Dialog({
	        title: "Payments Detalis",
	            fields: [
		               	{"fieldtype": "Data" , "fieldname": "amount_paid_by_customer" , "label": "Cash","default":"0.0","reqd":"true"},
		               	{"fieldtype": "Data" , "fieldname": "bank_card" , "label": "Bank card","default":"0.0","reqd":"true"},
		               	{"fieldtype": "Data" , "fieldname": "bank_transfer" , "label": "Bank transfer","default":"0.0","reqd":"true"},
		               	{"fieldtype": "Column Break" , "fieldname": "column"},
		               	{"fieldtype": "Data" , "fieldname": "discount" , "label": "Discount","default":"0.0","reqd":"true"},
		               	{"fieldtype": "Data" , "fieldname": "balance" , "label": "Balance"},
		               	{"fieldtype": "Section Break" , "fieldname": "section"},
		               	{"fieldtype": "Button" , "fieldname": "process_payment" , "label": "Process payment"},
		               	{"fieldtype": "Column Break" , "fieldname": "column"},	
		               	{"fieldtype": "HTML" , "fieldname": "msg"}
	            	],
	               	primary_action_label: "OK",
	               	primary_action: function(){
	               		console.log(this,me,"in primary_action")
	                    me.dialog.hide()
	                }
	   	});
	    this.inner_fd = this.inner_dialog.fields_dict;
	    me.set_value_of_balance(this.inner_dialog);
	},
	set_value_of_balance:function(inner_dialog){
		var me = this;
		console.log(inner_dialog,"inner_dialog")
		console.log(me,"me me")
		$(inner_dialog.body).parent().find('.btn-primary').hide()
       	if(me.values['cond'] == 2){
       		this.val_balance = 0 - flt(me.values['Total_payoff_amount'])
	       	inner_dialog.fields_dict.balance.set_input(this.val_balance)
			inner_dialog.show();
			me.init_for_trigger_of_amount_paid_by_customer();
			me.click_on_process_payment();
		}
		else if(me.values['cond'] == 1){
			this.val_balance = 0 - flt(me.values['s90_day_pay_Off'])
	       	inner_dialog.fields_dict.balance.set_input(this.val_balance)
			inner_dialog.show();
			me.init_for_trigger_of_amount_paid_by_customer();
			me.click_on_process_payment();
		}
	},
	init_for_trigger_of_amount_paid_by_customer:function(){
		var me = this;
		/*$(me.inner_fd.amount_paid_by_customer.input).change(function(){
			s90_day_pay_Off = 0 - flt(me.values['s90_day_pay_Off'])
			var val_of_balance = flt(me.inner_fd.amount_paid_by_customer.$input.val()) + s90_day_pay_Off
			console.log(val_of_balance,"val_of_balance")
			cur_dialog.fields_dict.balance.set_input(val_of_balance.toFixed(2))
		})*/	
		$(me.inner_fd.amount_paid_by_customer.input).change(function(){
			me.init_for_commom_calculation()
		})
		$(me.inner_fd.bank_card.input).change(function(){
			me.init_for_commom_calculation()
		})
		$(me.inner_fd.bank_transfer.input).change(function(){
			me.init_for_commom_calculation()
		})
		$(me.inner_fd.discount.input).change(function(){
			me.init_for_commom_calculation()
		})	
	},
	init_for_commom_calculation:function(){
		var me = this;
		console.log(me,"me inside init_for_commom_calculation")
		var val_of_balance = flt(me.inner_fd.amount_paid_by_customer.$input.val()) + flt(cur_dialog.fields_dict.bank_card.$input.val())
																			  + flt(cur_dialog.fields_dict.bank_transfer.$input.val())
																			  + flt(cur_dialog.fields_dict.discount.$input.val())
																			  + flt(me.val_balance)
		console.log(val_of_balance,"val_of_balance")
		cur_dialog.fields_dict.balance.set_input(val_of_balance.toFixed(2))
		me.inner_dialog.fields_dict.msg.$wrapper.empty()
		/*$(me.dialog.body).parent().find('.btn-primary').hide()*/
		/*$(me.dialog.body).find("[data-fieldname ='process_payment']").show();*/
	},
	click_on_process_payment:function(){
		var me = this;
		me.inner_dialog.fields_dict.process_payment.$input.click(function() {
			console.log(me,"me onClick of process_payment")
			if(parseFloat(me.inner_dialog.fields_dict.balance.$input.val()) > 0 ){
       			console.log("in if")
       			$(me.inner_dialog.body).find("[data-fieldname ='process_payment']").hide();
       			html = "<div class='row'>There Is "+me.inner_dialog.fields_dict.balance.$input.val()+" eur in balance Put It Into Receivables OR Give Change</div>"
       			me.inner_dialog.fields_dict.msg.$wrapper.empty()
       			me.inner_dialog.fields_dict.msg.$wrapper.append(html)
       			me.update_agreement_according_today_plus_90days();
       		}
       		if(parseFloat(me.inner_dialog.fields_dict.balance.$input.val()) < 0 ){
       			html = "<div class='row' style='margin-left: -88px;color: red;'>Error Message Balance Is Negative</div>"
       			/*$(me.dialog.body).parent().find('.btn-primary').hide()*/
       			me.inner_dialog.fields_dict.msg.$wrapper.empty()
       			me.inner_dialog.fields_dict.msg.$wrapper.append(html)
       		}

		});
	},
	update_agreement_according_today_plus_90days:function(){
		var me = this;
		frappe.call({
	        method: "customer_info.customer_info.doctype.payments_management.payments_management.update_agreement_according_today_plus_90days",
	       	args: {
	       		"customer_agreement":me.item['id'],
	        	"agreement_status":"Closed",
	        	"condition": me.values['cond']
	        },
	       	callback: function(r){
	       		console.log(r.message)
	    		render_agreements();
	    		/*msgprint("Changes Added")*/
	    		/*me.inner_dialog.hide();*/
	    	}
	    });	
	}

})


/*add_comment:function(frm){
		if(cur_frm.doc.comment){
			frappe.call({
            method: "frappe.desk.form.utils.add_comment",
            args: {
                doc:{
                    doctype: "Communication",
                    comment_type: "Comment",
                    reference_doctype: "Customer",
                    subject: cur_frm.doc.comment,
                    content: cur_frm.doc.comment,
                    reference_name: cur_frm.doc.customer,
                    comment: cur_frm.doc.comment,
                    communication_type:'Comment'
                }
            },
            callback: function(r) {
            	msgprint("Comment Added Successfully");
            	cur_frm.set_value("comment","")
            }
	        });
		}
	}
get_other_field_value_from_customer = function(){
	if(cur_frm.doc.customer){
		frappe.call({    
			method: "frappe.client.get_list",
			async:false,
		   	args: {
		    	doctype: "Customer",
		       	fields: ["first_name","last_name","company_phone_1","company_phone_2","prersonal_code","summary_of_notes","bonus"],
		       	filters: { "name" : cur_frm.doc.customer
		        	},
				},
				callback: function(res){
				if(res && res.message){
					console.log(res.message[0]['company_phone_1'])
					cur_frm.set_value("first_name",res.message[0]['first_name'])
					cur_frm.set_value("last_name",res.message[0]['last_name'])
					cur_frm.set_value("company_phone_1",res.message[0]['company_phone_1'])
					cur_frm.set_value("company_phone_2",res.message[0]['company_phone_2'])
					cur_frm.set_value("prersonal_code",res.message[0]['prersonal_code'])
					cur_frm.set_value("summary_of_notes",res.message[0]['summary_of_notes'])
					cur_frm.set_value("bonus",res.message[0]['bonus'])
				}
			}
		});
	}
}*/
