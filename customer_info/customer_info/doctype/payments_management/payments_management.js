{% include 'customer_info/customer_info/doctype/payments_management/payments_details.js' %};
{% include 'customer_info/customer_info/doctype/payments_management/suspended_payments_grid.js' %};

cur_frm.add_fetch('customer', 'first_name', 'first_name');
cur_frm.add_fetch('customer', 'last_name', 'last_name');
cur_frm.add_fetch('customer', 'company_phone_1', 'company_phone_1');
cur_frm.add_fetch('customer', 'company_phone_2', 'company_phone_2');
cur_frm.add_fetch('customer', 'prersonal_code', 'prersonal_code');
cur_frm.add_fetch('customer', 'summary_of_notes', 'summary_of_notes');
cur_frm.add_fetch('customer','company_email_id_1','company_email_id_1')
cur_frm.add_fetch('customer','bonus','bonus')
cur_frm.add_fetch('customer','bonus','static_bonus')
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
		$(cur_frm.fields_dict.payments_grid.wrapper).empty();
		$(cur_frm.fields_dict.payments_grid.wrapper).append("<table width='100%>\
  		<tr>\
		    <td valign='top' width='100%'>\
		      <div id='payments_grid' style='width:100%;height:200px;''></div>\
		    	</td>\
  			</tr>\
		</table>");
		if(cur_frm.doc.customer){
			calculate_total_charges("Onload");
			_get_bonus_summary();
			get_bonus_link();
			get_address_of_customer()
			render_agreements();
			render_suspended_agreements();
		}
	},
	customer:function(frm){
		if(cur_frm.doc.customer){
			get_bonus_link()
			calculate_total_charges("Customer");
			_get_bonus_summary();
			get_address_of_customer();			
			render_agreements();
			render_suspended_agreements();
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


_get_bonus_summary= function(frm){
	console.log("inside _get_bonus_summary")
	frappe.call({
	   	method:"customer_info.customer_info.doctype.payments_management.payments_management.get_bonus_summary",
		args: {
			"customer":	cur_frm.doc.customer
		},
		callback: function(r){
			console.log("_get_bonus_summary")
		}
	})	
}



render_suspended_agreements = function(frm){
	$(cur_frm.fields_dict.suspended_payments_grid.wrapper).empty();
	var me = this
	frappe.call({
   		method: "customer_info.customer_info.doctype.payments_management.payments_management.get_customer_agreement",
    	args: {
      		"customer": cur_frm.doc.customer,
      		"payment_date":cur_frm.doc.payment_date,
      		"flag":"Suspended"
    	},
    	callback: function(r){
			if(r.message){
				console.log("dsdddd",r.message,r.message['list_of_agreement'],r.message['list_of_agreement'].length)
				agreement_data = []
				agreement_data = r.message;
				if(r.message['list_of_agreement'].length > 0){
					cur_frm.set_df_property("suspended_agreement_detail","hidden",0)
					new suspended_payments(frm,agreement_data);
				}
				else{
					cur_frm.set_df_property("suspended_agreement_detail","hidden",1)
				}
			}
		}
	});	
}

get_bonus_link = function(){
	console.log("callback from payoff_details")
	$('[data-fieldname="bonus_link"]').empty();
	html = '<div class="row">\
            <label class="control-label" style="margin-left: 16px;">Active Bonus</label></div>\
            <div class="row">\
            <a class="bonus_link" style="margin-left: 16px;" value='+cur_frm.doc.static_bonus+'>' + flt(cur_frm.doc.static_bonus).toFixed(2) + '</a>\
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
	        if(r.message){
	        	if(r.message[0]['address_line1']){
	            	cur_frm.doc.full_address = r.message[0]["address_line1"] + "\n" + r.message[0]["city"]
	     			refresh_field('full_address')
	     		}
	     		else if(r.message[0]['address_line2']){
	     			cur_frm.doc.full_address = r.message[0]["address_line1"] + "\n" + r.message[0]["address_line2"] + "\n" + r.message[0]["city"]
	     			refresh_field("full_address")
	     		}
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
              	if(flag != "Process Payment"){
	           		cur_frm.doc.static_bonus = r.message['bonus'] > 0 ? r.message['bonus'] : "0";
              		refresh_field('static_bonus')	
	           	}
	           	console.log("inside tempory",r.message)	
              	cur_frm.doc.amount_of_due_payments = r.message['amount_of_due_payments'] > 0 ? r.message['amount_of_due_payments']:"0";
           		cur_frm.doc.total_charges = (r.message['amount_of_due_payments'] - r.message['receivables']) == 0 ? "0": (r.message['amount_of_due_payments'] - r.message['receivables']);
           		cur_frm.doc.receivables = r.message['receivables'] == 0 ? "0":r.message['receivables'];
           		cur_frm.doc.bonus = r.message['pre_select_payment_bonus'] // add bonus of pre select id on time bonus
           		cur_frm.refresh_fields();
            }
            else{
            	cur_frm.doc.total_charges = 0.0
	           	refresh_field('total_charges')	
            }
    	}	
    });
}

