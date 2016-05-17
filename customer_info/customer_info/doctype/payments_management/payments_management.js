frappe.require("assets/customer_info/js/slick/lib/firebugx.js");
frappe.require("assets/customer_info/js/slick/plugins/slick.cellrangedecorator.js");
frappe.require("assets/customer_info/js/slick/plugins/slick.cellrangeselector.js");
frappe.require("assets/customer_info/js/slick/plugins/slick.cellselectionmodel.js");



frappe.require("assets/customer_info/js/slick/slick.formatters.js");
frappe.require("assets/customer_info/js/slick/slick.editors.js");
frappe.require("assets/customer_info/js/slick/slick.grid.js");
frappe.require("assets/customer_info/js/slick/slick.core.js");



frappe.require("assets/customer_info/js/slick/slick.groupitemmetadataprovider.js");
frappe.require("assets/customer_info/js/slick/slick.dataview.js");
frappe.require("assets/customer_info/js/slick/controls/slick.pager.js");
frappe.require("assets/customer_info/js/slick/controls/slick.columnpicker.js");

frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.checkboxselectcolumn.js");
frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.rowselectionmodel.js");
frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.autotooltips.js");
frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.cellcopymanager.js");
frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.cellexternalcopymanager.js");
frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.rowselectionmodel.js");

var list_of_row_to_update_on_submit = [];
frappe.ui.form.on("Payments Management", {
	refresh: function(frm) {
		frm.disable_save();
	},
	onload:function(frm){
		$(cur_frm.fields_dict.payments_grid.wrapper).empty()
		$(cur_frm.fields_dict.payments_grid.wrapper).append("<table width='100%>\
  		<tr>\
		    <td valign='top' width='100%'>\
		      <div id='payments_grid' style='width:100%;height:200px;''></div>\
		    	</td>\
  			</tr>\
		</table>");
	},
	amount_paid_by_customer:function(frm){
		if(cur_frm.doc.amount_paid_by_customer){
			cur_frm.doc.remaining_amount = cur_frm.doc.amount_paid_by_customer
			refresh_field('remaining_amount')
		}
	},
	get_entries: function() {
		render_agreements()
	},
	submit:function(){
		/*console.log(list_of_row_to_update_on_submit,"list_of_row_to_update_on_submit")*/
		frappe.call({    
	        method: "customer_info.customer_info.doctype.payments_management.payments_management.update_payments_child_table_of_customer_agreement_on_submit",
           	args: {
           		/*"list_of_row_to_update_on_submit":list_of_row_to_update_on_submit,*/
            	"payment_date":cur_frm.doc.payment_date,
            	"customer":cur_frm.doc.customer
            },
           	callback: function(r){
           		console.log(r.message)
            	msgprint(__("Payments Summary Successfully Updated Against All Above Customer Agreement"))
            	/*if(r.message == "SuccesFully Update"){
            		list_of_row_to_update_on_submit = []
            	}*/
        	}
	    });
	}
})

