from __future__ import unicode_literals
from frappe import _


def get_data(): 
	return [
		{
			"label": _("Documents"),
			"icon": "icon-star",
			"items": [
				{
					"type": "doctype",
					"name": "Customer Agreement",
					"description": _("Record Of Customer Agreement"),
				},
				{
					"type": "doctype",
					"name": "Payments Management",
					"description": _("Record Of Payments"),
				}
			]
		}
	]