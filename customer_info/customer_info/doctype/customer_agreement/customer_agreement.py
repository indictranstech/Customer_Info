# -*- coding: utf-8 -*-
# Copyright (c) 2015, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import frappe.defaults
import json
from frappe import _
from frappe.utils import date_diff
from frappe.utils import flt, get_datetime, get_time, getdate
from frappe.utils import nowdate, getdate,add_months,add_days,get_last_day
from frappe.utils import now_datetime
from datetime import datetime, timedelta,date
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from customer_info.customer_info.doctype.payments_management.make_payment_history import make_payment_history


class CustomerAgreement(Document):	 
	def validate(self):
		self.change_sold_date_of_item()
		self.naming()
		self.comment_for_agreement_status_change()
		if not self.payments_record and self.name and self.due_date_of_next_month:
			self.check_date_diff_of_first_and_second_month_due_date()
			self.add_payments_record()	
		self.change_default_warehouse()
		self.changed_merchandise_status_according_to_agreement_status()
		self.payment_date_comment()

	def change_sold_date_of_item(self):
		"""
			change solde date when agreement is closed and agreement_closing_suspending_reason 
			in ["Early buy offer","90d SAC"] or Contract Term is over
		"""
		item = frappe.get_doc("Item",self.product)
		if self.agreement_status == "Closed" and self.agreement_closing_suspending_reason  in ["Early buy offer","90d SAC"]:
			item.old_sold_date = item.sold_date
			item.sold_date = datetime.now()
		
		elif self.agreement_status == "Closed" and self.agreement_closing_suspending_reason == "Contract Term is over" and self.merchandise_status == "Agreement over":	
			item.old_sold_date = item.sold_date
			item.sold_date = datetime.now()
			
		item.save(ignore_permissions=True)	

	"""
		change merchandise_status according to agreement_status
	"""	
	def changed_merchandise_status_according_to_agreement_status(self):	
		if self.agreement_status == "Closed" and self.agreement_closing_suspending_reason == "Return":
			self.merchandise_status = "Used"
		if self.agreement_status == "Suspended":
			self.merchandise_status = "Suspended"
		if  self.agreement_status == "Suspended" and self.agreement_closing_suspending_reason == "Fraud/Stolen":
			self.merchandise_status = "Stolen"
		if self.agreement_status == "Open" and self.agreement_closing_suspending_reason:
			self.merchandise_status = "New"
			self.agreement_closing_suspending_reason = ""
			self.suspended_from = ""
			self.agreement_close_date = ""				


			
	def change_default_warehouse(self):
		item = frappe.get_doc("Item",self.product)
		default_warehouse = item.default_warehouse
		if self.document_type == "Updated":
			old_agreement_item = frappe.get_doc("Item",frappe.get_doc("Customer Agreement",self.parent_name).product)	
			old_agreement_item.default_warehouse = "101 - Be kredito sandėlys - BK"
			old_agreement_item.save(ignore_permissions=True)
		if self.agreement_status == "Open":
			default_warehouse = "9101 – Prekė pas klientą - BK"
		if self.agreement_status in  ["Closed","Suspended"] and self.agreement_closing_suspending_reason in ["Return","Upgrade","Financial Difficulties","Temporary Leave"]:
			default_warehouse = "101 - Be kredito sandėlys - BK"	
		if self.agreement_status == "Closed" and self.agreement_closing_suspending_reason in ["Early buy offer","90d SAC","Contract Term is over"]:
			default_warehouse = "8101 – Ištrinta, grąžinta tiekėjui, sugadinta, naudojama įmonės reikmėms, pasibaigė sutartis, išsipirko anksčiau. - BK"
		if self.agreement_status == "Closed" and self.merchandise_status == "Stolen" and self.agreement_closing_suspending_reason == "Fraud/Stolen":
			default_warehouse = "9101 – Prekė pas klientą - BK"
		item.default_warehouse = default_warehouse
		item.save(ignore_permissions=True)

	def check_date_diff_of_first_and_second_month_due_date(self):
		if not self.update_due_date:
			due_date_of_next_month = datetime.strptime(self.due_date_of_next_month, '%Y-%m-%dT%H:%M:%S.%fZ') if isinstance(self.due_date_of_next_month, unicode) else getdate(self.due_date_of_next_month)
			diff_of_first_and_second_due_date = date_diff(due_date_of_next_month,self.date)
			if date_diff(due_date_of_next_month,self.date) > 44 :
				self.due_date_of_next_month = str(self.get_next_due_date(due_date_of_next_month,-1))+"T00:00:00.000Z"
				#frappe.throw("Decrease Payment Day")
			if date_diff(due_date_of_next_month,self.date) <= 14:
				self.due_date_of_next_month = str(self.get_next_due_date(due_date_of_next_month,1))+"T00:00:00.000Z"
				#frappe.throw("Increase Payment Day")

	def after_insert(self):
		self.add_bonus_for_this_agreement()
		self.comment_for_agreement_creation()
		self.change_sold_date_on_agreement_creation()  #change_sold_date_of_item_on_agreement_creation
		customer_agreement = frappe.get_doc("Customer Agreement",self.name)
		customer_agreement.balance = customer_agreement.monthly_rental_payment * float(customer_agreement.agreement_period)		
		customer_agreement.payments_left = customer_agreement.agreement_period
		customer_agreement.save(ignore_permissions=True)

	def add_bonus_for_this_agreement(self):
		customer_agreement = frappe.db.sql("""select name from `tabCustomer Agreement`
											where agreement_status = "Open" and  customer = '{0}'  
											and name != "{1}" order by creation desc limit 1""".format(self.customer,self.name),as_list=1)
		if  customer_agreement and customer_agreement[0][0] != self.name:
			customer_agreement_doc = frappe.get_doc("Customer Agreement",self.name)
			if customer_agreement_doc.document_type == "New":
				customer_agreement_doc.new_agreement_bonus = 20
				customer_agreement_doc.bonus = 20
				customer_agreement_doc.save(ignore_permissions=True)
				customer = frappe.get_doc("Customer",self.customer)
				customer.bonus = customer.bonus + 20
				customer.save(ignore_permissions=True)


	def change_sold_date_on_agreement_creation(self):
		item = frappe.get_doc("Item",self.product)
		item.old_sold_date = item.sold_date
		item.sold_date = datetime.now()
		item.save(ignore_permissions=True) 			

	def on_update(self):
		#self.payment_date_comment()
		self.get_agreement_closed_date()
		self.changed_merchandise_status()


	# For Naming	
	def naming(self):	
		new_name_list = []
		old_name_list = []
		counter = 1
		count = 10001		
		if self.document_type == "New" and self.flag == 0:
			old_name = frappe.db.sql("""select name from `tabCustomer Agreement` 
										where document_type = "New" 
										order by replace(name,"BK-","")*1 """,as_list=1)
			if len(old_name) > 0:
				new_name_list = old_name[-1][0].split("-")
				count = int(new_name_list[-1]) + 1
			self.name = "BK-0" + str(count)
			self.parent_name = self.name
			self.flag = 1

		elif self.document_type == "Updated" and self.flag == 0:
			parent_name = frappe.db.sql("""select name from `tabCustomer Agreement` 
										where parent_name like "{0}" 
										order by replace(name,"{0}","")*1 desc""".format(self.parent_name),as_list=1)
			
			parent = frappe.get_doc("Customer Agreement", self.agreement_no)
			if parent and parent.agreement_status != "Updated":
				parent.update({
					"agreement_status": "Updated",
					"merchandise_status": "Used",
					"old_agreement_status":parent.agreement_status,
					"agreement_update_date":datetime.now()
				})
				parent.save(ignore_permissions = True)


			if len(parent_name) == 1 and len(parent_name[0][0].split('-')) == 2:
				counter = 1

			elif len(parent_name) > 1 and (len(parent_name[0][0].split('-')) > 1 and len(parent_name[0][0].split('-')) == 2):			
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
		current_date = datetime.strptime(self.due_date_of_next_month, '%Y-%m-%dT%H:%M:%S.%fZ') if isinstance(self.due_date_of_next_month, unicode) else getdate(self.due_date_of_next_month)
		list_of_payments_record = []
		list_of_payments_record.append({
		'no_of_payments':'Payment 1',
		'monthly_rental_amount':self.monthly_rental_payment,
		'due_date':self.date,
		'payment_id':self.name + '-' + 'Payment 1'
		})	
		for i in range(1,int(self.agreement_period)):
			list_of_payments_record.append({
				'no_of_payments':'Payment {0}'.format(i+1),
				'monthly_rental_amount':self.monthly_rental_payment,
				'due_date':self.get_next_due_date(current_date,i-1),
				'payment_id':self.name + '-' + 'Payment {0}'.format(i+1)
				})

		for d in list_of_payments_record:
			nl = self.append('payments_record', {})
			nl.no_of_payments = d['no_of_payments']
			nl.monthly_rental_amount = d['monthly_rental_amount']
			nl.due_date = d['due_date']
			nl.payment_id = d['payment_id']	

	# get date after i month on changeing payment day	
	def change_due_dates_in_child_table(self):
		if not self.update_due_date:
			self.check_date_diff_of_first_and_second_month_due_date()
			due_date_of_next_month = datetime.strptime(self.due_date_of_next_month, '%Y-%m-%dT%H:%M:%S.%fZ')
			for i,row in enumerate(self.payments_record):
				if row.idx > 1 and row.check_box_of_submit == 0:
					row.update({
						"due_date":self.get_next_due_date(due_date_of_next_month,i-1)
					})

	# get date after i month
	def get_next_due_date(self,date,i):
		add_month_to_date = add_months(date,i)
		if isinstance(add_month_to_date, datetime):
			return add_month_to_date.date()	
		else:
			return add_month_to_date

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
			item.merchandise_status = self.merchandise_status
			item.save(ignore_permissions = True)
			item.old_status = self.merchandise_status
			item.save(ignore_permissions = True)
			# item.update({
			# "merchandise_status": self.merchandise_status,
			# "old_status": item.merchandise_status
			# })
		self.old_merchandise_status = self.merchandise_status


	# add comment on changing of agreement status		
	def comment_for_agreement_status_change(self):
		if self.agreement_status != self.old_agreement_status:
			comment = """ Agreement Status Changed From '{0}' To '{1}' """.format(self.old_agreement_status,self.agreement_status)
			self.add_comment("Comment",comment)
			self.old_agreement_status = self.agreement_status

	def comment_for_agreement_creation(self):
		#comment = """The agreement {0} is started on the {1}  """.format(self.name,datetime.now().date())
		comment = """The agreement {0} is started on the {1}  """.format(self.name,self.date)
		self.add_comment("Comment",comment)



