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
				},
			]
		}
	]