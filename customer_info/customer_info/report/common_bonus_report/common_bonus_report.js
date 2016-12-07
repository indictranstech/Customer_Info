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
	],
	"formatter":function (row, cell, value, columnDef, dataContext, default_formatter) {
		var nDecimals =  2;
		if (typeof columnDef.editorFixedDecimalPlaces == 'number' ){
			var nDecimals = columnDef.editorFixedDecimalPlaces ;  
		}
     	//value = "<span style='align:right'>" + value + "</span>";
		return Number(value).toFixed( nDecimals );
	}
}
