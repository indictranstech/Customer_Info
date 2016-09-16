# -*- coding: utf-8 -*-
# Copyright (c) 2015, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.utils import date_diff
import datetime
from frappe import _
from frappe.utils import flt, get_datetime, get_time, getdate
from frappe.utils import nowdate, getdate,add_months
from datetime import datetime,date
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document
from customer_info.customer_info.doctype.payments_management.make_payment_history import make_payment_history


class PaymentsManagement(Document):
	pass

@frappe.whitelist()
def update_bonus(customer,bonus,old_bonus):
	customer = frappe.get_doc("Customer",customer)
	if float(bonus):
		now_date = datetime.now().date()
		comment = """ {0} - Bonus Modified From {1} To {2}""".format(now_date,old_bonus,bonus)
		#frappe.throw(_("{0}").format(comment))
		customer.add_comment("Comment",comment)
	customer.bonus = bonus
	customer.save(ignore_permissions=True)

@frappe.whitelist()
def calculate_total_charges(customer,flag,payment_date):
	if flag == "Customer" or flag == "Onload":
		frappe.db.sql("""update `tabPayments Record` set check_box = 0,pre_select_uncheck = 0,payment_date = "",
						add_bonus_to_this_payment = 0	 
						where check_box_of_submit = 0 
						and parent in (select name from `tabCustomer Agreement`
						where customer = '{0}' and agreement_status = "Open") """.format(customer))

		frappe.db.sql("""update `tabCustomer Agreement` set number_of_payments = 0,total_due = 0,late_fees = 0,late_payment = 0 
						where customer = '{0}' 
						and agreement_status = "Open" """.format(customer))
	
	now_date = datetime.now().date()
	firstDay_this_month = date(now_date.year, now_date.month, 1)
	#firstDay_next_month = date(now_date.year, now_date.month+1, 1)
	due_payment_list = []
	late_payment_amount = []

	customer_agreement = frappe.db.sql("""select name from `tabCustomer Agreement`
									where customer = '{0}' 
									and agreement_status = 'Open'""".format(customer),as_list=1)

	receivables = frappe.db.get_value("Customer",{"name":customer},"receivables")
	bonus = frappe.db.get_value("Customer",{"name":customer},"bonus")
	for agreement in [e[0] for e in customer_agreement]:
		customer_agreement = frappe.get_doc("Customer Agreement",agreement)
		for row in customer_agreement.payments_record:
			if row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and getdate(row.due_date) >= firstDay_this_month and getdate(row.due_date) <= now_date:
				due_payment_list.append(row.monthly_rental_amount)
				if date_diff(payment_date,row.due_date) > 3:
					late_fee = (date_diff(payment_date,row.due_date) - 3) * row.monthly_rental_amount * 0.02
					late_payment_amount.append(late_fee)

			if (row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and getdate(row.due_date) < firstDay_this_month):
				due_payment_list.append(row.monthly_rental_amount)
				if date_diff(payment_date,row.due_date) > 3:
					late_fee = (date_diff(payment_date,row.due_date) - 3) * row.monthly_rental_amount * 0.02
					late_payment_amount.append(late_fee)

	late_payment_amount =  "{0:.2f}".format(sum(late_payment_amount))
	due_payment_list.append(float(late_payment_amount))			
	return {"amount_of_due_payments":sum(due_payment_list),
			"receivables":receivables,
			"bonus":bonus}


