# -*- coding: utf-8 -*-
# Copyright (c) 2015, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.utils import date_diff
import datetime
from frappe.utils import flt, get_datetime, get_time, getdate
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
										CASE WHEN DATEDIFF(suspension_date,now()) > 0 THEN DATE_FORMAT(suspension_date,'%d-%m-%Y') 
										ELSE "Postpone" 
										END AS suspension_date
										from `tabCustomer Agreement`
										where customer = '{0}' and agreement_status = 'Open' """.format(customer),as_list=1)
	}	


@frappe.whitelist()
def add_notes_in_customer(customer,notes_on_customer_payments,summary_of_notes=None):
	customer = frappe.get_doc("Customer",customer)
	if summary_of_notes == None:
		notes = notes_on_customer_payments
	else:	
		notes = "{0} \n{1}".format(summary_of_notes,notes_on_customer_payments)

	customer.update({
		"summary_of_notes" : notes
		})
	customer.save(ignore_permissions=True)


@frappe.whitelist()
def get_payments_record(customer_agreement,receivable):
	# return {
	# "payments_record" : frappe.db.sql("""select no_of_payments,monthly_rental_amount,
	# 									due_date,payment_date,payment_id,check_box,check_box_of_submit,pre_select_uncheck from `tabPayments Record` 
	# 									where parent = '{0}' 
	# 									order by due_date """.format(customer_agreement),as_dict=1)
	# }
	return {
	"payments_record" : frappe.db.sql("""select no_of_payments,monthly_rental_amount,
										due_date,payment_date,payment_id,check_box,check_box_of_submit,pre_select_uncheck from `tabPayments Record` 
										where parent = '{0}' 
										order by due_date """.format(customer_agreement),as_dict=1),
	"summary_records" : get_summary_records(customer_agreement,receivable)
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
	# customer_agreement.onload();			
	customer_agreement.save(ignore_permissions = True)


# @frappe.whitelist()
# def get_bonus(customer):
# 	sum_of_bonus = 0
# 	bonus = frappe.db.sql("""select bonus from `tabCustomer Agreement` where customer = '{0}' """.format(customer),as_list=1,debug=1)
# 	for i in [b[0] for b in bonus]:
# 		sum_of_bonus += i
# 	print sum_of_bonus,"sum_of_bonus"	
# 	customer_doc = frappe.get_doc("Customer",customer)
	
# 	customer_doc.update({
# 		"bonus": sum_of_bonus
# 		})
# 	customer_doc.save(ignore_permissions=True)
	# return sum_of_bonus

@frappe.whitelist()
def update_payments_child_table_of_customer_agreement_on_submit(payment_date,customer,bonus):
	frappe.db.sql("""update `tabPayments Record` 
								set check_box_of_submit = 1,
						payment_date = '{0}' where check_box = 1
						and parent in (select name from `tabCustomer Agreement`
						where customer = '{1}' and agreement_status = 'Open')""".format(payment_date,customer))
	
	agreements = frappe.db.sql("""select name from `tabCustomer Agreement` where customer = '{0}'
							and agreement_status = "Open" """.format(customer),as_list=1)

	customer = frappe.get_doc("Customer",customer)
	added_bonus = float(bonus) - customer.bonus
	customer.update({
		"bonus":bonus
		})
	if float(added_bonus) > 0:
		comment = """ {0} EUR Bonus Added """.format(added_bonus)
		customer.add_comment("Comment",comment)
	customer.save(ignore_permissions=True)

	for agreement in [agreement[0] for agreement in agreements]:
		customer_agreement = frappe.get_doc("Customer Agreement",agreement)
		set_values_in_agreement_on_submit(customer_agreement)
		# customer_agreement.save(ignore_permissions=True)

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
		customer_agreement.payments_left = len(customer_agreement.payments_record) - len(payment_made)
	customer_agreement.save(ignore_permissions=True)	

@frappe.whitelist()
def set_values_in_agreement_temporary(customer_agreement,frm_bonus,row_to_uncheck=None):
	print frm_bonus, "bonus",'bonus'
	row_to_uncheck = json.loads(row_to_uncheck)
	print row_to_uncheck,"row_to_uncheck"
	customer_agreement = frappe.get_doc("Customer Agreement",customer_agreement)
	now_date = datetime.now().date()
	firstDay_next_month = date(now_date.year, now_date.month+1, 1)
	late_payments = []
	amount_of_payment_left = []
	add_bonus_of_one_eur = []
	add_bonus_of_two_eur = []
	remove_bonus_of_one_eur = []
	remove_bonus_of_two_eur = []
	no_of_late_days = 0
	received_payments = []
	submitable_payments = []
	if customer_agreement.payments_record:
		for row in customer_agreement.payments_record:
			if row.check_box == 1 and row.check_box_of_submit == 0:
				received_payments.append(row.monthly_rental_amount)
			
			if row.due_date and row.payment_date and date_diff(row.payment_date,row.due_date) > 3:
				no_of_late_days += date_diff(row.payment_date,row.due_date) - 3
				late_payments.append(row.monthly_rental_amount)	
			
			if (getdate(row.due_date) >= firstDay_next_month) and row.check_box == 0:
			 	amount_of_payment_left.append(row.monthly_rental_amount)
			
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
				customer_agreement.next_due_date = customer_agreement.get_next_due_date(customer_agreement.current_due_date,1)
				break
			elif row.check_box == 0 and date_diff(row.due_date,datetime.now()) >= 0:
				customer_agreement.current_due_date = row.due_date
				customer_agreement.next_due_date = row.due_date	
				break		


	print len(submitable_payments),"submitable_payments"	

	received_payments = map(float,received_payments)				
	print received_payments,len(received_payments),"received_payments"
	amount_of_payment_left = map(float,amount_of_payment_left)
	#print sum(amount_of_payment_left),"amount_of_payment_left"

	late_payments = map(float,late_payments)
	#print sum(late_payments),"late_payments"

	bonus = len(add_bonus_of_one_eur)*1 + len(add_bonus_of_two_eur)*2
	print bonus,"bonus"

	subtract_bonus = len(remove_bonus_of_one_eur)*1 + len(remove_bonus_of_two_eur)*2
	print subtract_bonus,"sub tractbonus"


	if customer_agreement.payments_record and customer_agreement.date:

		customer_agreement.payments_left = len(customer_agreement.payments_record) - len(received_payments) - len(submitable_payments)
		customer_agreement.balance = customer_agreement.payments_left * customer_agreement.monthly_rental_payment
		customer_agreement.late_payments = sum(late_payments)
		customer_agreement.amount_of_payment_left = sum(amount_of_payment_left)
		customer_agreement.number_of_payments = len(received_payments)
		customer_agreement.late_fees = no_of_late_days * customer_agreement.monthly_rental_payment * 0.02
		customer_agreement.bonus = customer_agreement.bonus + bonus
		# customer = frappe.get_doc("Customer",customer_agreement.customer)
		# previsous_bonus = customer.bonus
	customer_agreement.save(ignore_permissions=True)
	total_bonus = float(frm_bonus) + bonus - subtract_bonus
	print  total_bonus,"total_bonus",type(total_bonus),"type of total_bonus"
	return str(total_bonus)


@frappe.whitelist()
def remove_all_old_check(customer):
	print "in side remove_all_old_check"
	return frappe.db.sql("""update `tabPayments Record` set check_box = 0,pre_select_uncheck = 0,payment_date = "" 
							where check_box_of_submit = 0 
							and parent in (select name from `tabCustomer Agreement`
							where customer = '{0}' and agreement_status = "Open") """.format(customer))



@frappe.whitelist()
def update_payments_child_table(customer):
	print "in update_payments_child_table"
	now_date = datetime.now().date()
	firstDay_this_month = date(now_date.year, now_date.month, 1)
	firstDay_next_month = date(now_date.year, now_date.month+1, 1)
	due_payment_list = []
	customer_agreement = frappe.db.sql("""select name from `tabCustomer Agreement`
							where customer = '{0}' and agreement_status = "Open" """.format(customer),as_list=1)
	for agreement in [e[0] for e in customer_agreement]:
		customer_agreement = frappe.get_doc("Customer Agreement",agreement)
		#print customer_agreement.name
		for row in customer_agreement.payments_record:
			# print row,"rowwwwwwwwww"
			# print type(getdate(row.due_date)),"row.due_date111111111112222222222222"
			# print (getdate(row.due_date) >= firstDay_this_month and getdate(row.due_date) < firstDay_next_month),"an or and"
			# if row.check_box == 0 and (row.due_date >= firstDay_this_month and row.due_date < firstDay_next_month):
			print getdate(row.due_date),"row.due_date"
			print firstDay_this_month,"firstDay_this_month"
			print (getdate(row.due_date) >= firstDay_this_month and getdate(row.due_date) < firstDay_next_month),"condition"
			if row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and getdate(row.due_date) >= firstDay_this_month and getdate(row.due_date) < firstDay_next_month:
				print "in if 1"
				# print row.idx,"idx"
				# print row.check_box,"check_box1"
				row.update({
					"check_box":1
				})
				#print row.check_box,"check_box1"
				row.save(ignore_permissions=True)
			# if (row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and row.due_date < firstDay_this_month) or (row.check_box == 1 and row.check_box_of_submit == 0):
			if (row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and getdate(row.due_date) < firstDay_this_month):
				#print "in if second"
				#print row.idx,"idx"
				row.update({
					"check_box":1
				})
				row.save(ignore_permissions=True)
		customer_agreement.save(ignore_permissions = True)

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
		discount = (agreement.balance / 100) * float(agreement.early_buy_discount_percentage)
		Total_payoff_amount = (agreement.early_buy_discount_percentage * agreement.balance) + agreement.late_payments + float(late_fees) - float(receivable)
		Total_payoff_amount = "{0:.2f}".format(Total_payoff_amount)
		return {"cond":2,
				"Receivables":"{0} EUR".format(receivable),
				"Amount_of_payments_left":"{0} EUR".format(agreement.balance),
				"Discounted_payment_amount":"{0} EUR".format("{0:.2f}".format(agreement.balance - float(discount))),
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
	
	receivable = frappe.db.get_value("Customer",{"name":customer},"receivables")
	for agreement in [e[0] for e in customer_agreement]:
		customer_agreement = frappe.get_doc("Customer Agreement",agreement)
		print customer_agreement.name
		for row in customer_agreement.payments_record:
			if(row.check_box_of_submit == 0 and row.check_box ==1):
				due_payment_list.append(row.monthly_rental_amount)
			# if row.check_box == 0 and (row.due_date >= firstDay_this_month and row.due_date < firstDay_next_month):
			# if row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and row.due_date >= firstDay_this_month and row.due_date < firstDay_next_month and row.pre_select_uncheck == 0:
			# 	print "in if first"
			# 	print row.idx,"row.idx"
			# 	due_payment_list.append(row.monthly_rental_amount)
				
			# # if (row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and row.due_date < firstDay_this_month) or (row.check_box == 1 and row.check_box_of_submit == 0):
			# if (row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and row.due_date < firstDay_this_month):
			# 	print "in if second"
			# 	print row.idx,"row.idx"
			# 	due_payment_list.append(row.monthly_rental_amount)
	
	return {"sum":sum(due_payment_list),"receivable":receivable}

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
def update_suspenison_date_in_agreement(customer_agreement,date):
	# date = datetime.strptime(date, '%d-%m-%Y')
	customer_agreement = frappe.get_doc("Customer Agreement",customer_agreement)
	customer_agreement.update({
		"suspension_date":date
		})
	customer_agreement.save(ignore_permissions = True)

	 

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