def reset_contact_result_of_sent_sms():
	now_date = datetime.now().date()
	customer_agreement = frappe.get_all("Customer Agreement", fields=["name"],filters={"agreement_status": "Open","contact_result":"Sent SMS/Email"})
	for agreement in customer_agreement:
		agreement_doc = frappe.get_doc("Customer Agreement",agreement)
		if agreement_doc.suspension_date <= now_date:
			agreement_doc.contact_result = ""
			agreement_doc.suspension_date = ""
		agreement_doc.save(ignore_permissions=True)	



def payments_done_by_scheduler():
	"""
	If we have enough receivables then make auto payment_date
	get all customers
	get all open agreements of customers
	get remaining payments of all agreements comming in current month and pending of last months
	add payments according to due_date
	add bonus for payments
	process payments 
	reduce receivables
	"""
	customer_list = frappe.db.sql("""select name from `tabCustomer` and customer_group = 'Individual' """,as_list=1)

	now_date = datetime.now().date()
	firstDay_of_month = date(now_date.year, now_date.month, 1)
	last_day_of_month = get_last_day(now_date)
	
	for name in [i[0] for i in customer_list]:
		customer_bonus = []
		customer_agreement = frappe.db.sql("""select name from `tabCustomer Agreement`
								where agreement_status = "Open" and customer = '{0}' """.format(name),as_list=1)
		
		payments_detalis_list = []
		payment_ids_list = []
		monthly_rental_amount = []
		merchandise_status = ""
		args = {'values':{}}
		args['receivables'] = frappe.get_doc("Customer",name).receivables
		for agreement in [e[0] for e in customer_agreement]:
			customer_agreement = frappe.get_doc("Customer Agreement",agreement)
			add_bonus_of_one_eur = []
			add_bonus_of_two_eur = []
			merchandise_status += str(customer_agreement.name)+"/"+str(customer_agreement.merchandise_status)+"/"+str(customer_agreement.agreement_closing_suspending_reason)+","
			for row in customer_agreement.payments_record:
				#if row.check_box_of_submit == 0 and getdate(row.due_date) >= firstDay_of_month and getdate(row.due_date) <= last_day_of_month and getdate(row.due_date) == now_date:
				if row.check_box_of_submit == 0 and firstDay_of_month <= getdate(row.due_date) <= last_day_of_month and getdate(row.due_date) == now_date:
					customer = frappe.get_doc("Customer",name)
					receivables = customer.receivables
					if float(receivables) >= float(row.monthly_rental_amount):
						payment_ids_list.append(row.payment_id)
						payments_detalis_list.append(str(row.payment_id)+"/"+str(row.due_date)+"/"+str(row.monthly_rental_amount)+"/"+str(row.payment_date))
						monthly_rental_amount.append(row.monthly_rental_amount)
						if row.idx != 1:
							add_bonus_of_one_eur.append(row.idx)
						row.update({
							"check_box":1,
							"check_box_of_submit":1,
							"payment_date":now_date,
							'add_bonus_to_this_payment':1 if row.idx != 1 else 0
						})
						row.save(ignore_permissions = True)

						customer.receivables = receivables - row.monthly_rental_amount
						customer.save(ignore_permissions=True)	

				if row.check_box_of_submit == 0 and firstDay_of_month <= getdate(row.due_date) <= last_day_of_month and getdate(row.due_date) > now_date:
					customer = frappe.get_doc("Customer",name)
					receivables = customer.receivables
					if float(receivables) >= float(row.monthly_rental_amount):
						payment_ids_list.append(row.payment_id)
						payments_detalis_list.append(str(row.payment_id)+"/"+str(row.due_date)+"/"+str(row.monthly_rental_amount)+"/"+str(row.payment_date))
						monthly_rental_amount.append(row.monthly_rental_amount)
						if row.idx != 1:
							add_bonus_of_two_eur.append(row.idx)
						row.update({
							"check_box":1,
							"check_box_of_submit":1,
							"payment_date":now_date,
							'add_bonus_to_this_payment':1 if row.idx != 1 else 0
						})
						row.save(ignore_permissions = True)

						customer.receivables = receivables - row.monthly_rental_amount
						customer.save(ignore_permissions=True)		
						
				if row.check_box_of_submit == 0 and getdate(row.due_date) < firstDay_of_month:
					customer = frappe.get_doc("Customer",name)
					receivables = customer.receivables
					if float(receivables) >= float(row.monthly_rental_amount):
						payment_ids_list.append(row.payment_id)
						payments_detalis_list.append(str(row.payment_id)+"/"+str(row.due_date)+"/"+str(row.monthly_rental_amount)+"/"+str(row.payment_date))
						monthly_rental_amount.append(row.monthly_rental_amount)
						row.update({
							"check_box":1,
							"check_box_of_submit":1,
							"payment_date":now_date,
						})
						row.save(ignore_permissions = True)

						customer.receivables = receivables - row.monthly_rental_amount
						customer.save(ignore_permissions=True)

		if len(payment_ids_list) > 0:
			customer_agreement.payment_on_time_bonus = customer_agreement.payment_on_time_bonus + len(add_bonus_of_one_eur)*1
			customer_agreement.early_payments_bonus = customer_agreement.early_payments_bonus +  len(add_bonus_of_two_eur)*2	
			customer_agreement.bonus = customer_agreement.bonus + len(add_bonus_of_one_eur)*1 + len(add_bonus_of_two_eur)*2
			customer_bonus.append(customer_agreement.bonus)
			customer_agreement.save(ignore_permissions = True)
			customer = frappe.get_doc("Customer",name)
			customer.bonus += sum(customer_bonus) if customer_bonus else 0
			customer.save(ignore_permissions=True)

			set_values_in_agreement(customer_agreement)
			args['assigned_bonus_discount'] = ""
			args['customer'] = name
			args['add_in_receivables'] = frappe.get_doc("Customer",name).receivables
			args['payment_date'] = str(now_date)
			args['rental_payment'] = sum(monthly_rental_amount)
			args['payment_type'] = "Normal Payment"
			args['late_fees'] = 0
			args['values']['amount_paid_by_customer'] = 0
			args['values']['bank_card'] = 0
			args['values']['bank_transfer'] = 0
			args['values']['discount'] = 0
			args['values']['bonus'] = 0
			args['new_bonus'] = len(add_bonus_of_one_eur)*1 + len(add_bonus_of_two_eur)*2
			args['total_charges'] = 0
			args['total_amount'] = 0
			make_payment_history(args,payments_detalis_list,payment_ids_list,"Normal Payment",merchandise_status,"","Rental Payment")
	

