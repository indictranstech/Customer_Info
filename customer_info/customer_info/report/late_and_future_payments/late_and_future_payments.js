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
        now_date = frappe.datetime.nowdate()
        console.log(dataContext["Suspension Date"],"daye tyepee")
	    if (dataContext["Contact Result"] == "WBI" && dataContext["Suspension Date"] < now_date) {
	    	console.log(dataContext,"customer customer")
            value = "<span style='color:#ff3300!important'>" + value + "</span>";
	    }
	    if (dataContext["Contact Result"] == "WBI" && dataContext["Suspension Date"] > now_date) {
	    	console.log(dataContext,"customer customer")
            value = "<span style='color:#4db8ff!important'>" + value + "</span>";
	    }
	    if (dataContext["Contact Result"] == "Sent SMS/Email") {
	    	console.log(dataContext,"customer customer")
            value = "<span style='color:#2eb82e!important'>" + value + "</span>";
	    }
	    return value;
	}
}