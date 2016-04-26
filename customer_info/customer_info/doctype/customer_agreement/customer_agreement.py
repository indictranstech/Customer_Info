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
		counter = 1
		count = 1001		
		if self.document_type == "New" and self.flag == 0:
			old_name = frappe.db.sql("""select name from 
										`tabCustomer Agreement` 
										where document_type = "New" """,as_list=1)
			if len(old_name) > 0:
				new_name_list = old_name[-1][0].split("-")
				count = int(new_name_list[-1]) + 1
			self.name = "BK-0" + str(count)
			self.parent_name = self.name
			self.flag = 1

		elif self.document_type == "Updated" and self.flag == 0:
			parent_name = frappe.db.sql("""select name from 
										`tabCustomer Agreement` 
										where parent_name like "{0}" """.format(self.parent_name),as_list=1)
			parent = frappe.get_doc("Customer Agreement", parent_name[0][0])
			if parent:
				parent.update({
					"agreement_status": "Updated",
					"merchandise_status": "Naudota"
				})
				parent.save(ignore_permissions = True)
			if len(parent_name) > 1:			
				old_name_list = parent_name[-1][0].split(('{0}').format(parent_name[0][0])+'-')
				counter = int(old_name_list[-1]) + 1
			self.name = self.parent_name + "-" + str(counter)
			self.flag = 1
		self.agreement_no = self.name	

	def on_update(self):
		self.payment_date_comment()
		self.last_status_update_date()
		self.changed_merchandise_status()
		self.diff_of_agreement_date_and_last_status_update_date_in_month()

	def payment_date_comment(self):
		if self.payment_day and self.old_date and self.payment_day != self.old_date:
			comment = """ Payment Day is Changed From '{0}' To '{1}' """.format(self.old_date,self.payment_day)
			self.add_comment("Comment",comment)
			self.old_date = self.payment_day	
	
	def last_status_update_date(self):
		if self.agreement_status and self.old_agreement_status and self.agreement_status != self.old_agreement_status and self.agreement_status != "Open":		
			self.agreement_status_changed_date = datetime.now().strftime("%Y-%m-%d")
			self.old_agreement_status = self.agreement_status

	def diff_of_agreement_date_and_last_status_update_date_in_month(self):
		active_month = 0
		if self.date and self.agreement_status_changed_date:	
			d1 = map(int,str(self.date).split("-"))
			d2 = map(int,str(self.agreement_status_changed_date).split("-"))
			active_month = (datetime(d2[0],d2[1],d2[2]).year - datetime(d1[0],d1[1],d1[2]).year)*12 + (datetime(d2[0],d2[1],d2[2]).month - datetime(d1[0],d1[1],d1[2]).month)
    		self.number_of_active_agreement_months = active_month



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
	target_doc = get_mapped_doc("Customer Agreement", source_name,
		{
			"Customer Agreement": {
				"doctype": "Customer Agreement",
			},
		}, target_doc)

	target_doc.document_type = "Updated"	
	target_doc.agreement_status = "Open"
	target_doc.product = ""
	target_doc.flag = 0
	return target_doc
				
# comment for date change
		# if self.payment_day and self.old_date and (date_diff(self.payment_day,self.old_date) > 0 or date_diff(self.payment_day,self.old_date) < 0):
		# 	payment_date = datetime.datetime.strptime(self.payment_day,'%Y-%m-%d').strftime('%d-%m-%Y')
		# 	old_date = datetime.datetime.strptime(self.old_date,'%Y-%m-%d').strftime('%d-%m-%Y')
		# 	comment = """ Payment Date is Changed From '{0}' To '{1}' """.format(old_date,payment_date)
		# 	self.add_comment("Comment",comment)
		# 	self.old_date = self.payment_day