render_agreements = function(flag){
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

	var current_due_date_editable = function(row, cell, value, columnDef, dataContext){
		var id = "current_due_date"+ String(row)
		console.log(dataContext['current_due_date'],"dataContext['current_due_date']")
		return "<a class='current_due_date' value="+dataContext['current_due_date']+">" + dataContext['current_due_date'] + "</a>";
	}

	var late_fees_editable = function(row, cell, value, columnDef, dataContext){
		var id = "late_fee"+ String(row)
		console.log(dataContext['late_fees'],"dataContext['late_fees']")
		return "<a class='late_fees' value="+dataContext['late_fees']+">" + dataContext['late_fees'] + "</a>";
	}

	var campaign_discount = function(row, cell, value, columnDef, dataContext){
		var id = "campaign_discount"+ String(row)
		console.log(dataContext['campaign_discount'],"dataContext['campaign_discount']")
		if(dataContext['campaign_discount'].split("-")[3] == "Yes"){			
			return "<a class='campaign_discount' value="+dataContext['campaign_discount']+">" + dataContext['campaign_discount'].split("-")[0] + "</a>";
		}
		else{
			return "<a class='campaign_discount' value="+dataContext['campaign_discount']+">" + 0.00 + "</a>";
		}
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
	    {id: "current_due_date", name: "Current Due Date", field: "current_due_date",width: 90,toolTip: "Current Due Date",formatter:current_due_date_editable},
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
    	//showHeaderRow:true,
    	//explicitInitialization: true
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
				if(r.message && r.message['list_of_agreement'].length > 0){
					console.log(r.message,"r.message1111222333")
					this.data = r.message;
					cur_frm.set_df_property("open_agreements","hidden",0)
					cur_frm.set_df_property("process_payment_section","hidden",0)
					make_grid(r.message,columns,options)
					if(flag == "from_late_fees"){
						var total_due_amount = 0
			        	$.each($("#payments_grid").find(".slick-row"),function(i,d){
							total_due_amount += flt($($(d).children()[10]).text())
						});
						console.log(total_due_amount,"total_due_amount")
						cur_frm.set_value("amount_of_due_payments",flt(total_due_amount) > 0 ? flt(total_due_amount):"0.00")
			     		cur_frm.set_value("total_charges",(flt(total_due_amount)-flt(cur_frm.doc.receivables)) > 0 ? flt(total_due_amount)-flt(cur_frm.doc.receivables):"0.00")      		
					}
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
						$.each($("#payments_grid").find(".slick-row"),function(i,d){
							console.log(String($($(d).children()[13]).find(".detail").attr("agreement")))
							if(String($($(d).children()[13]).find(".detail").attr("agreement")) == cur_frm.doc.customer_agreement){
								$(".detail[agreement="+cur_frm.doc.customer_agreement+"]").click();
								cur_frm.set_value("customer_agreement","")
							}
						});
					}
				}
				else{
					cur_frm.set_df_property("open_agreements","hidden",1)
					cur_frm.set_df_property("process_payment_section","hidden",1)
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

	grid = new Slick.Grid("#payments_grid", dataView, columns, options);
      
    // for row header filters
    var columnFilters = []
    function filter(item) {
	    for (var columnId in columnFilters) {
	      if (columnId !== undefined && columnFilters[columnId] !== "") {
	        var c = grid.getColumns()[grid.getColumnIndex(columnId)];
	        if (item[c.field] != columnFilters[columnId]) {
	          return false;
	        }
	      }
	    }
    	return true;
  	}	

    dataView.onRowCountChanged.subscribe(function (e, args) {
      grid.updateRowCount();
      grid.render();
    });

    dataView.onRowsChanged.subscribe(function (e, args) {
      grid.invalidateRows(args.rows);
      grid.render();
    });

    $(grid.getHeaderRow()).delegate(":input", "change keyup", function (e) {
      var columnId = $(this).data("columnId");
      if (columnId != null) {
        columnFilters[columnId] = $.trim($(this).val());
        dataView.refresh();
      }
    });

    grid.onHeaderRowCellRendered.subscribe(function(e, args) {
        $(args.node).empty();
        $("<input type='text'>")
           .data("columnId", args.column.id)
           .val(columnFilters[args.column.id])
           .appendTo(args.node);
    });
    grid.init();
    //dataView.setFilter(filter);
   	
   	//

    dataView.beginUpdate();
    dataView.setItems(data);
    dataView.endUpdate();


	grid.onClick.subscribe(function (e, args) {
        var item = dataView.getItem(args.row);
        if($(e.target).hasClass("detail")) {
            index = parseInt(index) + 1;
            var flag = "Open Agreement"
        	new Payments_Details(item,index,flag)
        }
        if($(e.target).hasClass("suspenison")) {
        	var id = $(e.target).attr('id')
        	//new manage_suspenison(id,item)
        	new call_commit(id,item)
        }
        if($(e.target).hasClass("current_due_date")) {
        	var id = $(e.target).attr('id')
        	new edit_current_due_date(id,item)
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
		me.get_bonus_summary()
	},
	get_bonus_summary:function(){
		var me =this;
		frappe.call({
		   	method:"customer_info.customer_info.doctype.payments_management.payments_management.get_bonus_summary",
			args: {
				"customer":	cur_frm.doc.customer
			},
			freeze: true,
			freeze_message: __("Please Wait..."),
		/*frappe.call({    
			method: "frappe.client.get_list",
		   	args: {
		    	doctype: "Customer Agreement",
		       	fields: ["early_payments_bonus","payment_on_time_bonus","new_agreement_bonus","name"],
		       	filters: {'agreement_status':'Open','customer':cur_frm.doc.customer},
			},*/	
			callback: function(r){
				if(r.message){
					total_bonus = {
									"name":"Total",
									"early_payments_bonus":0,
									"payment_on_time_bonus":0,
									"new_agreement_bonus":0,
									"status_list":[]
								}
					console.log(r.message)
					$.each(r.message,function(i,d){
						total_bonus["name"] = "Total"
						total_bonus["early_payments_bonus"] += d["early_payments_bonus"]  
						total_bonus["payment_on_time_bonus"] += d["payment_on_time_bonus"]
						total_bonus["new_agreement_bonus"] += d["new_agreement_bonus"] 
						total_bonus["status_list"].push(d["agreement_status"])
					})
					r.message.push(total_bonus)
					var all_closed = "false"  
					all_closed = r.message[r.message.length -1]["status_list"].every(function checkclosed(status) {
					    return status == "Closed";
					})
					me.dialog.show();
					var total_bonus_accumulated = r.message[r.message.length -1]["early_payments_bonus"] 
												+ r.message[r.message.length -1]["new_agreement_bonus"] 
												+ r.message[r.message.length -1]["payment_on_time_bonus"] 
												+ cur_frm.doc.assign_manual_bonus
					html = $(frappe.render_template("bonus_summary",{
						"bonus":r.message,
						"total_bonus_accumulated":total_bonus_accumulated.toFixed(2),
						"assign_manual_bonus":cur_frm.doc.assign_manual_bonus.toFixed(2),
						"used_bonus":cur_frm.doc.used_bonus.toFixed(2),
						"active_bonus":flt(total_bonus_accumulated).toFixed(2) - flt(cur_frm.doc.used_bonus).toFixed(2),
						"all_closed":all_closed,
						"cancelled_bonus":r.message[0]['cancelled_bonus']
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
		//me.trigger_bonus();
		me.update_bonus();
		me.add_comment();
	},
	trigger_bonus:function(){
		var me = this;
		$(me.dialog.fields_dict.bonus.input).change(function(){
			if(flt($(this).val()) < flt(me.bonus)){
				me.dialog.fields_dict.bonus.set_input(me.bonus)
				frappe.throw(__("Enter Amount greater or Equal to {0} for bonus",[flt(me.bonus).toFixed(2)]));
			}
		})
	},
	add_comment:function(){
		var me = this;
		me.dialog.fields_dict.add_comment.$input.click(function() {
			if(me.dialog.fields_dict.comment.$input.val()){
				cur_frm.set_value("notes_on_customer_payments","["+user+"]"+" "+"Bonus:"+" "+me.dialog.fields_dict.comment.$input.val())
				$('button[data-fieldname="add_notes"]').click();
				me.dialog.fields_dict.comment.set_input("")
			}
		})
	},
	update_bonus:function(){
		var me = this;
		/*me.dialog.fields_dict.update_bonus.$input.click(function() {
			if(me.dialog.fields_dict.bonus.$input.val() && flt(me.dialog.fields_dict.bonus.$input.val()) > flt(me.bonus)){
				frappe.call({
			        method: "customer_info.customer_info.doctype.payments_management.payments_management.update_bonus",
			        args: {
			          "customer": cur_frm.doc.customer,
			          "bonus":flt(me.dialog.fields_dict.bonus.$input.val()),
			          "assign_manual_bonus":flt(me.dialog.fields_dict.bonus.$input.val()) - flt(cur_frm.doc.static_bonus),
				      "payment_date":cur_frm.doc.payment_date	
			        },
			        callback: function(r){
			        	if(r.message){
			        		cur_frm.set_value("notes_on_customer_payments"," ["+user+"] "+r.message)
							$('button[data-fieldname="add_notes"]').click();
			        		cur_frm.set_value("notes_on_customer_payments","")
			        		var assign_manual_bonus = cur_frm.doc.assign_manual_bonus+(flt(me.dialog.fields_dict.bonus.$input.val()) - flt(cur_frm.doc.static_bonus))
			    			cur_frm.set_value("assign_manual_bonus",assign_manual_bonus)
			        		cur_frm.set_value("static_bonus",flt(me.dialog.fields_dict.bonus.$input.val()));
			        		cur_frm.set_value("bonus",flt(cur_frm.doc.bonus)+flt(cur_frm.doc.assign_manual_bonus));
			    			msgprint("Bonus Updated");
			    			me.dialog.hide();
			    			get_bonus_link();
			        	}
			    	}	
	    		});
			}
			else{
				frappe.throw(__("Enter Amount greater or Equal to {0} for bonus",[flt(me.bonus).toFixed(2)]));
			}
		})*/
		me.dialog.fields_dict.update_bonus.$input.click(function() {
			if(me.dialog.fields_dict.bonus.$input.val()){
				frappe.call({
			        method: "customer_info.customer_info.doctype.payments_management.payments_management.update_bonus",
			        args: {
			          "customer": cur_frm.doc.customer,
			          "bonus":flt(me.dialog.fields_dict.bonus.$input.val()),
			          "assign_manual_bonus":flt(me.dialog.fields_dict.bonus.$input.val()) - flt(cur_frm.doc.static_bonus),
				      "payment_date":cur_frm.doc.payment_date	
			        },
			        callback: function(r){
			        	if(r.message){
			        		cur_frm.set_value("notes_on_customer_payments"," ["+user+"] "+r.message)
							$('button[data-fieldname="add_notes"]').click();
			        		cur_frm.set_value("notes_on_customer_payments","")
			        		var assign_manual_bonus = cur_frm.doc.assign_manual_bonus+(flt(me.dialog.fields_dict.bonus.$input.val()) - flt(cur_frm.doc.static_bonus))
			    			cur_frm.set_value("assign_manual_bonus",assign_manual_bonus)
			        		cur_frm.set_value("static_bonus",flt(me.dialog.fields_dict.bonus.$input.val()));
			        		cur_frm.set_value("bonus",flt(cur_frm.doc.bonus)+flt(cur_frm.doc.assign_manual_bonus));
			    			msgprint("Bonus Updated");
			    			me.dialog.hide();
			    			get_bonus_link();
			        	}
			    	}	
				});
			}
			else{
				frappe.throw(__("Enter Amount greater or Equal to {0} for bonus",[flt(me.bonus).toFixed(2)]));
			}
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
		me.options_list = ["0"]
		if (flt(me.item["campaign_discount"].split("-")[1]) > 0){
			//me.item["campaign_discount"].split("-")[1]
			/*for(i=1;i<=flt(me.item["payments_left"]);i++){
				me.options_list.push(i*flt(me.item["campaign_discount"].split("-")[0]))
			}*/
			for(i=1;i<=flt(me.item["campaign_discount"].split("-")[2]);i++){
				console.log(i*flt(me.item["campaign_discount"].split("-")[1]))
				me.options_list.push(i*flt(me.item["campaign_discount"].split("-")[1]))
			}
		}
		this.dialog = new frappe.ui.Dialog({
    		title: "Contact result",
        	fields: [
           		{"fieldtype": "Select" ,"fieldname": "campaign_discount" ,"options":me.options_list.join("\n") ,"label": "Campaign Discount"},
           		//{"fieldtype": "Float" ,"fieldname": "due_amount","label": "Due Amount","precision":2},
           		//{"fieldtype": "Float" ,"fieldname": "total_charges_amount","label": "Total Charges Amount","precision":2}
           	],
           	primary_action_label: "Update",
           	primary_action: function(){
                me.update_campaign_discount();
            }
   		});
       	this.fd = this.dialog.fields_dict;
       	this.dialog.$wrapper.find('.modal-dialog').css("width", "500px");
       	this.dialog.$wrapper.find('.modal-dialog').css("height", "300px");
       	//this.dialog.$wrapper.find('.hidden-xs').css("margin-left","-2px");
		//$(this.dialog.$wrapper).find('[data-dismiss="modal"]').hide();
       	this.dialog.show();
 		if(me.item["campaign_discount"].split("-")[3] == "Yes"){
 			this.dialog.fields_dict.campaign_discount.set_input(flt(me.item["campaign_discount"].split("-")[0]))	
 		}
 		else{
 			this.dialog.fields_dict.campaign_discount.set_input(0)
 		}      	
       	
		//me.dialog.fields_dict.due_amount.set_input(cur_frm.doc.amount_of_due_payments)
	    //me.dialog.fields_dict.total_charges_amount.set_input(cur_frm.doc.total_charges)
		//this.campaign_discount();
	},
	/*campaign_discount:function(){
		var me = this;
		
			campaign discount should be preselected if given then that given campaign_discount
			if again select due will not deduct 
		
		$(me.dialog.fields_dict.campaign_discount.input).change(function(){
			if (inList(me.options_list, flt(me.item["campaign_discount"].split("-")[1]))){
				console.log("iside my list 1111111",flt(me.item["campaign_discount"].split("-")[1]))
				me.options_list = []
			}  			
			if(flt(me.dialog.fields_dict.campaign_discount.$input.val()) != flt(me.item["campaign_discount"].split("-")[1])) {
				me.dialog.fields_dict.due_amount.set_input(cur_frm.doc.amount_of_due_payments - flt(me.dialog.fields_dict.campaign_discount.$input.val()))
       			me.dialog.fields_dict.total_charges_amount.set_input(cur_frm.doc.total_charges - flt(me.dialog.fields_dict.campaign_discount.$input.val()))
			}
			if(flt(me.dialog.fields_dict.campaign_discount.$input.val()) == 0){
				me.dialog.fields_dict.due_amount.set_input(cur_frm.doc.amount_of_due_payments - flt(me.dialog.fields_dict.campaign_discount.$input.val()))
   				me.dialog.fields_dict.total_charges_amount.set_input(cur_frm.doc.total_charges - flt(me.dialog.fields_dict.campaign_discount.$input.val()))	
			}

		})
	},*/
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
	        		var amount_of_due_payments = cur_frm.doc.amount_of_due_payments+flt(me.item["campaign_discount"].split("-")[0])-flt(me.fd.campaign_discount.$input.val())
	        		var total_charges = cur_frm.doc.total_charges+flt(me.item["campaign_discount"].split("-")[0])-flt(me.fd.campaign_discount.$input.val())
	        		if(me.item["campaign_discount"].split("-")[3] == "Yes"){
	        			cur_frm.set_value("amount_of_due_payments",flt(amount_of_due_payments) == 0 ? "0.00":flt(amount_of_due_payments))
	    				cur_frm.set_value("total_charges",flt(total_charges) == 0 ? "0.00":flt(total_charges))	
	        		}
	        		else{
	    				cur_frm.set_value("amount_of_due_payments",cur_frm.doc.amount_of_due_payments - flt(me.fd.campaign_discount.$input.val()) == 0 ? "0.00":cur_frm.doc.amount_of_due_payments - flt(me.fd.campaign_discount.$input.val()))
	    				cur_frm.set_value("total_charges",cur_frm.doc.total_charges - flt(me.fd.campaign_discount.$input.val()) == 0 ? "0.00":cur_frm.doc.total_charges - flt(me.fd.campaign_discount.$input.val()))
	        		}
	        	}
	        	me.dialog.hide();
	        	render_agreements();
	        	//calculate_total_charges("Campaign Discount");
	        }
	    });
	}	
})

edit_current_due_date = Class.extend({
	init:function(id,item){
		this.item = item;
		this.id = id;
		this.make_editable();
	},
	make_editable:function(){
		var me = this;
		this.dialog = new frappe.ui.Dialog({
			title: "Update Current Due Date",
			fields: [
				{"fieldtype": "Date" , "fieldname": "current_due_date" , "label": "Current Due Date"}
			],
			primary_action_label: "Update",
			primary_action: function(){
				me.update_due_dates();
			}
		});
		this.fd = this.dialog.fields_dict;
		this.dialog.$wrapper.find('.modal-dialog').css("width", "500px");
		this.dialog.$wrapper.find('.modal-dialog').css("height", "300px");
		this.dialog.show();
		this.set_current_due_date();
	},
	set_current_due_date:function(){
		var me = this;
		me.dialog.fields_dict.current_due_date.set_input(me.item['current_due_date']);
	},
	update_due_dates:function(){
		var me = this;
		frappe.call({
	        method: "customer_info.customer_info.doctype.payments_management.payments_management.update_due_date",
			args: {
				"agreement":me.item['id'],
				"update_due_date": me.fd.current_due_date.$input.val()
			},
			callback: function(r) {
				if(r.message){
					render_agreements();
					me.dialog.hide();
				}
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
       	this.dialog.$wrapper.find('.modal-dialog').css("width", "500px");
       	this.dialog.$wrapper.find('.modal-dialog').css("height", "300px");
       	//this.dialog.$wrapper.find('.hidden-xs').css("margin-left","-2px");
       	this.dialog.show();
		//$(this.dialog.$wrapper).find('[data-dismiss="modal"]').hide()
		this.set_late_fees();
	},
	set_late_fees:function(){
		var me = this;
		me.dialog.fields_dict.late_fees.set_input(me.item['late_fees'])	
		//me.add_comment();
	},
	add_comment:function(){
		var me = this;
		//me.dialog.fields_dict.add_comment.$input.click(function() {
			if(flt(me.dialog.fields_dict.late_fees.$input.val()) >= 0){
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
	        	render_agreements("from_late_fees");
	        	me.dialog.hide();	        	
	        	//calculate_total_charges("Customer");
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
		this.select_contact_result();
		this.click_on_reset();
	},
	get_fields_values:function(){
		this.agreements = [];
		this.values_of_agreement = [];
		this.data_fieldname = $(this.dialog.body).find("[data-fieldname ='date_picker'],\
										[data-fieldname ='amount'],\
										[data-fieldname ='comment'],\
										[data-fieldname ='add_comment']") 
		this.data_fieldname.hide();
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
					if(me.item == "Common"){
						for(i=0;i<r.message.length;i++){
							/*me.agreements.push({"name":r.message[i]['name'],
												"call_commitment":r.message[i]['call_commitment']})*/
							
							if(r.message[i]['call_commitment'] == "All"){
								me.values_of_agreement.push({"amount_of_contact_result":r.message[i]['amount_of_contact_result'],
																		"contact_result":r.message[i]['contact_result'],
																		"suspension_date":r.message[i]['suspension_date'],
																		"call_commitment":r.message[i]['call_commitment']	
																		});
							}
						}
						if(me.values_of_agreement.length > 0){
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
					}
					else{
						if(r.message[0]['contact_result'] && r.message[0]['contact_result'] == "WBI"){
							me.contact_result = r.message[0]['contact_result']
							me.suspension_date = r.message[0]['suspension_date']
							me.amount_of_contact_result = r.message[0]['amount_of_contact_result']
							me.set_values()
						}
						else if(r.message[0]['contact_result'] && r.message[0]['contact_result'] == "Sent SMS/Email"){
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
		$(me.dialog.body).find("[data-fieldname ='comment'],\
								[data-fieldname ='add_comment']").show();
		me.dialog.fields_dict.contact_result.set_input(me.contact_result)
		me.dialog.fields_dict.date_picker.set_input(me.suspension_date)
		me.add_comment();
	},
	set_values:function(){
		var me = this;
		me.data_fieldname.show();
		me.dialog.fields_dict.contact_result.set_input(me.contact_result)
		me.dialog.fields_dict.date_picker.set_input(me.suspension_date)
		me.dialog.fields_dict.amount.set_input(me.amount_of_contact_result)
		me.add_comment();
	},
	select_contact_result:function(){
		var me = this;
		nowdate = frappe.datetime.nowdate()
		$(me.fd.contact_result.input).change(function(){
			if(me.fd.contact_result.$input.val() == "WBI"){
				me.data_fieldname.show();
				me.dialog.fields_dict.amount.set_input(flt(me.item["total_dues"]).toFixed(2))
				me.add_comment();
			}
			if(me.fd.contact_result.$input.val() == "Sent SMS/Email"){
				console.log(me.item["current_due_date"],"current_due_date1232212")
				me.dialog.fields_dict.date_picker.set_input(nowdate)
				me.dialog.fields_dict.amount.set_input("")
				$(me.dialog.body).find("[data-fieldname ='date_picker'],[data-fieldname ='amount']").hide();
				$(me.dialog.body).find("[data-fieldname ='comment'],[data-fieldname ='add_comment']").show();
				me.add_comment();
			}
			if(me.fd.contact_result.$input.val() == ""){
				me.data_fieldname.hide();
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
			$.each($("#payments_grid").find(".slick-row"),function(i,d){
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
		me.dialog.fields_dict.add_comment.$input.click(function() {
			if(me.dialog.fields_dict.comment.$input.val()){
				cur_frm.set_value("notes_on_customer_payments", " "+"["+user+"] "+" "+"CC:"+" "+me.dialog.fields_dict.comment.$input.val()+" "+"("+me.item['id']+")")
				$('button[data-fieldname="add_notes"]').click();
				me.dialog.fields_dict.comment.set_input("");
			}
		})
	}
});