def set_values_in_agreement(customer_agreement):
	payment_made = []

	if customer_agreement.payments_record:
		for row in customer_agreement.payments_record:
			if row.check_box_of_submit == 1:
				payment_made.append(row.monthly_rental_amount)				
		for index,row in enumerate(customer_agreement.payments_record):
			if row.check_box_of_submit == 0 and row.idx > 1 and row.idx < len(customer_agreement.payments_record):
				customer_agreement.current_due_date = row.due_date
				customer_agreement.next_due_date = customer_agreement.payments_record[index+1].due_date#get_next_due_date(row.due_date,1)
				break
			if row.check_box_of_submit == 0 and row.idx == 1:
				customer_agreement.current_due_date = customer_agreement.date
				customer_agreement.next_due_date = customer_agreement.payments_record[index+1].due_date#get_next_due_date(customer_agreement.due_date_of_next_month,0)
				break
			if row.check_box_of_submit == 0 and row.idx == len(customer_agreement.payments_record):
				customer_agreement.current_due_date = row.due_date
				customer_agreement.next_due_date = row.due_date
				break
	payment_made = map(float,payment_made)

	if customer_agreement.payments_record and customer_agreement.date:
		customer_agreement.payments_made = sum(payment_made)
		customer_agreement.number_of_payments = 0
		customer_agreement.discount_updated = "No"
		customer_agreement.payments_left = len(customer_agreement.payments_record) - len(payment_made)
		customer_agreement.balance = (len(customer_agreement.payments_record) - len(payment_made)) * customer_agreement.monthly_rental_payment
	customer_agreement.save(ignore_permissions=True)


