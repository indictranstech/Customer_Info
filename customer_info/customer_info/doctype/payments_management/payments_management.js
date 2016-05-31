cur_frm.add_fetch('customer', 'receivable', 'receivable');
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
		if(cur_frm.doc.customer){
			render_agreements()
			calculate_total_charges()
		}
	},
	/*amount_paid_by_customer:function(frm){
		if(cur_frm.doc.amount_paid_by_customer){
			cur_frm.doc.remaining_amount = cur_frm.doc.amount_paid_by_customer
			refresh_field('remaining_amount')
		}
	},*/
	customer:function(){
		if(cur_frm.doc.customer){
			render_agreements()
			calculate_total_charges()
		}
	},
	/*get_entries: function() {
		render_agreements()
		calculate_total_charges()
	},*/
	submit:function(){
		/*console.log(list_of_row_to_update_on_submit,"list_of_row_to_update_on_submit")*/
		frappe.call({
			async:false,    
	        method: "customer_info.customer_info.doctype.payments_management.payments_management.update_payments_child_table_of_customer_agreement_on_submit",
           	args: {
           		/*"list_of_row_to_update_on_submit":list_of_row_to_update_on_submit,*/
            	"payment_date":cur_frm.doc.payment_date,
            	"customer":cur_frm.doc.customer
            },
           	callback: function(r){
           		console.log(r.message)
            	msgprint(__("Payments Summary Successfully Updated Against All Above Customer Agreement"))
            	add_receivables_in_customer()
            	/*cur_frm.doc.receivables = cur_frm.doc.remaining_amount
            	refresh_field('receivables')*/
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


calculate_total_charges = function(frm){
	frappe.call({
            method: "customer_info.customer_info.doctype.payments_management.payments_management.calculate_total_charges",
            args: {
              "customer": cur_frm.doc.customer
            },
            callback: function(r){
            if(r.message){
              	console.log(r.message)
	           	cur_frm.doc.total_charges = r.message - cur_frm.doc.receivable
	           	refresh_field('total_charges')
            }
            else{
            	cur_frm.doc.total_charges = 0.0
	           	refresh_field('total_charges')	
            }
        }
    });
}


add_receivables_in_customer = function(frm){
	frappe.call({
            method: "customer_info.customer_info.doctype.payments_management.payments_management.add_receivables_in_customer",
            async:false,
            args: {
              "customer": cur_frm.doc.customer,
              "receivables":cur_frm.doc.receivables
            },
            callback: function(r){
              if(r.message){
              	/*var due_payment = 0
            	$.each(r.message, function(i, d) {
	           		due_payment = due_payment + parseFloat(d.monthly_rental_amount)
	           	});
	           	cur_frm.doc.total_charges = due_payment - cur_frm.doc.receivables
	           	refresh_field('total_charges')*/
            }
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
	            		$.each(res.message, function(i, d) {
	            	   		me.payments_record_list.push(d)
	            	   	});
	            	   	console.log(me.payments_record_list,"payments_record_listtttttttttt")
	            	   	console.log(me.row_to_update,"in render r message")
	            	   	for(i=0;i < me.payments_record_list[0].length; i++){
	            	   		if(me.payments_record_list[0][i]['check_box'] == 0){
	            	   			me.payments_record_list[0][i]['check_box'] = 1
	            	   			break;
	            	   		}
	            	   	}
	            	   	/*html = "<div  class='row'>\
								    <div class='col-xs-3'>Remaining Amount</div>\
								    <div class='col-xs-3 amount'></div>\
								    <div class='col-xs-3'></div>\
								</div><br>\
	            	   			<table class='table table-bordered table-condensed' id='header-fixed'>\
							   	<thead>\
							      <tr>\
							        <td align='center' style='width:25%;'><b>Payments</b></td>\
							        <td align='center' style='width:24%;'><b>Monthly Rental Amount</b></td>\
						            <td align='center' style='width:24%;'><b>Due Date</b></td>\
							        <td align='center' style='width:27%;'><b>Payment Date</b></td>\
							      </tr>\
							    </thead>"

	            	   	$(me.fd.payments_record.$wrapper).append(html)
	            	   	$(me.fd.payments_record.$wrapper).append(frappe.render_template("payments_management",{"post":me.payments_record_list,
	            	   									"payment_date":cur_frm.doc.payment_date
	            	   									}));*/

	            	   	html = $(frappe.render_template("payments_management",{
	            	   				"post":me.payments_record_list,
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
    		if($(this).is(':not(:checked)')){
    			me.row_to_uncheck.push($(item).val())
    		}
        });
		if(me.row_to_update.length > 0 || me.row_to_uncheck.length > 0 || me.checked_row_from_child_table.length > 0){
			var me = this
		/*if(me.check_amount() == "true" || me.row_to_uncheck.length > 0){*/
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
	           		"checked_row_from_child_table":me.checked_row_from_child_table,
	           		"parent":this.item['id'],
	           		"payment_date":cur_frm.doc.payment_date
	            },
	           	callback: function(res){
	        		render_agreements()
	            	cur_frm.doc.remaining_amount = parseFloat($(cur_dialog.body).find('div.amount').text())
	            	cur_frm.doc.receivables = cur_frm.doc.remaining_amount
	            	refresh_field(["remaining_amount","receivables"])
	        		me.hide_dialog()
	            	/*if(res && res.message){				
	            	}*/
	        	}
	        });
	    }    
	},
	increase_decrease_remaining_amount:function(){
		var me = this
		this.checked_row_from_child_table = []
        $.each($(this.fd.payments_record.wrapper).find('input[data-from="from_child_table"]'), function(name, item){
    		if($(this).is(':checked')){
    			me.checked_row_from_child_table.push($(item).val())
    		}
        });
        /*console.log($(this.fd.payments_record.wrapper).find('#monthly_rental_amount').text(),"monthly_rental_amount")*/
        console.log(me.checked_row_from_child_table,"checked_row_from_child_table")
        var factor = this.payments_record_list[0][1].monthly_rental_amount;
		var minus = parseFloat(factor)*me.checked_row_from_child_table.length
		console.log(typeof(minus),"aaaaaaaaaaaaaaaaa")
		me.initial_amount = me.initial_amount - minus;
		$(this.fd.payments_record.wrapper).find('div.amount').append(me.initial_amount.toFixed(2))
		$(this.fd.payments_record.wrapper).find('div.initial_amount').append(cur_frm.doc.remaining_amount)
		$('input[data-from=""]').change(function() {  
		    var selectedval = ($(this).val());
		    if ($(this).is(':checked')){
				var decrease = me.initial_amount - parseFloat(factor).toFixed(2)
				if(me.initial_amount >= decrease && decrease > 0){
					me.initial_amount = decrease
					$(cur_dialog.body).find('div.amount').empty()
					$(cur_dialog.body).find('div.amount').append(me.initial_amount.toFixed(2))
					/*$('input[data-from=""]').removeClass("un-paid")
					$('input[data-from=""]').addClass("paid")*/
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
					/*$('input[data-from=""]').removeClass("paid")
					$('input[data-from=""]').addClass("un-paid")*/
				}
    		}
		});
		$('input[data-from="from_child_table"]').change(function() {  
		    var selectedval = ($(this).val());
		    if ($(this).is(':checked')){
				var decrease = me.initial_amount - parseFloat(factor).toFixed(2)
				if(me.initial_amount >= decrease && decrease > 0){
					me.initial_amount = decrease
					$(cur_dialog.body).find('div.amount').empty()
					$(cur_dialog.body).find('div.amount').append(me.initial_amount.toFixed(2))
					/*$('input[data-from=""]').removeClass("un-paid")
					$('input[data-from=""]').addClass("paid")*/
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
					/*$('input[data-from=""]').removeClass("paid")
					$('input[data-from=""]').addClass("un-paid")*/
				}
    		}
		});
	}	
})
