cur_frm.add_fetch('customer', 'first_name', 'first_name');
cur_frm.add_fetch('customer', 'last_name', 'last_name');
cur_frm.add_fetch('customer', 'company_phone_1', 'company_phone_1');
cur_frm.add_fetch('customer', 'company_phone_2', 'company_phone_2');
cur_frm.add_fetch('customer', 'prersonal_code', 'prersonal_code');
cur_frm.add_fetch('customer', 'summary_of_notes', 'summary_of_notes');
cur_frm.add_fetch('customer','bonus','bonus')
cur_frm.add_fetch('customer','bonus','static_bonus')
cur_frm.add_fetch('customer','company_email_id_1','company_email_id_1')
cur_frm.add_fetch('customer','assign_manual_bonus','assign_manual_bonus')
cur_frm.add_fetch('customer','used_bonus','used_bonus')

var index = 0
frappe.ui.form.on("Payments Management", {
	refresh: function(frm) {
		frm.disable_save();
		$(".orange").hide()
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
			calculate_total_charges("Onload");
			get_bonus_link();
			get_address_of_customer()
			render_agreements();
		}
	},
	customer:function(){
		if(cur_frm.doc.customer){
			get_bonus_link()
			calculate_total_charges("Customer");
			get_address_of_customer();			
			render_agreements();
		}
	},
	/*static_bonus:function(){
		if(cur_frm.doc.static_bonus){
			cur_frm.set_value("bonus",cur_frm.doc.static_bonus)
		}
	},*/
	bonus_summary:function(){
		console.log("in bonus_summary")
		new bonus_summary()
	},
	submit:function(){
		if(cur_frm.doc.customer){
			var me = "Process Payments";
			new payoff_details(me)
		}
		else{
			frappe.throw("Select Customer First")
		}
	},
	call_commitment:function(frm){
		if(cur_frm.doc.customer){
			var item = "Common"
			var id = "Common"
			new call_commit(id,item)	
	    }
	    else{
			frappe.throw("Select Customer First")
		}    
	},
	add_notes:function(frm){
		if(cur_frm.doc.notes_on_customer_payments){
			frappe.call({
	            method: "customer_info.customer_info.doctype.payments_management.payments_management.add_notes_in_customer",
	            args: {
	            	"customer":cur_frm.doc.customer,
	            	"notes_on_customer_payments":cur_frm.doc.notes_on_customer_payments ? frappe.datetime.nowdate() + " - " + cur_frm.doc.notes_on_customer_payments:" ",
	            	"summary_of_notes":cur_frm.doc.summary_of_notes
	            },
	            callback: function(r) {
	            	if(r.message){
	            		cur_frm.set_value("summary_of_notes",r.message)
	            	}
	            	cur_frm.set_value("notes_on_customer_payments","")
	            }
	        });
		}
	}
})


get_bonus_link = function(){
	console.log("callback from payoff_details")
	$('[data-fieldname="bonus_link"]').empty();
	html = '<div class="row">\
            <label class="control-label" style="margin-left: 16px;">Active Bonus</label></div>\
            <div class="row">\
            <a class="bonus_link" style="margin-left: 16px;" value='+cur_frm.doc.static_bonus+'>' + cur_frm.doc.static_bonus + '</a>\
            </div>'
	$(cur_frm.fields_dict.bonus_link.wrapper).html(html);
	bonus = cur_frm.doc.static_bonus
	$('a.bonus_link').click(function(){			
		new edit_bonus(bonus)
	})
}


