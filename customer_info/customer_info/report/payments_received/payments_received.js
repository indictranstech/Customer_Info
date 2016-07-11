// Copyright (c) 2013, indictrans and contributors
// For license information, please see license.txt

frappe.query_reports["Payments Received"] = {
	"filters": [
		{
			"fieldname":"customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"width": "80"
		}
	]
}
