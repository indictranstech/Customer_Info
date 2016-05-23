# -*- coding: utf-8 -*-
# Copyright (c) 2015, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
import frappe.defaults
from frappe.utils import date_diff
from frappe.utils import nowdate, getdate,add_months
from frappe.utils import now_datetime
from datetime import datetime, timedelta
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class CustomerAgreement(Document):	 
	def validate(self):
		self.naming()
		if not self.payments_record and self.name and self.due_date_of_next_month:
			self.add_payments_record()

	def onload(self):
		payment_received = 0
		no_of_late_days = 0
		received_payments = []
		if self.payments_record:
			for row in self.payments_record:
				if row.check_box == 1:
					received_payments.append(row.monthly_rental_amount)
				if row.due_date and row.payment_date and date_diff(row.payment_date,row.due_date) > 3:
					no_of_late_days += date_diff(row.payment_date,row.due_date) - 3
		if self.payments_record:
			for row in self.payments_record:		
				if row.check_box == 0 and date_diff(row.due_date,datetime.now()) < 0:
					self.current_date = row.due_date
					self.next_due_date = self.get_next_due_date(self.current_due_date,1)
					break
				elif row.check_box == 0 and date_diff(row.due_date,datetime.now()) >= 0:
					self.current_due_date = row.due_date
					self.next_due_date = row.due_date	
					break
		received_payments = map(float,received_payments)

		for i in received_payments:
			payment_received += i

		if self.payments_record and self.date:
			self.payments_left = len(self.payments_record) - len(received_payments)
			self.balance = self.payments_left * self.monthly_rental_payment
			self.payments_made = "{0} Out Of {1}".format(len(received_payments),self.agreement_period)
			self.number_of_payments = int(self.agreement_period) - len(received_payments)
			self.late_fees = no_of_late_days * self.monthly_rental_payment * 0.02

	def naming(self):	
		new_name_list = []
		old_name_list = []
		counter = 1
		count = 10001		
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
			
			parent = frappe.get_doc("Customer Agreement", self.agreement_no)
			if parent and parent.agreement_status != "Updated" and parent.merchandise_status != "Used":
				parent.update({
					"agreement_status": "Updated",
					"merchandise_status": "Used"
				})
				parent.save(ignore_permissions = True)
				
			if len(parent_name) > 1:			
				old_name_list = parent_name[-1][0].split(('{0}').format(parent_name[0][0])+'-')
				counter = int(old_name_list[-1]) + 1
			self.name = self.parent_name + "-" + str(counter)
			self.flag = 1
			self.agreement_status = "Updated"
		self.agreement_no = self.name

	# add row in child table	
	def add_payments_record(self):
		print self.due_date_of_next_month
		current_date = datetime.strptime(self.due_date_of_next_month, '%Y-%m-%dT%H:%M:%S.%fZ')
		print type(current_date),"type current_date"
		print current_date,"current_dateeeeeeeeee"
		list_of_payments_record = []
		for i in range(int(self.agreement_period)):
			list_of_payments_record.append({
				'no_of_payments':'Payment {0}'.format(i+1),
				'monthly_rental_amount':self.monthly_rental_payment,
				'due_date':self.get_next_due_date(current_date,i),
				'payment_id':self.name + '-' + 'Payment {0}'.format(i+1)
				})

		for d in list_of_payments_record:
			nl = self.append('payments_record', {})
			nl.no_of_payments = d['no_of_payments']
			nl.monthly_rental_amount = d['monthly_rental_amount']
			nl.due_date = d['due_date']
			nl.payment_id = d['payment_id']

	def get_next_due_date(self,date,i):
		add_month_to_date = add_months(date,i)
		return str(add_month_to_date)[0:10]	
		
	def on_update(self):
		self.payment_date_comment()
		self.last_status_update_date()
		self.changed_merchandise_status()
		self.diff_of_agreement_date_and_last_status_update_date_in_month()
		#self.update_due_date_according_to_payment_day()

	# def update_due_date_according_to_payment_day(self):
	# 	current_date = datetime.strptime(self.due_date_of_next_month, '%Y-%m-%dT%H:%M:%S.%fZ')
	# 	if self.payments_record:
	# 		for i in self.payments_record:
	# 			print i.due_date,"iiiiiiiiiiii"
	# 			if i.due_date:
	# 				i.due_date = ""
	# 				i.due_date = self.get_next_due_date(current_date,i)
				# i.due_date = self.get_next_due_date(current_date,i)
	
	# def get_count_of_payments(self):
	# 	payment_received = 0
	# 	no_of_late_days = 0
	# 	received_payments = []
	# 	if self.payments_record:
	# 		for row in self.payments_record:
	# 			if row.check_box == 1:
	# 				received_payments.append(row.monthly_rental_amount)
	# 			if row.due_date and row.payment_date and date_diff(row.payment_date,row.due_date) > 3:
	# 				no_of_late_days += date_diff(row.payment_date,row.due_date) - 3
	# 	received_payments = map(float,received_payments)

	# 	for i in received_payments:
	# 		payment_received += i
		
	# 	total_payment = self.monthly_rental_payment * int(self.agreement_period)
	# 	payment_left = total_payment - payment_received

	# 	return {"length":len(received_payments),"payment_left":payment_left,"no_of_late_days":no_of_late_days}			

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

# @frappe.whitelist()
# def get_address(customer,address):
# 	address = frappe.db.sql("""select address_line1,address_line2,city 
# 								from `tabAddress` 
# 								where customer = '{0}' 
# 								and name = '{1}' """.format(customer,address),as_dict=1)
# 	return address

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
	target_doc.date = ""
	target_doc.agreement_status_changed_date = ""
	target_doc.suspended_until = ""
	target_doc.suspended_from = ""
	target_doc.merchandise_status = ""
	target_doc.flag = 0
	target_doc.payments_record = ""
	return target_doc

@frappe.whitelist()
def get_product(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""select item_name, merchandise_status from `tabItem` 
							where item_name not in (select product from `tabCustomer Agreement` 
												where agreement_status = "Open") 
							and merchandise_status = "Used" or merchandise_status = "New" 
							and (item_name like '{txt}'
											or merchandise_status like '{txt}') limit 20 """.format(txt= "%%%s%%" % txt),as_list=1,debug=1)
# comment for date change
		# if self.payment_day and self.old_date and (date_diff(self.payment_day,self.old_date) > 0 or date_diff(self.payment_day,self.old_date) < 0):
		# 	payment_date = datetime.datetime.strptime(self.payment_day,'%Y-%m-%d').strftime('%d-%m-%Y')
		# 	old_date = datetime.datetime.strptime(self.old_date,'%Y-%m-%d').strftime('%d-%m-%Y')
		# 	comment = """ Payment Date is Changed From '{0}' To '{1}' """.format(old_date,payment_date)
		# 	self.add_comment("Comment",comment)
		# 	self.old_date = self.payment_day
