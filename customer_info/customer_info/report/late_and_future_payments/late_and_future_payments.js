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
	    if (dataContext["Contact Result"] && columnDef.id != "Email"){
        	concad = dataContext["Contact Result"].split(" ")
	    	if(concad[0] == "WBI" && concad[1] < now_date && flt(dataContext["Late Days"]) > 0) { //red
	            value = "<span style='color:#ff3300!important'>" + value + "</span>";
	    	}
		    if (concad[0] == "WBI" && concad[1] > now_date) { //green
	            value = "<span style='color:#2eb82e!important'>" + value + "</span>";
		    }
		    if (dataContext["Contact Result"] == "Sent SMS/Email") { // blue
	            value = "<span style='color:#4db8ff!important'>" + value + "</span>";
		    }
	    }
	    if(columnDef.id == "Email") {
	    	console.log(dataContext,"customer customer")
            value = "<a class='email_id' email="+dataContext['Email']+" customer_name="+JSON.stringify(dataContext['Customer'])+" onclick='click_on_email()'>" + value + "</a>";
	    }
	    return value;
	}
}

click_on_email = function(){
	console.log($(".email_id").attr("email"))
	var communication_composer = new frappe.views.CommunicationComposer({
	    subject: 'Report [' + frappe.datetime.nowdate() + ']',
	    recipients: ''+$(".email_id").attr("email"),
	    message: "Hi"+" "+$(".email_id").attr("customer_name")+",",
	    doc: {
	        doctype: "User",
	        name: user
	    }
	});
}
