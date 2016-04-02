# -*- coding: utf-8 -*-
# Copyright (c) 2015, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ProductCategory(Document):
	pass

@frappe.whitelist()
def new_item_group(category_name):
	group = frappe.db.get_value("Item Group",{"name":category_name},"name")
	if not group:
		group = frappe.new_doc("Item Group")
		group.item_group_name = category_name
		group.parent_item_group = "All Item Groups"
		group.is_group = "No"
		group.save(ignore_permissions = True)
		return "True"

@frappe.whitelist()
def get_category_name(name):
	name_list = frappe.db.sql("""select category_name from `tabProduct Category`""",as_list=1)
	if name in [e[0] for e in name_list]:
		return "Product Category of name '{0}' Already Exist".format(name)