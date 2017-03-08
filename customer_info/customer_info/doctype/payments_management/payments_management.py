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
from customer_info.customer_info.doctype.customer_agreement.customer_agreement import update_due_dates_of_payments


class PaymentsManagement(Document):
	pass

@frappe.whitelist()
def get_bonus_summary(customer):
	"""
	update early_payments_bonus and payment_on_time_bonus

	"""
	for agreement in [agreement for agreement in frappe.get_all("Customer Agreement",\
					 filters={"customer":customer})]:
		agreement_doc = frappe.get_doc("Customer Agreement",agreement['name'])
		# print frappe.db.sql("""select payment_id from `tabPayments Record` 
		# 	where parent ='{0}' and add_bonus_to_this_payment =1 """.format(agreement['name']))
		agreement_doc.early_payments_bonus = frappe.db.sql("""select sum(I.BONUS) from
			(select  CASE WHEN add_bonus_to_this_payment = 1 AND check_box_of_submit = 1
			AND payment_date < due_date THEN add_bonus_to_this_payment * 2 ELSE 0 END 
			AS bonus 
			from `tabPayments Record` where parent = "{0}")I
			""".format(agreement['name']),as_list=1)[0][0]
		agreement_doc.payment_on_time_bonus = frappe.db.sql("""select sum(I.BONUS) from
			(select  CASE WHEN add_bonus_to_this_payment = 1 AND check_box_of_submit = 1
			AND payment_date = due_date THEN add_bonus_to_this_payment * 1 ELSE 0 END 
			AS bonus 
			from `tabPayments Record` where parent = "{0}")I
			""".format(agreement['name']),as_list=1)[0][0]		
		agreement_doc.bonus = agreement_doc.new_agreement_bonus + agreement_doc.payment_on_time_bonus + agreement_doc.early_payments_bonus# - agreement_doc.temporary_new_bonus
		#agreement_doc.bonus = agreement_doc.bonus  - agreement_doc.temporary_new_bonus + agreement_doc.payment_on_time_bonus + agreement_doc.early_payments_bonus
		#agreement_doc.temporary_new_bonus = 0
		agreement_doc.save(ignore_permissions=True)

	return frappe.db.get_values("Customer Agreement",{"customer":customer},["name","new_agreement_bonus",\
								"early_payments_bonus","payment_on_time_bonus","agreement_status"],as_dict=1)


@frappe.whitelist()
def update_bonus(customer,bonus,assign_manual_bonus,payment_date):
	customer = frappe.get_doc("Customer",customer)
	if float(bonus) >= 0:
		now_date = datetime.now().date()
		comment = """ Bonus Modified From {1} To {2}""".format(now_date,customer.bonus,bonus)
		#frappe.throw(_("{0}").format(comment))
		customer_bonus_records = customer.append("customer_bonus_records")
		customer_bonus_records.amount = assign_manual_bonus
		customer_bonus_records.bonus_type = "Adding Manual Bonus"
		customer_bonus_records.payment_date = payment_date
		customer.add_comment("Comment",comment)
		customer.bonus = bonus
		customer.assign_manual_bonus = float(customer.assign_manual_bonus) + float(assign_manual_bonus) #float(bonus) - float(old_bonus)
		customer.assign_manual_bonus_date = now_date
		customer.save(ignore_permissions=True)
		return comment

