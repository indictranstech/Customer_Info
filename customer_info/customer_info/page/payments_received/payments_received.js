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
		//this.render_payments_details();
	},
	set_fields: function() {
		var me = this;
		html = "<div>\
				<div class='col-xs-2 customer'></div>\
				<div class='col-xs-2 from_date'></div>\
  				<div class='col-xs-2 to_date'></div>\
  				<div class='col-xs-2 agreement'></div>\
  				<div class='col-xs-2 data_limit'></div>\
  				<div class='col-xs-2 payment_type_filter'></div>\
  				<div class='col-xs-2' ></div>\
  				</div>\
				<table id='tableSearchResults' class='table table-hover  table-striped table-condensed' style='font-size:12px;margin-bottom: 0px;'>\
			     	<thead>\
			            <tr>\
			                <th width='7%'>Payment Date</th>\
			                <th width='7%'>Customer Name</th>\
			                <th width='7%'>Payment Type</th>\
			                <th width='7%'>Payment Amount</th>\
			                <th width='6%'>Late Fees Amount</th>\
			                <th width='5%'>Receivables Amount</th>\
			                <th width='5%'>Discount Amount</th>\
			                <th width='5%'>Campaign Discount Amount</th>\
			                <th width='5%'>Bonus Amount</th>\
			                <th width='13%'>Total calculated payment amount</th>\
			                <th width='11%'>Bank Transfer Amount</th>\
			                <th width='5%'>Receivables Collected</th>\
			                <th width='5%'>Cash Amount</th>\
			                <th width='3%'>Bank Card Amount</th>\
			                <th width='4%'>Associate</th>\
			                <th width='3%'>Refund Payment</th>\
			                <th width='2%'></th>\
			            </tr>\
			        </thead></table>"
		me.page.html(html)
		me.customer_link = frappe.ui.form.make_control({
			parent: me.page.find(".customer"),
			df: {
			fieldtype: "Link",
			options: "Customer",
			fieldname: "customer",
			label:"Customer",
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
				label:"From Date",
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
				label:"To Date",
				placeholder: "To Date"
			},
			render_input: true
		});
		me.to_date.refresh();
		me.agreement = frappe.ui.form.make_control({
			parent: me.page.find(".agreement"),
			df: {
				fieldtype: "Link",
				fieldname: "agreement",
				label:"Customer Agreement",
				placeholder: "Customer Agreement",
				options:"Customer Agreement"
			},
			render_input: true
		});
		me.agreement.refresh();

		me.data_limit = frappe.ui.form.make_control({
			parent: me.page.find(".data_limit"),
			df: {
				fieldtype: "Select",
				fieldname: "data_limit",
				label:"Data Limit",
				placeholder: "Data Limit",
				options:["","0-100","0-200","0-300","0-400","0-500","All"]
			},
			render_input: true
		});

		me.payment_type_filter = frappe.ui.form.make_control({
		parent: me.page.find(".payment_type_filter"),
		df: {
				fieldtype: "Select",
				fieldname: "payment_type_filter",
				label:"Payment Type",
				placeholder: "payment_type",
				options:["","Rental Payment","Modification Of Receivables","90d SAC"]
			},
			render_input: true
		});
		me.payment_type_filter.refresh();
		
		this.render_payments_details();	

		me.customer_link.$input.on("change", function(){
			var old_me = me;
			old_me.render_payments_details()
		});

		me.from_date.$input.on("change", function(){
			var old_me = me;
			old_me.render_payments_details()
		});

		me.to_date.$input.on("change", function(){
			var old_me = me;
			old_me.render_payments_details()
		});

		me.agreement.$input.on("change", function(){
			var old_me = me;
			old_me.render_payments_details()
		});

		me.data_limit.$input.on("change", function(){
			var old_me = me;
			old_me.render_payments_details()
		});

		me.payment_type_filter.$input.on("change", function(){
			var old_me = me;
			old_me.render_payments_details()
		});
	},
	render_payments_details: function() {
		var me = this;
		//var _agreement_name =  window.location.href.split("=")[1] ? window.location.href.split("=")[1]:""
		//me.agreement.$input.val(_agreement_name)
		var me = this;
		console.log("------------ggg-----",me.payment_type_filter.$input.val())
		this.data = ""
		frappe.call({
			method: "customer_info.customer_info.page.payments_received.payments_received.get_payments_details",
			args: {
				"customer": me.customer_link.$input.val(),
				"from_date": me.from_date.$input.val(),
				"to_date":me.to_date.$input.val(),
				"agreement":me.agreement.$input.val(),// ? me.agreement.$input.val():_agreement_name,
				"data_limit":me.data_limit.$input.val(),
				"pmt_type" :me.payment_type_filter.$input.val()	
			},
			freeze: true,
			freeze_message: __("Please Wait..."),
			callback: function(r) {
        	   	me.page.find(".data").empty();
				$.each(r.message["data"], function(i, d) {
					/*if(d["payoff_cond"]){
						me.payoff_cond = d["payoff_cond"]
					}
					if(d["payment_type"]){
						me.payment_type = d["payment_type"]
					}*/
					me.payoff_cond = d["payoff_cond"] ? d["payoff_cond"] : ""
					me.payment_type = d["payment_type"] ? d["payment_type"]: ""
					me.payments_ids = d["payments_ids"]
					me.late_fees_updated = d["late_fees_updated"]
					me.updated_late_fees = d["late_fees"]
					d["payments_ids"] = d["payments_ids"] ? me.update_dict_by_payment_ids():""
        	   	});
        	   	me.data = r.message["data"];
        	   	html = frappe.render_template("payments_received",{"data": r.message["data"],"total":r.message["total"]})
				me.page.append(html)
				me.refund();
			}
		})
	},
	update_dict_by_payment_ids:function(){
		var me = this;
		var flt_precision = frappe.defaults.get_default("float_precision")
		var dict_of_payments_ids = []
		var __dict_of_payments_ids = []
		if(me.payment_type != "Modification Of Receivables"){
			//console.log(me.payments_ids,"payments_ids12122121",String(me.payments_ids.slice(1,-1)).split(","))
			var formatted_list_of_payment_ids = String(me.payments_ids.slice(1,-1)).split(",")//JSON.parse("[" + me.payments_ids.slice(0,-1) + '"' + "]")[0].split(",")
			if(me.payoff_cond != "Rental Payment"){
				late_fees = ""
				rental_payment = 0
				total = ""
				payment_id = ""
				payments_ids = []
				$.each(formatted_list_of_payment_ids, function(i, d) {
					payment_id = d.split("/")[0].split("-P")[0],
					payments_ids.push(d.split("/")[0]),
					late_fees = "-",
					rental_payment = parseFloat(flt(d.split("/")[2]).toFixed(2)),
					total = "-"
		   		});
		   		__dict_of_payments_ids.push({
		   			"payments_id":payment_id+"-"+me.payoff_cond,
					"payment_id_list": JSON.stringify(payments_ids.toString()),
					"due_date":"-",
					"rental_payment":rental_payment.toFixed(2),
					"late_fees":late_fees,
					"total": total
		   		})
				return __dict_of_payments_ids
			}
			else{
				if(me.late_fees_updated == "Yes"){
					//console.log("inside late_fees_updated")
					/*oldest_date = {"payments_id":"","due_date":""}
					var due_date_list = []
					$.each(formatted_list_of_payment_ids, function(i, d) {
						console.log(d.split("/")[0],i,"$$$$$$$$%%%%%%%%%%%%%%")
						due_date_list.push(d.split("/")[1])
						function dmyOrdA(a,b){ return myDate(a) - myDate(b);}
						function myDate(s){var a=s.split(/-|\//); return new Date(a[0],a[1]-1,a[2]);}
						due_date_list.sort(dmyOrdA);
						oldest_date["due_date"] = due_date_list[0]
						if(oldest_date["due_date"] == d.split("/")[1]){
							oldest_date["payments_id"] = d.split("/")[0]
						}
					})*/
				   	$.each(formatted_list_of_payment_ids, function(i, d) {
				   		//if (d.split("/")[0] == oldest_date["payments_id"]){
				   		if (i == 0){
				   			dict_of_payments_ids.push({
				   				"late_fees": me.updated_late_fees,
				   				"payments_id":d.split("/")[0],
								"due_date":d.split("/")[1],
								"rental_payment":d.split("/")[2],
								"total": parseFloat(flt(me.updated_late_fees) + flt(d.split("/")[2])).toFixed(2) 
				   			})
				   		}	
				   		else{
				   			dict_of_payments_ids.push({	
				   				"late_fees":0,
				   				"payments_id":d.split("/")[0],
								"due_date":d.split("/")[1],
								"rental_payment":d.split("/")[2],
								"total": parseFloat(0 + flt(d.split("/")[2])).toFixed(2) 
				   			})
				   		}
			   		});
				}
				else{
					//console.log("in else inside late_fees_updated")
					$.each(formatted_list_of_payment_ids, function(i, d) {
				   		dict_of_payments_ids.push({
				   			"payments_id":d.split("/")[0],
							"due_date":d.split("/")[1],
							"rental_payment":d.split("/")[2],
							"late_fees":parseFloat(me.get_late_fees(d.split("/")[0].split("-P")[0],d.split("/")[1],d.split("/")[3],d.split("/")[2])).toFixed(2),
							"total": parseFloat(flt(me.get_late_fees(d.split("/")[0].split("-P")[0],d.split("/")[1],d.split("/")[3],d.split("/")[2])) + flt(d.split("/")[2])).toFixed(2)
							//parseFloat(me.get_late_fees(d.split("/")[0].split("-P")[0],d.split("/")[1],d.split("/")[3],d.split("/")[2]) + flt(d.split("/")[2])).toFixed(2) 
				   		})
			   		});
				}
				return dict_of_payments_ids
			}
		}	
	},
	get_late_fees : function(agreement_name,date1,date2,rental_payment){
		//console.log(agreement_name,"agreement_name",date1,date2)
		var date_diff = frappe.datetime.get_diff(date2,date1)
		var late_fees_amount = 0
		frappe.call({
			async:false,
            method: "frappe.client.get_value",
            args: {
                doctype: "Customer Agreement",
                fieldname: "late_fees_rate",
                filters: { name: agreement_name },
            },
            callback: function(res){
            //	console.log("********************8888")
                if (res && res.message){
                //	console.log("rerer",res.message,date_diff)
					if(flt(date_diff) > 3){
				//		console.log("insdie 333333333")
						late_fees_amount = (flt(date_diff) - 3) * rental_payment * (flt(res.message.late_fees_rate)/100)
					}
                }
            }
        });
		if(flt(date_diff) > 3 && late_fees_amount){
			return late_fees_amount.toFixed(2)
		}
		else{
			return 0
		}
	},
	refund:function(){
		var me = this;		
		$(me.page).find(".refund").click(function() {
			me.ph_name = $(this).attr("ph-name")
			me.show_dialog();
		});
	},
	show_dialog:function(){
		var me = this;
		this.dialog = new frappe.ui.Dialog({
            		title: "Refund Process",
                	fields: [
                   		{"fieldtype": "Select" , "fieldname": "refund" , "label": "Do You Want To Refund","options":["No","Yes"],"default":"No"},
                   		{"fieldtype": "Button" , "fieldname": "refund_payment" , "label": "Refund"}
                   	],
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
		me.fd.refund.$wrapper.find('[data-fieldtype="Select"]').attr("dir","rtl");
		me.fd.refund_payment.$wrapper.find('[data-fieldname="refund_payment"]').css({"float":"right"});
		me.fd.refund_payment.$input.click(function() {
			me.make_refund_payment()
		})	
	},
	make_refund_payment:function(){
		var me = this;
		if(me.fd.refund.$input.val() == "Yes"){
			var id_list = []
			len = $('.'+String(me.ph_name)).length
			if($('.'+String(me.ph_name)).attr("payment-ids")){
				id_list = $('.'+String(me.ph_name)).attr("payment-ids").split(",")
			}
			else{
				for(i=0;i<len;i++){
					id_list.push($($('.'+String(me.ph_name))[i]).text())
				}
			}
			//if(id_list.length>0){
			//}
			frappe.call({
		        method: "customer_info.customer_info.page.payments_received.payments_received.make_refund_payment",
	           	args: {
	           		"payments_ids":id_list,
	            	"ph_name":me.ph_name ? me.ph_name :""
	            },
		       	callback: function(r){
		       		$('tr#'+String(me.ph_name)).hide()
		       		me.dialog.hide();
		       		me.render_payments_details();
		    	}
	    	});
		}
		else{
			me.dialog.hide();
		}
	},
	get_data_export:function(){
		var me = this;
		/*window.location.href = repl(frappe.request.url +
		'?cmd=%(cmd)s&data=%(data)s', {
			cmd: "customer_info.customer_info.page.payments_received.payments_received.create_csv",
			data:JSON.stringify(me["data"])
		});*/
		window.location.href = repl(frappe.request.url +
		'?cmd=%(cmd)s&from_date=%(from_date)s&to_date=%(to_date)s&customer=%(customer)s&agreement=%(agreement)s&data_limit=%(data_limit)s', {
			cmd: "customer_info.customer_info.page.payments_received.payments_received.create_csv",
			from_date: me.from_date.$input.val(),
			to_date: me.to_date.$input.val(),
			customer: me.customer_link.$input.val(),
			agreement: me.agreement.$input.val(),
			data_limit: me.data_limit.$input.val(),
		});
	}
});