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
# from customer_info.customer_info.doctype.payments_management.payments_management import get_bonus_summary
from datetime import datetime, timedelta,date
from frappe.utils import flt, get_datetime, get_time, getdate
from customer_info.customer_info.report.customer_agreements_report.financial import xirr
from numpy import irr



class CustomerAgreement(Document):	 
	def validate(self):
		#self.change_sold_date_of_item()
		self.naming()
		self.comment_for_agreement_status_change()
		if not self.payments_record and self.name and self.due_date_of_next_month:
			self.check_date_diff_of_first_and_second_month_due_date() # check days for 44
			self.add_payments_record()	#add payments record
		self.change_default_warehouse()
		self.changed_merchandise_status_according_to_agreement_status()
		self.payment_date_comment()
		self.get_active_agreement_month()
		self.merchandise_return_agreement_closing()
		#self.remove_bonus_of_customer()
	
	def merchandise_return_agreement_closing(self):
		if self.merchandise_status == "Returned to supplier":		
			item =frappe.get_doc("Item",self.product)
			default_warehouse = "8101 – Ištrinta, grąžinta tiekėjui, sugadinta, naudojama įmonės reikmėms, pasibaigė sutartis, išsipirko anksčiau. - BK"
			item.default_warehouse = default_warehouse
			item.save(ignore_permissions=True)

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
			pass
			# self.merchandise_status = "Suspended"

		if  self.agreement_status == "Suspended" and self.agreement_closing_suspending_reason == "Fraud/Stolen":
			self.merchandise_status = "Stolen"
		if self.agreement_status == "Open" and self.agreement_closing_suspending_reason:
			self.merchandise_status = "New"
			self.agreement_closing_suspending_reason = ""
			self.suspended_from = ""
			self.agreement_close_date = ""

	"""
	change default ware house of item according to agreement_status
	"""		
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
		self.add_item_log()

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
		#self.get_agreement_closed_date()
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
	# def get_agreement_closed_date(self):
	# 	if self.agreement_close_date and self.agreement_status == "Closed":
	# 		self.get_active_agreement_month()

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


	def remove_bonus_of_customer(self):
		if self.agreement_status == "Closed":
			agreements_status = frappe.db.sql("""select agreement_status
										from `tabCustomer Agreement` where customer = '{0}' 
										and name <> '{1}'
										and agreement_status <> 'Updated' """.format(self.customer,self.name),as_list=1)
			if all(status == "Closed" for status in [s[0] for s in agreements_status]):
				customer_doc = frappe.get_doc("Customer",self.customer)
				customer_doc.cancelled_bonus = float(customer_doc.cancelled_bonus) + float(customer_doc.bonus)
				customer_doc.bonus = 0
				customer_doc.save(ignore_permissions=True)

	def add_item_log(self):
		product = self.product
		agreement =self.name
		if product and agreement:
			comment = "{0} is assigned for the agreement <b> <a href ='/desk#Form/Customer%20Agreement/{1}'> [{1}] </a></b> on the {2}".format(product,agreement,self.date)
			product_doc = frappe.get_doc("Item",product)
			comment = comment+"\n"+product_doc.log if product_doc.log else comment
			product_doc.add_comment("Comment",comment)  
			product_doc.save(ignore_permissions=1)
			
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
	from customer_info.customer_info.doctype.payments_management.payments_management import get_bonus_summary
	"""
	If we have enough receivables then make auto payment_date
	get all customers
	get all open agreements of customers
	get remaining payments of all agreements comming in current month and pending of last months
	add payments according to due_date
	add bonus for payments
	process payments
	reduce receivables
	Early payments are stopped from normal auto payments 
	Early payments are process using flagged receiable api.
	"""
	customer_list = frappe.db.sql("""select name from `tabCustomer` where customer_group = 'Individual' """,as_list=1)

	now_date = datetime.now().date()
	firstDay_of_month = date(now_date.year, now_date.month, 1)
	last_day_of_month = get_last_day(now_date)
	for name in [customer[0] for customer in customer_list]:
		get_bonus_summary(name)
		customer_agreement = frappe.db.sql("""select name from `tabCustomer Agreement`
								where agreement_status = "Open" and customer = '{0}' """.format(name),as_list=1)
	
		args = {'values':{}}
		args['receivables'] = frappe.get_doc("Customer",name).receivables
		for agreement in [e[0] for e in customer_agreement]:
			customer_bonus = []
			payments_detalis_list = []
			payment_ids_list = []
			monthly_rental_amount = []
			merchandise_status = ""
			customer_agreement = frappe.get_doc("Customer Agreement",agreement)
			add_bonus_of_one_eur = []
			add_bonus_of_two_eur = []
			late_payments = []
			late_fees = []
			merchandise_status += str(customer_agreement.name)+"/"+str(customer_agreement.merchandise_status)+"/"+str(customer_agreement.agreement_closing_suspending_reason)+","
			for row in customer_agreement.payments_record:
				#if row.check_box_of_submit == 0 and getdate(row.due_date) >= firstDay_of_month and getdate(row.due_date) <= last_day_of_month and getdate(row.due_date) == now_date:
				
				# Late Payment
				if row.check_box_of_submit == 0 and (getdate(row.due_date) < firstDay_of_month or getdate(row.due_date) < now_date):
					customer = frappe.get_doc("Customer",name)
					receivables = customer.receivables
					if date_diff(now_date,row.due_date) > 3:
						no_of_late_days = date_diff(row.payment_date,row.due_date) - 3
						late_payments.append(row.monthly_rental_amount)
						if customer_agreement.late_fees_updated == "No":
							customer_agreement.late_fees = "{0:.2f}".format(float(no_of_late_days * customer_agreement.monthly_rental_payment * (customer_agreement.late_fees_rate/100)))
						late_fees.append(customer_agreement.late_fees)
					total_charges = float(row.monthly_rental_amount) + float(customer_agreement.late_fees)
					if float(receivables) >= total_charges:
						payment_ids_list.append(row.payment_id)
						payments_detalis_list.append(str(row.payment_id)+"/"+str(row.due_date)+"/"+str(row.monthly_rental_amount)+"/"+str(now_date))
						monthly_rental_amount.append(row.monthly_rental_amount)
						row.update({
							"check_box":1,
							"check_box_of_submit":1,
							"payment_date":now_date,
						})
						row.save(ignore_permissions = True)
						customer.receivables = receivables - total_charges
						customer.save(ignore_permissions=True)
						auto_payment_notification(customer.name,customer_agreement.name,total_charges)	

				# Todays Payment
				if row.check_box_of_submit == 0 and getdate(row.due_date) == now_date:
					customer = frappe.get_doc("Customer",name)
					receivables = customer.receivables
					if date_diff(now_date,row.due_date) > 3:
						no_of_late_days = date_diff(row.payment_date,row.due_date) - 3
						late_payments.append(row.monthly_rental_amount)
						if customer_agreement.late_fees_updated == "No":
							customer_agreement.late_fees = "{0:.2f}".format(float(no_of_late_days * customer_agreement.monthly_rental_payment * (customer_agreement.late_fees_rate/100)))
						late_fees.append(customer_agreement.late_fees)
					total_charges = float(row.monthly_rental_amount) + float(customer_agreement.late_fees)
					if float(receivables) >= total_charges:
						payment_ids_list.append(row.payment_id)
						payments_detalis_list.append(str(row.payment_id)+"/"+str(row.due_date)+"/"+str(row.monthly_rental_amount)+"/"+str(now_date))
						monthly_rental_amount.append(row.monthly_rental_amount)
						if row.idx != 1:
							add_bonus_of_one_eur.append(row.idx)
						row.update({
							"check_box":1,
							"check_box_of_submit":1,
							"payment_date":now_date,
							'add_bonus_to_this_payment':1 if row.idx != 1 else 0,
							'bonus_type':"On Time Bonus" if row.idx != 1 else ""
						})
						row.save(ignore_permissions = True)
						customer.receivables = receivables - total_charges
						customer.save(ignore_permissions=True)
						auto_payment_notification(customer.name,customer_agreement.name,total_charges)	

				# (Early Payements)Future Payments Stopped in auto payments 
				# Early Payments 
				# if row.check_box_of_submit == 0 and firstDay_of_month <= getdate(row.due_date) <= last_day_of_month and getdate(row.due_date) > now_date:
				# 	customer = frappe.get_doc("Customer",name)
				# 	receivables = customer.receivables
				# 	if date_diff(now_date,row.due_date) > 3:
				# 		no_of_late_days = date_diff(row.payment_date,row.due_date) - 3
				# 		late_payments.append(row.monthly_rental_amount)
				# 		if customer_agreement.late_fees_updated == "No":
				# 			customer_agreement.late_fees = "{0:.2f}".format(float(no_of_late_days * customer_agreement.monthly_rental_payment * (customer_agreement.late_fees_rate/100)))					
				# 		late_fees.append(customer_agreement.late_fees)
				# 	total_charges = float(row.monthly_rental_amount) + float(customer_agreement.late_fees)
				# 	if float(receivables) >= total_charges:
				# 		payment_ids_list.append(row.payment_id)
				# 		payments_detalis_list.append(str(row.payment_id)+"/"+str(row.due_date)+"/"+str(row.monthly_rental_amount)+"/"+str(now_date))
				# 		monthly_rental_amount.append(row.monthly_rental_amount)
				# 		if row.idx != 1:
				# 			add_bonus_of_two_eur.append(row.idx)
				# 		row.update({
				# 			"check_box":1,
				# 			"check_box_of_submit":1,
				# 			"payment_date":now_date,
				# 			'add_bonus_to_this_payment':1 if row.idx != 1 else 0,
				# 			'bonus_type':"Early Bonus" if row.idx != 1 else "",
				# 		})
				# 		row.save(ignore_permissions = True)
				# 		customer.receivables = receivables - total_charges
				# 		customer.save(ignore_permissions=True)		
						
				#if row.check_box_of_submit == 0 and (getdate(row.due_date) < firstDay_of_month or (firstDay_of_month <= getdate(row.due_date) <= last_day_of_month and getdate(row.due_date) < now_date)):
				
			if len(payment_ids_list) > 0:
				customer_agreement.payment_on_time_bonus = customer_agreement.payment_on_time_bonus + len(add_bonus_of_one_eur)*1
				customer_agreement.early_payments_bonus = customer_agreement.early_payments_bonus +  len(add_bonus_of_two_eur)*2
				customer_agreement.bonus = customer_agreement.bonus + len(add_bonus_of_one_eur)*1 + len(add_bonus_of_two_eur)*2
				customer_agreement.late_payment = sum(late_payments)
				customer_bonus.append(customer_agreement.bonus)
				customer_agreement.save(ignore_permissions = True)
				customer = frappe.get_doc("Customer",name)
				customer.bonus = sum(customer_bonus) if customer_bonus else 0
				customer.save(ignore_permissions=True)

				set_values_in_agreement(customer_agreement)
				args['assigned_bonus_discount'] = ""
				args['customer'] = name
				args['add_in_receivables'] = frappe.get_doc("Customer",name).receivables
				args['payment_date'] = str(now_date)
				args['rental_payment'] = sum(monthly_rental_amount)
				args['payment_type'] = "Normal Payment"
				args['late_fees'] = sum(map(float,late_fees))
				args['values']['amount_paid_by_customer'] = 0
				args['values']['bank_card'] = 0
				args['values']['bank_transfer'] = 0
				args['values']['discount'] = 0
				args['values']['bonus'] = 0
				args['new_bonus'] = len(add_bonus_of_one_eur)*1 + len(add_bonus_of_two_eur)*2
				args['total_charges'] = 0
				args['total_amount'] = 0
				args['special_associate'] = "Automatic"
				make_payment_history(args,payments_detalis_list,payment_ids_list,"Normal Payment",merchandise_status,"","Rental Payment")
				# auto_payment(customer_agreement.name,args,payments_detalis_list)

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
		customer_agreement.late_fees_updated = "No"
		customer_agreement.payments_left = len(customer_agreement.payments_record) - len(payment_made)
		
		if float(customer_agreement.payments_left) == 0:
			customer_agreement.agreement_status = "Closed"
			customer_agreement.agreement_closing_suspending_reason = "Contract Term is over"
			customer_agreement.merchandise_status = "Agreement over"
			customer_agreement.agreement_close_date = datetime.now().date()
			closed_agreement_notification(customer_agreement.customer,customer_agreement.name)
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

