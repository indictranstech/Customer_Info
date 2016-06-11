# -*- coding: utf-8 -*-
# Copyright (c) 2015, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import datetime
from datetime import datetime,date
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document

class PaymentsManagement(Document):
	pass

@frappe.whitelist()
def get_customer_agreement(customer):
	return {
	"list_of_agreement": frappe.db.sql("""select agreement_no,agreement_period,product,number_of_payments,
										monthly_rental_payment,current_due_date,next_due_date,
										payments_left,balance,late_fees,total_due,
										CASE WHEN DATEDIFF(suspension_date,now()) > 0 THEN DATE_FORMAT(suspension_date,'%d-%m-%Y') 
										ELSE "Suspension" 
										END AS suspension_date
										from `tabCustomer Agreement`
										where customer = '{0}' and agreement_status = 'Open' """.format(customer),as_list=1,debug=1)
	}	


@frappe.whitelist()
def get_payments_record(customer_agreement):
	return {
	"payments_record" : frappe.db.sql("""select no_of_payments,monthly_rental_amount,
										due_date,payment_date,payment_id,check_box,check_box_of_submit,pre_select_uncheck from `tabPayments Record` 
										where parent = '{0}' 
										order by due_date """.format(customer_agreement),as_dict=1)
	}

@frappe.whitelist()
def temporary_payments_update_to_child_table_of_customer_agreement(row_to_update=None,row_to_uncheck=None,row_to_check=None,row_to_pre_select_uncheck=None,parent=None,payment_date=None):
	row_to_update = json.loads(row_to_update)
	row_to_uncheck = json.loads(row_to_uncheck)
	row_to_check = json.loads(row_to_check)
	# checked_row_from_child_table = json.loads(checked_row_from_child_table)
	# unchecked_pre_select = json.loads(unchecked_pre_select)
	if row_to_update:
		set_check_and_uncheck(row_to_update,parent,1,0,payment_date)

	if row_to_uncheck:
		set_check_and_uncheck(row_to_uncheck,parent,0,"")

	if row_to_pre_select_uncheck:
		set_check_and_uncheck(row_to_pre_select_uncheck,parent,0,1,"")

	if row_to_check:
		set_check_and_uncheck(row_to_check,parent,1,0,payment_date)

	# if checked_row_from_child_table:
	# 	set_check_and_uncheck(checked_row_from_child_table,parent,1,payment_date)
	# if unchecked_pre_select:
	# 	set_check_and_uncheck(unchecked_pre_select,parent,0)		

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
	customer_agreement.onload();			
	customer_agreement.save(ignore_permissions = True)


@frappe.whitelist()
def update_payments_child_table_of_customer_agreement_on_submit(payment_date,customer):
	return frappe.db.sql("""update `tabPayments Record` 
							set check_box_of_submit = 1,
							payment_date = '{0}' where check_box = 1
							and parent in (select name from `tabCustomer Agreement`
							where customer = '{1}' and agreement_status = 'Open')""".format(payment_date,customer))


@frappe.whitelist()
def remove_all_old_check(customer):
	return frappe.db.sql("""update `tabPayments Record` set check_box = 0,pre_select_uncheck = 0,payment_date = "" 
							where check_box_of_submit = 0 
							and parent in (select name from `tabCustomer Agreement`
							where customer = '{0}' and agreement_status = "Open") """.format(customer),debug=1)



@frappe.whitelist()
def update_payments_child_table(customer):
	print "in update_payments_child_table"
	now_date = datetime.now().date()
	firstDay_this_month = date(now_date.year, now_date.month, 1)
	firstDay_next_month = date(now_date.year, now_date.month+1, 1)
	due_payment_list = []
	customer_agreement = frappe.db.sql("""select name from `tabCustomer Agreement`
							where customer = '{0}' and agreement_status = "Open" """.format(customer),as_list=1,debug=1)
	for agreement in [e[0] for e in customer_agreement]:
		customer_agreement = frappe.get_doc("Customer Agreement",agreement)
		print customer_agreement.name
		for row in customer_agreement.payments_record:
			print row,"rowwwwwwwwww"
			# if row.check_box == 0 and (row.due_date >= firstDay_this_month and row.due_date < firstDay_next_month):
			if row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and row.due_date >= firstDay_this_month and row.due_date < firstDay_next_month:
				print "in if 1"
				print row.idx,"idx"
				print row.check_box,"check_box1"
				row.update({
					"check_box":1
				})
				print row.check_box,"check_box1"
				row.save(ignore_permissions=True)
			# if (row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and row.due_date < firstDay_this_month) or (row.check_box == 1 and row.check_box_of_submit == 0):
			if (row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and row.due_date < firstDay_this_month):
				print "in if second"
				print row.idx,"idx"
				row.update({
					"check_box":1
				})
				row.save(ignore_permissions=True)
		customer_agreement.save(ignore_permissions = True)








@frappe.whitelist()
def calculate_total_charges(customer):
	print "in calculate_total_charges"
	now_date = datetime.now().date()
	firstDay_this_month = date(now_date.year, now_date.month, 1)
	firstDay_next_month = date(now_date.year, now_date.month+1, 1)
	due_payment_list = []
	customer_agreement = frappe.db.sql("""select name from `tabCustomer Agreement`
							where customer = '{0}' and agreement_status = "Open" """.format(customer),as_list=1,debug=1)
	
	receivable = frappe.db.get_value("Customer",{"name":customer},"receivable")
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
	customer = frappe.get_doc("Customer",customer)
	customer.update({
		"receivable":receivables
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