/*frappe.pages['payments-received'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Payments Received',
		single_column: true
	});
}
*/
frappe.pages['payments-received'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Payments Received',
		single_column: true
	});
	wrapper.payments_received = new payments_received(wrapper)
	frappe.breadcrumbs.add("Customer Info");
}

payments_received = Class.extend({
	init: function(wrapper) {
		var me = this;
		this.wrapper_page = wrapper.page;
		this.page = $(wrapper).find('.layout-main-section-wrapper');
		this.wrapper = $(wrapper).find('.page-content');
		export_btn: wrapper.page.set_secondary_action(__("Export"),
		function() { 
					me.get_data_export();
				}, "icon-refresh");
		this.set_fields();
		this.render_payments_details();
	},
	set_fields: function() {
		var me = this;
		html = "<div>\
				<div class='col-xs-2 customer'></div>\
				<div class='col-xs-2 from_date'></div>\
  				<div class='col-xs-2 to_date'></div>\
  				<div class='col-xs-6'></div>\
  				</div>\
				<table id='tableSearchResults' class='table table-hover  table-striped table-condensed' style='font-size:12px;margin-bottom: 0px;'>\
			     	<thead>\
			            <tr>\
			                <th width='10%'>Payment Date</th>\
			                <th width='7%'>Customer</th>\
			                <th width='9%'>Rental Payment</th>\
			                <th width='7%'>Late Fees</th>\
			                <th width='7%'>Receivables</th>\
			                <th width='13%'>Total Rental Received</th>\
			                <th width='12%'>Bank Transfer</th>\
			                <th width='6%'>Cash</th>\
			                <th width='7%'>Bank Card</th>\
			                <th width='6%'>Balance</th>\
			                <th width='5%'>Discount</th>\
			                <th width='5%'>Bonus</th>\
			                <th width='5%'>Refund</th>\
			            </tr>\
			        </thead></table>"
		me.page.html(html)
		me.customer_link = frappe.ui.form.make_control({
			parent: me.page.find(".customer"),
			df: {
			fieldtype: "Link",
			options: "Customer",
			fieldname: "customer",
			placeholder: "Select Customer"
			},
			render_input: true
		});
		me.customer_link.refresh();
		me.from_date = frappe.ui.form.make_control({
			parent: me.page.find(".from_date"),
			df: {
				fieldtype: "Date",
				fieldname: "from_date",
				placeholder: "From Date"
			},
			render_input: true
		});
		me.from_date.refresh();
		me.to_date = frappe.ui.form.make_control({
			parent: me.page.find(".to_date"),
			df: {
				fieldtype: "Date",
				fieldname: "to_date",
				placeholder: "To Date"
			},
			render_input: true
		});
		me.to_date.refresh();

		me.customer_link.$input.on("change", function(){
			var old_me = me;
			console.log(old_me,"meeeeeeee")
			old_me.render_payments_details()
		});

		me.from_date.$input.on("change", function(){
			var old_me = me;
			console.log(old_me,"meeeeeeee")
			old_me.render_payments_details()
		});

		me.to_date.$input.on("change", function(){
			var old_me = me;
			console.log(old_me,"meeeeeeee")
			old_me.render_payments_details()
		});
				
	},
	render_payments_details: function() {
		var me = this;
		this.data = ""
		frappe.call({
			method: "customer_info.customer_info.page.payments_received.payments_received.get_payments_details",
			args: {
				"customer": me.customer_link.$input.val(),
				"from_date": me.from_date.$input.val(),
				"to_date":me.to_date.$input.val(),
			},
			freeze: true,
			freeze_message: __("Please Wait..."),
			callback: function(r) {
				console.log(r.message,"data data")
        	   	me.page.find(".data").empty();
				$.each(r.message, function(i, d) {
					/*console.log(d["refund"])*/
        	   		/*d["only_payment_ids_list"] = update_dict_by_payment_ids(d["payments_ids"],d["refund"])["only_payment_ids_list"]*/
					d["payments_ids"] = update_dict_by_payment_ids(d["payments_ids"],d["refund"])["payments_list_of_dict"]
        	   	});
        	   	console.log(r.message,"r.messagesssssssssssssssss")
        	   	me.data = r.message;
        	   	html = frappe.render_template("payments_received",{"data": r.message})
				me.page.append(html)
				me.refund();
			}
		})
	},
	refund:function(){
		var me = this;
		console.log($(me.page),"me inside refund refund")
		$(me.page).find(".refund").click(function() {
			me.show_dialog();
			console.log($(this).attr("ph-name"))
			console.log($(this).attr("payments-ids"),"pa")
		});
	},
	show_dialog:function(){
		var me = this;
		this.dialog = new frappe.ui.Dialog({
            		title: "Refund Process",
                	fields: [
                   		{"fieldtype": "Select" , "fieldname": "refund" , "label": "Do You Want To Refund","options":["","Yes","No"]},
                   		{"fieldtype": "Button" , "fieldname": "refund_payment" , "label": "Refund"}
                   	],
                   	/*primary_action_label: "Refund",
                   	primary_action: function(){
                        me.make_refund_payment()
                    }*/
	       		});
       	this.fd = this.dialog.fields_dict;
       	this.dialog.$wrapper.find('.modal-dialog').css("width", "350px");
       	this.dialog.$wrapper.find('.modal-dialog').css("height", "300px");
       	this.dialog.$wrapper.find('.hidden-xs').css("margin-left","-2px");
       	this.dialog.show();
       	me.click_on_refund_inside_dialog();
	},
	click_on_refund_inside_dialog:function(){
		var me = this;
		me.fd.refund_payment.$input.click(function() {
			console.log("inside refund_payment")
			me.make_refund_payment()
		})	
	},
	make_refund_payment:function(){
		var me = this;
		if(me.fd.refund.$input.val() == "Yes"){
			var refund = $(me.page).find(".refund")
			var ph_name = $(refund).attr("ph-name")
			var id_list = []
			console.log($('.'+String(ph_name)).length,"ccccccccccc")
			len = $('.'+String(ph_name)).length
			for(i=0;i<len;i++){
				id_list.push($($('.'+String(ph_name))[i]).text())
			}
			console.log(id_list,"id_list")
			if(id_list.length>0){
				frappe.call({
			        method: "customer_info.customer_info.doctype.payments_management.payments_management.make_refund_payment",
		           	args: {
		           		"payments_ids":id_list,
		            	"ph_name":$(refund).attr("ph-name")
		            },
			       	callback: function(r){
			       		$('tr#'+String(ph_name)).hide()
			       		me.dialog.hide();
			    	}
		    	});
			}
		}
		else{
			me.dialog.hide();
		}
	},
	get_data_export:function(){
		var me = this;
		console.log(me,"in export")
		window.location.href = repl(frappe.request.url +
		'?cmd=%(cmd)s&to_date=%(to_date)s&from_date=%(from_date)s&customer=%(customer)s', {
			cmd: "customer_info.customer_info.page.payments_received.payments_received.create_csv",
			to_date:me.to_date.$input.val(),
			from_date: me.from_date.$input.val(),
			customer: me.customer_link.$input.val()
		});
	}
})

	
update_dict_by_payment_ids = function(payments_ids,ph_name){
	console.log(ph_name,"ph_name 11111")
	var payments_details = payments_ids
	var payments_info = []
	var payments_list_of_dict = []
	var flt_precision = frappe.defaults.get_default("float_precision")
	var string = payments_details.slice(0,-1) + '"'
	var array = JSON.parse("[" + string + "]");
	$.each(array[0].split(","), function(i, d) {
		payments_info.push(d.split("/"))
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
	if(payments_list_of_dict.length > 0 ){
		frappe.call({
			async:false,
			method: "customer_info.customer_info.page.payments_received.payments_received.set_payments_history_record",
			args: {
				"record_data":payments_list_of_dict,
				"parent":ph_name
			},
			callback: function(r) {
			}
		})	
		return {"payments_list_of_dict":payments_list_of_dict}
	}
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
	return timeDifferenceInDays
}