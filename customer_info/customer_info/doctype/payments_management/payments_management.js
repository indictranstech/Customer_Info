cur_frm.add_fetch('customer', 'receivable', 'receivables');
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
	customer:function(){
		if(cur_frm.doc.customer){
			render_agreements()
			calculate_total_charges()
		}
	},
	submit:function(){
		if(cur_frm.doc.customer){	
			var me = this;
			this.dialog = new frappe.ui.Dialog({
	            title: "Payments Detalis",
	                fields: [
	                   	{"fieldtype": "Data" , "fieldname": "amount_paid_by_customer" , "label": "Amount Paid By Customer"},
	                   	{"fieldtype": "Button" , "fieldname": "process_payment" , "label": "Process payment"},
	                   	{"fieldtype": "Button" , "fieldname": "add_in_receivables" , "label": "Add To Receivable"},
	                   	{"fieldtype": "Button" , "fieldname": "return_to_customer" , "label": "Give Change"},
	                   	{"fieldtype": "Column Break" , "fieldname": "column"},
	                   	{"fieldtype": "Data" , "fieldname": "balance" , "label": "Balance"},
	                   	],
	                   	primary_action_label: "OK",
	                   	primary_action: function(){
	                   		console.log(this,me,"in primary_action")
	                        update_payments_records()
	                        me.dialog.hide()
	                    }
	       	});
	       	this.fd = this.dialog.fields_dict;
	       	$(this.fd.amount_paid_by_customer.input).change(function(){
	       		var val_of_balance = parseFloat(cur_dialog.fields_dict.amount_paid_by_customer.$input.val()) - cur_frm.doc.total_charges
	       		console.log(val_of_balance,"val_of_balance")
	       		cur_dialog.fields_dict.balance.set_input(val_of_balance)
	       	})
	       	$('button[data-fieldname="add_in_receivables"]').css("display","none");
	       	$('button[data-fieldname="return_to_customer"]').css("display","none");
	       	this.dialog.show();
	       	me.dialog.fields_dict.process_payment.$input.click(function() {
	       		console.log(cur_dialog.fields_dict.balance.$input.val(),"balanceeeeee123")
	       		console.log(parseFloat(cur_dialog.fields_dict.balance.$input.val()) > 0 )
	       		if(parseFloat(cur_dialog.fields_dict.balance.$input.val()) > 0 ){
	       			console.log("in if")
	       			$('button[data-fieldname="add_in_receivables"]').removeAttr("style");
	       			$('button[data-fieldname="return_to_customer"]').removeAttr("style");
	       			msgprint(__("There Is {0} eur in balance Put It Into Receivables OR Give Change",[cur_dialog.fields_dict.balance.$input.val()]))
	       		}
	       		if(parseFloat(cur_dialog.fields_dict.balance.$input.val()) < 0 ){
	       			msgprint("Error Message Balance Is Negative")
	       		}
	       	})
	       	me.dialog.fields_dict.add_in_receivables.$input.click(function() {
				value = me.dialog.get_values();
				/*console.log(value.balance)*/
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
		            		msgprint("Receivables Added In Customer Record")
		            	}
		        	}
			    });	
			})
		}
		else{
			msgprint("Select Customer First")
		}
	}
})


update_payments_records = function(){
	frappe.call({
		async:false,    
        method: "customer_info.customer_info.doctype.payments_management.payments_management.update_payments_child_table_of_customer_agreement_on_submit",
       	args: {
        	"payment_date":cur_frm.doc.payment_date,
        	"customer":cur_frm.doc.customer
        },
       	callback: function(r){
       		console.log(r.message)
       		cur_frm.doc.total_charges = cur_frm.doc.amount_of_due_payments - cur_frm.doc.receivables
        	refresh_field("total_charges")
        	msgprint(__("Payments Summary Successfully Updated Against All Above Customer Agreement"))
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
				return "<input type='button' value = 'Suspenison' id= "+id+" class='suspenison' style='height:20px;padding: 0px;width: 70px;'; />";		
			}
	}

		var columns = [
	    {id: "serial", name: "#", field: "serial", cssClass: "cell-selection", width: 20, resizable: false, selectable: false, focusable: false },
	    {id: "agreement_no", name: "Agreement No", field: "agreement_no",width: 90},
	    {id: "agreement_period", name: "Agreement Period", field: "agreement_period",width: 80},
	    {id: "product", name: "Product", field: "product",width: 100},
	    {id: "number_of_payments", name: "# of Payments", field: "number_of_payments",width: 90},
	    {id: "monthly_rental_payment", name: "Rental Payments", field: "monthly_rental_payment",width: 90},
	    {id: "current_due_date", name: "Current Due Date", field: "current_due_date",width: 90},
	    {id: "next_due_date", name: "Next Due Date", field: "next_due_date",width: 90},
	    {id: "payments_left", name: "Payments left", field: "payments_left",width: 90},
	    {id: "balance", name: "Balance", field: "balance",width: 70},
	    {id: "late_fees", name: "Late Fees", field: "late_fees",width: 50},
	    {id: "total_dues", name: "Total Dues", field: "total_dues",width: 50},
	    {id: "detail", name: "Detail", field: "detail",formatter: buttonFormat_detail},
	    {id: "suspenison", name: "Suspenison", field: "suspenison",formatter: buttonFormat_suspension}
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
            suspenison: data1.list_of_agreement[i][11]
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
            var me = this;            
        	new Payments_Details(item)
        }
        if($(e.target).hasClass("suspenison")) {
        	console.log("in mybutton",$(e.target).attr('id'))
        	var id = $(e.target).attr('id')
        	get_datepicker(id,item)
        }
    });
}