@frappe.whitelist()
def get_customer_agreement(customer,payment_date):
	#WHEN DATEDIFF(suspension_date,now()) > 0 AND contact_result = "WBI" THEN DATE_FORMAT(suspension_date,'%d-%m-%Y')
	data = {
	"list_of_agreement": frappe.db.sql("""select agreement_no,agreement_period,
										concade_product_name_and_category,number_of_payments,
										monthly_rental_payment,current_due_date,next_due_date,
										payments_left,balance,late_fees,total_due,payments_made,
										CASE 
										WHEN DATEDIFF(suspension_date,now()) > 0 AND contact_result = "WBI" THEN "WBI"
										WHEN contact_result = "Sent SMS/Email" THEN "SMS/Email" 
										ELSE "Call/Commitment" 
										END AS suspension_date
										from `tabCustomer Agreement`
										where customer = '{0}' and agreement_status = 'Open' """.format(customer),as_list=1)
	}
	for entry in data['list_of_agreement']:
		payments_left = float(entry[1]) - frappe.db.sql("""select count(payment_id) from
										`tabPayments Record`
										where parent = '{1}' and check_box_of_submit = 1 """.format(payment_date,entry[0]),as_list=1)[0][0]
		entry[7] = payments_left
		if float(entry[3]) == 0:
			late_fees = frappe.db.sql("""select
										CASE WHEN due_date < '{0}' AND DATEDIFF('{0}',due_date) > 3 
										THEN (DATEDIFF('{0}',due_date) - 3) * monthly_rental_amount * 0.02 ELSE 0 END AS late_fees from
										`tabPayments Record`
										where parent = '{1}' and check_box_of_submit = 0 """.format(payment_date,entry[0]),as_list=1)		
			#entry[3] = len([e[0] for e in late_fees if e[0] > 0])
			entry[9] = "{0:.2f}".format(sum([e[0] for e in late_fees]))
			entry[10] = "{0:.2f}".format(float(entry[4])+sum([e[0] for e in late_fees])) if sum([e[0] for e in late_fees]) else "0.00"
		else:
			entry[9] = "{0:.2f}".format(entry[9])
			entry[10] = entry[10]
			#entry[3] = entry[3]
	return data	


@frappe.whitelist()
def temporary_payments_update_to_child_table_of_customer_agreement(row_to_update=None,row_to_uncheck=None,row_to_check=None,row_to_pre_select_uncheck=None,parent=None,payment_date=None):
	row_to_update = json.loads(row_to_update)
	row_to_uncheck = json.loads(row_to_uncheck)
	row_to_check = json.loads(row_to_check)
	row_to_pre_select_uncheck = json.loads(row_to_pre_select_uncheck)
 
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
def set_values_in_agreement_temporary(customer_agreement,frm_bonus,flag=None,row_to_uncheck=None):
	if flag != "Make Refund" and row_to_uncheck:
		row_to_uncheck = json.loads(row_to_uncheck)
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

	customer_agreement = frappe.get_doc("Customer Agreement",customer_agreement)
	
	if customer_agreement.payments_record:
		for row in customer_agreement.payments_record:
			if row.check_box == 1 and row.check_box_of_submit == 0:
				received_payments.append(row.monthly_rental_amount)
			
			if row.due_date and row.payment_date and date_diff(row.payment_date,row.due_date) > 3 and row.check_box == 1 and row.check_box_of_submit == 0:
				no_of_late_days += date_diff(row.payment_date,row.due_date) - 3
				late_payments.append(row.monthly_rental_amount)	

			if not row.payment_date:
			 	amount_of_payment_left.append(row.monthly_rental_amount)
			
			if row.check_box_of_submit == 1:
				submitable_payments.append(row.idx)
			
			if customer_agreement.customer_group == "Individual" and flag != "Payoff":
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

	received_payments = map(float,received_payments)
	
	amount_of_payment_left = map(float,amount_of_payment_left)

	late_payments = map(float,late_payments)

	bonus = len(add_bonus_of_one_eur)*1 + len(add_bonus_of_two_eur)*2

	subtract_bonus = len(remove_bonus_of_one_eur)*1 + len(remove_bonus_of_two_eur)*2

	if customer_agreement.payments_record and customer_agreement.date:
		customer_agreement.payments_left = len(customer_agreement.payments_record) - len(received_payments) - len(submitable_payments)
		customer_agreement.total_late_payments = sum(late_payments)
		customer_agreement.late_payment = sum(late_payments)
		customer_agreement.amount_of_payment_left = sum(amount_of_payment_left)
		customer_agreement.number_of_payments = len(received_payments)
		customer_agreement.late_fees = "{0:.2f}".format(float(no_of_late_days * customer_agreement.monthly_rental_payment * 0.02))
		customer_agreement.bonus = customer_agreement.bonus + bonus - subtract_bonus
		customer_agreement.total_due = "{0:.2f}".format(len(received_payments) * customer_agreement.monthly_rental_payment + (no_of_late_days * customer_agreement.monthly_rental_payment * 0.02))
	customer_agreement.save(ignore_permissions=True)

	total_bonus = float(frm_bonus) + bonus - subtract_bonus
	#print  total_bonus,"total_bonus",type(total_bonus),"type of total_bonus"
	return str(total_bonus)


