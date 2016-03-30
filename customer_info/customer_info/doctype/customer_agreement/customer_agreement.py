# -*- coding: utf-8 -*-
# Copyright (c) 2015, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
import frappe.defaults
from frappe.utils import date_diff
from frappe.model.document import Document

class CustomerAgreement(Document):


	def validate(self):
		self.changed_merchandise_status()
		if self.name:
			self.agreement_no = self.name

	def on_update(self):
		self.payment_date_comment()

	def payment_date_comment(self):
		if self.payment_day and self.old_date and (date_diff(self.payment_day,self.old_date) > 0 or date_diff(self.payment_day,self.old_date) < 0):
			payment_date = datetime.datetime.strptime(self.payment_day,'%Y-%m-%d').strftime('%d-%m-%Y')
			old_date = datetime.datetime.strptime(self.old_date,'%Y-%m-%d').strftime('%d-%m-%Y')
			comment = """ Payment Date is Changed From '{0}' To '{1}' """.format(old_date,payment_date)
			self.add_comment("Comment",comment)
			self.old_date = self.payment_day
			# frappe.db.set_value("Customer Agreement",self.name,"old_date",self.payment_day)
	
	def changed_merchandise_status(self):
		if self.merchandise_status:
			item = frappe.get_doc("Item",self.product)
			item.update({
			"merchandise_status": self.merchandise_status,
			})
			item.save(ignore_permissions = True)

@frappe.whitelist()
def get_address(customer):
	address = frappe.db.sql("""select name,address_line1,address_line2,city 
								from `tabAddress` 
								where customer = '{0}' 
								and is_primary_address = 1 """.format(customer),as_dict=1)
	return address	