# not working for now
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


#sync item price
@frappe.whitelist()
def update_90sac_and_monthly_rental(customer_agreement):
	agreement_doc = frappe.get_doc("Customer Agreement",customer_agreement)
	product_doc = frappe.get_doc("Item",agreement_doc.product)
	if agreement_doc.monthly_rental_payment != product_doc.monthly_rental_payment and agreement_doc.s90d_sac_price != product_doc.s90d_sac_price:
		return {"s90d_sac_price":product_doc.s90d_sac_price,"monthly_rental_payment":product_doc.monthly_rental_payment} if update_value(agreement_doc) == True else frappe.throw(update_value(agreement_doc))
	else:
		frappe.msgprint("Item Price Already Sync")	

def update_value(agreement_doc):
	result = True
	for row in agreement_doc.payments_record:
		if row.check_box_of_submit == 1:
			result = ("Please refund already made payments of <b>"+row.parent+"</b> before Sync Item Price In\
							\n <a href=http://"+frappe.request.host+"/desk#payments-received?agreement="+agreement_doc.name+" target='blank'><b>Payments Received Report</b></a>")
			break
	return result

# Auto Payment Email Notification
@frappe.whitelist()
def auto_payment(customer_agreement,args,payments_detalis_list):
	if customer_agreement:
		cust_agree_doc = frappe.get_doc("Customer Agreement",customer_agreement)
		customer = cust_agree_doc.customer
		first_name = frappe.db.get_value("Customer",{"name":customer},"first_name")
		last_name = frappe.db.get_value("Customer",{"name":customer},"last_name")
		if first_name: 
			customer = first_name 
		if last_name:
			customer += " " + last_name 