@frappe.whitelist()
def get_next_due_date(date,i):
	add_month_to_date = add_months(date,i)
	return add_month_to_date


@frappe.whitelist()
def get_late_payment(agreements):
	agreements = json.loads(agreements)
	print agreements,"agreements","\n\n\n\n\n"
	_condition = ""
	if len(agreements) > 1:
		agreements = tuple([x.encode('UTF8') for x in list(agreements) if x])
		_condition = "where name in {0}".format(agreements)
	if len(agreements) == 1:
		#agreements = agreements.split(",")[0]
		_condition = "where name = '{0}'".format(agreements[0])
	late_payment = frappe.db.sql("""select format(sum(late_payment),2) from 
								`tabCustomer Agreement` {0} """.format(_condition),as_list=1)
	return late_payment[0][0]

@frappe.whitelist()
def update_on_submit(values,customer,receivables,add_in_receivables,payment_date,bonus,total_charges,rental_payment,late_fees):

	values = json.loads(values)
	cond = "(select name from `tabCustomer Agreement` where customer = '{0}' and agreement_status = 'Open')".format(customer)

	submitted_payments_ids = frappe.db.sql("""select payment_id,due_date,
							payment_date,monthly_rental_amount from `tabPayments Record` where 
							parent in {0}
							and check_box = 1 
							and check_box_of_submit = 0 
							and payment_date = '{1}' order by idx """.format(cond,payment_date),as_dict=1)
	
	frappe.db.sql("""update `tabPayments Record` 
						set check_box_of_submit = 1
						where check_box = 1 and check_box_of_submit = 0
						and  payment_date = '{0}'
						and parent in {1}""".format(payment_date,cond))
	
	agreements = frappe.db.sql("""{0}""".format(cond),as_list=1)
	

	completed_agreement_list = []
	merchandise_status = ""
	for agreement in [agreement[0] for agreement in agreements]:
		customer_agreement = frappe.get_doc("Customer Agreement",agreement)
		merchandise_status += str(customer_agreement.name)+"/"+str(customer_agreement.merchandise_status)+"/"+str(customer_agreement.agreement_closing_suspending_reason)+","
		set_values_in_agreement_on_submit(customer_agreement)
		if float(customer_agreement.payments_left) == 0:
			completed_agreement_list.append(customer_agreement.name)	
		flag = "Process Payment"
	
	#add_bonus_and_receivables_to_customer(customer,bonus,receivables,flag)
	#add_bonus_and_receivables_to_customer(customer,bonus,values['balance'],flag)
	add_bonus_and_receivables_to_customer(customer,bonus,add_in_receivables,flag)

	payments_detalis_list = []
	payment_ids_list = []
	for d in submitted_payments_ids:	
		payments_detalis_list.append(str(d["payment_id"])+"/"+str(d["due_date"])+"/"+str(d["monthly_rental_amount"])+"/"+str(d["payment_date"]))
		payment_ids_list.append(d["payment_id"])
	make_payment_history(values,customer,receivables,add_in_receivables,payment_date,total_charges,payments_detalis_list,payment_ids_list,rental_payment,0,late_fees,"Normal Payment",merchandise_status,"Rental Payment")	
	return completed_agreement_list

