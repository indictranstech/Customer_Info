from __future__ import unicode_literals
import json
import frappe
from datetime import datetime
from frappe.utils import nowdate, nowtime
from datetime import datetime, timedelta,date
from frappe.utils import nowdate, getdate,add_months,add_days,get_last_day
from frappe.utils import date_diff,flt
from customer_info.customer_info.doctype.customer_agreement.customer_agreement import closed_agreement_notification
from customer_info.customer_info.doctype.payments_management.make_payment_history import make_payment_history


# Version 2 API

"""
Addding receivables to customer for payment process
"""
@frappe.whitelist()
def add_receivables(customer,receivables):
	cust_doc = frappe.get_doc("Customer",customer)
	if cust_doc and float(receivables):
		try:
			cust_doc.receivables += float(receivables)
			cust_doc.save(ignore_permissions=True)
			frappe.db.commit()
			return "%Receivables are successfully added for customer {0}#".format(cust_doc.name)
		except Exception, e:
			raise e
	else:
			return "%Invalid Customer#"

"""
Addding flagged receivables to customer for payment process
"""
@frappe.whitelist()
def add_flagged_receivables(customer,flagged_receivables):
	cust_doc = frappe.get_doc("Customer",customer)
	if cust_doc and float(flagged_receivables):
		try:
			cust_doc.flagged_receivables += float(flagged_receivables)
			cust_doc.save(ignore_permissions=True)
			frappe.db.commit()
			payments_done_by_api(customer)
			return "%Flagged Receivables are successfully added for customer {0}#".format(cust_doc.name)
		except Exception, e:
			raise e
	else:
			return "%Invalid Customer#"


@frappe.whitelist()
def payments_done_by_api(customer):
	from customer_info.customer_info.doctype.payments_management.payments_management import get_bonus_summary
	now_date = datetime.now().date()
	firstDay_of_month = date(now_date.year, now_date.month, 1)
	last_day_of_month = get_last_day(now_date)
	get_bonus_summary(customer)
	
	# Step - 1 : Get All Customer Agreement
	customer_agreements = frappe.db.sql("""select name from `tabCustomer Agreement`
										where agreement_status = "Open" and customer = '{0}'""".format(customer),as_list=1)
	# Step - 2 : Globally declare all payment list
	payments = {}
	payments_sorted = []
	customer_bonus = []
	payments_detalis_list = []
	payment_ids_list = []
	# print " 1 **********",payment_ids_list
	monthly_rental_amount = []
	merchandise_status = ""
	add_bonus_of_one_eur = []
	add_bonus_of_two_eur = []
	late_payments = []
	late_fees = []
	args = {'values':{}}
		
	
	# Step - 3 : Find out pending payment's from all customer open agreements.
	for agreement in customer_agreements:
		agreement_doc =frappe.get_doc("Customer Agreement",agreement[0])
		for row in agreement_doc.payments_record:
			if row.check_box_of_submit == 0:
				payments[row.payment_id] = row.due_date
	
	# Step - 4 : Sort Pending Payments
	for key, value in sorted(payments.iteritems(), key=lambda (k,v): (v,k)):
		payments_sorted.append(key)
	
	# Step - 5 :Get Flagged Receivables amount
	args['flagged_receivables'] = frappe.get_doc("Customer",customer).flagged_receivables
	# Step - 6 : Process Pending Payments
	for payment in payments_sorted:
	# Step -6(1) - Validate Agreement
		if frappe.db.exists("Customer Agreement", payment.split('-P')[0]):				
			customer_agreement = frappe.get_doc("Customer Agreement",payment.split('-P')[0])	
			
			# Step -6(2) - Validate Payment
		 	for row in customer_agreement.payments_record:
		 		if row.payment_id == payment:											
		 			merchandise_status += str(customer_agreement.name)+"/"+str(customer_agreement.merchandise_status)+"/"+str(customer_agreement.agreement_closing_suspending_reason)+","

		 			if row.check_box_of_submit == 0 and row.payment_id == payment:
		 				# Step -6(3) Late Payments
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
		 						# campaign_discount = frappe.get_doc("Customer Agreement",customer_agreement).campaign_discount
		 						# discounted_payments_left = frappe.get_doc("Customer Agreement",customer_agreement).discounted_payments_left
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
		 						# auto_payment_notification(customer_doc.name,customer_agreement.name,total_charges)
		 						# print "____Latepayments__",row.payment_id
		 				# Step -6(4) Todays Payment (on_time Payments)
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
		 						# auto_payment_notification(customer_doc.name,customer_agreement.name,total_charges)
		 						# print "____Todayspayments__",row.payment_id
		 				#  Step -6(5) Early Payments (Future Payments)
		 				if firstDay_of_month <= getdate(row.due_date) and getdate(row.due_date) > now_date:	
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
		 						# auto_payment_notification(customer_doc.name,customer_agreement.name,total_charges)
		 						# print "____Earlypayments__",row.payment_id
			# print "_____Payments ids list",payment_ids_list

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
		args['add_in_receivables'] =  flt(frappe.get_doc("Customer",customer).receivables) + flt(frappe.get_doc("Customer",customer).flagged_receivables)
		args['payment_date'] = str(now_date)
		args['rental_payment'] = sum(monthly_rental_amount)
		args['payment_type'] = "Normal Payment"
		args['late_fees'] = sum(map(float,late_fees))
		args['values']['amount_paid_by_customer'] = 0
		args['values']['bank_card'] = 0
		args['values']['bank_transfer'] = args['flagged_receivables']
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