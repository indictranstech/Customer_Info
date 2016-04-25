# -*- coding: utf-8 -*-
# Copyright (c) 2015, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
import frappe.defaults
from frappe.utils import date_diff
from frappe.utils import nowdate, getdate
from frappe.utils import now_datetime
from datetime import datetime, timedelta
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class CustomerAgreement(Document):	 

	def validate(self):
		new_name_list = []
		old_name_list = []
		if self.document_type == "New":
			old_name = frappe.db.sql("""select name from `tabCustomer Agreement`""",as_list=1)
			if len(old_name) == 0:
				self.name = 'BK-0' + '1001'
				self.parent_name = self.name
				self.agreement_no = self.name
			elif len(old_name) > 0:
					for i in [e[0] for e in old_name]:
						if len(i.split("-")) == 2:
							new_name_list = i.split("-")
					count = int(new_name_list[1]) + 1
					self.name = "BK-0" + str(count)
					self.parent_name = self.name
					self.agreement_no = self.name

		elif self.document_type == "Updated":
			parent_name = frappe.db.sql("""select name from `tabCustomer Agreement` where parent_name like "{0}" """.format(self.parent_name),as_list=1)
			if self.parent_name == parent_name[0][0] and len(parent_name) == 1:	
				self.name = self.parent_name + "-" + "1"
				self.agreement_no = self.name

			elif self.parent_name == parent_name[0][0] and len(parent_name) > 1:			
				for i in [e[0] for e in parent_name[1:]]:
					old_name_list = i.split(('{0}').format(parent_name[0][0])+'-')
				counter = int(old_name_list[-1]) + 1	
			 	self.name = self.parent_name + "-" + str(counter)
			 	self.agreement_no = self.name



	def on_update(self):
		self.payment_date_comment()
		self.last_status_update_date()

	def payment_date_comment(self):
		if self.payment_day and self.old_date and self.payment_day != self.old_date:
			comment = """ Payment Day is Changed From '{0}' To '{1}' """.format(self.old_date,self.payment_day)
			self.add_comment("Comment",comment)
			self.old_date = self.payment_day	
	
	def last_status_update_date(self):
		if self.agreement_status and self.old_agreement_status and self.agreement_status != self.old_agreement_status:		
			self.agreement_status_changed_date = datetime.now().strftime("%Y-%m-%d")
			self.old_agreement_status = self.agreement_status

	def changed_merchandise_status(self):
		if self.merchandise_status:
			item = frappe.get_doc("Item",self.product)
			item.update({
			"merchandise_status": self.merchandise_status,
			"old_status": item.merchandise_status
			})
			item.save(ignore_permissions = True)

@frappe.whitelist()
def get_primary_address(customer):
	address = frappe.db.sql("""select name,address_line1,address_line2,city 
								from `tabAddress` 
								where customer = '{0}' 
								and is_primary_address = 1 """.format(customer),as_dict=1)
	return address

@frappe.whitelist()
def get_address(customer,address):
	address = frappe.db.sql("""select address_line1,address_line2,city 
								from `tabAddress` 
								where customer = '{0}' 
								and name = '{1}' """.format(customer,address),as_dict=1)
	return address

@frappe.whitelist()
def make_update_agreement(source_name, target_doc=None):
	# ca = frappe.get_doc("Customer Agreement", source_name)
	target_doc = get_mapped_doc("Customer Agreement", source_name,
		{
			"Customer Agreement": {
				"doctype": "Customer Agreement",
			},
		}, target_doc)

	# target_doc.agreement_no = "BK-" + str("{0}".format(ca.agreement_no).split("K-")[1]) + "-" + "1"
	target_doc.document_type = "Updated"	
	return target_doc
				
# comment for date change
		# if self.payment_day and self.old_date and (date_diff(self.payment_day,self.old_date) > 0 or date_diff(self.payment_day,self.old_date) < 0):
		# 	payment_date = datetime.datetime.strptime(self.payment_day,'%Y-%m-%d').strftime('%d-%m-%Y')
		# 	old_date = datetime.datetime.strptime(self.old_date,'%Y-%m-%d').strftime('%d-%m-%Y')
		# 	comment = """ Payment Date is Changed From '{0}' To '{1}' """.format(old_date,payment_date)
		# 	self.add_comment("Comment",comment)
		# 	self.old_date = self.payment_day