def set_values_in_agreement_on_submit(customer_agreement,flag=None):
	payment_made = []
	if customer_agreement.payments_record:
		for row in customer_agreement.payments_record:
			if row.check_box_of_submit == 1:
				payment_made.append(row.monthly_rental_amount)				

	payment_made = map(float,payment_made)
	#print sum(payment_made),"sum of payments_made"

	if customer_agreement.payments_record and customer_agreement.date:
		customer_agreement.payments_made = sum(payment_made)
		customer_agreement.number_of_payments = 0
		customer_agreement.late_fees = 0
		customer_agreement.late_payment = 0
		customer_agreement.payments_left = len(customer_agreement.payments_record) - len(payment_made)
		customer_agreement.balance = (len(customer_agreement.payments_record) - len(payment_made)) * customer_agreement.monthly_rental_payment
		customer_agreement.total_due = 0
	#customer_agreement.save(ignore_permissions=True)
	if float(customer_agreement.payments_left) == 0 and flag != "Payoff Payment":
		customer_agreement.agreement_status = "Closed"
		customer_agreement.agreement_closing_suspending_reason = "Contract Term is over"
		customer_agreement.merchandise_status = "Agreement over"
	customer_agreement.save(ignore_permissions=True)		

def add_bonus_and_receivables_to_customer(customer,bonus,receivables,flag):
	customer_doc = frappe.get_doc("Customer",customer)
	if flag == "Process Payment":
		if bonus > 0 and customer_doc.customer_group == "Individual":
			added_bonus = float(bonus) - customer_doc.bonus
			customer_doc.update({
				"bonus":float(bonus)
			})
			customer_doc.save(ignore_permissions=True)
			if float(added_bonus) > 0:
				comment = """ {0} EUR Bonus Added """.format(added_bonus)
				#frappe.throw(_("{0}").format(comment))
				customer_doc.add_comment("Comment",comment)
		customer_doc.update({
			"receivables":float(receivables)
		}) 	
		customer_doc.save(ignore_permissions=True)
	elif flag == "Payoff Payment":
		customer_doc.update({
				"receivables":float(customer_doc.receivables) + float(receivables)
			}) 	
		customer_doc.save(ignore_permissions=True)	


@frappe.whitelist()
def update_payments_records_on_payoff_submit(payment_date,customer_agreement):
	frappe.db.sql("""update `tabPayments Record` 
						set check_box = 1,payment_date = '{0}'
						where check_box_of_submit = 0
						and parent = '{1}' """.format(payment_date,customer_agreement))

	set_values_in_agreement_temporary(customer_agreement,0,"Payoff")
	agreement = frappe.get_doc("Customer Agreement",customer_agreement)
	late_fees = agreement.late_fees
	rental_payment = agreement.total_due
	
	submitted_payments_ids = frappe.db.sql("""select payment_id,due_date,
							payment_date,monthly_rental_amount from `tabPayments Record` where 
							parent = '{0}'
							and check_box = 1 
							and check_box_of_submit = 0 
							and payment_date = '{1}' order by idx """.format(customer_agreement,payment_date),as_dict=1)
	return {"submitted_payments_ids":submitted_payments_ids,"late_fees":late_fees,"rental_payment":rental_payment}

