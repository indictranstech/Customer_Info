# -*- coding: utf-8 -*-
# Copyright (c) 2015, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
import frappe.defaults
import json
from frappe.utils import date_diff
from frappe.utils import flt, get_datetime, get_time, getdate
from frappe.utils import nowdate, getdate,add_months
from frappe.utils import now_datetime
from datetime import datetime, timedelta,date
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class CustomerAgreement(Document):	 
	def validate(self):
		self.naming()
		self.comment_for_agreement_status_change()
		if not self.payments_record and self.name and self.due_date_of_next_month:
			self.add_payments_record()

	def after_insert(self):
		self.comment_for_agreement_creation()		

	def onload(self):
		payment_received = 0
		payment_made = []
		late_payments = []
		amount_of_payment_left = []
		add_bonus_of_one_eur = []
		add_bonus_of_two_eur = []
		no_of_late_days = 0
		received_payments = []
		if self.payments_record:
			for row in self.payments_record:
				if row.check_box == 1:
					received_payments.append(row.monthly_rental_amount)
				if row.due_date and row.payment_date and date_diff(row.payment_date,row.due_date) > 3:
					no_of_late_days += date_diff(row.payment_date,row.due_date) - 3
					late_payments.append(row.monthly_rental_amount)
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

		now_date = datetime.now().date()
		firstDay_next_month = date(now_date.year, now_date.month+1, 1)
		print type(firstDay_next_month)	
		print firstDay_next_month,"firstDay_next_month"

		if self.payments_record:
			for row in self.payments_record:
				print type(row.due_date),"due_date"
				if row.check_box_of_submit == 0 and row.check_box == 1:
					payment_made.append(row.monthly_rental_amount)
					# datetime.strptime(row.due_date,'%b%d%Y').strftime('%m/%d/%Y')
				if (getdate(row.due_date) >= firstDay_next_month) and row.check_box == 0:
				 	amount_of_payment_left.append(row.monthly_rental_amount)
				if row.payment_date and getdate(row.payment_date) == getdate(row.due_date):
					add_bonus_of_one_eur.append(row.idx)
				if row.payment_date and getdate(row.payment_date) < getdate(row.due_date):
					add_bonus_of_two_eur.append(row.idx)		 	  	



		payment_made = map(float,payment_made)
		print sum(payment_made),"sum of payments_made"

		amount_of_payment_left = map(float,amount_of_payment_left)
		print sum(amount_of_payment_left),"amount_of_payment_left"

		late_payments = map(float,late_payments)
		print sum(late_payments),"late_payments"

		bonus = len(add_bonus_of_one_eur)*1 + len(add_bonus_of_two_eur)*2
		print bonus,"bonus"

		for i in received_payments:
			payment_received += i

		if self.payments_record and self.date:
			self.payments_left = len(self.payments_record) - len(received_payments)
			self.balance = self.payments_left * self.monthly_rental_payment
			self.payments_made = sum(payment_made)
			self.late_payments = sum(late_payments)
			self.amount_of_payment_left = sum(amount_of_payment_left)
			# self.payments_made = "{0} Out Of {1}".format(len(received_payments),self.agreement_period)
			self.number_of_payments = len(received_payments)
			self.late_fees = no_of_late_days * self.monthly_rental_payment * 0.02
			self.bonus = bonus

	def on_update(self):
		self.payment_date_comment()
		self.get_agreement_closed_date()
		self.changed_merchandise_status()

	# For Naming	
	def naming(self):	
		new_name_list = []
		old_name_list = []
		counter = 1
		count = 10001		
		if self.document_type == "New" and self.flag == 0:
			old_name = frappe.db.sql("""select name from 
										`tabCustomer Agreement` 
										where document_type = "New" order by replace(name,"BK-","")*1 """,as_list=1)
			if len(old_name) > 0:
				new_name_list = old_name[-1][0].split("-")
				print new_name_list[-1]
				count = int(new_name_list[-1]) + 1
			self.name = "BK-0" + str(count)
			self.parent_name = self.name
			self.flag = 1

		elif self.document_type == "Updated" and self.flag == 0:
			parent_name = frappe.db.sql("""select name from 
										`tabCustomer Agreement` 
										where parent_name like "{0}" """.format(self.parent_name),as_list=1)
			
			parent = frappe.get_doc("Customer Agreement", self.agreement_no)
			if parent and parent.agreement_status != "Updated":
				parent.update({
					"agreement_status": "Updated",
					"merchandise_status": "Used",
					"old_agreement_status":parent.agreement_status,
					"agreement_update_date":datetime.now()
				})
				parent.save(ignore_permissions = True)

			# if len(parent_name) > 1:			
			# 	old_name_list = parent_name[-1][0].split(('{0}').format(parent_name[0][0])+'-')
			# 	counter = int(old_name_list[-1]) + 1
			if len(parent_name) == 1 and len(parent_name[0][0].split('-')) == 2:
				print "my cond 00000"
				counter = 1

			elif len(parent_name) > 1 and (len(parent_name[0][0].split('-')) > 1 and len(parent_name[0][0].split('-')) == 2):			
				print "in my cond 11111111111111111111111"
				old_name_list = parent_name[-1][0].split(('{0}').format(parent_name[0][0])+'-')
				counter = int(old_name_list[-1]) + 1

			elif len(parent_name) >= 1 and (len(parent_name[0][0].split('-')) > 1 and len(parent_name[0][0].split('-')) == 3):			
				old_counter = int(parent_name[-1][0].split('-')[-1])
				counter = old_counter + 1	

			self.name = self.parent_name + "-" + str(counter)
			self.flag = 1
		self.agreement_no = self.name



	# add row in child table	
	def add_payments_record(self):
		current_date = datetime.strptime(self.due_date_of_next_month, '%Y-%m-%dT%H:%M:%S.%fZ')
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


	# get date after i month
	def get_next_due_date(self,date,i):
		add_month_to_date = add_months(date,i)
		return add_month_to_date.date()
		# return str(add_month_to_date)[0:10]					


	# get date after i month on changeing payment day	
	def change_due_dates_in_child_table(self):
	    due_date_of_next_month = datetime.strptime(self.due_date_of_next_month, '%Y-%m-%dT%H:%M:%S.%fZ')
	    for row in self.payments_record:
	    	# print row.due_date,"row.due_date"
	    	print type(row.due_date),"1"
	    	row.update({
	    		"due_date":self.get_next_due_date(due_date_of_next_month,row.idx-1)
	    		})
	    	print type(row.due_date),"2"
	    	# row.due_date = getdate(get_next_month_date(due_date_of_next_month,row.idx-1))
	    	# row.save(ignore_permissions=True)	

	# Comment For Changing Payment Day
	def payment_date_comment(self):
		if self.payment_day and self.old_date and self.payment_day != self.old_date:
			comment = """ Payment Day is Changed From '{0}' To '{1}' """.format(self.old_date,self.payment_day)
			self.add_comment("Comment",comment)
			self.old_date = self.payment_day	
	
	# get_agreement_closed_date
	def get_agreement_closed_date(self):
		if self.agreement_close_date and self.agreement_status == "Closed":
			self.get_active_agreement_month()

	# get_active_agreement_month
	def get_active_agreement_month(self):
		active_month = 0
		if self.date and self.agreement_close_date:	
			d1 = map(int,str(self.date).split("-"))
			d2 = map(int,str(self.agreement_close_date).split("-"))
			active_month = (datetime(d2[0],d2[1],d2[2]).year - datetime(d1[0],d1[1],d1[2]).year)*12 + (datetime(d2[0],d2[1],d2[2]).month - datetime(d1[0],d1[1],d1[2]).month)
    		self.number_of_active_agreement_months = active_month

    
    # changed_merchandise_status in Item Master 	
	def changed_merchandise_status(self):
		if self.merchandise_status and self.old_merchandise_status and self.merchandise_status != self.old_merchandise_status:
			item = frappe.get_doc("Item",self.product)
			item.update({
			"merchandise_status": self.merchandise_status,
			"old_status": item.merchandise_status
			})
			item.save(ignore_permissions = True)
			self.old_merchandise_status = self.merchandise_status

	# add comment on changing of agreement status		
	def comment_for_agreement_status_change(self):
		if self.agreement_status != self.old_agreement_status:
			comment = """ Agreement Status Changed From '{0}' To '{1}' """.format(self.old_agreement_status,self.agreement_status)
			self.add_comment("Comment",comment)
			self.old_agreement_status = self.agreement_status

	def comment_for_agreement_creation(self):
		comment = """The agreement {0} is started on the {1}  """.format(self.name,datetime.now().date())
		self.add_comment("Comment",comment)		


