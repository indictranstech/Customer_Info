// Copyright (c) 2013, indictrans and contributors
// For license information, please see license.txt

frappe.query_reports["Common bonus report"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80"
		}
	]
}