@frappe.whitelist()
def calculate_total_charges(customer,flag,payment_date):
	receivables = frappe.db.get_value("Customer",{"name":customer},"receivables")
	bonus = frappe.db.get_value("Customer",{"name":customer},"bonus")

	if flag == "Customer" or flag == "Onload":
		frappe.db.sql("""update `tabPayments Record` set check_box = 0,pre_select_uncheck = 0,payment_date = "",
						add_bonus_to_this_payment = 0,
						bonus_type = ""	 
						where check_box_of_submit = 0 
						and parent in (select name from `tabCustomer Agreement`
						where customer = '{0}' and agreement_status = "Open") """.format(customer))

		# frappe.db.sql("""update `tabCustomer Agreement` set number_of_payments = 0,total_due = 0,
		# 				late_payment = 0,
		# 				late_fees = CASE WHEN late_fees_updated = "No"
		#  				THEN 0 ELSE late_fees END
		# 				where customer = '{0}' 
		# 				and agreement_status = "Open" """.format(customer))
		
		# by above query remain late fees as it is,after update late fees

		frappe.db.sql("""update `tabCustomer Agreement` set number_of_payments = 0,total_due = 0,
						late_payment = 0,
						late_fees = 0,late_fees_updated = "No",
						discount_updated = "No"
						where customer = '{0}' 
						and agreement_status = "Open" """.format(customer))
	
	now_date = datetime.now().date()
	firstDay_this_month = date(now_date.year, now_date.month, 1)
	agreements_due_amount_list = []
	agreements_and_late_fees_dict = {}
	agreements_discount_list = []


	customer_agreement = frappe.db.sql("""select name from `tabCustomer Agreement`
									where customer = '{0}' 
									and agreement_status = 'Open'""".format(customer),as_list=1)

	
	for agreement in [e[0] for e in customer_agreement]:
		customer_agreement = frappe.get_doc("Customer Agreement",agreement)
		late_fees_of_agreement = []
		rental_amount_of_late_payments = []
		for row in customer_agreement.payments_record:

			if row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and getdate(row.due_date) >= firstDay_this_month and getdate(row.due_date) <= now_date:
				agreements_due_amount_list.append(row.monthly_rental_amount)
				row.check_box = 1
				row.payment_date = payment_date
				if date_diff(payment_date,row.due_date) > 3:
					late_fee = (date_diff(payment_date,row.due_date) - 3) * row.monthly_rental_amount * 0.02
					if agreement in agreements_and_late_fees_dict.keys():
						agreements_and_late_fees_dict[agreement] += late_fee
					else:
						agreements_and_late_fees_dict[agreement] = late_fee
					late_fees_of_agreement.append(late_fee)
					rental_amount_of_late_payments.append(row.monthly_rental_amount) # for adding rental payment of late payment of agreement
			if (row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and getdate(row.due_date) < firstDay_this_month):
				agreements_due_amount_list.append(row.monthly_rental_amount)
				row.check_box = 1
				row.payment_date = payment_date
				if date_diff(payment_date,row.due_date) > 3:
					late_fee = (date_diff(payment_date,row.due_date) - 3) * row.monthly_rental_amount * 0.02
					late_fees_of_agreement.append(late_fee) # for adding late fees of agreement
					if agreement in agreements_and_late_fees_dict.keys(): # for adding late fees of all agreements
						agreements_and_late_fees_dict[agreement] += late_fee
					else:
						agreements_and_late_fees_dict[agreement] = late_fee
					rental_amount_of_late_payments.append(row.monthly_rental_amount) # for adding rental payment of late payment of agreement

		#print rental_amount_of_late_payments,"rental_amount_of_late_payments","\n\n\n\n\n\n\n"				
		customer_agreement.late_payment = sum(rental_amount_of_late_payments)	# 	updating by addition of rental payment of late payment of agreement
		#customer_agreement.total_late_payments = sum(rental_amount_of_late_payments)


		if customer_agreement.late_fees_updated == "No":
			customer_agreement.late_fees = float("{0:.2f}".format(sum(late_fees_of_agreement)))

		if customer_agreement.discount_updated == "Yes":
			#agreements_discount_list.append(customer_agreement.campaign_discount)
			agreements_discount_list.append(customer_agreement.discount)

		if customer_agreement.late_fees_updated == "Yes":
			agreements_and_late_fees_dict[customer_agreement.name] = customer_agreement.late_fees	

		customer_agreement.save(ignore_permissions=True)

	discount_amount_of_agreements = "{0:.2f}".format(sum(agreements_discount_list))
	agreements_due_amount_list.append(float("{0:.2f}".format(sum(agreements_and_late_fees_dict.values()))))
	return {"amount_of_due_payments":sum(agreements_due_amount_list) - float(discount_amount_of_agreements), # deduct campaign discount of all agreements
			"receivables":receivables,
			"bonus":bonus}

# @frappe.whitelist()
# def calculate_total_charges(customer,flag,payment_date):
# 	if flag == "Customer" or flag == "Onload":
# 		frappe.db.sql("""update `tabPayments Record` set check_box = 0,pre_select_uncheck = 0,payment_date = "",
# 						add_bonus_to_this_payment = 0	 
# 						where check_box_of_submit = 0 
# 						and parent in (select name from `tabCustomer Agreement`
# 						where customer = '{0}' and agreement_status = "Open") """.format(customer))

# 		frappe.db.sql("""update `tabCustomer Agreement` set number_of_payments = 0,total_due = 0,
# 						late_payment = 0,
# 						late_fees = CASE WHEN late_fees_updated = "No"
# 		 				THEN 0 ELSE late_fees END
# 						where customer = '{0}' 
# 						and agreement_status = "Open" """.format(customer))

# 		# frappe.db.sql("""update `tabCustomer Agreement` set 
# 		# 				late_fees = CASE WHEN late_fees_updated = "No"
# 		# 				THEN 0 ELSE late_fees END 
# 		# 				where customer = '{0}' 
# 		# 				and agreement_status = "Open" """.format(customer))

# 	#firstDay_next_month = date(now_date.year, now_date.month+1, 1)
		
	

# 	now_date = datetime.now().date()
# 	firstDay_this_month = date(now_date.year, now_date.month, 1)
# 	due_payment_list = []
# 	late_payment_amount = []
# 	discount = []


# 	customer_agreement = frappe.db.sql("""select name from `tabCustomer Agreement`
# 									where customer = '{0}' 
# 									and agreement_status = 'Open'""".format(customer),as_list=1)

# 	receivables = frappe.db.get_value("Customer",{"name":customer},"receivables")
# 	bonus = frappe.db.get_value("Customer",{"name":customer},"bonus")
# 	for agreement in [e[0] for e in customer_agreement]:
# 		customer_agreement = frappe.get_doc("Customer Agreement",agreement)
# 		late_fees_of_agreement = []
# 		late_payments_rental_payment = []
# 		for row in customer_agreement.payments_record:

# 			if row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and getdate(row.due_date) >= firstDay_this_month and getdate(row.due_date) <= now_date:
# 				due_payment_list.append(row.monthly_rental_amount)
# 				row.check_box = 1
# 				row.payment_date = payment_date
# 				if date_diff(payment_date,row.due_date) > 3:
# 					late_fee = (date_diff(payment_date,row.due_date) - 3) * row.monthly_rental_amount * 0.02
# 					late_payment_amount.append(late_fee)
# 					late_fees_of_agreement.append(late_fee)
# 					late_payments_rental_payment.append(row.monthly_rental_amount) # for adding rental payment of late payment of agreement
# 			if (row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and getdate(row.due_date) < firstDay_this_month):
# 				due_payment_list.append(row.monthly_rental_amount)
# 				row.check_box = 1
# 				row.payment_date = payment_date
# 				if date_diff(payment_date,row.due_date) > 3:
# 					late_fee = (date_diff(payment_date,row.due_date) - 3) * row.monthly_rental_amount * 0.02
# 					late_fees_of_agreement.append(late_fee) # for adding late fees of agreement
# 					late_payment_amount.append(late_fee) # for adding late fees of all agreements
# 					late_payments_rental_payment.append(row.monthly_rental_amount) # for adding rental payment of late payment of agreement

