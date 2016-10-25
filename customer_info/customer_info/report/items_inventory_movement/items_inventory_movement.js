// Copyright (c) 2013, indictrans and contributors
// For license information, please see license.txt

frappe.query_reports["items inventory movement"] = {
	"filters": [
		{
			"fieldname":"sold_from_date",
			"label": __("Sold Date From"),
			"fieldtype": "Date",
			"width": "80"
		},
		{
			"fieldname":"sold_to_date",
			"label": __("To Sold Date"),
			"fieldtype": "Date",
			"width": "80"
		},
		{
			"fieldname":"purchase_from_date",
			"label": __("Purchase Date From"),
			"fieldtype": "Date",
			"width": "80"
		},
		{
			"fieldname":"purchase_to_date",
			"label": __("To Purchase Date"),
			"fieldtype": "Date",
			"width": "80"
		}
	]
}
