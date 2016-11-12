from __future__ import unicode_literals
from frappe import _


def get_data(): 
	return [
		{
			"label": _("Masters"),
			"icon": "icon-star",
			"items": [
				{
					"type": "doctype",
					"name": "Brand Name",
					"description": _("Brand Name"),
				},
				{
					"type": "doctype",
					"name": "Brand",
					"description": _("Details Of Brand"),
				},
				{
					"type": "doctype",
					"name": "Product Category",
					"description": _("Details Of Product Category"),
				},
				{
					"type": "doctype",
					"name": "Period",
					"description": _("Details Of Period"),
				},
				{
					"type": "doctype",
					"name": "Ratio",
					"description": _("Details Of Ratio"),
				}
			]
		},
		{
			"label": _("Standard Reports"),
			"icon": "icon-star",
			"items": [
				# {
				# 	"type": "report",
				# 	"is_query_report": True,
				# 	"name": "late payment on daily basis",
				# 	"label": _("Late Payments On Daily Basis"),
				# 	"description": _("Record of late Payment"),
				# 	"doctype": "Customer Agreement",
				# },
				{
					"type": "report",
					"is_query_report": True,
					"name": "late and future payments",
					"label": _("Late and future payments"),
					"description": _("Record of late and future payments"),
					"doctype": "Customer Agreement",
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Future payments",
					"label": _("Future payments"),
					"description": _("Record of future Payment"),
					"doctype": "Customer Agreement",
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "items inventory movement",
					"label": _("Items inventory movement"),
					"description": _("items inventory movement"),
					"doctype": "Customer Agreement",
					#"icon": "icon-bar-chart",
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Common bonus report",
					"label": _("Common bonus report"),
					"description": _("Common bonus report"),
					"doctype": "Customer Agreement",
					#"icon": "icon-bar-chart",
				},
				{
					"type": "page",
					"name": "payments-received",
					"label": _("Received Payment"),
					"description": _("Record of Received Payment"),
					"doctype": "Payments History",
					"icon": "icon-bar-chart",
				}
			]
		},
	]