// Copyright (c) 2013, indictrans and contributors
// For license information, please see license.txt

frappe.query_reports["Customer Agreements Report"] = {
	"filters": [
		{
			"fieldname":"agreement_period",
			"label": __("Agreement Period"),
			"fieldtype": "Int",
			"width": "10"
		},
		{
			"fieldname":"agreement_status",
			"label": __("Agreement Status"),
			"fieldtype": "Select",
			"options": " \nOpen\nClosed",
			"width": "10",
			"on_change": function(query_report) {
				var agreement_status = query_report.get_values().agreement_status;
				if (agreement_status == "Open") {
					console.log("agreement_status",agreement_status)
					$("[data-fieldname=agreement_close_date_from]").hide()
					$("[data-fieldname=agreement_close_date_to]").hide()
					$("[data-fieldname=agreement_close_reason]").hide()
					$("[data-fieldname=agreement_start_date_from]").show()
					$("[data-fieldname=agreement_start_date_to]").show()
					
				}
				else if (agreement_status == "Closed") {
					console.log("agreement_status",agreement_status)
					$("[data-fieldname=agreement_start_date_from]").hide()
					$("[data-fieldname=agreement_start_date_to]").hide()
					$("[data-fieldname=agreement_close_date_from]").show()
					$("[data-fieldname=agreement_close_date_to]").show()
					$("[data-fieldname=agreement_close_reason]").show()
				}
				else{
					$("[data-fieldname=agreement_start_date_from]").show()
					$("[data-fieldname=agreement_start_date_to]").show()
					$("[data-fieldname=agreement_close_date_from]").show()
					$("[data-fieldname=agreement_close_date_to]").show()
					$("[data-fieldname=agreement_close_reason]").show()

					// $("[data-fieldname=agreement_start_date_from]").hide()
					// $("[data-fieldname=agreement_start_date_to]").hide()
					// $("[data-fieldname=agreement_close_date_from]").hide()
					// $("[data-fieldname=agreement_close_date_to]").hide()
					// $("[data-fieldname=agreement_close_reason]").hide()
				}
			}
		},
		{
			"fieldname":"agreement_start_date_from",
			"label": __("Agreement Start Date From"),
			"fieldtype": "Date",
			"width": "10",
		},
		{
			"fieldname":"agreement_close_date_from",
			"label": __("Agreement Close Date From"),
			"fieldtype": "Date",
			"width": "10",
		},
		{
			"fieldname":"agreement_start_date_to",
			"label": __("Agreement Start Date To"),
			"fieldtype": "Date",
			"width": "10",
		},
		{
			"fieldname":"agreement_close_date_to",
			"label": __("Agreement Close Date To"),
			"fieldtype": "Date",
			"width": "10",
		},
		
		{
			"fieldname":"agreement_close_reason",
			"label": __("Agreement close reason"),
			"fieldtype": "Select",
			"options": '\n90d SAC\nEarly buy offer\nReturn\nUpgrade\nFraud/Stolen\nContract term is over\nFinancial difficulties\nTemporary leave\nMerchandise returned to supplier\nAgreement sold',
			"width": "10",
		},
	]
}
