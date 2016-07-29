# -*- coding: utf-8 -*-
# Copyright (c) 2015, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.utils import date_diff
import datetime
from frappe.utils import flt, get_datetime, get_time, getdate
from frappe.utils import nowdate, getdate,add_months
from datetime import datetime,date
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document

class PaymentsManagement(Document):
	pass

@frappe.whitelist()
def get_customer_agreement(customer):
	return {
	"list_of_agreement": frappe.db.sql("""select agreement_no,agreement_period,
										concade_product_name_and_category,number_of_payments,
										monthly_rental_payment,current_due_date,next_due_date,
										payments_left,balance,late_fees,total_due,payments_made,
										CASE 
										WHEN DATEDIFF(suspension_date,now()) > 0 THEN DATE_FORMAT(suspension_date,'%d-%m-%Y')
										WHEN contact_result = "Sent SMS/Email" THEN "SMS/Email" 
										ELSE "Call/Commitment" 
										END AS suspension_date
										from `tabCustomer Agreement`
										where customer = '{0}' and agreement_status = 'Open' """.format(customer),as_list=1)
	}	

@frappe.whitelist()
def temporary_payments_update_to_child_table_of_customer_agreement(row_to_update=None,row_to_uncheck=None,row_to_check=None,row_to_pre_select_uncheck=None,parent=None,payment_date=None):
	row_to_update = json.loads(row_to_update)
	row_to_uncheck = json.loads(row_to_uncheck)
	row_to_check = json.loads(row_to_check)

	if len(row_to_update) > 0:
		set_check_and_uncheck(row_to_update,parent,1,0,payment_date)

	if len(row_to_uncheck) > 0:
		set_check_and_uncheck(row_to_uncheck,parent,0,"")

	if len(row_to_pre_select_uncheck) > 0:
		set_check_and_uncheck(row_to_pre_select_uncheck,parent,0,1,"")

	if len(row_to_check) > 0:
		set_check_and_uncheck(row_to_check,parent,1,0,payment_date)		

def set_check_and_uncheck(list_of_payment_id,parent,value=None,pre_select_uncheck=None,payment_date=None):
	for i in list_of_payment_id:
		customer_agreement = frappe.get_doc("Customer Agreement",parent)
		for row in customer_agreement.payments_record:
				if row.payment_id in list_of_payment_id:
					row.update({
							'check_box':value,
							'payment_date':payment_date,
							'pre_select_uncheck':pre_select_uncheck
					})
					row.save(ignore_permissions = True)
	customer_agreement.save(ignore_permissions = True)

@frappe.whitelist()
def update_on_submit(payment_date,customer,bonus):

	submitted_payments_ids = frappe.db.sql("""select payment_id,due_date,
							payment_date,monthly_rental_amount from `tabPayments Record` where 
							parent in (select name from `tabCustomer Agreement`
							where customer = '{0}' and agreement_status = 'Open')
							and check_box = 1 
							and check_box_of_submit = 0 
							and payment_date = '{1}' order by idx """.format(customer,payment_date),as_dict=1)

	frappe.db.sql("""update `tabPayments Record` 
						set check_box_of_submit = 1
						where check_box = 1 and check_box_of_submit = 0
						and  payment_date = '{0}'
						and parent in (select name from `tabCustomer Agreement`
						where customer = '{1}' and agreement_status = 'Open')""".format(payment_date,customer),debug=1)
	
	agreements = frappe.db.sql("""select name from `tabCustomer Agreement` where customer = '{0}'
							and agreement_status = "Open" """.format(customer),as_list=1)
	
	for agreement in [agreement[0] for agreement in agreements]:
		customer_agreement = frappe.get_doc("Customer Agreement",agreement)
		set_values_in_agreement_on_submit(customer_agreement)
	
	customer_doc = frappe.get_doc("Customer",customer)
	added_bonus = float(bonus) - customer_doc.bonus
	customer_doc.update({
		"bonus":bonus
		})
	if float(added_bonus) > 0:
		comment = """ {0} EUR Bonus Added """.format(added_bonus)
		customer_doc.add_comment("Comment",comment)
	customer_doc.save(ignore_permissions=True)

	return submitted_payments_ids