@frappe.whitelist()
def get_primary_address(customer):
	address = frappe.db.sql("""select name,address_line1,address_line2,city 
								from `tabAddress` 
								where customer = '{0}' 
								and is_primary_address = 1 """.format(customer),as_dict=1)
	return address

@frappe.whitelist()
def make_update_agreement(source_name, target_doc=None):
	print source_name
	customer_agreement = frappe.get_doc("Customer Agreement",source_name)
	target_doc = get_mapped_doc("Customer Agreement", source_name,
		{
			"Customer Agreement": {
				"doctype": "Customer Agreement",
			},
		}, target_doc)

	target_doc.document_type = "Updated"	
	target_doc.product = ""
	target_doc.product_category = ""
	target_doc.concade_product_name_and_category = ""
	target_doc.agreement_status_changed_date = ""
	target_doc.suspended_until = ""
	target_doc.suspended_from = ""
	target_doc.merchandise_status = ""
	target_doc.old_merchandise_status = ""
	target_doc.flag = 0
	target_doc.due_date_of_next_month = ""
	target_doc.payments_record = []
	target_doc.payment_day = ""
	target_doc.agreement_status = "Open"
	target_doc.duplicate_today_plus_90_days = customer_agreement.today_plus_90_days

	return target_doc


# filter Product
@frappe.whitelist()
def get_product(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""select item_name,merchandise_status from `tabItem` 
							where item_name not in (select product from `tabCustomer Agreement` 
													where agreement_status = "Open") 
							and (merchandise_status = "Used" or merchandise_status = "New" )
							and (item_name like '{txt}'
											or merchandise_status like '{txt}') limit 20 """.format(txt= "%%%s%%" % txt),as_list=1,debug=1)