@frappe.whitelist()
def get_primary_address(customer):
	address = frappe.db.sql("""select name,address_line1,address_line2,city 
								from `tabAddress` 
								where customer = '{0}' 
								and is_primary_address = 1 """.format(customer),as_dict=1)
	return address

@frappe.whitelist()
def update_due_dates_of_payments(update_date,name):
	agreement = frappe.get_doc("Customer Agreement",name)
	counter_of_row = 0
	date_dict = {}
	for row in agreement.payments_record:
		if row.check_box_of_submit == 0:
			date_dict[row.payment_id] = get_next_due_date(update_date,counter_of_row)
			counter_of_row += 1
	return date_dict

@frappe.whitelist()
def get_next_due_date(date,i):
	add_month_to_date = add_months(date,i)
	return add_month_to_date

# @frappe.whitelist()
# def make_update_agreement(source_name, target_doc=None):
# 	customer_agreement = frappe.get_doc("Customer Agreement",source_name)
# 	target_doc = get_mapped_doc("Customer Agreement", source_name,
# 		{
# 			"Customer Agreement": {
# 				"doctype": "Customer Agreement",
# 			},
# 		}, target_doc)

# 	target_doc.document_type = "Updated"	
# 	target_doc.payments_left = ""
# 	target_doc.balance = 0
# 	target_doc.payments_made = 0
# 	target_doc.amonut_of_payment_left = ""
# 	target_doc.late_payments = 0
# 	target_doc.total_due = 0
# 	target_doc.late_fees = 0
# 	target_doc.number_of_payments = 0
# 	target_doc.bonus = 0
# 	target_doc.product = ""
# 	target_doc.product_category = ""
# 	#target_doc.concade_product_name_and_category = ""
# 	target_doc.agreement_status_changed_date = ""
# 	target_doc.suspended_until = ""
# 	target_doc.suspended_from = ""
# 	target_doc.merchandise_status = ""
# 	target_doc.old_merchandise_status = ""
# 	target_doc.flag = 0
# 	target_doc.due_date_of_next_month = ""
# 	target_doc.payments_record = []
# 	target_doc.payment_day = ""
# 	target_doc.agreement_status = "Open"
# 	target_doc.duplicate_today_plus_90_days = customer_agreement.today_plus_90_days
# 	target_doc.contact_result = ""
# 	target_doc.suspension_date = ""
# 	target_doc.amount_of_contact_result = 0
# 	target_doc.call_commitment = ""
# 	target_doc.new_agreement_bonus = 0
# 	target_doc.early_payments_bonus = 0
# 	target_doc.payment_on_time_bonus = 0

# 	return target_doc


# filter Product
@frappe.whitelist()
def get_product(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""select name,merchandise_status 
								from `tabItem` 
								where name not in 
									(select product from `tabCustomer Agreement` 
										where agreement_status = "Open") 
									and merchandise_status in ("Used","New" )
									and (item_name like '{txt}'
									or merchandise_status like '{txt}') 
								limit 20 """.format(txt= "%%%s%%" % txt),as_list=1)


@frappe.whitelist()
def set_bonus_in_customer(customer,bonus):
	customer = frappe.get_doc("Customer",customer)
	previuos_bonus = customer.bonus
	total_bonus = previuos_bonus + float(bonus)
	customer.update({
		"bonus":total_bonus
	})
	#if float(bonus) > 0:
		#comment = """ {0} EUR Bonus Added """.format(bonus)
		#customer.add_comment("Comment",comment)
	customer.save(ignore_permissions=True)