def set_values_in_agreement_on_submit(customer_agreement):
	payment_made = []
	if customer_agreement.payments_record:
		for row in customer_agreement.payments_record:
			if row.check_box_of_submit == 1:
				payment_made.append(row.monthly_rental_amount)				

	payment_made = map(float,payment_made)
	print sum(payment_made),"sum of payments_made"

	if customer_agreement.payments_record and customer_agreement.date:
		customer_agreement.payments_made = sum(payment_made)
		customer_agreement.number_of_payments = 0
		customer_agreement.late_fees = 0
		customer_agreement.payments_left = len(customer_agreement.payments_record) - len(payment_made)
		customer_agreement.balance = (len(customer_agreement.payments_record) - len(payment_made)) * customer_agreement.monthly_rental_payment
		customer_agreement.total_due = 0
	customer_agreement.save(ignore_permissions=True)	



@frappe.whitelist()
def make_refund_payment(payments_ids,ph_name):
	payments_ids = json.loads(payments_ids)
	payment_history = frappe.get_doc("Payments History",ph_name)
	print payments_ids,"payments_ids"
	customer = frappe.get_doc("Customer",payment_history.customer)
	payments_id_list = []
	agreement_list = []
	for i in payments_ids:
		frappe.db.sql("""update `tabPayments Record` set check_box = 0,pre_select_uncheck = 0,
							payment_date = "",check_box_of_submit = 0 
							where check_box_of_submit = 1 
							and payment_id = '{0}' """.format(i))
		payments_id_list.append(i)
		agreement_list.append(i.split("-P")[0])
	print payments_id_list,"payments_id_list"
	agreement_list =  list(set(agreement_list))
	print agreement_list,"agreement_list"
	cond = 2
	for agreement in agreement_list:
		customer_agreement = frappe.get_doc("Customer Agreement",agreement)
		set_values_in_agreement_on_submit(customer_agreement)
		customer.bonus = set_values_in_agreement_temporary(agreement,customer.bonus,cond,payments_id_list)
		customer.refund_to_customer = float(payment_history.cash) + float(payment_history.bank_card) + float(payment_history.bank_transfer) - float(payment_history.bonus) - float(payment_history.discount)
		customer.receivables = float(payment_history.rental_payment) - float(payment_history.late_fees) - float(payment_history.total_charges)
		customer.save(ignore_permissions=True)
		frappe.delete_doc("Payments History", ph_name)


