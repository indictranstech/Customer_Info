# -*- coding: utf-8 -*-
# Copyright (c) 2015, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


class ItemCategory(Document):
	pass

@frappe.whitelist()
def new_item_group(category_name):
	group = frappe.new_doc("Item Group")
	group.item_group_name = category_name
	group.parent_item_group = "All Item Groups"
	group.is_group = "No"
	group.save(ignore_permissions = True)
	return "True"


