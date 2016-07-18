frappe.query_reports["late and future payments"] = {
	"filters": [
		{
			"fieldname":"date",
			"label": __("Date"),
			"fieldtype": "Date",
			"width": "80"
		}
	],
	"formatter":function (row, cell, value, columnDef, dataContext, default_formatter) {
        value = default_formatter(row, cell, value, columnDef, dataContext);
	    console.log(columnDef['name'],"columnDef columnDef")
	    columnDef["toolTip"] = "namwe"
	    /*
	    if (columnDef.id != "Customer" && columnDef.id != "Payment Date" && dataContext["Rental Payment"] > 50 && (row == 0 || row == 2)) {
	    	console.log(dataContext["Customer"],"customer customer")
	    	get_agreement_according_to_contact_result(dataContext["Customer"]);
            value = "<span style='color:red!important;font-weight:bold'>" + value + "</span>";
	    }
	    if (columnDef.id != "Customer" && columnDef.id != "Payment Date" && dataContext["Rental Payment"] < 100 && row == 1) {
            value = "<span style='color:green!important;font-weight:bold'>" + value + "</span>";
	    }
	    return value;*/
	},
}



get_agreement_according_to_contact_result = function(customer){
	frappe.call({
        method: "customer_info.customer_info.report.late_and_future_payments.late_and_future_payments.get_agreement_according_to_contact_result",
        args: {
        	"customer":customer
        },
        callback: function(r) {

        }
    });
}	