@frappe.whitelist()
def set_values_in_agreement_temporary(customer_agreement,frm_bonus,cond,row_to_uncheck=None):
	print frm_bonus, "bonus",'bonus'
	if cond == 1 and row_to_uncheck:
		row_to_uncheck = json.loads(row_to_uncheck)
	print row_to_uncheck,"row_to_uncheck"
	customer_agreement = frappe.get_doc("Customer Agreement",customer_agreement)
	now_date = datetime.now().date()
	firstDay_next_month = date(now_date.year, now_date.month+1, 1)
	no_of_late_days = 0
	late_payments = []
	amount_of_payment_left = []
	add_bonus_of_one_eur = []
	add_bonus_of_two_eur = []
	remove_bonus_of_one_eur = []
	remove_bonus_of_two_eur = []
	received_payments = []
	submitable_payments = []
	if customer_agreement.payments_record:
		for row in customer_agreement.payments_record:
			if row.check_box == 1 and row.check_box_of_submit == 0:
				received_payments.append(row.monthly_rental_amount)
			
			# if row.due_date and row.payment_date and date_diff(row.payment_date,row.due_date) > 3:
			# 	no_of_late_days += date_diff(row.payment_date,row.due_date) - 3
			# 	late_payments.append(row.monthly_rental_amount)	
			
			if row.due_date and row.payment_date and date_diff(row.payment_date,row.due_date) > 3 and row.check_box == 1 and row.check_box_of_submit == 0:
				print no_of_late_days,"no_of_late_days"
				print row.payment_id,"payment_id of late_fees"
				no_of_late_days += date_diff(row.payment_date,row.due_date) - 3
				late_payments.append(row.monthly_rental_amount)	

			if not row.payment_date:
				print row.payment_id,"payment_id pa papa"
			 	amount_of_payment_left.append(row.monthly_rental_amount)

			# if (getdate(row.due_date) >= firstDay_next_month) and row.check_box == 0:
			#  	amount_of_payment_left.append(row.monthly_rental_amount)
			
			if row.check_box_of_submit == 1:
				submitable_payments.append(row.idx)
			
			if row.payment_date and getdate(row.payment_date) == getdate(row.due_date) and row.add_bonus_to_this_payment == 0:
				add_bonus_of_one_eur.append(row.idx)
				row.update({
					'add_bonus_to_this_payment':1
					})
				row.save(ignore_permissions = True)

			elif row.payment_date and getdate(row.payment_date) < getdate(row.due_date)  and row.add_bonus_to_this_payment == 0:
				add_bonus_of_two_eur.append(row.idx)
				row.update({
					'add_bonus_to_this_payment':1
					})
				row.save(ignore_permissions = True)
			
			if row.payment_id in row_to_uncheck and getdate(now_date) == getdate(row.due_date) and row.add_bonus_to_this_payment == 1:
				remove_bonus_of_one_eur.append(row.idx)
				row.update({
					'add_bonus_to_this_payment':0
					})
				row.save(ignore_permissions = True)


			elif row.payment_id in row_to_uncheck and getdate(now_date) < getdate(row.due_date) and row.add_bonus_to_this_payment == 1:
				remove_bonus_of_two_eur.append(row.idx)	
				row.update({
					'add_bonus_to_this_payment':0
					})
				row.save(ignore_permissions = True)

		for row in customer_agreement.payments_record:
			if row.check_box == 0 and date_diff(row.due_date,datetime.now()) < 0:
				customer_agreement.current_date = row.due_date
				customer_agreement.next_due_date = get_next_due_date(customer_agreement.current_due_date,1)
				break
			elif row.check_box == 0 and date_diff(row.due_date,datetime.now()) >= 0:
				customer_agreement.current_due_date = row.due_date
				customer_agreement.next_due_date = row.due_date	
				break		


	print len(submitable_payments),"submitable_payments"	

	received_payments = map(float,received_payments)				
	print received_payments,len(received_payments),"received_payments"
	amount_of_payment_left = map(float,amount_of_payment_left)

	late_payments = map(float,late_payments)

	bonus = len(add_bonus_of_one_eur)*1 + len(add_bonus_of_two_eur)*2
	print bonus,"bonus"

	subtract_bonus = len(remove_bonus_of_one_eur)*1 + len(remove_bonus_of_two_eur)*2
	print subtract_bonus,"sub tractbonus"

	print no_of_late_days,"no_of_late_days"

	if customer_agreement.payments_record and customer_agreement.date:
		customer_agreement.payments_left = len(customer_agreement.payments_record) - len(received_payments) - len(submitable_payments)
		customer_agreement.late_payments = sum(late_payments)
		customer_agreement.amount_of_payment_left = sum(amount_of_payment_left)
		customer_agreement.number_of_payments = len(received_payments)
		customer_agreement.late_fees = no_of_late_days * customer_agreement.monthly_rental_payment * 0.02
		customer_agreement.bonus = customer_agreement.bonus + bonus - subtract_bonus
		customer_agreement.total_due = len(received_payments) * customer_agreement.monthly_rental_payment + (no_of_late_days * customer_agreement.monthly_rental_payment * 0.02)
	customer_agreement.save(ignore_permissions=True)
	total_bonus = float(frm_bonus) + bonus - subtract_bonus
	print  total_bonus,"total_bonus",type(total_bonus),"type of total_bonus"
	return str(total_bonus)