@frappe.whitelist()
def auto_payment_notification(customer,agreement,last_payment):
	date = frappe.utils.data.now_datetime()
	frappe.sendmail(
				#recipients = "sukrut.j@indictranstech.com",
				recipients = "lukas@povilauskas.lt",
				sender = "pagalba@bekredito.lt",
				subject = "Auto Payment Notification For Agreement "+ agreement,
				message = frappe.render_template("templates/email/auto_payment_notification.html", {"last_payment":last_payment,"customer": customer,"agreement":agreement,"date": date}),
	)

@frappe.whitelist()
def closed_agreement_notification(customer,agreement):
	date = frappe.utils.data.now_datetime()
	frappe.sendmail(
				#recipients = "sukrut.j@indictranstech.com",
				recipients = "lukas@povilauskas.lt",
				sender = "pagalba@bekredito.lt",
				subject = "Closed Agreemnet Notification For Agreement "+ agreement,
				message = frappe.render_template("templates/email/closed_agreement_notification.html", {"agreement":agreement,"customer": customer,"date": date}),
	)


# Schedular for Calculating IRR and XIRR values will save to respective customer Agreement
def get_IRR_XIRR():
	now_date = datetime.now().date()
	result = frappe.db.sql("""select 
				cus.first_name,
				cus.last_name,
				cus.prersonal_code,
				ca.name,
				ca.agreement_status,
				ca.date,
				ca.agreement_close_date,
				ca.product_category,
				item.brand,
				format(ca.monthly_rental_payment,2),
				format(ca.agreement_period,2),
				format(ca.s90d_sac_price,2),
				item.purchase_price_with_vat,
				item.wholesale_price,
				item.transportation_costs_incoming,
				item.transportation_costs_outgoing,
				format((ca.s90d_sac_price - item.purchase_price_with_vat)/item.purchase_price_with_vat * 100,2),
				format((ca.monthly_rental_payment * ca.agreement_period -item.purchase_price_with_vat)/item.purchase_price_with_vat * 100,2),
				format(ca.monthly_rental_payment * ca.agreement_period,2),
				format(ca.payments_made,2),
				case when ca.agreement_status = "Closed" then ca.agreement_close_date
				when ca.agreement_status = "Suspended" then ca.suspended_from
				else "-" end as agreement_closing_suspension_date,
				case when ca.agreement_closing_suspending_reason = "Early buy offer" then
				concat(ca.early_buy_discount_percentage,"% ",ca.agreement_closing_suspending_reason)
				else ca.agreement_closing_suspending_reason end as agreement_closing_suspension_reason,
				case when ca.agreement_close_date then period_diff(date_format(ca.agreement_close_date, "%Y%m"), date_format(ca.date, "%Y%m")) else period_diff(date_format(now(), "%Y%m"), date_format(ca.date, "%Y%m")) end as active_agreement_months,
				format(ca.payments_made - item.purchase_price_with_vat,2),
				format((ca.payments_made - item.purchase_price_with_vat)/item.purchase_price_with_vat * 100,2),
				format(ca.payments_left,2) as remaining_months_till_the_end_of_agreement,
				ca.campaign_discount_code,
				ca.irr,
				ca.xirr
				from `tabCustomer Agreement` ca ,`tabCustomer` cus,`tabItem` item
				where ca.customer = cus.name and ca.product = item.name""",as_list=1)
	
	for row in result:
		# IIR Calculation		
		# print "Agree",row[3]
		if frappe.get_doc("Customer Agreement",row[3]).agreement_status == "Open":	
			if row[12] and float(row[12])>0:
				if row[13] and float(row[13]) > 0.0:
					payments_rental_amount =[]
					submitted_payments_rental_amount = [-(float(row[13])+float(row[14])+float(row[15]))]
					customer_agreement_doc = frappe.get_doc("Customer Agreement",row[3])
					payments_record_doc = customer_agreement_doc.payments_record
					if payments_record_doc:
						for payment_r in payments_record_doc:
							if payment_r.check_box_of_submit == 1:
								if date_diff(payment_r.payment_date,payment_r.due_date) > 1:
									payments_rental_amount.append(0)
								else:
									payments_rental_amount.append(payment_r.monthly_rental_amount)
						submitted_payments_rental_amount.extend(payments_rental_amount) # Processed Payments
						submitted_payments_rental_amount.extend([payment.get("monthly_rental_amount") for payment in frappe.get_doc("Customer Agreement",row[3]).payments_record if payment.get("check_box_of_submit") == 0 and getdate(payment.get("due_date")) >= getdate(now_date)])	# Early Payents (Future Payments)				try:
						frappe.db.set_value("Customer Agreement",row[3],"irr_calculation_value",str(submitted_payments_rental_amount))
						try:
							print "submitted_payments_rental_amount",submitted_payments_rental_amount
							row[27] = round(irr(submitted_payments_rental_amount),5) if len(submitted_payments_rental_amount) > 1 else ""
							if row[27]:						
								IRR = round((float(row[27]) * 12 * 100),2)
								if IRR:
									frappe.db.set_value("Customer Agreement",row[3],"irr",IRR)
						except Exception,e:
							row[27] = ""
							frappe.db.set_value("Customer Agreement",row[3],"irr",row[27]) 
				else:
					row[27] ="Wholesale price is not set"
					frappe.db.set_value("Customer Agreement",row[3],"irr",row[27])
		elif frappe.get_doc("Customer Agreement",row[3]).agreement_status == "Closed":
			if row[12] and float(row[12]) > 0 and row[21] =="Contract Term is over" :  
				if row[13] and float(row[13]) > 0.0:
					payments_rental_amount =[]
					submitted_payments_rental_amount = [-(float(row[13])+float(row[14])+float(row[15]))]
					customer_agreement_doc = frappe.get_doc("Customer Agreement",row[3])
					payments_record_doc = customer_agreement_doc.payments_record
					if payments_record_doc:
						for payment_r in payments_record_doc:
							if payment_r.check_box_of_submit == 1:
								if date_diff(payment_r.payment_date,payment_r.due_date) > 1:
									payments_rental_amount.append(0)
								else:
									payments_rental_amount.append(payment_r.monthly_rental_amount)								
							# payments_rental_amount.append(payment_r.monthly_rental_amount)
						submitted_payments_rental_amount.extend(payments_rental_amount) # Processed Payments
						frappe.db.set_value("Customer Agreement",row[3],"irr_calculation_value",str(submitted_payments_rental_amount))
						try:
							# print "submitted_payments_rental_amount",submitted_payments_rental_amount
							row[27] = round(irr(submitted_payments_rental_amount),5) if len(submitted_payments_rental_amount) > 1 else ""
							if row[27]:
								IRR = round((float(row[27]) * 12 * 100),2)
								# print "IRR",IRR
								if IRR:
									frappe.db.set_value("Customer Agreement",row[3],"irr",IRR)
									# print "Updated"
						except Exception,e:
							row[27] = ""
							frappe.db.set_value("Customer Agreement",row[3],"irr",row[27])	
						# print "\nContract Term is over IRR",row[27]
				else:
					row[27] ="Wholesale price is not set"
					frappe.db.set_value("Customer Agreement",row[3],"irr",row[27])
			
			if row[12] and float(row[12]) > 0 and row[21] =="90d SAC":
				if row[13] and float(row[13]) > 0.0:
					payments_rental_amount =[]
					Total_payoff_amount = 0.0
					submitted_payments_rental_amount = [-(float(row[13])+float(row[14])+float(row[15]))]
					customer_agreement_doc = frappe.get_doc("Customer Agreement",row[3])
					payments_record_doc = customer_agreement_doc.payments_record
					if payments_record_doc:
						for payment_r in payments_record_doc:
							payment_type = frappe.db.get_value("Payments History",{"name":payment_r.payment_history},"payment_type")
							payoff_cond = frappe.db.get_value("Payments History",{"name":payment_r.payment_history},"payoff_cond")
							if payment_type =="Normal Payment" and payoff_cond =="Rental Payment" and payment_r.check_box_of_submit ==1:
								if date_diff(payment_r.payment_date,payment_r.due_date) > 1:
									payments_rental_amount.append(0)
								else:
									payments_rental_amount.append(payment_r.monthly_rental_amount)
									# payments_rental_amount.append(payment_r.monthly_rental_amount)
							if payment_type == "Payoff Payment" and  payoff_cond == "90d SAC":
								Total_payoff_amount = frappe.db.get_value("Payments History",{"name":payment_r.payment_history},"total_payment_received")
						payments_rental_amount.append(Total_payoff_amount)
						submitted_payments_rental_amount.extend(payments_rental_amount)				
						frappe.db.set_value("Customer Agreement",row[3],"irr_calculation_value",str(submitted_payments_rental_amount))
						try:
							# print "submitted_payments_rental_amount",submitted_payments_rental_amount	
							row[27] = round(irr(submitted_payments_rental_amount),5) if len(submitted_payments_rental_amount) > 1 else ""
							# print "row[27]",row[27]
							if row[27]:
								IRR = round((float(row[27]) * 12 * 100),2)
								if IRR:
									frappe.db.set_value("Customer Agreement",row[3],"irr",float(IRR))
									# print "Updated IIR",IRR
						except Exception,e:
							row[27] = ""
							frappe.db.set_value("Customer Agreement",row[3],"irr",row[27])
						# print "\n90d SAC",row[27]
				else:
					row[27] ="Wholesale price is not set"
					frappe.db.set_value("Customer Agreement",row[3],"irr",row[27])
			if row[12] and float(row[12]) > 0 and row[21] =="30% Early buy offer":
				if row[13] and float(row[13]) > 0.0:
					payments_rental_amount =[]
					submitted_payments_rental_amount = [-(float(row[13])+float(row[14])+float(row[15]))]
					customer_agreement_doc = frappe.get_doc("Customer Agreement",row[3])
					payments_record_doc = customer_agreement_doc.payments_record
					if payments_record_doc:
						payment_history =''
						for payment_r in payments_record_doc:
							payment_type = frappe.db.get_value("Payments History",{"name":payment_r.payment_history},"payment_type")
							payoff_cond = frappe.db.get_value("Payments History",{"name":payment_r.payment_history},"payoff_cond")
							if payment_type =="Normal Payment" and payoff_cond =="Rental Payment" and payment_r.check_box_of_submit ==1:
								if date_diff(payment_r.payment_date,payment_r.due_date) > 1:
									payments_rental_amount.append(0)
								else:
									payments_rental_amount.append(payment_r.monthly_rental_amount)
								# payments_rental_amount.append(payment_r.monthly_rental_amount)
							if payment_type =="Payoff Payment" and payoff_cond =="Early buy-30" and payment_r.check_box_of_submit ==1:
								payment_history = payment_r.payment_history
						Total_payoff_amount = frappe.db.get_value("Payments History",{"name":payment_history},"total_payment_received")
						payments_rental_amount.append(float(Total_payoff_amount)) if Total_payoff_amount else ""
						submitted_payments_rental_amount.extend(payments_rental_amount)
						frappe.db.set_value("Customer Agreement",row[3],"irr_calculation_value",str(submitted_payments_rental_amount))
						try:
							# print "submitted_payments_rental_amount",submitted_payments_rental_amount
							row[27] = round(irr(submitted_payments_rental_amount),5) if len(submitted_payments_rental_amount) > 1 else ""
							if row[27]:
								IRR = round((float(row[27]) * 12 * 100),2)
								if IRR:
									frappe.db.set_value("Customer Agreement",row[3],"irr",IRR)			
						except Exception,e:
							row[27] = ""
							frappe.db.set_value("Customer Agreement",row[3],"irr",row[27])
						# print "\n30% Early buy offer",row[27]
				else:
					row[27] ="Wholesale price is not set"
					frappe.db.set_value("Customer Agreement",row[3],"irr",row[27])		
			else:
				row[27] = ""
 		else:
 			row[27] = ""

 		#XIIR Calculations
 		if frappe.get_doc("Customer Agreement",row[3]).agreement_status == "Open":
			if row[12] and float(row[12])>0: 
				if row[13] and float(row[13]) > 0.0:
					submitted_payments_rental_amount = []
					agreement_doc = frappe.get_doc("Customer Agreement",row[3])
					payments = agreement_doc.payments_record
					if payments:
						purchase_date = frappe.db.get_value("Item",{"name":agreement_doc.product},"purchase_date")
						submitted_payments_rental_amount = [(purchase_date,-(float(row[13])+float(row[14])+float(row[15])))]
						for payment_r in payments:
							if payment_r.check_box_of_submit == 1:
								if date_diff(payment_r.payment_date,payment_r.due_date) > 1:
									submitted_payments_rental_amount.append((payment_r.due_date,0))
								else:
									submitted_payments_rental_amount.append((payment_r.payment_date,payment_r.monthly_rental_amount))
							if payment_r.check_box_of_submit == 0 and payment_r.due_date >= getdate(now_date):
								submitted_payments_rental_amount.append((payment_r.due_date,payment_r.monthly_rental_amount))	
						frappe.db.set_value("Customer Agreement",row[3],"xirr_calculation_value",str(submitted_payments_rental_amount))
						try:
							# print "submitted_payments_rental_amount",submitted_payments_rental_amount
							row[28] = xirr(submitted_payments_rental_amount,0.1)	
							XIRR = round((float(row[28]) * 100),2)
							if XIRR:					
								frappe.db.set_value("Customer Agreement",row[3],"xirr",XIRR)			
						except Exception,e:
							row[28] = ""
							frappe.db.set_value("Customer Agreement",row[3],"xirr",row[28])	 		
						# print "\nOPEN XIRR",row[28] 
				else:
					row[28] ="Wholesale price is not set"
					frappe.db.set_value("Customer Agreement",row[3],"xirr",row[28])	
	 	
	 	elif frappe.get_doc("Customer Agreement",row[3]).agreement_status == "Closed":
			if row[12] and float(row[12]) > 0 and row[21] =="Contract Term is over":
				if row[13] and float(row[13]) > 0.0:
		 			submitted_payments_rental_amount = []
					agreement_doc = frappe.get_doc("Customer Agreement",row[3])
					payments = agreement_doc.payments_record
					if payments:
						purchase_date = frappe.db.get_value("Item",{"name":agreement_doc.product},"purchase_date")					
						submitted_payments_rental_amount = [(purchase_date,-(float(row[13])+float(row[14])+float(row[15])))]
						for payment_r in payments:
							if payment_r.check_box_of_submit == 1:
								if date_diff(payment_r.payment_date,payment_r.due_date) > 1:
									submitted_payments_rental_amount.append((payment_r.due_date,0))
								else:
									submitted_payments_rental_amount.append((payment_r.payment_date,payment_r.monthly_rental_amount))
						frappe.db.set_value("Customer Agreement",row[3],"xirr_calculation_value",str(submitted_payments_rental_amount))
						try:
							# print "submitted_payments_rental_amount",submitted_payments_rental_amount
							row[28] = xirr(submitted_payments_rental_amount,0.1)
							if row[28]:
								XIRR = round((float(row[28]) * 100),2)
								if XIRR:
									frappe.db.set_value("Customer Agreement",row[3],"xirr",XIRR)
						except Exception,e:
							row[28] = ""
							frappe.db.set_value("Customer Agreement",row[3],"xirr",row[28] )
						# print "\nContract Term is over XIRR",row[28] 
				else:
					row[28] ="Wholesale price is not set"
					frappe.db.set_value("Customer Agreement",row[3],"xirr",row[28])
			
			if row[12] and float(row[12]) > 0 and row[21] =="90d SAC":
 				if row[13] and float(row[13]) > 0.0:
	 				submitted_payments_rental_amount = []
	 				pay_off_date = ""
	 				total_payment_received = 0.0
					agreement_doc = frappe.get_doc("Customer Agreement",row[3])
					payments = agreement_doc.payments_record
	 				if payments:
	 					purchase_date = frappe.db.get_value("Item",{"name":agreement_doc.product},"purchase_date")
						submitted_payments_rental_amount = [(purchase_date,-(float(row[13])+float(row[14])+float(row[15])))]
	 					for payment_r in payments_record_doc:
							payment_type = frappe.db.get_value("Payments History",{"name":payment_r.payment_history},"payment_type")
							payoff_cond = frappe.db.get_value("Payments History",{"name":payment_r.payment_history},"payoff_cond")
							if payment_type == "Normal Payment" and payoff_cond == "Rental Payment" and payment_r.check_box_of_submit ==1:
								if date_diff(payment_r.payment_date,payment_r.due_date) > 1:
									submitted_payments_rental_amount.append((payment_r.due_date,0))
								else:
									submitted_payments_rental_amount.append((payment_r.payment_date,payment_r.monthly_rental_amount))
							if payment_type == "Payoff Payment" and  payoff_cond == "90d SAC":
								pay_off_date = payment_r.payment_date
								total_payment_received = frappe.db.get_value("Payments History",{"name":payment_r.payment_history},"total_payment_received")
						submitted_payments_rental_amount.append((pay_off_date,total_payment_received))
						frappe.db.set_value("Customer Agreement",row[3],"xirr_calculation_value",str(submitted_payments_rental_amount))					   
					   	try:
							# print "submitted_payments_rental_amount",submitted_payments_rental_amount
							row[28] = xirr(submitted_payments_rental_amount,0.1)
							if row[28]:
								XIRR = round((float(row[28])* 100),2)
								if XIRR:
									frappe.db.set_value("Customer Agreement",row[3],"xirr",XIRR)
						except Exception,e:
							row[28] = ""
							frappe.db.set_value("Customer Agreement",row[3],"xirr",row[28])
						# print "\n90d SAC",XIIR 
				else:
					row[28] ="Wholesale price is not set"
					frappe.db.set_value("Customer Agreement",row[3],"xirr",row[28])
		
 			if row[12] and float(row[12]) > 0 and row[21] =="30% Early buy offer":
 				if row[13] and float(row[13]) > 0.0:
	 				submitted_payments_rental_amount = []
	 				payment_history = ""
					Total_payoff_amount =""
					payment_date =''
					agreement_doc = frappe.get_doc("Customer Agreement",row[3])
					payments = agreement_doc.payments_record
	 				if payments:
	 					purchase_date = frappe.db.get_value("Item",{"name":agreement_doc.product},"purchase_date")
						submitted_payments_rental_amount = [(purchase_date,-(float(row[13])+float(row[14])+float(row[15])))]
	 					for payment_r in payments_record_doc:
							payment_type = frappe.db.get_value("Payments History",{"name":payment_r.payment_history},"payment_type")
							payoff_cond = frappe.db.get_value("Payments History",{"name":payment_r.payment_history},"payoff_cond")
							if payment_type == "Normal Payment" and payoff_cond == "Rental Payment" and payment_r.check_box_of_submit ==1:
								if date_diff(payment_r.payment_date,payment_r.due_date) > 1:
									submitted_payments_rental_amount.append((payment_r.due_date,0))
								else:
									submitted_payments_rental_amount.append((payment_r.payment_date,payment_r.monthly_rental_amount))
								# submitted_payments_rental_amount.append((payment_r.payment_date,payment_r.monthly_rental_amount))
	 						if payment_type =="Payoff Payment" and payoff_cond =="Early buy-30" and payment_r.check_box_of_submit ==1:
								payment_history = payment_r.payment_history
						Total_payoff_amount = frappe.db.get_value("Payments History",{"name":payment_history},"total_payment_received")
						payment_date = frappe.db.get_value("Payments History",{"name":payment_history},"payment_date")
						submitted_payments_rental_amount.append((payment_date,Total_payoff_amount))
						frappe.db.set_value("Customer Agreement",row[3],"xirr_calculation_value",str(submitted_payments_rental_amount))
						try:
							# print "submitted_payments_rental_amount",submitted_payments_rental_amount
							row[28] = xirr(submitted_payments_rental_amount,0.1)
							if row[28]:
								XIRR = round((float(row[28]) * 100),2)
								if XIRR:
									frappe.db.set_value("Customer Agreement",row[3],"xirr",XIRR)
						except Exception,e:
								row[28] = ""
								frappe.db.set_value("Customer Agreement",row[3],"xirr",row[28])
						# print "\n30% Early buy offer",row[28] 
				else:
					row[28] ="Wholesale price is not set"
					frappe.db.set_value("Customer Agreement",row[3],"xirr",row[28])
			else:
				row[28] = ""
		else:
			row[28] = ""