render_agreements = function(){
	list_of_row_to_update_on_submit = [];
	var grid;

	var buttonFormat = function (row, cell, value, columnDef, dataContext) {
		return "<input type='button' value='Detail' class='btn' style='height:20px;padding: 0px;width: 82px;'; />";    
	}

		var columns = [
	    {id: "serial", name: "#", field: "serial", cssClass: "cell-selection", width: 40, resizable: false, selectable: false, focusable: false },
	    {id: "agreement_no", name: "Agreement No", field: "agreement_no",width: 150},
	    {id: "agreement_period", name: "Agreement Period", field: "agreement_period",width: 150},
	    {id: "product", name: "Product", field: "product",width: 150},
	    {id: "number_of_payments", name: "# of Payments", field: "number_of_payments",width: 150},
	    {id: "monthly_rental_payment", name: "Rental Payments", field: "monthly_rental_payment",width: 150},
	    {id: "current_due_date", name: "Current Due Date", field: "current_due_date",width: 150},
	    {id: "next_due_date", name: "Next Due Date", field: "next_due_date",width: 150},
	    {id: "payments_left", name: "Payments left", field: "payments_left",width: 150},
	    {id: "balance", name: "Balance", field: "balance",width: 150},
	    {id: "late_fees", name: "Late Fees", field: "late_fees",width: 150},
	    {id: "total_dues", name: "Total Dues", field: "total_dues",width: 150},
	    {id: "detail", name: "Detail", field: "detail",formatter: buttonFormat,width: 100}
  	];
  	var options = {
    	enableCellNavigation: true,
    	enableColumnReorder: false
  	};
  	var data = [];
  	frappe.call({
            method: "customer_info.customer_info.doctype.payments_management.payments_management.get_customer_agreement",
            type: "GET",
            async: false,
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
	for (var i = 0; i<data1.list_of_agreement.length; i++) {
          	data[i] = {
          	id : data1.list_of_agreement[i][0],	
          	serial:i,	
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
        };
    }

    dataView = new Slick.Data.DataView();    
    dataView.beginUpdate();
    dataView.setItems(data);
    dataView.endUpdate();

	grid = new Slick.Grid("#payments_grid", dataView, columns, options);
	grid.onClick.subscribe(function (e, args) {
        if ($(e.target).hasClass("btn")) {
            var item = dataView.getItem(args.row);
            var me = this;            
        	new Payments_Details(item)
        }
    });
}


/*	{"fieldtype": "Button", "label": __("Get"), "fieldname": "get"},
							]
					});

					dialog.fields_dict.get.$input.click(function() {
						value = dialog.get_values();*/


Payments_Details = Class.extend({
	init:function(item){
		this.item = item;
		/*this.update_payments_records_on_submit = {};*/
		this.init_for_render_dialog();
	},
	init_for_render_dialog:function(){
		console.log(this.item)
		console.log(this,"in init_for_render_dialog")
		var me = this;
		this.dialog = new frappe.ui.Dialog({
            title: "Payments Detalis",
                fields: [
                	/*{"fieldtype": "float" , "fieldname": "amount" , "label": "Amount Paid By Customer"},*/
                   	{"fieldtype": "HTML" , "fieldname": "payments_record" , "label": "Relative Items"},
                   	],
                   	primary_action_label: "OK",
                   	primary_action: function(){
                   		console.log(this,me,"in primary_action")
                        me.make_list_of_payments_checked()
                        /*me.hide_dialog()*/
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
		if(this.item['id']){
			frappe.call({    
		        method: "customer_info.customer_info.doctype.payments_management.payments_management.get_payments_record",
		        async: false,
	           	args: {
	           		"customer_agreement":this.item['id']
	            },
	           	callback: function(res){
	            	if(res && res.message){
	            		console.log(res.message)
	            	   	console.log(this,"this of callback")
	            		$.each(res.message, function(i, d) {
	            	   		me.payments_record_list.push(d)
	            	   	});
	            	   	console.log(me.payments_record_list,"payments_record_listtttttttttt")
	            	   	console.log(me.row_to_update,"in render r message")
	            	   	html = $(frappe.render_template("payments_management",{"post":me.payments_record_list,
	            	   									"payment_date":cur_frm.doc.payment_date
	            	   									})).appendTo(me.fd.payments_record.wrapper);
	            		me.dialog.show();
	            		me.increase_decrease_remaining_amount()
	            	}  
	        	}
	        });
		}
	},
	make_list_of_payments_checked:function(){
		this.row_to_update = []
		this.row_to_uncheck = []
		var me = this;
        $.each($(this.fd.payments_record.wrapper).find('.select:checked[data-from=""]'), function(name, item){
                me.row_to_update.push($(item).val());
        });
		$.each($(this.fd.payments_record.wrapper).find('.new-entry'), function(name, item){
            console.log($(this),"$$$$$$thisssssssssss")
    		if($(this).is(':not(:checked)')){
    			me.row_to_uncheck.push($(item).val())
    		}
        });
		console.log(this.row_to_update,"row_to_update")
		console.log(this.row_to_uncheck,"row_to_uncheck")
		if(me.check_amount() == "true" || me.row_to_uncheck.length > 0){
	   		/*me.update_payments_records_on_submit = {
        	'parent':me.item['id'],
        	'list_of_payment_id':me.row_to_update
        	}
        	list_of_row_to_update_on_submit.push(me.update_payments_records_on_submit)
	        console.log(me.update_payments_records_on_submit,"update_payments_records_on_submit")
	        console.log(list_of_row_to_update_on_submit,"list_of_row_to_update_on_submit")*/
	   		frappe.call({    
		        method: "customer_info.customer_info.doctype.payments_management.payments_management.temporary_payments_update_to_child_table_of_customer_agreement",
		        async: false,
	           	args: {
	           		"row_to_update":me.row_to_update,
	           		"row_to_uncheck":me.row_to_uncheck,
	           		"parent":this.item['id'],
	           		"payment_date":cur_frm.doc.payment_date
	            },
	           	callback: function(res){
	        		render_agreements()
	        		me.hide_dialog()
	            	if(res && res.message){		
	            	}
	        	}
	        });
	    }    
	},
	check_amount:function(){
		if(this.row_to_update.length > 0){
			console.log(this.row_to_update,"row_to_update")
			console.log(this.initial_amount,"initial_amount")
			var subtract = this.row_to_update.length * this.payments_record_list[0][1].monthly_rental_amount
			var remain = cur_frm.doc.remaining_amount - subtract.toFixed(2)
			if(cur_frm.doc.remaining_amount >= subtract){
				console.log(remain,"remain")
				cur_frm.set_value("remaining_amount",parseFloat(remain))
				return "true"
			}
			else{
				msgprint(__("Remaining Amount Less Than Monthly Rental Amount"))
			}
		}
	},
	increase_decrease_remaining_amount:function(){
		console.log(this.payments_record_list[0][1].monthly_rental_amount,"this")
		console.log("in increase_decrease_remaining_amount")
        var factor = this.payments_record_list[0][1].monthly_rental_amount;
		var me = this
		console.log(me.initial_amount,"above if")
		$(this.fd.payments_record.wrapper).find('div.amount').append(me.initial_amount.toFixed(2))
		$('input[data-from=""]').change(function() {  
		    var selectedval = ($(this).val());
		    if ($(this).is(':checked')){
				var decrease = me.initial_amount - parseFloat(factor).toFixed(2)
				console.log(decrease,"decrease")
				console.log(me.initial_amount,"initial_amount")
				if(me.initial_amount >= decrease && decrease > 0){
					me.initial_amount = decrease
					$(cur_dialog.body).find('div.amount').empty()
					$(cur_dialog.body).find('div.amount').append(me.initial_amount.toFixed(2))
					$('input[data-from=""]').removeClass("un-paid")
					$('input[data-from=""]').addClass("paid")
				}
				else{
					$(this).attr('checked', false);
					msgprint(__("Remaining Amount Less Than Monthly Rental Amount"))
				}
    		} 
    		else {
				var increase = me.initial_amount + parseFloat(parseFloat(factor).toFixed(2))
				if(me.initial_amount < increase){
					me.initial_amount = increase
					$(cur_dialog.body).find('div.amount').empty()
					$(cur_dialog.body).find('div.amount').append(me.initial_amount.toFixed(2))
					$('input[data-from=""]').removeClass("paid")
					$('input[data-from=""]').addClass("un-paid")
				}
    		}
		});
	}	
})