@frappe.whitelist()
def get_next_due_date(date,i):
	add_month_to_date = add_months(date,i)
	return add_month_to_date

@frappe.whitelist()
def remove_all_not_submitted(customer):
	print "in side remove_all_not_submitted"
	frappe.db.sql("""update `tabPayments Record` set check_box = 0,pre_select_uncheck = 0,payment_date = "" 
							where check_box_of_submit = 0 
							and parent in (select name from `tabCustomer Agreement`
							where customer = '{0}' and agreement_status = "Open") """.format(customer))

	frappe.db.sql("""update `tabCustomer Agreement` set number_of_payments = 0,total_due = 0,late_fees = 0 
					where customer = '{0}' 
					and agreement_status = "Open" """.format(customer),debug=1)

@frappe.whitelist()
def update_payments_record_by_due_date(customer):
	print "in update_payments_record_by_due_date"
	now_date = datetime.now().date()
	firstDay_this_month = date(now_date.year, now_date.month, 1)
	firstDay_next_month = date(now_date.year, now_date.month+1, 1)
	due_payment_list = []
	customer_agreement = frappe.db.sql("""select name from `tabCustomer Agreement`
							where customer = '{0}' and agreement_status = "Open" """.format(customer),as_list=1)
	for agreement in [e[0] for e in customer_agreement]:
		customer_agreement = frappe.get_doc("Customer Agreement",agreement)
		for row in customer_agreement.payments_record:
			if row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and getdate(row.due_date) >= firstDay_this_month and getdate(row.due_date) < firstDay_next_month:
				row.update({
					"check_box":1
				})
				row.save(ignore_permissions=True)
			if (row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and getdate(row.due_date) < firstDay_this_month):
				row.update({
					"check_box":1
				})
				row.save(ignore_permissions=True)
		customer_agreement.save(ignore_permissions = True)

@frappe.whitelist()
def get_payments_record(customer_agreement,receivable):
	return {
	"payments_record" : frappe.db.sql("""select no_of_payments,monthly_rental_amount,
										due_date,payment_date,payment_id,check_box,check_box_of_submit,pre_select_uncheck from `tabPayments Record` 
										where parent = '{0}' 
										order by due_date """.format(customer_agreement),as_dict=1),
	"summary_records" : get_summary_records(customer_agreement,receivable)
	}

@frappe.whitelist()
def get_summary_records(agreement,receivable):
	agreement = frappe.get_doc("Customer Agreement",agreement)
	late_fees = "{0:.2f}".format(agreement.late_fees)
	payments_made = "{0:.2f}".format(agreement.payments_made + float(receivable))
	if agreement.today_plus_90_days >= datetime.now().date():
		day_pay_Off = "{0:.2f}".format(agreement.s90d_sac_price - agreement.payments_made - float(receivable) + float(late_fees))
		return {"cond":1,
				"s90d_SAC_price":"{0} EUR".format(agreement.s90d_sac_price),
				"Expires":agreement.today_plus_90_days,
				"Payments_made":"{0} EUR".format(payments_made),
				"Late_fees":"{0} EUR".format(float(late_fees)),
				"s90_day_pay_Off":"{0} EUR".format(float(day_pay_Off)),
				"Number_of_payments_left":agreement.payments_left
				}

	elif agreement.today_plus_90_days < datetime.now().date():
		balance = float(agreement.payments_left) * agreement.monthly_rental_payment
		discount = (balance / 100) * float(agreement.early_buy_discount_percentage)
		Total_payoff_amount = (balance - float(discount)) + float(agreement.late_payments) + agreement.late_fees - float(receivable)
		Total_payoff_amount = "{0:.2f}".format(Total_payoff_amount)
		return {"cond":2,
				"Receivables":"{0} EUR".format(receivable),
				"Amount_of_payments_left":"{0} EUR".format(balance),
				"Discounted_payment_amount":"{0} EUR".format("{0:.2f}".format(balance - float(discount))),
				"Late_payments":"{0} EUR".format(agreement.late_payments),
				"Late_fees":"{0} EUR".format(float(late_fees)),
				"Total_payoff_amount":"{0} EUR".format(float(Total_payoff_amount)),
				"discount":"{0} EUR".format("{0:.2f}".format(discount)),
				"discount_percentage":"{0}% discount".format(agreement.early_buy_discount_percentage)
				}	
			 			