get_address_of_customer = function(){
	cur_frm.set_value("full_address","")
	frappe.call({
        method: "customer_info.customer_info.doctype.customer_agreement.customer_agreement.get_primary_address",
        args: {
            "customer": cur_frm.doc.customer,
        },
     	callback: function(r){
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

calculate_total_charges = function(flag){
	frappe.call({
		async:false,
        method: "customer_info.customer_info.doctype.payments_management.payments_management.calculate_total_charges",
        args: {
          "customer": cur_frm.doc.customer,
          "flag":flag,
          "payment_date":cur_frm.doc.payment_date
        },
        callback: function(r){
            if(r.message){
              	cur_frm.doc.amount_of_due_payments = r.message['amount_of_due_payments'] > 0 ? r.message['amount_of_due_payments']:"0";
           		cur_frm.doc.receivables = r.message['receivables'] == 0 ? "0":r.message['receivables'];
           		cur_frm.doc.total_charges = (r.message['amount_of_due_payments'] - r.message['receivables']) == 0 ? "0": (r.message['amount_of_due_payments'] - r.message['receivables']);
           		cur_frm.refresh_fields()
              	if(flag != "Process Payment"){
	           		cur_frm.doc.static_bonus = r.message['bonus'] > 0 ? r.message['bonus'] : "0";
              		refresh_field('static_bonus')	
	           	}	
            }
            else{
            	cur_frm.doc.total_charges = 0.0
	           	refresh_field('total_charges')	
            }
    	}	
    });
}

render_agreements = function(){
	var grid;

	var buttonFormat_detail = function (row, cell, value, columnDef, dataContext) {
		return "<input type='button' value='Detail' agreement = "+dataContext['agreement_no']+" class='detail' style='height:20px;padding: 0px;width: 70px;'; />";    
	}

	var buttonFormat_suspension = function (row, cell, value, columnDef, dataContext) {
		var id = "mybutton" + String(row);
		if(dataContext['suspenison']){
			return "<input type='button' value = "+dataContext['suspenison']+" id= "+id+" class='suspenison' style='height:20px;padding: 0px;width: 70px;'; />";		    
		}
		else{
			return "<input type='button' value = 'Call/Commitment' id= "+id+" class='suspenison' style='height:20px;padding: 0px;width: 100px;'; />";		
		}
	}

	var late_fees_editable = function(row, cell, value, columnDef, dataContext){
		var id = "late_fee"+ String(row)
		console.log(dataContext['late_fees'],"dataContext['late_fees']")
		return "<a class='late_fees' value="+dataContext['late_fees']+">" + dataContext['late_fees'] + "</a>";
	}

	var campaign_discount = function(row, cell, value, columnDef, dataContext){
		var id = "campaign_discount"+ String(row)
		console.log(dataContext['campaign_discount'],"dataContext['campaign_discount']")
		return "<a class='campaign_discount' value="+dataContext['campaign_discount']+">" + dataContext['campaign_discount'].split("-")[1] + "</a>";
		/*if(dataContext['campaign_discount'].split("-")[3] == "Yes"){
			return "<a class='campaign_discount' value="+dataContext['campaign_discount']+">" + dataContext['campaign_discount'].split("-")[1] + "</a>";
		}
		else{
			return "<a class='campaign_discount' value="+dataContext['campaign_discount']+">" + dataContext['campaign_discount'].split("-")[0] + "</a>";
		}*/
	}

	var columns = [
	    /*{id: "serial", name: "#", field: "serial", cssClass: "cell-selection", width: 20, resizable: false, selectable: false, focusable: false },*/
	    {id: "agreement_no", name: "Agreement No", field: "agreement_no",width: 80,toolTip: "Agreement No"},
	    {id: "agreement_period", name: "Agreement Period", field: "agreement_period",width: 80,toolTip: "Agreement Period"},
	    {id: "product", name: "Product", field: "product",width: 120,toolTip: "Product"},
	    {id: "number_of_payments", name: "# of Payments", field: "number_of_payments",width: 70,toolTip: "# of Payments"},
	    {id: "monthly_rental_payment", name: "Rental Payments", field: "monthly_rental_payment",width: 90,toolTip: "Rental Payments"},
	    {id: "current_due_date", name: "Current Due Date", field: "current_due_date",width: 90,toolTip: "Current Due Date"},
	    {id: "next_due_date", name: "Next Due Date", field: "next_due_date",width: 90,toolTip: "Next Due Date"},
	    {id: "payments_left", name: "Payments left", field: "payments_left",width: 70,toolTip: "Payments left"},
	    {id: "balance", name: "Balance", field: "balance",width: 70,toolTip: "Balance"},
	    {id: "late_fees", name: "Late Fees", field: "late_fees",width: 50,toolTip: "Late Fees",formatter:late_fees_editable},
	    {id: "total_dues", name: "Total Dues", field: "total_dues",width: 50,toolTip: "Total Dues"},
	    {id: "Campaign discount", name: "Campaign discount", field: "campaign_discount",width: 50,toolTip: "Campaign discount",formatter:campaign_discount},
	    {id: "payments_made", name: "Payments Made", field: "payments_made",width: 50,toolTip: "Payments Made"},
	    {id: "detail", name: "Detail", field: "detail",formatter: buttonFormat_detail,toolTip: "Detail"},
	    {id: "suspenison", name: "Call/Commitment", field: "suspenison",formatter: buttonFormat_suspension,toolTip: "Call/Commitment"}
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
              "customer": cur_frm.doc.customer,
              "payment_date":cur_frm.doc.payment_date
            },
            callback: function(r){
				if(r.message){
					this.data = r.message;
					make_grid(r.message,columns,options)
					/*cur_frm.doc.payment_management_record = []
					$.each($(".slick-row"),function(i,d){
						console.log(String($($(d).children()[12]).find(".detail").attr("agreement")))
						var row = frappe.model.add_child(cur_frm.doc, "Payment Management Record", "payment_management_record");	
						row.product = String($($(d).children()[2]).text());
						row.late_fees = $($(d).children()[9]).text() ? flt($($(d).children()[9]).text()):0
						row.rental_payment = flt($($(d).children()[4]).text());
						row.no_of_late_days = i;
						row.total = flt($($(d).children()[4]).text()) + flt($($(d).children()[9]).text())
					});
					refresh_field("payment_management_record");*/

					if(cur_frm.doc.customer_agreement){
						$.each($(".slick-row"),function(i,d){
							console.log(String($($(d).children()[12]).find(".detail").attr("agreement")))
							/*var row = frappe.model.add_child(cur_frm.doc, "Payment Management Record", "payment_management_record");	
							row.product = String($($(d).children()[2]).text());
							row.late_fees = flt($($(d).children()[9]).text());
							row.rental_payment = flt($($(d).children()[4]).text());
							row.no_of_late_days = flt($($(d).children()[4]).text());*/
							if(String($($(d).children()[12]).find(".detail").attr("agreement")) == cur_frm.doc.customer_agreement){
								$(".detail[agreement="+cur_frm.doc.customer_agreement+"]").click();
								cur_frm.set_value("customer_agreement","")
							}
						});
						//refresh_field("payment_management_record");
						/*$.each(r.message, function(i, d) {
                           
                       });*/
					}
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
            suspenison: data1.list_of_agreement[i][12],
            campaign_discount: data1.list_of_agreement[i][13],
        };
    }

    dataView = new Slick.Data.DataView();    
    dataView.beginUpdate();
    dataView.setItems(data);
    dataView.endUpdate();

	grid = new Slick.Grid("#payments_grid", dataView, columns, options);
	grid.onClick.subscribe(function (e, args) {
        var item = dataView.getItem(args.row);
        if($(e.target).hasClass("detail")) {
            index = parseInt(index) + 1;
        	new Payments_Details(item, index)
        }
        if($(e.target).hasClass("suspenison")) {
        	var id = $(e.target).attr('id')
        	//new manage_suspenison(id,item)
        	new call_commit(id,item)
        }
        if($(e.target).hasClass("late_fees")) {
        	var id = $(e.target).attr('id')
        	//new manage_suspenison(id,item)
        	new edit_late_fees(id,item)
        }
        if($(e.target).hasClass("campaign_discount")) {
        	var id = $(e.target).attr('id')
        	//new manage_suspenison(id,item)
        	new edit_campaign_discount(id,item)
        }
    });

}


bonus_summary = Class.extend({
	init:function(){
		this.show_dialog();
	},
	show_dialog:function(){
		this.dialog = new frappe.ui.Dialog({
    		title: "Bonus Summary",
        	fields: [
           		{"fieldtype": "HTML" , "fieldname": "bonus_summary"},
           	]
   		});
       	this.fd = this.dialog.fields_dict;
       	this.render_bonus_summary();
	},
	render_bonus_summary:function(){
		var me = this;
		me.get_bonus_details()
	},
	get_bonus_details:function(){
		var me =this;
		frappe.call({    
			//method: "frappe.client.get_list",
		   	method:"customer_info.customer_info.doctype.payments_management.payments_management.get_bonus_details",
		   	/*args: {
		    	doctype: "Customer Agreement",
		       	fields: ["name","new_agreement_bonus","early_payments_bonus","payment_on_time_bonus"],
		       	filters: {"agreement_status":"Open","customer":cur_frm.doc.customer},
			},*/
			args: {
				"customer":	cur_frm.doc.customer
			},
			callback: function(r){
				console.log(r.message,"e.message get_bonus_details")
				if(r.message){
					total_bonus = {"name":"Total",
									"early_payments_bonus":0,
									"payment_on_time_bonus":0,
									"new_agreement_bonus":0
								}
					$.each(r.message,function(i,d){
						total_bonus["name"] = "Total"
						total_bonus["early_payments_bonus"] += d["early_payments_bonus"]  
						total_bonus["payment_on_time_bonus"] += d["payment_on_time_bonus"]
						total_bonus["new_agreement_bonus"] += d["new_agreement_bonus"] 
					})
					r.message.push(total_bonus)
					me.dialog.show();
					console.log(r.message[r.message.length -1])
					var total_bonus_accumulated = r.message[r.message.length -1]["early_payments_bonus"] 
												+ r.message[r.message.length -1]["new_agreement_bonus"] 
												+ r.message[r.message.length -1]["payment_on_time_bonus"] 
												+ cur_frm.doc.assign_manual_bonus
					html = $(frappe.render_template("bonus_summary",{
						"bonus":r.message,
						"total_bonus_accumulated":total_bonus_accumulated,
						"assign_manual_bonus":cur_frm.doc.assign_manual_bonus,
						"used_bonus":cur_frm.doc.used_bonus,
						"active_bonus":flt(total_bonus_accumulated) - cur_frm.doc.used_bonus
					})).appendTo(me.fd.bonus_summary.wrapper);
				}
			}
		})	
	}
})


edit_bonus = Class.extend({
	init:function(bonus){
		this.bonus = bonus;
		this.show_dialog();
	},
	show_dialog:function(){
		var me = this;
		this.dialog = new frappe.ui.Dialog({
    		title: "Update Bonus",
        	fields: [
           		{"fieldtype": "Float" , "fieldname": "bonus" , "label": "Bonus","precision":2},
           		{"fieldtype": "Small Text" , "fieldname": "comment" , "label": "Comment"},
           		{"fieldtype": "Section Break" , "fieldname": "section"},
           		{"fieldtype": "Button" , "fieldname": "add_comment" , "label": "Add Comment"},
           		{"fieldtype": "Column Break" , "fieldname": "column"},
           		{"fieldtype": "Column Break" , "fieldname": "column"},
           		{"fieldtype": "Button" , "fieldname": "update_bonus" , "label": "Update Bonus"}
           	],
           	/*primary_action_label: "Update",
           	primary_action: function(){
            		me.update_bonus();
            }*/
   		});
       	this.fd = this.dialog.fields_dict;
       	this.dialog.$wrapper.find('.modal-dialog').css("width", "350px");
       	this.dialog.$wrapper.find('.modal-dialog').css("height", "300px");
       	this.dialog.$wrapper.find('.hidden-xs').css("margin-left","-2px");
       	//this.dialog.$wrapper.find('[data-dismiss="modal"]').hide()
       	this.set_value_of_bonus();
	},
	set_value_of_bonus:function(){
		var me = this;
		me.dialog.fields_dict.bonus.set_input(me.bonus)
		me.dialog.show();
		me.update_bonus();
		me.add_comment();
	},
	add_comment:function(){
		var me = this;
		console.log("in my function")
		me.dialog.fields_dict.add_comment.$input.click(function() {
			if(me.dialog.fields_dict.comment.$input.val()){
				cur_frm.set_value("notes_on_customer_payments"," "+me.dialog.fields_dict.comment.$input.val())
				$('button[data-fieldname="add_notes"]').click();
				me.dialog.fields_dict.comment.set_input("")
			}
		})
	},
	update_bonus:function(){
		var me = this;
		me.dialog.fields_dict.update_bonus.$input.click(function() {
			console.log(me.dialog.fields_dict.bonus.$input.val(),"bonus value")
			frappe.call({
		        method: "customer_info.customer_info.doctype.payments_management.payments_management.update_bonus",
		        args: {
		          "customer": cur_frm.doc.customer,
		          "bonus":flt(me.dialog.fields_dict.bonus.$input.val()),
		          "old_bonus":cur_frm.doc.bonus
		        },
		        callback: function(r){
		        	if(r.message){
		        		cur_frm.set_value("notes_on_customer_payments"," ["+user+"] "+r.message)
						$('button[data-fieldname="add_notes"]').click();
		        		cur_frm.set_value("notes_on_customer_payments","")
		    			cur_frm.set_value("assign_manual_bonus",cur_frm.doc.assign_manual_bonus+(flt(me.dialog.fields_dict.bonus.$input.val()) - flt(cur_frm.doc.static_bonus)))
		        		cur_frm.set_value("static_bonus",flt(me.dialog.fields_dict.bonus.$input.val()));
		        		cur_frm.set_value("bonus",flt(cur_frm.doc.bonus)+flt(cur_frm.doc.assign_manual_bonus));
		    			msgprint("Bonus Updated");
		    			me.dialog.hide();
		    			get_bonus_link();
		        	}
		    	}	
    		});
		})
	}
});	

edit_campaign_discount = Class.extend({
	init:function(id,item){
		this.item = item;
		this.id = id;
		this.make_campaign_discount_edit();
	},
	make_campaign_discount_edit:function(){
		var me = this;
		console.log(me.item["campaign_discount"])
		var options_list = ["0"]
		if (flt(me.item["campaign_discount"].split("-")[0]) > 0){
			//me.item["campaign_discount"].split("-")[1]
			for(i=1;i<=flt(me.item["campaign_discount"].split("-")[2]);i++){
				options_list.push(i*flt(me.item["campaign_discount"].split("-")[0]))
			}
			console.log(options_list,"options_list")
		}	
		this.dialog = new frappe.ui.Dialog({
    		title: "Contact result",
        	fields: [
           		{"fieldtype": "Select" ,"fieldname": "campaign_discount" ,"options":options_list.join("\n") ,"label": "Campaign Discount"},
           		{"fieldtype": "Float" ,"fieldname": "due_amount","label": "Due Amount","precision":2},
           		{"fieldtype": "Float" ,"fieldname": "total_charges_amount","label": "Total Charges Amount","precision":2}
           	],
           	primary_action_label: "Update",
           	primary_action: function(){
                me.update_campaign_discount();
            }
   		});
       	this.fd = this.dialog.fields_dict;
       	this.dialog.$wrapper.find('.modal-dialog').css("width", "350px");
       	this.dialog.$wrapper.find('.modal-dialog').css("height", "300px");
       	this.dialog.$wrapper.find('.hidden-xs').css("margin-left","-2px");
       	this.dialog.show();
       	this.dialog.fields_dict.campaign_discount.set_input(flt(me.item["campaign_discount"].split("-")[1]))
       	//this.dialog.fields_dict.due_amount.set_input(cur_frm.doc.amount_of_due_payments - flt(me.item["campaign_discount"].split("-")[1]))
       	//this.dialog.fields_dict.total_charges_amount.set_input(cur_frm.doc.total_charges - flt(me.item["campaign_discount"].split("-")[1]))
       	//this.dialog.fields_dict.campaign_discount.set_input(0)
       	
		/*if(String(me.item["campaign_discount"].split("-")[3]) == "Yes"){
			me.dialog.fields_dict.due_amount.set_input(cur_frm.doc.amount_of_due_payments - flt(me.item["campaign_discount"].split("-")[1]))
       		me.dialog.fields_dict.total_charges_amount.set_input(cur_frm.doc.total_charges - flt(me.item["campaign_discount"].split("-")[1]))	
		}
		else{
			me.dialog.fields_dict.due_amount.set_input(cur_frm.doc.amount_of_due_payments)
	       	me.dialog.fields_dict.total_charges_amount.set_input(cur_frm.doc.total_charges)
		}*/
		me.dialog.fields_dict.due_amount.set_input(cur_frm.doc.amount_of_due_payments)
	    me.dialog.fields_dict.total_charges_amount.set_input(cur_frm.doc.total_charges)
		$(this.dialog.$wrapper).find('[data-dismiss="modal"]').hide();
		this.campaign_discount();
	},
	campaign_discount:function(){
		var me = this;
		/*
			campaign discount should be preselected if given then that given campaign_discount
			if again select due will not deduct 
		*/
		$(me.dialog.fields_dict.campaign_discount.input).change(function(){
			//if(flt(me.item["campaign_discount"].split("-")[1]) > 0){
				if(flt(me.dialog.fields_dict.campaign_discount.$input.val()) != flt(me.item["campaign_discount"].split("-")[1])) {
					me.dialog.fields_dict.due_amount.set_input(cur_frm.doc.amount_of_due_payments - flt(me.dialog.fields_dict.campaign_discount.$input.val()))
	       			me.dialog.fields_dict.total_charges_amount.set_input(cur_frm.doc.total_charges - flt(me.dialog.fields_dict.campaign_discount.$input.val()))
				}
				if(flt(me.dialog.fields_dict.campaign_discount.$input.val()) == 0){
					me.dialog.fields_dict.due_amount.set_input(cur_frm.doc.amount_of_due_payments - flt(me.dialog.fields_dict.campaign_discount.$input.val()))
       				me.dialog.fields_dict.total_charges_amount.set_input(cur_frm.doc.total_charges - flt(me.dialog.fields_dict.campaign_discount.$input.val()))	
				}
			//}
			console.log((flt(me.dialog.fields_dict.campaign_discount.$input.val()) == 0),"(flt(me.dialog.fields_dict.campaign_discount.$input.val()) == 0)")
			/*else if(flt(me.item["campaign_discount"].split("-")[1]) == 0){
				me.dialog.fields_dict.due_amount.set_input(cur_frm.doc.amount_of_due_payments - flt(me.dialog.fields_dict.campaign_discount.$input.val()))
       			me.dialog.fields_dict.total_charges_amount.set_input(cur_frm.doc.total_charges - flt(me.dialog.fields_dict.campaign_discount.$input.val()))
			}
			else if(flt(me.dialog.fields_dict.campaign_discount.$input.val()) == 0) {
				me.dialog.fields_dict.due_amount.set_input(cur_frm.doc.amount_of_due_payments - flt(me.dialog.fields_dict.campaign_discount.$input.val()))
       			me.dialog.fields_dict.total_charges_amount.set_input(cur_frm.doc.total_charges - flt(me.dialog.fields_dict.campaign_discount.$input.val()))
			}*/
		})
	},
	update_campaign_discount:function(){
		var me = this;
		console.log(me.fd.campaign_discount.$input.val())		
		frappe.call({
	        method: "customer_info.customer_info.doctype.payments_management.payments_management.update_campaign_discount",
	        args: {
	        	"agreement":me.item['id'],
	        	"campaign_discount": flt(me.fd.campaign_discount.$input.val())
	        },
	        callback: function(r) {
	        	if(r.message){
	        		cur_frm.set_value("amount_of_due_payments",flt(me.fd.due_amount.$input.val()))
	    			cur_frm.set_value("total_charges",flt(me.fd.total_charges_amount.$input.val()))    	
	        	}
	        	me.dialog.hide();
	        	//calculate_total_charges("Campaign Discount");
	        	render_agreements();
	        }
	    });
	}	
})

edit_late_fees = Class.extend({
	init:function(id,item){
		this.item = item;
		this.id = id;
		this.make_late_editable();
	},
	make_late_editable:function(){
		var me = this;
		this.dialog = new frappe.ui.Dialog({
    		title: "Contact result",
        	fields: [
           		{"fieldtype": "Float" , "fieldname": "late_fees" , "label": "Late Fees","precision":2},
           		//{"fieldtype": "Small Text" , "fieldname": "comment" , "label": "Comment"},
           		{"fieldtype": "Section Break" , "fieldname": "section"},
           		{"fieldtype": "Column Break" , "fieldname": "column"},
           		{"fieldtype": "Column Break" , "fieldname": "column"},
           		{"fieldtype": "Column Break" , "fieldname": "column"},
           		//{"fieldtype": "Button" , "fieldname": "add_comment" , "label": "Add Comment"}
           	],
           	primary_action_label: "Update",
           	primary_action: function(){
            		me.add_comment();
                //me.update_late_fees();
            }
   		});
       	this.fd = this.dialog.fields_dict;
       	this.dialog.$wrapper.find('.modal-dialog').css("width", "350px");
       	this.dialog.$wrapper.find('.modal-dialog').css("height", "300px");
       	this.dialog.$wrapper.find('.hidden-xs').css("margin-left","-2px");
       	this.dialog.show();
		$(this.dialog.$wrapper).find('[data-dismiss="modal"]').hide()
		this.set_late_fees();
	},
	set_late_fees:function(){
		var me = this;
		me.dialog.fields_dict.late_fees.set_input(me.item['late_fees'])	
		//me.add_comment();
	},
	add_comment:function(){
		var me = this;
		console.log("in my function")
		//me.dialog.fields_dict.add_comment.$input.click(function() {
			if(flt(me.dialog.fields_dict.late_fees.$input.val()) > 0){
				console.log("in mybutton mybutton 11223")
				comment =  "["+user+"]- "+" "+"Late fees modified from "+me.item['late_fees']+" "+"to"+" "+ me.dialog.fields_dict.late_fees.$input.val() +" ("+me.item['id']+")"
				cur_frm.set_value("notes_on_customer_payments",comment)
				$('button[data-fieldname="add_notes"]').click()
				//me.dialog.fields_dict.comment.set_input("")
				me.update_late_fees();
			}
			else{
				me.dialog.hide();
			}
		//})
	},
	update_late_fees:function(){
		var me = this;
		console.log(me.fd.late_fees.$input.val())		
		frappe.call({
	        method: "customer_info.customer_info.doctype.payments_management.payments_management.update_late_fees",
	        args: {
	        	"agreement":me.item['id'],
	        	"late_fees": flt(me.fd.late_fees.$input.val())
	        },
	        callback: function(r) {
	        	me.dialog.hide();
	        	render_agreements();
	        }
	    });
	}
})


call_commit = Class.extend({
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
                   		{"fieldtype": "Currency" , "fieldname": "amount" , "label": "Amount"},
                   		{"fieldtype": "Small Text" , "fieldname": "comment" , "label": "Comment"},
                   		{"fieldtype": "Section Break" , "fieldname": "section"},
                   		{"fieldtype": "Column Break" , "fieldname": "column"},
                   		{"fieldtype": "Column Break" , "fieldname": "column"},
                   		{"fieldtype": "Column Break" , "fieldname": "column"},
                   		{"fieldtype": "Button" , "fieldname": "add_comment" , "label": "Add Comment"}
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
       	this.get_fields_values();
		this.before_select_contact_result();
		this.select_contact_result();
		this.click_on_reset();
	},
	get_fields_values:function(){
		this.agreements = [];
		this.values_of_agreement = []; 
		var me = this;
		if(me.item == "Common" && me.id == "Common"){
			me.filters = {"agreement_status" : "Open","customer":cur_frm.doc.customer}
		}
		else{
			me.filters = { "name" : me.item['id']}
		}
		frappe.call({    
			method: "frappe.client.get_list",
		   	args: {
		    	doctype: "Customer Agreement",
		       	fields: ["contact_result","suspension_date","amount_of_contact_result","call_commitment"],
		       	filters: me.filters,
			},
			callback: function(r){
				if(r && r.message){
					console.log("r.message",r.message)
					if(me.item == "Common"){
						for(i=0;i<r.message.length;i++){
							me.agreements.push({"name":r.message[i]['name'],
												"call_commitment":r.message[i]['call_commitment']})
							if(r.message[i]['call_commitment'] == "All"){
								me.values_of_agreement.push({"amount_of_contact_result":r.message[i]['amount_of_contact_result'],
																		"contact_result":r.message[i]['contact_result'],
																		"suspension_date":r.message[i]['suspension_date'],
																		"call_commitment":r.message[i]['call_commitment']	
																		});
							}
						}
						if(me.values_of_agreement[0]['contact_result'] == "WBI" && me.values_of_agreement[0]['amount_of_contact_result'] && me.values_of_agreement[0]["call_commitment"] == "All"){
							me.contact_result = me.values_of_agreement[0]['contact_result']
							me.suspension_date = me.values_of_agreement[0]['suspension_date']
							me.amount_of_contact_result = me.values_of_agreement[0]['amount_of_contact_result']
							me.set_values();
						}
						else if(me.values_of_agreement[0]['contact_result'] == "Sent SMS/Email" && me.values_of_agreement[0]["call_commitment"] == "All"){
							me.contact_result = r.message[0]['contact_result']
							me.suspension_date = me.values_of_agreement[0]['suspension_date']
							me._set_values()
						}
					}
					else{
						if(r && r.message[0]['contact_result'] == "WBI"){
							me.contact_result = r.message[0]['contact_result']
							me.suspension_date = r.message[0]['suspension_date']
							me.amount_of_contact_result = r.message[0]['amount_of_contact_result']
							me.set_values()
						}
						else if(r && r.message[0]['contact_result'] == "Sent SMS/Email"){
							me.contact_result = r.message[0]['contact_result']
							me.suspension_date = r.message[0]['suspension_date']
							me._set_values()
						}
					}
				}
			}
		});
	},
	_set_values:function(){
		var me = this;
		$(me.dialog.body).find("[data-fieldname ='date_picker']").hide();
		$(me.dialog.body).find("[data-fieldname ='comment']").show();
		$(me.dialog.body).find("[data-fieldname ='add_comment']").show();
		me.dialog.fields_dict.contact_result.set_input(me.contact_result)
		me.dialog.fields_dict.date_picker.set_input(me.suspension_date)
		me.add_comment();
	},
	set_values:function(){
		var me = this;
		$(me.dialog.body).find("[data-fieldname ='date_picker']").show();
		$(me.dialog.body).find("[data-fieldname ='amount']").show();
		$(me.dialog.body).find("[data-fieldname ='comment']").show();
		$(me.dialog.body).find("[data-fieldname ='add_comment']").show();
		me.dialog.fields_dict.contact_result.set_input(me.contact_result)
		me.dialog.fields_dict.date_picker.set_input(me.suspension_date)
		me.dialog.fields_dict.amount.set_input(me.amount_of_contact_result)
		me.add_comment();
	},
	before_select_contact_result:function(){
		var me = this;
		$(me.dialog.body).find("[data-fieldname ='date_picker']").hide();
		$(me.dialog.body).find("[data-fieldname ='amount']").hide();
		$(me.dialog.body).find("[data-fieldname ='comment']").hide();
		$(me.dialog.body).find("[data-fieldname ='add_comment']").hide();
	},
	select_contact_result:function(){
		var me = this;
		nowdate = frappe.datetime.nowdate()
		$(me.fd.contact_result.input).change(function(){
			if(me.fd.contact_result.$input.val() == "WBI"){
				$(me.dialog.body).find("[data-fieldname ='date_picker']").show();
				$(me.dialog.body).find("[data-fieldname ='amount']").show();
				$(me.dialog.body).find("[data-fieldname ='comment']").show();
				$(me.dialog.body).find("[data-fieldname ='add_comment']").show();					
				me.dialog.fields_dict.amount.set_input(flt(me.item["total_dues"]).toFixed(2))
				me.add_comment();
			}
			if(me.fd.contact_result.$input.val() == "Sent SMS/Email"){
				console.log(me.item["current_due_date"],"current_due_date1232212")
				me.dialog.fields_dict.date_picker.set_input(nowdate)
				me.dialog.fields_dict.amount.set_input("")
				$(me.dialog.body).find("[data-fieldname ='date_picker']").hide();					
				$(me.dialog.body).find("[data-fieldname ='amount']").hide();
				$(me.dialog.body).find("[data-fieldname ='comment']").show();
				$(me.dialog.body).find("[data-fieldname ='add_comment']").show();
				me.add_comment();
			}
			if(me.fd.contact_result.$input.val() == ""){
				console.log("inside hol")
				$(me.dialog.body).find("[data-fieldname ='date_picker']").hide();
				$(me.dialog.body).find("[data-fieldname ='amount']").hide();
				$(me.dialog.body).find("[data-fieldname ='comment']").hide();
				$(me.dialog.body).find("[data-fieldname ='add_comment']").hide();			
			}
		})
	},
	click_on_reset:function(){
		var me = this;
		me.dialog.fields_dict.contact_result.set_input("")
		me.dialog.fields_dict.date_picker.set_input("")
		me.dialog.fields_dict.amount.set_input("")
		var agreements_name = []
		if(me.item == "Common"){
			$.each($(".slick-row"),function(i,d){
				agreements_name.push($($(d).children()[0]).text())
			});
		}	
		me.agreements_name = agreements_name
		me.dialog.fields_dict.reset.$input.click(function() {
			frappe.call({
	            method: "customer_info.customer_info.doctype.payments_management.payments_management.set_or_reset_call_commitment",
	            args: {
	            	"customer":cur_frm.doc.customer,
	            	"agreement_name":me.item == "Common"? "Common":me.item['id'],
	            	"agreements": me.agreements_name
	            },
	            callback: function(r) {
	            	me.dialog.hide();
	            	render_agreements();
	            }
	        });
		})
	},
	change_name_of_buttons:function(){
		var me = this;
		date = me.fd.date_picker.$input.val()
		if(me.fd.contact_result.$input.val() == "WBI"){
			if(me.id != "Common"){	
				id = "#" + me.id
				$(id).attr('value', date);
			}
			me.date = date
			me.update_call_commitment_data_in_agreement()
			me.dialog.hide();
		}
		if(me.fd.contact_result.$input.val() == "Sent SMS/Email"){
			if(me.id != "Common"){	
				id = "#" + me.id
				$(id).attr('value', "SMS/Email");
			}
			me.date = date;
			me.update_call_commitment_data_in_agreement()
			me.dialog.hide();
		}
	},
	update_call_commitment_data_in_agreement:function(){
		var me  = this;
		console.log(me.agreements_name,"agreements")
		frappe.call({
            method: "customer_info.customer_info.doctype.payments_management.payments_management.update_call_commitment_data_in_agreement",
            args: {
              "customer_agreement": me.item == "Common" ? me.agreements_name:me.item['id'],
              "date": me.date ? me.date :"",
              "contact_result": me.fd.contact_result.$input.val(),
              "amount":flt(me.fd.amount.$input.val()) > 0 ?  me.fd.amount.$input.val():0,
              "all_or_individual":me.item == "Common" ? "All":"Individual"		
            },
            callback: function(r){
        		render_agreements();
        	}
	    });
	},
	add_comment:function(){
		var me = this;
		console.log("in my function")
		me.dialog.fields_dict.add_comment.$input.click(function() {
			if(me.dialog.fields_dict.comment.$input.val()){
				console.log("in mybutton mybutton 11223")
				cur_frm.set_value("notes_on_customer_payments", " "+"["+user+"] "+" "+"CC:"+" "+me.dialog.fields_dict.comment.$input.val()+" "+"("+me.item['id']+")")
				$('button[data-fieldname="add_notes"]').click()
				me.dialog.fields_dict.comment.set_input("")
			}
		})
	}
});


Payments_Details = Class.extend({
	init:function(item, index){
		this.item = item;
		this.index = index;
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
		console.log(me.item,"ttttttttttttttttt")
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
				else if(r.message && me.template_name == "payments_management"){
					me.remove_id_of_nav_tab_and_hide_primary_button()
					$('#history'+ me.index).hide();
					me.rendering_data = r.message
					me.check_pre_select = "No"
					html = $(frappe.render_template("payments_management",{
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
			
					if(r.message['summary_records']['cond'] == 1){
						$('button[data-fieldname="pay_off_agreement"]').show();
						me.values = r.message["summary_records"];
						new payoff_details(me)
					}
					else if(r.message['summary_records']['cond'] == 2){
						$('button[data-fieldname="s90_day_pay_Off"]').show();
						me.values = r.message["summary_records"];
						new payoff_details(me)
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
			me.template_name = "payments_management"
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
	    if(checking_sequence == ""){
	    	me.common_function_for_add_checkbox();
	    }
	    if(add_list.length == 1 && add_list[0] == "1"){
		    me.common_function_for_add_checkbox();
	    }
	    if(add_list.length == 1 && add_list[0] != "1"){
	    	frappe.throw("Error Please Add Payment In sequence")
	    }
	    if(me.row_to_check.concat(me.row_to_update).length == 0){
	    	frappe.throw("Please Any Payment")
	    }
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
	},
	add_date_on_check:function(){
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
		me.old_instance.dialog.fields_dict.pay_off_agreement.$input.click(function() {
			me.old_dialog = me.old_instance.dialog;
			me.show_dialog();
		});
	},
	click_on_90_day_pay_Off: function(){
		var me = this;
		me.old_instance.dialog.fields_dict.s90_day_pay_Off.$input.click(function() {
			me.old_dialog = me.old_instance.dialog;
			me.show_dialog();
		});
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
	},
	set_value_of_balance:function(){
		var me = this;
		me.hide_button();
		$(me.dialog.body).parent().find('.btn-primary').hide()
	    if(me.old_instance != "Process Payments"){
    		me.fd.bonus.df.hidden=1;
   			me.fd.bonus.refresh();
	       	if(me.old_instance.values['cond'] == 2){
	       		this.val_balance = 0 - flt(me.old_instance.values['Total_payoff_amount'])
		       	me.dialog.fields_dict.balance.set_input(this.val_balance)
				me.dialog.show();
				me.init_for_trigger_of_amount_paid_by_customer();
				me.click_on_process_payment();
			}
			else if(me.old_instance.values['cond'] == 1){
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
		$.each($(".slick-row"),function(i,d){
			console.log(Number((flt($($(d).children()[9]).text())).toFixed(flt_precision)), Number((flt($($(d).children()[10]).text())).toFixed(flt_precision)))
			if(flt($($(d).children()[3]).text()) > 0 ){
				late_fees += Number((flt($($(d).children()[9]).text())).toFixed(flt_precision))
				total_due += Number((flt($($(d).children()[10]).text())).toFixed(flt_precision))  
				
			}
			agreements.push($($(d).children()[0]).text())
			number_of_payments += Number((flt($($(d).children()[10]).text())).toFixed(flt_precision))
		});
		this.rental_payment = total_due - late_fees;
       	this.late_fees = late_fees;
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
	    			console.log("late_payment",r.message["late_payment"],"me.rental_payment",me.rental_payment,r.message["first_payment"])
	    			console.log(flt(me.late_payment) + flt(r.message["first_payment"]),"aaaaaaaaaaaaaaaaaaaaaaaaaaaa")
	    			me.late_payment = r.message["late_payment"]
	    			me.first_payment = r.message["first_payment"]
	    			me.payable_by_bonus = flt(me.late_payment) + flt(r.message["first_payment"])
	    			if(flt(me.payable_by_bonus) == flt((me.rental_payment).toFixed(2))){
	    				me.payable_by_bonus = flt((me.rental_payment).toFixed(2)) - flt(me.late_payment) - flt(r.message["first_payment"])
	    			}
	    			else{
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
			console.log(me.payable_by_bonus)
			if($(me.fd.bonus.input).val() == ""){
				me.dialog.set_value("bonus","0.0")	
			}
			if ((flt($(me.fd.bonus.input).val()) <= cur_frm.doc.static_bonus) && (flt($(me.fd.bonus.input).val()) <= flt(me.payable_by_bonus))) {
				me.init_for_commom_calculation();
			}
			if ((flt($(me.fd.bonus.input).val()) <= cur_frm.doc.static_bonus) && (flt($(me.fd.bonus.input).val())) > flt(me.payable_by_bonus)) {
				cur_dialog.fields_dict.bonus.set_input("0.0")		
				//msgprint(__("Bonus Is not Used For Late Payments \n Enter less then or Equal to {0} for bonus",[flt(me.payable_by_bonus).toFixed(2)]));
				frappe.throw(__("Enter less then or Equal to {0} for bonus",[flt(me.payable_by_bonus).toFixed(2)]));
			}
			if( (flt($(me.fd.bonus.input).val()) > cur_frm.doc.static_bonus) ){
				cur_dialog.fields_dict.bonus.set_input("0.0")		
				frappe.throw(__("Please Enter less then or Equal to {0} for bonus", [cur_frm.doc.static_bonus]));
			}
		})		
	},
	init_for_commom_calculation:function(){
		var me = this;
		me.hide_button();
		if(me.old_instance != "Process Payments"){
			console.log("in if")
			var val_of_balance = flt(me.fd.amount_paid_by_customer.$input.val()) + flt(cur_dialog.fields_dict.bank_card.$input.val())
																				  + flt(cur_dialog.fields_dict.bank_transfer.$input.val())
																				  + flt(cur_dialog.fields_dict.discount.$input.val())
																				  + flt(me.val_balance)
			console.log("bal", val_of_balance)
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
			console.log("in else - bal", val_of_balance)
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
			if(parseFloat(me.dialog.fields_dict.balance.$input.val()) >= 0 ){
       			$(me.dialog.body).find("[data-fieldname ='process_payment']").hide();
       			html = "<div class='row'>There Is "+(flt(me.dialog.fields_dict.balance.$input.val()) - flt(me.dialog.fields_dict.bonus.$input.val()))+" eur in balance Put It Into Receivables OR Give Change</div>"
       			me.dialog.fields_dict.msg.$wrapper.empty()
       			me.dialog.fields_dict.msg.$wrapper.append(html)
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
       		if(parseFloat(me.dialog.fields_dict.balance.$input.val()) < 0 && me.old_instance == "Process Payments"){
       			me.calculate_underpayment();
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
	calculate_underpayment:function(){
		var me = this;
		value = me.dialog.get_values();
		if (flt(value.bonus) > 0){
			frappe.throw(__("No Bonus For Partial Payment"));
		}
		else{
			console.log(value.amount_paid_by_customer,"values")
			frappe.call({
		        method: "customer_info.customer_info.doctype.payments_management.payments_management.calculate_underpayment",
		       	args: {
		       		"agreements":me.agreements,
		        	"payment_date":cur_frm.doc.payment_date,
		        	"amount_paid_by_customer":value.amount_paid_by_customer,
		        	"receivables":cur_frm.doc.receivables
		        },
		       	callback: function(r){
					r.message = Number((flt(r.message)).toFixed(2))
		       		sum_of_cash_card_transfer = flt(me.dialog.fields_dict.bank_transfer.$input.val()) + flt(me.dialog.fields_dict.bank_card.$input.val()) + flt(me.dialog.fields_dict.amount_paid_by_customer.$input.val())
		       		if(r.message && (parseFloat(me.dialog.fields_dict.balance.$input.val()) < 0) && sum_of_cash_card_transfer >= parseFloat(r.message)){
			       		$('button[data-fieldname="process_payment"]').hide();
					    $('button[data-fieldname="return_to_customer"]').hide();
						$('button[data-fieldname="add_in_receivables"]').show();
						html = "<div class='row' style='margin-left: -88px;color: green;'>Cash amount >= "+" "+(flt(r.message) - flt(value.bonus))+" add in receivables</div>"
					    me.dialog.fields_dict.msg.$wrapper.empty()
					    me.dialog.fields_dict.msg.$wrapper.append(html)
					    me.click_on_add_in_receivables();
					    me.click_on_return_to_customer();
					}
			       	if(r.message && (parseFloat(me.dialog.fields_dict.balance.$input.val()) < 0) && sum_of_cash_card_transfer < parseFloat(r.message)){
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
			me.add_in_receivables = value.balance - value.bonus;
			me.hide_other_and_show_complete_payment();
			me.click_on_submit();
		})
	},
	click_on_return_to_customer:function(){
		var me =this;
		me.dialog.fields_dict.return_to_customer.$input.click(function() {
			var val_of_cash = flt($(me.fd.amount_paid_by_customer.input).val()) - flt($(me.fd.balance.input).val())
			cur_dialog.fields_dict.amount_paid_by_customer.set_input(val_of_cash.toFixed(2))
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
		console.log(me.add_in_receivables,"add_in_receivables")
		console.log(me.rental_payment,"rental_payment")
		/*console.log(me.old_instance)
		console.log(me.old_instance['values']['s90d_SAC_price'],"old_dialog")
		console.log(me.old_instance['values']['s90_day_pay_Off'],"old_dialog")*/
		me.dialog.fields_dict.submit_payment.$input.click(function(){
			if(me.old_instance == "Process Payments" && me.number_of_payments > 0){
				me.update_payments_records();
			}
			else if(me.old_instance == "Process Payments" && me.number_of_payments == 0){
				frappe.throw("Please Add Any Payment")
			}
			else{
				me.payoff_submit();	
			}
		});
	},
	payoff_submit:function(){
		console.log("inside payoff_submit")
		var me = this;
		frappe.call({
	        method: "customer_info.customer_info.doctype.payments_management.payments_management.update_payments_records_on_payoff_submit",
	       	args: {
	       		"customer_agreement":me.old_instance.item['id'],
	        	"payment_date":cur_frm.doc.payment_date,
	        },
	       	callback: function(r){
	    		if(r.message){
	    			console.log(r.message,"aaaaaaaaaaaa")		
	    			me.update_on_payoff(r.message)
	    		}
	    	}
	    });	
	},
	update_on_payoff:function(data){
		var me = this;
		value = me.dialog.get_values();
		console.log(me.old_instance,"me old_instance ")
		frappe.call({
	        method: "customer_info.customer_info.doctype.payments_management.payments_management.payoff_submit",
	       	args: {
	       		"customer_agreement":me.old_instance.item['id'],
	        	"agreement_status":"Closed",
	        	"condition": me.old_instance.values['cond'],
	        	"customer":cur_frm.doc.customer,
	        	//"receivables":me.add_in_receivables,
	        	"receivables":cur_frm.doc.receivables,
	        	"add_in_receivables":me.add_in_receivables,
	        	"values":JSON.stringify(value),
	        	"payment_date":cur_frm.doc.payment_date,
	        	"total_charges":cur_frm.doc.total_charges,
              	"data":data,
              	"rental_payment":me.old_instance['values']['s90d_SAC_price'] ? me.old_instance['values']['s90d_SAC_price'] : me.old_instance['values']['Discounted_payment_amount'],
              	"total_amount":me.old_instance['values']['s90_day_pay_Off'] ? me.old_instance['values']['s90_day_pay_Off'] : me.old_instance['values']['Total_payoff_amount']
	        },
	       	callback: function(r){
	       		me.dialog.hide();
				me.old_dialog.hide();
				calculate_total_charges("Payoff");
	    		render_agreements();
	    		msgprint("Agreement paid off successfully")
	    	}
	    });
	},
	update_payments_records:function(){
		console.log("in update_payments_records")
		var me = this;
		value = me.dialog.get_values();
		frappe.call({
			async:false,    
	        method: "customer_info.customer_info.doctype.payments_management.payments_management.update_on_submit",
	       	args: {
	       		"values":JSON.stringify(value),
	       		"rental_payment":me.rental_payment,
	       		"late_fees":me.late_fees,
	        	"payment_date":cur_frm.doc.payment_date,
	        	"customer":cur_frm.doc.customer,
	        	"bonus":cur_frm.doc.bonus - flt(value.bonus),
	        	"manual_bonus":cur_frm.doc.assign_manual_bonus,
	        	"used_bonus":flt(value.bonus),
	        	//"receivables":me.add_in_receivables,
	        	"add_in_receivables":me.add_in_receivables,
              	"receivables":cur_frm.doc.receivables,
              	"total_charges":cur_frm.doc.total_charges,
	        },
	       	callback: function(r){
	       		if(flt(value.bonus) == cur_frm.doc.bonus){
	       			cur_frm.set_value("bonus",cur_frm.doc.static_bonus)
	       		}
	       		else{
	       			cur_frm.set_value("bonus",cur_frm.doc.bonus - flt(value.bonus))
		       		cur_frm.set_value("static_bonus",cur_frm.doc.bonus)
	       		}
	       		cur_frm.set_value("used_bonus",flt(value.bonus))
	            if(r.message){
	            	msgprint(r.message+"\n"+"Agreement Payoff successfully")
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