# 		print late_payments_rental_payment,"late_payments_rental_payment","\n\n\n\n\n\n\n"				
# 		customer_agreement.late_payment = sum(late_payments_rental_payment)	# 	updating by addition of rental payment of late payment of agreement
			
# 		if customer_agreement.late_fees_updated == "No":
# 			customer_agreement.late_fees = float("{0:.2f}".format(sum(late_fees_of_agreement)))
# 		if customer_agreement.discount_updated == "Yes":
# 			discount.append(customer_agreement.campaign_discount)

# 		customer_agreement.save(ignore_permissions=True)
# 	discount_amount_of_agreements = "{0:.2f}".format(sum(discount))
# 	due_payment_list.append(float("{0:.2f}".format(sum(late_payment_amount))))
# 	return {"amount_of_due_payments":sum(due_payment_list) - float(discount_amount_of_agreements), # deduct campaign discount of all agreements
# 			"receivables":receivables,
# 			"bonus":bonus}

@frappe.whitelist()
def update_due_date(agreement,update_due_date):
	customer_agreement = frappe.get_doc("Customer Agreement",agreement)
	date_dict = update_due_dates_of_payments(update_due_date,agreement)
	for row_data in customer_agreement.payments_record:
		if row_data.payment_id in date_dict.keys():
			row_data.due_date = date_dict[row_data.payment_id]
	customer_agreement.payment_day = str(update_due_date.split("-")[2])
	customer_agreement.update_due_date = update_due_date
	customer_agreement.current_due_date = update_due_date
	customer_agreement.next_due_date = get_next_due_date(update_due_date,1)
	customer_agreement.save(ignore_permissions=True)
	return "True"

@frappe.whitelist()
def update_late_fees(agreement,late_fees):
	customer_agreement = frappe.get_doc("Customer Agreement",agreement)
	customer_agreement.late_fees_updated = "Yes"
	customer_agreement.late_fees = late_fees
	customer_agreement.save(ignore_permissions=True)	

@frappe.whitelist()
def update_campaign_discount(agreement,campaign_discount):
	customer_agreement = frappe.get_doc("Customer Agreement",agreement)
	customer_agreement.discount_updated = "Yes"
	#customer_agreement.campaign_discount = campaign_discount
	customer_agreement.discount = campaign_discount
	customer_agreement.save(ignore_permissions=True)		
	return customer_agreement.campaign_discount