@frappe.whitelist()
def calculate_total_charges(customer):
	print "in calculate_total_charges"
	now_date = datetime.now().date()
	firstDay_this_month = date(now_date.year, now_date.month, 1)
	firstDay_next_month = date(now_date.year, now_date.month+1, 1)
	due_payment_list = []
	customer_agreement = frappe.db.sql("""select name from `tabCustomer Agreement`
							where customer = '{0}' and agreement_status = "Open" """.format(customer),as_list=1)
	
	receivables = frappe.db.get_value("Customer",{"name":customer},"receivables")
	for agreement in [e[0] for e in customer_agreement]:
		customer_agreement = frappe.get_doc("Customer Agreement",agreement)
		print customer_agreement.name
		for row in customer_agreement.payments_record:
			if(row.check_box_of_submit == 0 and row.check_box ==1):
				due_payment_list.append(row.monthly_rental_amount)	
	return {"amount_of_due_payments":sum(due_payment_list),"receivables":receivables}

@frappe.whitelist()
def add_receivables_in_customer(customer,receivables):
	receivables = float(receivables)
	print receivables,"receivables"
	customer = frappe.get_doc("Customer",customer)
	customer.update({
		"receivables":receivables
		})
	customer.save(ignore_permissions = True)
	return "True"


@frappe.whitelist()
def update_call_commitment_data_in_agreement(customer_agreement,date,contact_result,amount,all_or_individual):
	print customer_agreement,date,contact_result,amount,all_or_individual,"assssssssssssssssss"
	# date = datetime.strptime(date, '%d-%m-%Y')
	
	if all_or_individual == "individual" and date:
		customer_agreement = frappe.get_doc("Customer Agreement",customer_agreement)
		customer_agreement.update({
			"suspension_date":date,
			"contact_result": contact_result,
			"amount_of_contact_result":amount,
			"call_commitment":"Individual"
			})
		customer_agreement.save(ignore_permissions = True)

	if 	all_or_individual == "individual" and not date:
		customer_agreement = frappe.get_doc("Customer Agreement",customer_agreement)
		customer_agreement.update({
			"suspension_date":"",
			"contact_result": contact_result,
			"amount_of_contact_result":0,
			"call_commitment":"Individual"
			})
		customer_agreement.save(ignore_permissions = True)


	if all_or_individual == "all" and date:
		print "1111111111111111111111111111111111111111111111"
		agreements = json.loads(customer_agreement)
		for agreement in agreements:
			customer_agreement = frappe.get_doc("Customer Agreement",agreement)
			customer_agreement.update({
				"suspension_date":date,
				"contact_result": contact_result,
				"amount_of_contact_result":amount,
				"call_commitment":"All"
				})
			customer_agreement.save(ignore_permissions = True)

	if all_or_individual == "all" and not date:
		print "222222222222222222222222222222222222222"
		agreements = json.loads(customer_agreement)
		for agreement in agreements:
			customer_agreement = frappe.get_doc("Customer Agreement",agreement)
			customer_agreement.update({
				"suspension_date":"",
				"contact_result": contact_result,
				"amount_of_contact_result":0,
				"call_commitment":"All"
				})
			customer_agreement.save(ignore_permissions = True)			
	 
	