"""
Payment By Rest API 
when Flagged Receivables added through api then payments_done_by_api() called and it will process 
pending,ondate and future payments for pertcular customer.
Get all open agreements of customers
Get remaining payments of all agreements comming in current month and pending of last months
Add payments according to due_date
Add bonus for payments
Process payments
Reduce receivables
"""
def payments_done_by_api():
# def payments_done_by_api(customer):

	customer = "NC"
	from customer_info.customer_info.doctype.payments_management.payments_management import get_bonus_summary
	now_date = datetime.now().date()
	firstDay_of_month = date(now_date.year, now_date.month, 1)
	last_day_of_month = get_last_day(now_date)
	get_bonus_summary(customer)
	customer_agreements = frappe.db.sql("""select name from `tabCustomer Agreement`
										where agreement_status = "Open" and customer = '{0}'""".format(customer),as_list=1)
	payments = []
	for agreement in customer_agreements:
		agreement_doc =frappe.get_doc("Customer Agreement",agreement[0])
		for row in agreement_doc.payments_record:
			if row.check_box_of_submit == 0:
				payments.append({ row.due_date:row.payment_id })
	payments.sort()
	args = {'values':{}}
	args['flagged_receivables'] = frappe.get_doc("Customer",customer).flagged_receivables
	for payment in payments:
		for key in payment:
			if frappe.db.exists("Customer Agreement", payment[key].split('-P')[0]):	
				customer_agreement = frappe.get_doc("Customer Agreement",payment[key].split('-P')[0])	
				for row in customer_agreement.payments_record:
					if row.due_date == key:
						customer_bonus = []
						payments_detalis_list = []
						payment_ids_list = []
						monthly_rental_amount = []
						merchandise_status = ""
						# customer_agreement = frappe.get_doc("Customer Agreement",payment[key].split('-P')[0])
						add_bonus_of_one_eur = []
						add_bonus_of_two_eur = []
						late_payments = []
						late_fees = []
						merchandise_status += str(customer_agreement.name)+"/"+str(customer_agreement.merchandise_status)+"/"+str(customer_agreement.agreement_closing_suspending_reason)+","
						if row.check_box_of_submit == 0 and row.payment_id == payment[key]:
							# Late Payment
							if (getdate(row.due_date) < firstDay_of_month or getdate(row.due_date) < now_date):
								customer_doc = frappe.get_doc("Customer",customer)
								flagged_receivables = customer_doc.flagged_receivables
								if date_diff(now_date,row.due_date) > 3:
									no_of_late_days = date_diff(row.payment_date,row.due_date) - 3
									late_payments.append(row.monthly_rental_amount)
									if customer_agreement.late_fees_updated == "No":
										customer_agreement.late_fees = "{0:.2f}".format(float(no_of_late_days * customer_agreement.monthly_rental_payment * (customer_agreement.late_fees_rate/100)))
									late_fees.append(customer_agreement.late_fees)
								total_charges = float(row.monthly_rental_amount) + float(customer_agreement.late_fees)
								if float(flagged_receivables) >= total_charges:
									payment_ids_list.append(row.payment_id)
									payments_detalis_list.append(str(row.payment_id)+"/"+str(row.due_date)+"/"+str(row.monthly_rental_amount)+"/"+str(now_date))
									monthly_rental_amount.append(row.monthly_rental_amount)
									row.update({
										"check_box":1,
										"check_box_of_submit":1,
										"payment_date":now_date,
									})
									row.save(ignore_permissions = True)
									customer_doc.flagged_receivables = flagged_receivables - total_charges
									customer_doc.save(ignore_permissions=True)
									auto_payment_notification(customer_doc.name,customer_agreement.name,total_charges)
							
							# Todays Payment (on_time Payments)
							if getdate(row.due_date) == now_date:
								customer_doc = frappe.get_doc("Customer",customer)
								flagged_receivables = customer_doc.flagged_receivables
								if date_diff(now_date,row.due_date) > 3:
									no_of_late_days = date_diff(row.payment_date,row.due_date) - 3
									late_payments.append(row.monthly_rental_amount)
									if customer_agreement.late_fees_updated == "No":
										customer_agreement.late_fees = "{0:.2f}".format(float(no_of_late_days * customer_agreement.monthly_rental_payment * (customer_agreement.late_fees_rate/100)))
								late_fees.append(customer_agreement.late_fees)
								total_charges = float(row.monthly_rental_amount) + float(customer_agreement.late_fees)
								if float(flagged_receivables) >= total_charges:				
									payment_ids_list.append(row.payment_id)
									payments_detalis_list.append(str(row.payment_id)+"/"+str(row.due_date)+"/"+str(row.monthly_rental_amount)+"/"+str(now_date))
									monthly_rental_amount.append(row.monthly_rental_amount)
									if row.idx != 1:
										add_bonus_of_one_eur.append(row.idx)
									row.update({
										"check_box":1,
										"check_box_of_submit":1,
										"payment_date":now_date,
										'add_bonus_to_this_payment':1 if row.idx != 1 else 0,
										'bonus_type':"On Time Bonus" if row.idx != 1 else ""
									})
									row.save(ignore_permissions = True)
									customer_doc.flagged_receivables = flagged_receivables - total_charges
									customer_doc.save(ignore_permissions=True)
									auto_payment_notification(customer_doc.name,customer_agreement.name,total_charges)
					
							# Early Payments (Future Payments)
							if firstDay_of_month <= getdate(row.due_date):	
								customer_doc = frappe.get_doc("Customer",customer)
								flagged_receivables = customer_doc.flagged_receivables
								if date_diff(now_date,row.due_date) > 3:
									no_of_late_days = date_diff(row.payment_date,row.due_date) - 3
									late_payments.append(row.monthly_rental_amount)
									if customer_agreement.late_fees_updated == "No":
										customer_agreement.late_fees = "{0:.2f}".format(float(no_of_late_days * customer_agreement.monthly_rental_payment * (customer_agreement.late_fees_rate/100)))					
									late_fees.append(customer_agreement.late_fees)
								total_charges = float(row.monthly_rental_amount) + float(customer_agreement.late_fees)
								if float(flagged_receivables) >= total_charges:
									payment_ids_list.append(row.payment_id)
									payments_detalis_list.append(str(row.payment_id)+"/"+str(row.due_date)+"/"+str(row.monthly_rental_amount)+"/"+str(now_date))
									monthly_rental_amount.append(row.monthly_rental_amount)
									if row.idx != 1:
										add_bonus_of_two_eur.append(row.idx)
									row.update({
										"check_box":1,
										"check_box_of_submit":1,
										"payment_date":now_date,
										'add_bonus_to_this_payment':1 if row.idx != 1 else 0,
										'bonus_type':"Early Bonus" if row.idx != 1 else "",
									})
									row.save(ignore_permissions = True)
									customer_doc.flagged_receivables = flagged_receivables - total_charges
									customer_doc.save(ignore_permissions=True)
									auto_payment_notification(customer_doc.name,customer_agreement.name,total_charges)

						if len(payment_ids_list) > 0:
							customer_agreement.early_payments_bonus = customer_agreement.early_payments_bonus +  len(add_bonus_of_two_eur)*2
							bonus_amount = len(add_bonus_of_one_eur)*1 + len(add_bonus_of_two_eur)*2
							customer_agreement.bonus = customer_agreement.bonus + len(add_bonus_of_one_eur)*1 + len(add_bonus_of_two_eur)*2
							customer_agreement.late_payment = sum(late_payments)
							customer_bonus.append(customer_agreement.bonus)
							customer_agreement.save(ignore_permissions = True)
							customer_doc = frappe.get_doc("Customer",customer)
							customer_doc.bonus = customer_doc.bonus + bonus_amount 
							customer_doc.save(ignore_permissions=True)
							set_values_in_agreement(customer_agreement)
							args['assigned_bonus_discount'] = ""
							args['customer'] = customer
							args['receivables'] = frappe.get_doc("Customer",customer).receivables
							args['add_in_receivables'] = frappe.get_doc("Customer",customer).receivables
							args['payment_date'] = str(now_date)
							args['rental_payment'] = sum(monthly_rental_amount)
							args['payment_type'] = "Normal Payment"
							args['late_fees'] = sum(map(float,late_fees))
							args['values']['amount_paid_by_customer'] = 0
							args['values']['bank_card'] = 0
							args['values']['bank_transfer'] = 0
							args['values']['discount'] = 0
							args['values']['bonus'] = 0
							args['new_bonus'] = len(add_bonus_of_one_eur)*1 + len(add_bonus_of_two_eur)*2
							args['total_charges'] = 0
							args['total_amount'] = 0
							args['special_associate'] = "Automatic API"
							make_payment_history(args,payments_detalis_list,payment_ids_list,"Normal Payment",merchandise_status,"","Rental Payment")		
	
	cust_doc = frappe.get_doc("Customer",customer)
	cust_doc.receivables = float(cust_doc.receivables) + float(cust_doc.flagged_receivables)
	cust_doc.flagged_receivables = 0.0
	cust_doc.save()