@frappe.whitelist()
def get_customer_agreement(customer,payment_date,flag=None):
	#WHEN DATEDIFF(suspension_date,now()) > 0 AND contact_result = "WBI" THEN DATE_FORMAT(suspension_date,'%d-%m-%Y')
	condition =  "and agreement_status = '{0}' ".format("Suspended" if flag else "Open") 
	suspended_until_date = ",suspended_until" if flag else ""
	data = {
	"list_of_agreement": frappe.db.sql("""select agreement_no,agreement_period,
										concat(product," ",product_category),number_of_payments,
										monthly_rental_payment,current_due_date,next_due_date,
										payments_left,balance,late_fees,total_due,payments_made,
										CASE 
										WHEN DATEDIFF(suspension_date,now()) > 0 AND contact_result = "WBI" THEN "WBI"
										WHEN contact_result = "Sent SMS/Email" THEN "SMS/Email" 
										ELSE "Call/Commitment" 
										END AS suspension_date,
										concat(format(discount,2),"-",format(campaign_discount,2),"-",format(discounted_payments_left,2),"-",discount_updated) as discounted_payments_left,
										/* CASE WHEN discount_updated = "Yes" THEN campaign_discount ELSE 0 END as campaign_discount */
										CASE WHEN discount_updated = "Yes" THEN discount ELSE 0 END as campaign_discount {2}
										from `tabCustomer Agreement`
										where customer = '{0}' {1} """.format(customer,condition,suspended_until_date),as_list=1)
	}
	for entry in data['list_of_agreement']:
		entry[7] = float(entry[1]) - frappe.db.sql("""select count(payment_id) from
										`tabPayments Record`
										where parent = '{1}' and check_box_of_submit = 1 """.format(payment_date,entry[0]),as_list=1)[0][0]
		

		if entry[3] == 0:
			entry[3] = frappe.db.sql("""select count(payment_id) from
										`tabPayments Record`
										where parent = '{1}' and check_box =1 and check_box_of_submit = 0 """.format(payment_date,entry[0]),as_list=1)[0][0]
			if entry[3] > 0:
				entry[10] = "{0:.2f}".format(float(entry[4])*float(entry[3])+ float(entry[9])-float(entry[14]))
			else:	
				entry[10] = "{0:.2f}".format(float(entry[9])-float(entry[14]))

		if float(entry[3]) > 0:
			entry[10] = "{0:.2f}".format(float(entry[4])*float(entry[3])+ float(entry[9])-float(entry[14]))

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
	#firstDay_next_month = date(now_date.year, now_date.month+1, 1)
	
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
			
			if customer_agreement.customer_group == "Individual" and flag != "Payoff":# and customer_agreement.document_type == "New":
				if row.payment_date and row.idx != 1 and getdate(row.payment_date) == getdate(row.due_date) and row.add_bonus_to_this_payment == 0 and row.check_box_of_submit==0 and row.check_box == 1:
					add_bonus_of_one_eur.append(row.idx)
					row.update({
						'add_bonus_to_this_payment':1,
						'bonus_type':"On Time Bonus"
						})
					row.save(ignore_permissions = True)

				elif row.payment_date and row.idx != 1 and getdate(row.payment_date) < getdate(row.due_date)  and row.add_bonus_to_this_payment == 0 and row.check_box_of_submit==0 and row.check_box == 1:
					add_bonus_of_two_eur.append(row.idx)
					row.update({
						'add_bonus_to_this_payment':1,
						'bonus_type':"Early Bonus"
						})
					row.save(ignore_permissions = True)
				
				if row.payment_id in row_to_uncheck and row.idx != 1 and getdate(now_date) == getdate(row.due_date) and row.add_bonus_to_this_payment == 1 and (row.check_box_of_submit==0 or row.check_box_of_submit==1):
					remove_bonus_of_one_eur.append(row.idx)
					row.update({
						'add_bonus_to_this_payment':0,
						'bonus_type':""
						})
					row.save(ignore_permissions = True)

				elif row.payment_id in row_to_uncheck and row.idx != 1 and getdate(now_date) < getdate(row.due_date) and row.add_bonus_to_this_payment == 1 and (row.check_box_of_submit==0 or row.check_box_of_submit==1):
					remove_bonus_of_two_eur.append(row.idx)	
					row.update({
						'add_bonus_to_this_payment':0,
						'bonus_type':""
						})
					row.save(ignore_permissions = True)

	received_payments = map(float,received_payments)
	
	amount_of_payment_left = map(float,amount_of_payment_left)

	late_payments = map(float,late_payments)

	add_bonus = len(add_bonus_of_one_eur)*1 + len(add_bonus_of_two_eur)*2

	subtract_bonus = len(remove_bonus_of_one_eur)*1 + len(remove_bonus_of_two_eur)*2



	if customer_agreement.payments_record and customer_agreement.date:
		#customer_agreement.payments_left = len(customer_agreement.payments_record) - len(received_payments) - len(submitable_payments)
		customer_agreement.total_late_payments = sum(late_payments)
		customer_agreement.late_payment = sum(late_payments)
		customer_agreement.amount_of_payment_left = sum(amount_of_payment_left)
		customer_agreement.number_of_payments = len(received_payments)
		customer_agreement.payment_on_time_bonus = customer_agreement.payment_on_time_bonus + (len(add_bonus_of_one_eur)*1 - len(remove_bonus_of_one_eur)*1)  # update early payment bonus
		customer_agreement.early_payments_bonus = customer_agreement.early_payments_bonus +  (len(add_bonus_of_two_eur)*2 - len(remove_bonus_of_two_eur)*2) # update on time payment bonus
		
		if customer_agreement.late_fees_updated == "No":
			customer_agreement.late_fees = "{0:.2f}".format(float(no_of_late_days * customer_agreement.monthly_rental_payment * 0.02))

		customer_agreement.bonus = customer_agreement.bonus + add_bonus - subtract_bonus
		# if  flag != "Make Refund":
		# 	customer_agreement.temporary_new_bonus = add_bonus - subtract_bonus
		# else:
		# 	customer_agreement.temporary_new_bonus = 0
		customer_agreement.total_due = "{0:.2f}".format(len(received_payments) * customer_agreement.monthly_rental_payment + (no_of_late_days * customer_agreement.monthly_rental_payment * 0.02))
	customer_agreement.save(ignore_permissions=True)

	#print frm_bonus,"frm_bonus","\n\n\n\n",bonus," add bonus","\n\n\n\n",subtract_bonus,"subtract_bonus","\n\n\n\n\n\n"
	total_bonus = float(frm_bonus) + add_bonus - float(subtract_bonus)

	return str(total_bonus)


@frappe.whitelist()
def get_next_due_date(date,i):
	add_month_to_date = add_months(date,i)
	return add_month_to_date


@frappe.whitelist()
def get_late_payment(agreements,payment_date):
	agreements = json.loads(agreements)
	_condition = ""
	first_payment = []
	if len(agreements) > 1:
		agreements = tuple([x.encode('UTF8') for x in list(agreements) if x])
		_condition = "where name in {0}".format(agreements)
		for i in agreements:
			customer_agreement = frappe.get_doc("Customer Agreement",i)
			for row in customer_agreement.payments_record:
				if row.check_box == 1 and row.check_box_of_submit == 0 and row.idx == 1:# and getdate(row.due_date) >= getdate(payment_date):
					first_payment.append(row.monthly_rental_amount)
					
	if len(agreements) == 1:
		#agreements = agreements.split(",")[0]
		customer_agreement = frappe.get_doc("Customer Agreement",agreements[0])
		for row in customer_agreement.payments_record:
			if row.check_box == 1 and row.check_box_of_submit == 0 and row.idx == 1:# and getdate(row.due_date) >= getdate(payment_date):
				first_payment.append(row.monthly_rental_amount)
		_condition = "where name = '{0}'".format(agreements[0])
	late_payment = frappe.db.sql("""select format(sum(late_payment),2) from 
								`tabCustomer Agreement` {0} """.format(_condition),as_list=1)

	return {"late_payment":late_payment[0][0],"first_payment":sum(first_payment)}