@frappe.whitelist()
def set_or_reset_call_commitment(customer=None,agreement_name=None):
	now_date = datetime.now().date()
	if customer and not agreement_name:	
		agreement = frappe.db.sql("""select name from `tabCustomer Agreement`
									where customer = '{0}' 
									and agreement_status = 'Open'""".format(customer),as_list=1)	
		for i in [i[0] for i in agreement]:
			agreement_doc = frappe.get_doc("Customer Agreement",i)
			agreement_doc.update({
				"suspension_date":now_date,
				"contact_result":" ",
				"amount_of_contact_result":0,
				"call_commitment":" "
				})
			agreement_doc.save(ignore_permissions=True)

	if agreement_name:
		agreement_doc = frappe.get_doc("Customer Agreement",agreement_name)
		agreement_doc.update({
			"suspension_date":now_date,
			"contact_result":" ",
			"amount_of_contact_result":0,
			"call_commitment":" "
			})
		agreement_doc.save(ignore_permissions=True)				

@frappe.whitelist()
def make_payment_history(cash,bank_card,bank_transfer,balance,receivables,customer,payment_date,discount,bonus,rental_payment,late_fees,payment_ids,total_charges):
	print cash,bank_card,bank_transfer,balance,receivables,customer,discount,type(bonus)
	payment_ids = json.loads(payment_ids)
	payment_date = datetime.strptime(payment_date, '%Y-%m-%d')
	payments_history = frappe.new_doc("Payments History")
	payments_history.cash = float(cash)
	payments_history.bank_card = float(bank_card)
	payments_history.bank_transfer = float(bank_transfer)
	payments_history.balance = float(balance)
	payments_history.receivables = float(receivables)
	payments_history.customer = customer
	payments_history.payment_date = payment_date.date()
	payments_history.bonus = float(bonus)
	payments_history.discount = float(discount)
	payments_history.rental_payment = float(rental_payment)
	payments_history.total_charges = float(total_charges)
	payments_history.late_fees = float(late_fees)
	for i in payment_ids:
		if payments_history.payments_ids:
			payments_history.payments_ids = payments_history.payments_ids + str(i) + ','
		else:
			payments_history.payments_ids = '"' + str(i) + ','
		# 	payments_history.payments_ids = payments_history.payments_ids + "['" + str(i) + "']," + "\n"
		# else:
		# 	payments_history.payments_ids = "['" + str(i) + "']," + "\n"
	payments_history.save(ignore_permissions = True)


@frappe.whitelist()
def add_notes_in_customer(customer,notes_on_customer_payments,summary_of_notes=None):
	now_date = datetime.now().date()
	customer = frappe.get_doc("Customer",customer)
	if summary_of_notes == None:
		notes = notes_on_customer_payments
	else:	
		notes = "{0} \n{1} - {2}".format(notes_on_customer_payments,summary_of_notes,now_date)

	customer.update({
		"summary_of_notes" : notes
		})
	customer.save(ignore_permissions=True)
	return customer.summary_of_notes

@frappe.whitelist()
def update_agreement_according_today_plus_90days(customer_agreement,agreement_status,condition):
	now_date = datetime.now().date()
	agreement = frappe.get_doc("Customer Agreement",customer_agreement)
	if int(condition) == 2 and agreement.agreement_status == "Open":
		agreement.update({
			"agreement_status":"Closed",
			"agreement_close_date":now_date,
			"agreement_closing_suspending_reason":"90d SAC"
		})
		agreement.save(ignore_permissions=True)
	elif int(condition) == 1 and agreement.agreement_status == "Open":
		agreement.update({
			"agreement_status":"Closed",
			"agreement_close_date":now_date,
			"agreement_closing_suspending_reason":"40% Offer"
		})
		agreement.save(ignore_permissions=True)


# call From Customer master OnClick Button Payment management 
@frappe.whitelist()
def get_payments_management(source_name, target_doc=None):
	target_doc = get_mapped_doc("Customer", source_name,
		{
			"Customer": {
				"doctype": "Payments Management",
			},
		}, target_doc)

	target_doc.customer = source_name
	return target_doc