@frappe.whitelist()
def payoff_submit(customer_agreement,agreement_status,condition,customer,receivables,add_in_receivables,values,payment_date,total_charges,data,rental_payment,total_amount):
	now_date = datetime.now().date()
	
	frappe.db.sql("""update `tabPayments Record` 
						set check_box_of_submit = 1
						where check_box = 1 and check_box_of_submit = 0
						and  payment_date = '{0}'
						and parent = '{1}' """.format(payment_date,customer_agreement),debug=1)
	frappe.db.commit()
	
	agreement = frappe.get_doc("Customer Agreement",customer_agreement)
	set_values_in_agreement_on_submit(agreement,"Payoff Payment")
	merchandise_status = agreement.merchandise_status
	if int(condition) == 2 and agreement.agreement_status == "Open":
		agreement.update({
			"agreement_status":"Closed",
			"agreement_close_date":now_date,
			"agreement_closing_suspending_reason":"40% Offer"
		})
		agreement.save(ignore_permissions=True)
		payoff_cond = "Early buy"+"-"+str(agreement.early_buy_discount_percentage)

	elif int(condition) == 1 and agreement.agreement_status == "Open":
		agreement.update({
			"agreement_status":"Closed",
			"agreement_close_date":now_date,
			"agreement_closing_suspending_reason":"90d SAC"
		})
		agreement.save(ignore_permissions=True)
		payoff_cond = "90d SAC"

	flag = "Payoff Payment"	
	#add_bonus_and_receivables_to_customer(customer,0,receivables,flag)
	values = json.loads(values)
	
	#add_bonus_and_receivables_to_customer(customer,0,values['balance'],flag)
	add_bonus_and_receivables_to_customer(customer,0,add_in_receivables,flag)
	
	data = json.loads(data)
	_total_charges = 0
	payments_detalis_list = []
	payment_ids_list = []
	for d in data['submitted_payments_ids']:	
		payments_detalis_list.append(str(d["payment_id"])+"/"+str(d["due_date"])+"/"+str(d["monthly_rental_amount"])+"/"+str(d["payment_date"]))
		payment_ids_list.append(d["payment_id"])
		_total_charges += d["monthly_rental_amount"]

	total_charges = float(total_charges) + float(_total_charges)
	total_amount = float(total_amount.split(" ")[0])
	rental_payment = float(rental_payment.split(" ")[0])

	make_payment_history(values,customer,receivables,add_in_receivables,payment_date,total_charges,payments_detalis_list,payment_ids_list,rental_payment,total_amount,data['late_fees'],"Payoff Payment",merchandise_status,payoff_cond)	
	

@frappe.whitelist()
def get_payments_record(customer_agreement,receivable,late_fees,payment_date):
	return {
	"payments_record" : frappe.db.sql("""select no_of_payments,monthly_rental_amount,
										due_date,payment_date,payment_id,check_box,check_box_of_submit,pre_select_uncheck,
										CASE WHEN due_date < '{1}' AND DATEDIFF('{1}',due_date) > 3 
										THEN (DATEDIFF('{1}',due_date) - 3) * monthly_rental_amount * 0.02 ELSE 0 END AS late_fee
										from `tabPayments Record` 
										where parent = '{0}' 
										order by idx """.format(customer_agreement,payment_date),as_dict=1),
	"summary_records" : get_summary_records(customer_agreement,receivable,late_fees),
	"history_record" : get_history_records(customer_agreement)
	}


def get_summary_records(agreement,receivable,late_fees):
	agreement = frappe.get_doc("Customer Agreement",agreement)
	late_fees = "{0:.2f}".format(flt(late_fees))
	#payments_made = "{0:.2f}".format(agreement.payments_made + float(receivable))
	payments_made = "{0:.2f}".format(agreement.payments_made)
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
		Total_payoff_amount = (balance - float(discount)) + float(agreement.total_late_payments) + float(late_fees) - float(receivable)
		Total_payoff_amount = "{0:.2f}".format(Total_payoff_amount)
		format(Total_payoff_amount)
		return {"cond":2,
				"Receivables":"{0} EUR".format(receivable),
				"Amount_of_payments_left":"{0} EUR".format(balance),
				"Discounted_payment_amount":"{0} EUR".format("{0:.2f}".format(balance - float(discount))),
				"Late_payments":"{0} EUR".format(agreement.total_late_payments),
				"Late_fees":"{0} EUR".format(float(late_fees)),
				"Total_payoff_amount":"{0} EUR".format(float(Total_payoff_amount)),
				"discount":"{0} EUR".format("{0:.2f}".format(discount)),
				"discount_percentage":"{0}% discount".format(agreement.early_buy_discount_percentage)
				}