@frappe.whitelist()
#def update_on_submit(values,customer,receivables,add_in_receivables,payment_date,bonus,manual_bonus,used_bonus,new_bonus,total_charges,rental_payment,late_fees):
def update_on_submit(args,flag):
	print "insdie update_on_submit\n\n\n\n\n\n\n"
	#args = json.loads(args) if not flag else args
	args = json.loads(args) if flag == "from_payoff" else args
	#values = json.loads(values)
	#cond = "(select name from `tabCustomer Agreement` where customer = '{0}' and agreement_status = 'Open')".format(args['customer'])
	cond = "(select name from `tabCustomer Agreement` where customer = '{0}' {1})".format(args['customer'],"" if flag == "from_import_payment" else "and agreement_status = 'Open'")

	submitted_payments_ids_info = frappe.db.sql("""select payment_id,due_date,
							payment_date,monthly_rental_amount from `tabPayments Record` where 
							parent in {0}
							and check_box = 1 
							and check_box_of_submit = 0 
							and payment_date = '{1}' order by idx """.format(cond,args['payment_date']),as_dict=1)
	
	# checking  all payment done by bonus then update payments record remove new given bonus
	args['assigned_bonus_discount'] = ""
	if submitted_payments_ids_info and (float(args['values']['bonus']) > 0 or float(args['values']['discount']) > 0):
		args['assigned_bonus_discount'] = add_assigned_bonus_and_discount(args,submitted_payments_ids_info)#return agreement name 


		"""
		remove bonus when payment only done by bonus with no receivables

		"""

		if float(args['values']['amount_paid_by_customer']) == 0 and float(args['values']['bank_card']) == 0 and float(args['values']['bank_transfer']) == 0 and\
			float(args['values']['discount']) == 0 and float(args['values']['bonus']) > 0 and float(args['receivables']) == 0:
			remove_new_bonus(submitted_payments_ids_info)
			args['bonus'] = float(args['bonus'] - float(args['new_bonus']))
			args['new_bonus'] = 0


		"""
		remove_bonus from all payments when any payments have late_fees	

		"""	

		if float(args['late_fees']) > 0 or float(args['receivables']) < 0 or float(args['add_in_receivables']) < 0:
			remove_new_bonus(submitted_payments_ids_info)
			args['bonus'] = float(args['bonus'] - float(args['new_bonus']))	
			args['new_bonus'] = 0

	frappe.db.sql("""update `tabPayments Record` 
						set check_box_of_submit = 1
						where check_box = 1 and check_box_of_submit = 0
						and  payment_date = '{0}'
						and parent in {1}""".format(args['payment_date'],cond))
	
	agreements = frappe.db.sql("""{0}""".format(cond),as_list=1)
	
	completed_agreement_list = []
	merchandise_status = ""
	discount_amount = 0
	campaign_discount_of_agreements = ""
	late_fees_updated_status = ""
	for agreement in [agreement[0] for agreement in agreements]:
		customer_agreement = frappe.get_doc("Customer Agreement",agreement)
		merchandise_status += str(customer_agreement.name)+"/"+str(customer_agreement.merchandise_status)+"/"+str(customer_agreement.agreement_closing_suspending_reason)+","
		if customer_agreement.discount_updated == "Yes":
			#discount_amount += customer_agreement.campaign_discount
			campaign_discount_of_agreements += str(customer_agreement.name)+"/"+str(customer_agreement.discount)+"/"+str(customer_agreement.discounted_payments_left)+","
			discount_amount += customer_agreement.discount

		set_values_in_agreement_on_submit(customer_agreement)
		
		if float(customer_agreement.payments_left) == 0:
			completed_agreement_list.append(customer_agreement.name)		
		
		if customer_agreement.late_fees_updated == "Yes":
			late_fees_updated_status = "Yes"
			customer_agreement.late_fees_updated = "No"
			customer_agreement.save(ignore_permissions=True)
		flag = "Process Payment"

	""""
	add_assigned_campaing_discount_discount		
	"""
	if campaign_discount_of_agreements:
		add_assigned_campaing_discount_discount(campaign_discount_of_agreements)

	#add_bonus_and_receivables_to_customer(customer,bonus,manual_bonus,used_bonus,add_in_receivables,flag)
	used_bonus_of_customer = add_bonus_and_receivables_to_customer(args,flag)

	payments_detalis_list = []
	payment_ids_list = []
	if submitted_payments_ids_info:
		for d in submitted_payments_ids_info:
			payments_detalis_list.append(str(d["payment_id"])+"/"+str(d["due_date"])+"/"+str(d["monthly_rental_amount"])+"/"+str(d["payment_date"]))
			payment_ids_list.append(d["payment_id"])

		#make_payment_history(values,customer,receivables,add_in_receivables,payment_date,total_charges,payments_detalis_list,payment_ids_list,rental_payment,0,late_fees,"Normal Payment",merchandise_status,late_fees_updated_status,"Rental Payment",discount_amount,new_bonus)	
		args['total_amount'] = 0
		make_payment_history(args,payments_detalis_list,payment_ids_list,"Normal Payment",merchandise_status,late_fees_updated_status,"Rental Payment",discount_amount,campaign_discount_of_agreements)	
		

		# remove customer bonus when all agreements are closed
		if set(completed_agreement_list) == set([agreement[0] for agreement in agreements]):
			customer_doc = frappe.get_doc("Customer",args['customer'])
			customer_doc.bonus = 0
			customer_doc.save(ignore_permissions=True)

		return {"completed_agreement_list":completed_agreement_list if len(completed_agreement_list) > 0 else "",
				"used_bonus_of_customer":used_bonus_of_customer,
				"remove_bonus":"True" if set(completed_agreement_list) == set([agreement[0] for agreement in agreements]) else "False"}

	else:
		args['total_amount'] = 0
		make_payment_history(args,payments_detalis_list,payment_ids_list,"Modification Of Receivables",merchandise_status,late_fees_updated_status,"Modification Of Receivables",discount_amount,campaign_discount_of_agreements)		

"""
add assigned_campaing_discount if campaign discount given
"""
def add_assigned_campaing_discount_discount(campaign_discount_data):
	campaign_discount_of_agreements_list = []
	campaign_discount_of_agreements_list = [x.encode('UTF8') for x in campaign_discount_data.split(",")[0:-1] if x]	
	campaign_discount_of_agreements_list.sort()
	for row in campaign_discount_of_agreements_list:
		agreement_doc = frappe.get_doc("Customer Agreement",row.split("/")[0])
		agreement_doc.assigned_campaign_discount += float(row.split("/")[1])
		agreement_doc.save(ignore_permissions=True)

