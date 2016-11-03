# -*- coding: utf-8 -*-
# Copyright (c) 2015, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ProductCategory(Document):
	pass

@frappe.whitelist(allow_guest = True)	
def new_item_group(self,method):
	print self.category_name,"\n\n","category_name"
	group = frappe.db.get_value("Item Group",{"name":self.category_name},"name")
	if not group:
		group = frappe.new_doc("Item Group")
		group.item_group_name = self.category_name
		group.parent_item_group = "All Item Groups"
		group.is_group = "No"
		group.save(ignore_permissions = True)
		return "True"

@frappe.whitelist(allow_guest = True)	
def make_category_and_brand_name(self,method):
	brand_name = frappe.db.get_value("Brand Name",{"name":self.brand_name},"name")
	if not brand_name:
		brand_name = frappe.new_doc("Brand Name")
		brand_name.brand_name = self.brand_name
		brand_name.save(ignore_permissions=True)


@frappe.whitelist()
def get_category_name(name):
	name_list = frappe.db.sql("""select category_name from `tabProduct Category`""",as_list=1)
	if name in [e[0] for e in name_list]:
		return "Product Category of name '{0}' Already Exist".format(name)