get_datepicker = function(id,item){
	var me  = this;
	this.dialog = new frappe.ui.Dialog({
            		title: "Pick A Date",
                	fields: [
                   		{"fieldtype": "Date" , "fieldname": "date_picker" , "label": "Date"},
                   	],
                   	primary_action_label: "OK",
                   	primary_action: function(){
                   		var dialog = this.dialog;
                        change_name_of_buttom(id,this.fd,item,dialog)
                    }
		       	});
		       	this.fd = this.dialog.fields_dict;
		       	this.dialog.$wrapper.find('.modal-dialog').css("width", "300px");
		       	this.dialog.$wrapper.find('.modal-dialog').css("height", "300px");
		       	this.dialog.$wrapper.find('.hidden-xs').css("display","none");
		       	this.dialog.show();
}

change_name_of_buttom = function(id,fd,item,dialog){
	id = "#" + id
	date = fd.date_picker.$input.val()
	if(date){
		$(id).attr('value', date);
		update_suspenison_date_in_agreement(item,date)
		dialog.hide();
	}
	else{
		msgprint("Please Select Date")
	}
}

update_suspenison_date_in_agreement = function(item,date){
	frappe.call({
            method: "customer_info.customer_info.doctype.payments_management.payments_management.update_suspenison_date_in_agreement",
            args: {
              "customer_agreement": item['id'],
              "date":date
            },
            callback: function(r){
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
              	cur_frm.doc.amount_of_due_payments = r.message['sum']
              	cur_frm.doc.receivables = r.message['receivable']
	           	cur_frm.doc.total_charges = r.message['sum'] - cur_frm.doc.receivables
	           	refresh_field(['amount_of_due_payments','total_charges','receivables'])
            }
            else{
            	cur_frm.doc.total_charges = 0.0
	           	refresh_field('total_charges')	
            }
        }
    });
}

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
                   	{"fieldtype": "HTML" , "fieldname": "payments_record" , "label": "Relative Items"},
                   	],
                   	primary_action_label: "OK",
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
	            	   			/*me.payments_record_list[0][i]['pre_select'] = 1*/
	            	   			break;
	            	   		}
	            	   	}
	            	   	console.log(me.payments_record_list,"after pre_select")
	            	   	html = $(frappe.render_template("payments_management",{
	            	   				"post":me.payments_record_list,
	            	   				"payment_date":cur_frm.doc.payment_date
	            	   			})).appendTo(me.fd.payments_record.wrapper);
	            		me.dialog.show();
	            		me.increase_decrease_total_charges_and_due_payment();
	            	}  
	        	}
	        });
		}
	},
	make_list_of_payments_checked:function(){
		this.row_to_update = []
		this.row_to_check = []
		this.row_to_uncheck = []
		var me = this;
        $.each($(this.fd.payments_record.wrapper).find('.select:checked[data-from=""]'), function(name, item){
                me.row_to_update.push($(item).val());
        });
        $.each($(this.fd.payments_record.wrapper).find('.new-entry'), function(name, item){
    		if($(this).is(':checked')){
    			me.row_to_check.push($(item).val())
    		}
    		if($(this).is(':not(:checked)')){
    			me.row_to_uncheck.push($(item).val())
    		}
        });
        console.log(me.row_to_update,"row_to_update")
        console.log(me.row_to_uncheck,"row_to_uncheck")
        console.log(me.row_to_check,"row_to_check")
		if(me.row_to_update.length > 0 || me.row_to_uncheck.length > 0 || me.row_to_check.length > 0){
			var me = this
			// for filter duplicate from array
			/*array1 = array1.filter(function(val) {
  				return array2.indexOf(val) == -1;
			});*/

			/*me.checked_row_from_child_table = me.checked_row_from_child_table.filter(function(val) {
  				return me.row_to_uncheck.indexOf(val) == -1;
			});
			console.log(me.checked_row_from_child_table,"after filter")*/
	   		frappe.call({    
		        method: "customer_info.customer_info.doctype.payments_management.payments_management.temporary_payments_update_to_child_table_of_customer_agreement",
		        async: false,
	           	args: {
	           		"row_to_update":me.row_to_update,
	           		"row_to_uncheck":me.row_to_uncheck,
	           		"row_to_check":me.row_to_check,
	           		"parent":this.item['id'],
	           		"payment_date":cur_frm.doc.payment_date
	            },
	           	callback: function(res){
	        		render_agreements()
	            	me.update_total_charges_and_due_payments()
	        		me.hide_dialog()
	        	}
	        });
	    }
	},
	increase_decrease_total_charges_and_due_payment:function(){
		var me = this
        var factor = this.payments_record_list[0][1].monthly_rental_amount;		
		$(this.fd.payments_record.wrapper).find('div.due_payments').append((cur_frm.doc.amount_of_due_payments).toFixed(2))
		$(this.fd.payments_record.wrapper).find('div.total_charges').append((cur_frm.doc.total_charges).toFixed(2))
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
		cur_frm.set_value("total_charges",parseFloat($(cur_dialog.body).find('div.total_charges').text()))
		cur_frm.set_value("amount_of_due_payments",parseFloat($(cur_dialog.body).find('div.due_payments').text()))
	}	
})