""" 
add assigned bonus ,dicount to agreement  
which has the longest valid 90d SAC price.(date) 
"""
def add_assigned_bonus_and_discount(args,submitted_payments_ids_info):
	agreement_name = []
	for agreement_id in submitted_payments_ids_info:	
		agreement_name.append(agreement_id["payment_id"].split("-P")[0])

	agreement_name = tuple([x.encode('UTF8') for x in set(agreement_name) if x])
	if len(agreement_name) > 1:
		agreement = frappe.db.sql("""select name from `tabCustomer Agreement`
		where customer = '{0}' and name in {1}
		order by today_plus_90_days desc limit 1""".format(args['customer'],agreement_name),as_list=1)[0][0]
	if len(agreement_name) == 1:
		agreement = agreement_name[0]
	
	agreement_doc = frappe.get_doc("Customer Agreement",agreement)
	if float(args['values']['bonus']) > 0:	
		agreement_doc.assigned_bonus +=  float(args['values']['bonus'] )
	
	if float(args['values']['discount']) > 0:
		agreement_doc.assigned_discount +=  float(args['values']['discount'] 	)
	agreement_doc.save(ignore_permissions=True)
	return agreement 
# def add_assigned_bonus_to_agreement(customer,bonus):
# 	agreement = frappe.db.sql("""select name from `tabCustomer Agreement`
# 		where customer = '{0}' and agreement_status = "Open" 
# 		order by today_plus_90_days desc limit 1""".format(customer),as_list=1)[0][0]
# 	agreement_doc = frappe.get_doc("Customer Agreement",agreement)
# 	agreement_doc.assigned_bonus +=  bonus
# 	agreement_doc.save(ignore_permissions=True)
	# today_plus_90_days_date = ""
	# frappe.errprint([agreement[0] for agreement in agreements])
	# for agreement in [agreement[0] for agreement in agreements]:
	# 	frappe.errprint(agreement)
	# 	agreement_doc = frappe.get_doc("Customer Agreement",agreement)
	# 	if agreement_doc.today_plus_90_days and today_plus_90_days_date:
	# 		if getdate(today_plus_90_days_date) < getdate(agreement_doc.today_plus_90_days):
	# 			today_plus_90_days_date = agreement_doc.today_plus_90_days
	# 	elif agreement_doc.today_plus_90_days and today_plus_90_days_date == "":
	# 			today_plus_90_days_date = agreement_doc.today_plus_90_days

	# frappe.errprint([today_plus_90_days_date,"today_plus_90_days_date"])


"""remove newly added bonus of payments"""

def remove_new_bonus(submitted_payments_ids_info):
	submitted_payments_ids = []
	for d in submitted_payments_ids_info:	
		submitted_payments_ids.append(d["payment_id"])

	submitted_payments_ids = tuple([x.encode('UTF8') for x in submitted_payments_ids if x])	
	if len(submitted_payments_ids) > 1:
		condi = "where payment_id in {0}".format(submitted_payments_ids)
	elif len(submitted_payments_ids) == 1:
		condi = "where payment_id = '{0}'".format(submitted_payments_ids[0])	
	frappe.db.sql("""update `tabPayments Record` 
					set add_bonus_to_this_payment = 0,bonus_type=""
					{0} and add_bonus_to_this_payment=1""".format(condi))




def set_values_in_agreement_on_submit(customer_agreement,flag=None):
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
			#if row.check_box == 0 and row.idx == 1:
			if row.check_box_of_submit == 0 and row.idx == 1:
				customer_agreement.current_due_date = customer_agreement.date
				customer_agreement.next_due_date = customer_agreement.payments_record[index+1].due_date#get_next_due_date(customer_agreement.due_date_of_next_month,0)
				break
			#if row.check_box == 0 and row.idx == len(customer_agreement.payments_record):
			if row.check_box_of_submit == 0 and row.idx == len(customer_agreement.payments_record):
				customer_agreement.current_due_date = row.due_date
				customer_agreement.next_due_date = row.due_date
				break			
			# if row.idx == 1:
			# 	customer_agreement.current_due_date = customer_agreement.date
			# 	customer_agreement.next_due_date = get_next_due_date(row.due_date,1)
			# 	break	
	payment_made = map(float,payment_made)
	#print sum(payment_made),"sum of payments_made"

	if customer_agreement.payments_record and customer_agreement.date:
		customer_agreement.payments_made = sum(payment_made)
		customer_agreement.number_of_payments = 0
		customer_agreement.late_fees = 0
		customer_agreement.late_payment = 0
		customer_agreement.discount_updated = "No"
		#customer_agreement.temporary_new_bonus = 0
		customer_agreement.payments_left = len(customer_agreement.payments_record) - len(payment_made)
		if customer_agreement.discounted_payments_left > 0 and customer_agreement.discount > 0 and customer_agreement.campaign_discount > 0:
			customer_agreement.discounted_payments_left = float(customer_agreement.discounted_payments_left) - (float(customer_agreement.discount)/float(customer_agreement.campaign_discount))
		customer_agreement.balance = (len(customer_agreement.payments_record) - len(payment_made)) * customer_agreement.monthly_rental_payment
		customer_agreement.total_due = 0
	#customer_agreement.save(ignore_permissions=True)
	if float(customer_agreement.payments_left) == 0 and flag != "Payoff Payment":
		customer_agreement.agreement_status = "Closed"
		customer_agreement.agreement_closing_suspending_reason = "Contract Term is over"
		customer_agreement.merchandise_status = "Agreement over"
	customer_agreement.save(ignore_permissions=True)		