def get_history_records(customer_agreement):
	history_record_dict = frappe.db.sql("""select payment_id,due_date,payment_date,
											monthly_rental_amount,"balance" as balance,pmt,
											"asso" as associate, "late" as late_days,total_transaction_amount from `tabPayments Record`
											where parent ='{0}' and check_box_of_submit = 1 order by idx""".format(customer_agreement),as_dict=1)
	# balance = frappe.db.get_value("Customer Agreement",{"name":customer_agreement},"balance")
	agreement = frappe.get_doc("Customer Agreement",customer_agreement)
	balance = "{0:.2f}".format(float(agreement.agreement_period) * float(agreement.monthly_rental_payment))
	for i in history_record_dict:
		i['associate'] = frappe.session.user
		if float(balance) > float(i["monthly_rental_amount"]):
			i["balance"] = "{0:.2f}".format(float(balance) - float(i['monthly_rental_amount']))
			balance = float(balance) - float(i['monthly_rental_amount'])
		if date_diff(i['payment_date'],i['due_date']) > 0:
			i["late_days"] = "+" + str(date_diff(i['payment_date'],i['due_date']))
		elif date_diff(i['payment_date'],i['due_date']) == 0:
			i["late_days"] = 0
		elif date_diff(i['payment_date'],i['due_date']) < 0:
			i["late_days"] = date_diff(i['payment_date'],i['due_date'])
	print history_record_dict,"history_record_dict history_record_dict","\n\n\n\n\n\n"		
	return history_record_dict

	
@frappe.whitelist()
def update_call_commitment_data_in_agreement(customer_agreement,date,contact_result,amount,all_or_individual):
		if all_or_individual == "Individual":
			if not date:
				date = ""
				amount = 0
			customer_agreement = frappe.get_doc("Customer Agreement",customer_agreement)
			customer_agreement.update({
				"suspension_date":date,
				"contact_result": contact_result,
				"amount_of_contact_result":amount,
				"call_commitment":all_or_individual
				})
			customer_agreement.save(ignore_permissions = True)

		if all_or_individual == "All":
			agreements = json.loads(customer_agreement)
			if not date:
				date = ""
				amount = 0
			for agreement in agreements:
				customer_agreement = frappe.get_doc("Customer Agreement",agreement)
				customer_agreement.update({
					"suspension_date":date,
					"contact_result": contact_result,
					"amount_of_contact_result":amount,
					"call_commitment":all_or_individual
					})
				customer_agreement.save(ignore_permissions = True)

@frappe.whitelist()
def set_or_reset_call_commitment(customer,agreement_name,agreements):
	now_date = datetime.now().date()
	agreements = json.loads(agreements)
	#if customer and not agreement_name:	
	if customer and agreement_name == "Common":	
		for i in agreements:
			agreement_doc = frappe.get_doc("Customer Agreement",i)
			agreement_doc.update({
				"suspension_date":now_date,
				"contact_result":" ",
				"amount_of_contact_result":0,
				"call_commitment":" "
				})
			agreement_doc.save(ignore_permissions=True)

	#if agreement_name:
	if agreement_name != "Common":
		agreement_doc = frappe.get_doc("Customer Agreement",agreement_name)
		agreement_doc.update({
			"suspension_date":now_date,
			"contact_result":" ",
			"amount_of_contact_result":0,
			"call_commitment":" "
			})
		agreement_doc.save(ignore_permissions=True)			



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

# call From Customer master OnClick Button Payment management 
@frappe.whitelist()
def _get_payments_management(source_name, target_doc=None):
	customer_agreement = frappe.get_doc("Customer Agreement",source_name)
	target_doc = get_mapped_doc("Customer Agreement", source_name,
		{
			"Customer Agreement": {
				"doctype": "Payments Management",
			},
		}, target_doc)

	target_doc.customer = customer_agreement.customer
	target_doc.customer_agreement = source_name
	return target_doc

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


@frappe.whitelist()
def calculate_underpayment(agreements,payment_date,amount_paid_by_customer,receivables):

	agreements = json.loads(agreements)

	id_list = tuple([x.encode('UTF8') for x in list(agreements) if x])
	
	if len(id_list) == 1:
		cond ="where parent = '{0}' ".format(id_list[0]) 
	elif len(id_list) > 1:	
		cond = "where parent in {0} ".format(id_list)  
	
	record = frappe.db.sql("""select monthly_rental_amount from `tabPayments Record`
							{0} and payment_date = '{1}' and check_box = 1 and check_box_of_submit = 0
							order by due_date""".format(cond,payment_date),as_list=1)
	add = sum([e[0] for e in record][0:-1]) + [e[0] for e in record][-1]/2
	total = float(add) - float(receivables)
	return total
	# if float(amount_paid_by_customer) >= float(total):
	# 	return float(total)
