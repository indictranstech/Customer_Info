// Copyright (c) 2013, indictrans and contributors
// For license information, please see license.txt
frappe.query_reports["Payments Received"] = {
	"filters": [
		// {
		// 	"fieldname":"customer",
		// 	"label": __("Customer"),
		// 	"fieldtype": "Link",
		// 	"options": "Customer",
		// 	"width": "80"
		// },
		// {
		// 	"fieldname":"from_date",
		// 	"label": __("From Date"),
		// 	"fieldtype": "Date",
		// 	"width": "80"
		// },
		// {
		// 	"fieldname":"to_date",
		// 	"label": __("To Date"),
		// 	"fieldtype": "Date",
		// 	"width": "80"
		// }
	],
	"formatter":function (row, cell, value, columnDef, dataContext, default_formatter) {
        value = default_formatter(row, cell, value, columnDef, dataContext);
	    if (columnDef.id == "Refund") {
	    	var ph_name = JSON.stringify(value)
            value = "<button type='button' class='refund' onclick='click_on_refund("+ph_name+")' style='height:20px;padding: 0px;width: 70px;';>Refund</button>";
	    }
	    return value;
	}
}


click_on_refund = function(ph_name){
	console.log("in click_on_refund")	
	console.log(ph_name)
	frappe.call({    
        method: "frappe.client.get_list",
           args: {
               doctype: "Payments History",
               fields: ["payments_ids"],
               filters: { 'name':ph_name },
           },
       	callback: function(res){
        	if(res && res.message){
        		console.log(res.message,"res.messagevvdfffdbd")
        		var payments_info = []
        		var payments_list_of_dict = []
        		var flt_precision = frappe.defaults.get_default("float_precision")
        		var payments_details = res.message[0]
        		var string = payments_details["payments_ids"].slice(0,-1) + '"'
        		var array = JSON.parse("[" + string + "]");
        		$.each(array[0].split(","), function(i, d) {
        			payments_info.push(d.split("/"))
        			console.log(d.split("/"),"Alternate Items")
        	   	});
        	   	$.each(payments_info, function(i, d) {
        			payments_list_of_dict.push({"payments_id":d[0],
        				"due_date":d[1],
        				"rental_payment":d[2],
        				"late_fees":Number((get_late_fees(d[1],d[3],d[2])).toFixed(flt_precision)),
        				"total": Number((get_late_fees(d[1],d[3],d[2]) + flt(d[2])).toFixed(flt_precision)) 
        	   		});
        	   	});	
        		console.log(payments_list_of_dict,"payments_list_of_dict")	
        		show_dialog(payments_list_of_dict,ph_name);
        	}
        }	
    });
}	

show_dialog = function(payments_list_of_dict,ph_name){
	this.dialog = new frappe.ui.Dialog({
        		title: "Payment Details",
            	fields: [                   		
               		{"fieldtype": "HTML" , "fieldname": "payment_details"},
               		{"fieldtype": "Button" , "fieldname": "refund" , "label": "Refund"},
               	]
       		});
		this.fd = this.dialog.fields_dict;
		html = "<table class='table' id='tr-table'><thead><tr class='row'>\
		<td align='center'><b>Payment Ids</b></td>\
		<td align='center'><b>Due Date</b></td>\
		<td align='center'><b>Rental Payment</b></td>\
		<td align='center'><b>Late Fees</b></td>\
		<td align='center'><b>Total</b></td></tr></thead>"
		for(var s=0, ls=payments_list_of_dict.length; s < ls; s++){						
			html +=	 "<tr class='row'>"
			if(payments_list_of_dict[s]["payments_id"]) {
				html += "<td align='center'>"+payments_list_of_dict[s]["payments_id"]+"</td>"
			}
			if(payments_list_of_dict[s]["due_date"]) {
				html += "<td align='center'>"+payments_list_of_dict[s]["due_date"]+"</input></td>"
			}
			if(payments_list_of_dict[s]["rental_payment"]) {
				html += "<td align='center'>"+payments_list_of_dict[s]["rental_payment"]+"</td>"
			}
			if(payments_list_of_dict[s]["late_fees"]) {
				html += "<td align='center'>"+payments_list_of_dict[s]["late_fees"]+"</td>"
			}
			else if(!payments_list_of_dict[s]["late_fees"]){
				html += "<td align='center'>0.00</td>"						
			}
			if(payments_list_of_dict[s]["total"]) {
				html += "<td align='center'>"+payments_list_of_dict[s]["total"]+"</td>"
			}	
		}
	html += "</tr></tbody></table>"
    $(this.fd.payment_details.$wrapper).append(html)
    this.dialog.show();
    dialog_refund(ph_name,this.fd,payments_list_of_dict);
}

dialog_refund =function(ph_name,fd,payments_list_of_dict){
	fd.refund.$input.click(function() {
		console.log("in primary_action 123423123")	
		frappe.call({
	        method: "customer_info.customer_info.doctype.payments_management.payments_management.make_refund_payment",
           	args: {
           		"payments_ids":payments_list_of_dict,
            	"ph_name":ph_name
            },
	       	callback: function(r){
	    		cur_dialog.hide();
	    		frappe.query_report.refresh();
	    	}
    	});
	});
}

get_late_fees = function(date1,date2,rental_payment){
	if(flt(get_late_days(date1,date2)) > 3){
		return flt(get_late_days(date1,date2)) * rental_payment * 0.02	
	}
	else{
		return 0
	}	
}


get_late_days = function(date1,date2){
	var date1 = date1;
	var date2 = date2;

	// First we split the values to arrays date1[0] is the year, [1] the month and [2] the day
	date1 = date1.split('-');
	date2 = date2.split('-');

	// Now we convert the array to a Date object, which has several helpful methods
	date1 = new Date(date1[0], date1[1], date1[2]);
	date2 = new Date(date2[0], date2[1], date2[2]);

	// We use the getTime() method and get the unixtime (in milliseconds, but we want seconds, therefore we divide it through 1000)
	date1_unixtime = parseInt(date1.getTime() / 1000);
	date2_unixtime = parseInt(date2.getTime() / 1000);

	// This is the calculated difference in seconds
	var timeDifference = date2_unixtime - date1_unixtime;

	// in Hours
	var timeDifferenceInHours = timeDifference / 60 / 60;

	// and finaly, in days :)
	var timeDifferenceInDays = timeDifferenceInHours  / 24;
	console.log(timeDifferenceInDays,"timeDifferenceInDays")
	return timeDifferenceInDays
}