def add_bonus_and_receivables_to_customer(args,flag):
	customer_doc = frappe.get_doc("Customer",args['customer'])
	if flag == "Process Payment":
		if args['bonus'] >= 0 and customer_doc.customer_group == "Individual":
			#added_bonus = float(bonus) - customer_doc.bonus
			now_date = datetime.now().date()
			customer_bonus_records = customer_doc.append("customer_bonus_records")
			customer_bonus_records.amount = float(args['used_bonus'])
			customer_bonus_records.bonus_type = "Used Bonus"
			customer_bonus_records.payment_date = args['payment_date']
			customer_doc.update({
				"bonus":float(args['bonus']),
				"used_bonus":float(customer_doc.used_bonus) + float(args['used_bonus']),
				"used_bonus_date":now_date
			})
			customer_doc.save(ignore_permissions=True)
			#if float(added_bonus) > 0:
				#comment = """ {0} EUR Bonus Added """.format(added_bonus)
				#frappe.throw(_("{0}").format(comment))
				#customer_doc.add_comment("Comment",comment)
		customer_doc.update({
			"receivables":float(args['add_in_receivables']),
			"old_receivables":float(args['add_in_receivables'])
		}) 	
		customer_doc.save(ignore_permissions=True)
		return customer_doc.used_bonus

	elif flag == "Payoff Payment":
		customer_doc.update({
			"receivables":float(args['add_in_receivables']),
			"old_receivables":float(args['add_in_receivables'])	
			#"receivables":float(customer_doc.receivables) + float(receivables)
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
#def payoff_submit(customer_agreement,agreement_status,condition,customer,receivables,add_in_receivables,values,payment_date,total_charges,data,rental_payment,total_amount):
def payoff_submit(args,from_import_payment=None):
	args = json.loads(args) if not from_import_payment else args
	now_date = datetime.now().date()
	discount_amount = 0
	late_fees_updated_status = "No"
	frappe.db.sql("""update `tabPayments Record` 
						set check_box_of_submit = 1
						where check_box = 1 and check_box_of_submit = 0
						and  payment_date = '{0}'
						and parent = '{1}' """.format(args['payment_date'],args['customer_agreement']))
	frappe.db.commit()
	
	agreement = frappe.get_doc("Customer Agreement",args['customer_agreement'])
	late_payment = agreement.late_payment
	set_values_in_agreement_on_submit(agreement,"Payoff Payment")
	merchandise_status = agreement.merchandise_status
	#if args['condition'] == "90 day pay Off" and agreement.agreement_status == "Open":
	if args['condition'] == "90 day pay Off":# and agreement.agreement_status == "Open":
		agreement.update({
			"agreement_status":"Closed",
			"agreement_close_date":now_date,
			"agreement_closing_suspending_reason":"Early buy offer",
			"merchandise_status":"Early buy"
		})
		agreement.save(ignore_permissions=True)
		payoff_cond = "Early buy"+"-"+str(agreement.early_buy_discount_percentage)

	
	#elif args['condition'] == "pay off agreement" and agreement.agreement_status == "Open":
	elif args['condition'] == "pay off agreement":# and agreement.agreement_status == "Open":
		agreement.update({
			"agreement_status":"Closed",
			"agreement_close_date":now_date,
			"agreement_closing_suspending_reason":"90d SAC",
			"merchandise_status":"Sold" if date_diff(args['payment_date'],agreement.date) <= 2 else "90d SAC"
		})
		agreement.save(ignore_permissions=True)
		payoff_cond = "90d SAC"

	if agreement.discount_updated == "Yes":
		discount_amount = agreement.discount	
	if agreement.late_fees_updated == "Yes":
		late_fees_updated_status = "Yes"
		agreement.late_fees_updated = "No"
		agreement.save(ignore_permissions=True)	

	flag = "Payoff Payment"
	add_bonus_and_receivables_to_customer(args,flag)
	
	data = args['data']
	_total_charges = 0
	payments_detalis_list = []
	payment_ids_list = []
	args['late_fees'] = data['late_fees']
	args['assigned_bonus_discount'] = ""
	for d in data['submitted_payments_ids']:	
		payments_detalis_list.append(str(d["payment_id"])+"/"+str(d["due_date"])+"/"+str(d["monthly_rental_amount"])+"/"+str(d["payment_date"]))
		payment_ids_list.append(d["payment_id"])
		_total_charges += d["monthly_rental_amount"]

	args['total_charges'] = float(_total_charges)	
	

	#args['total_charges'] = float(args['total_charges']) + float(_total_charges)
	args['total_amount'] = float(args['total_amount'].split(" ")[0]) if not from_import_payment else float(args['total_amount'])
	if args['condition'] == "90 day pay Off":
		args['rental_payment'] = float(args['rental_payment'].split(" ")[0]) if not from_import_payment else float(args['rental_payment']) + float(late_payment)
	else:
		args['rental_payment'] = float(args['rental_payment'].split(" ")[0]) if not from_import_payment else float(args['rental_payment'])	
	args['new_bonus'] = 0
	#make_payment_history(values,customer,receivables,add_in_receivables,payment_date,total_charges,payments_detalis_list,payment_ids_list,rental_payment,total_amount,data['late_fees'],"Payoff Payment",merchandise_status,late_fees_updated_status,payoff_cond,discount_amount)	
	make_payment_history(args,payments_detalis_list,payment_ids_list,"Payoff Payment",merchandise_status,late_fees_updated_status,payoff_cond,discount_amount)	
	return checking_all_agreements_closed(agreement.customer)


def checking_all_agreements_closed(customer):
	customer_doc = frappe.get_doc("Customer",customer)
	agreements_status = frappe.db.sql("""select agreement_status 
								from `tabCustomer Agreement` where customer = '{0}' 
								and agreement_status <> 'Updated' """.format(customer),as_list=1)
	customer_doc.bonus = 0 if all(status == "Closed" for status in [s[0] for s in agreements_status]) else customer_doc.bonus
	customer_doc.save(ignore_permissions=True)
	return "True" if all(status == "Closed" for status in [s[0] for s in agreements_status]) else "False"



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
		return {"cond":"pay off agreement",#1,
				"s90d_SAC_price":"{0} EUR".format(agreement.s90d_sac_price),
				"Expires":agreement.today_plus_90_days,
				"Payments_made":"{0} EUR".format(payments_made),
				"Bonus_payments":"{0} EUR".format(agreement.assigned_bonus),
				"Discount_payments":"{0} EUR".format(agreement.assigned_discount),
				"assigned_campaign_discount":"{0} EUR".format(agreement.assigned_campaign_discount),
				"Late_fees":"{0} EUR".format(float(late_fees)),
				"s90_day_pay_Off":"{0} EUR".format(float(day_pay_Off)),
				"Number_of_payments_left":agreement.payments_left
				}

	elif agreement.today_plus_90_days < datetime.now().date():
		balance = float(agreement.payments_left) * agreement.monthly_rental_payment
		discount = ((balance - float(agreement.late_payment)) / 100) * float(agreement.early_buy_discount_percentage)
		#Total_payoff_amount = (balance - float(discount)) + float(agreement.total_late_payments) + float(late_fees) - float(receivable)
		#Total_payoff_amount = (balance - float(discount)) + float(agreement.late_payment) + float(late_fees) - float(receivable)
		Total_payoff_amount = float(late_fees) + balance - float(discount) - float(receivable)
		Total_payoff_amount = "{0:.2f}".format(Total_payoff_amount)
		#format(Total_payoff_amount)
		return {"cond":"90 day pay Off",#2,
				"Receivables":"{0} EUR".format(receivable),
				#"Amount_of_payments_left":"{0} EUR".format(float(balance)-float(agreement.total_late_payments)),
				"Amount_of_payments_left":"{0} EUR".format(float(balance)-float(agreement.late_payment)),
				"Discounted_payment_amount":"{0} EUR".format("{0:.2f}".format(balance - float(discount) -float(agreement.late_payment) )),
				#"Late_payments":"{0} EUR".format(agreement.total_late_payments),
				"Late_payments":"{0} EUR".format(agreement.late_payment),
				"Late_fees":"{0} EUR".format(float(late_fees)),
				"Total_payoff_amount":"{0} EUR".format(float(Total_payoff_amount)),
				"discount":"{0} EUR".format("{0:.2f}".format(discount)),
				"discount_percentage":"{0}% discount".format(agreement.early_buy_discount_percentage)
				}


def get_history_records(customer_agreement):
	total_transaction_amount = ""
	history_record_dict = frappe.db.sql("""select payment_id,due_date,payment_date,
											monthly_rental_amount,"balance" as balance,pmt,
											"asso" as associate, "late" as late_days,total_transaction_amount from `tabPayments Record`
											where parent ='{0}' and check_box_of_submit = 1 order by idx""".format(customer_agreement),as_dict=1)
	# balance = frappe.db.get_value("Customer Agreement",{"name":customer_agreement},"balance")
	agreement = frappe.get_doc("Customer Agreement",customer_agreement)
	balance = "{0:.2f}".format(float(agreement.agreement_period) * float(agreement.monthly_rental_payment))
	for i in history_record_dict:
		i['associate'] = frappe.session.user
		total_transaction_amount = i["total_transaction_amount"]
		i["total_transaction_amount"] = total_transaction_amount.split("/")[0] if total_transaction_amount else 0
		i["total_calculated_payment_amount"] = total_transaction_amount.split("/")[1]  if total_transaction_amount else 0
		if float(balance) > float(i["monthly_rental_amount"]):
			i["balance"] = "{0:.2f}".format(float(balance) - float(i['monthly_rental_amount']))
			balance = float(balance) - float(i['monthly_rental_amount'])
		if date_diff(i['payment_date'],i['due_date']) > 0:
			i["late_days"] = "+" + str(date_diff(i['payment_date'],i['due_date']))
		elif date_diff(i['payment_date'],i['due_date']) == 0:
			i["late_days"] = 0
		elif date_diff(i['payment_date'],i['due_date']) < 0:
			i["late_days"] = date_diff(i['payment_date'],i['due_date'])
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
def get_payments_management_from_agreement(source_name, target_doc=None):
	customer_agreement = frappe.get_doc("Customer Agreement",source_name)
	customer_doc = frappe.get_doc("Customer",customer_agreement.customer)
	target_doc = get_mapped_doc("Customer Agreement", source_name,
		{
			"Customer Agreement": {
				"doctype": "Payments Management",
			},
		}, target_doc)

	target_doc.customer = customer_agreement.customer
	target_doc.customer_agreement = source_name
	target_doc.bonus = customer_doc.bonus
	target_doc.static_bonus = customer_doc.bonus
	target_doc.used_bonus = customer_doc.used_bonus
	target_doc.assign_manual_bonus = customer_doc.assign_manual_bonus
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
def calculate_underpayment(agreements,payment_date,amount_paid_by_customer,receivables,late_fees):
	#print late_fees,"\n\n\n\n"
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

	total = float(add) - float(receivables) + float(late_fees)
	return total
	# if float(amount_paid_by_customer) >= float(total):
	# 	return float(total)
