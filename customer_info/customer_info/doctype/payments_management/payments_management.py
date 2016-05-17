# -*- coding: utf-8 -*-
# Copyright (c) 2015, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document

class PaymentsManagement(Document):
	pass

@frappe.whitelist()
def get_customer_agreement(customer):
	return {
	"list_of_agreement": frappe.db.sql("""select agreement_no,agreement_period,product,number_of_payments,
										monthly_rental_payment,current_due_date,next_due_date,
										payments_left,balance,late_fees,total_due
										from `tabCustomer Agreement`
										where customer = '{0}' and agreement_status = 'Open' """.format(customer),as_list=1,debug=1)
	}	


@frappe.whitelist()
def get_payments_record(customer_agreement):
	return {
	"payments_record" : frappe.db.sql("""select no_of_payments,monthly_rental_amount,
										due_date,payment_id,check_box,check_box_of_submit from `tabPayments Record` 
										where parent = '{0}' 
										order by due_date """.format(customer_agreement),as_dict=1)
	}

@frappe.whitelist()
def temporary_payments_update_to_child_table_of_customer_agreement(row_to_update=None,row_to_uncheck=None,parent=None,payment_date=None):
	row_to_update = json.loads(row_to_update)
	row_to_uncheck = json.loads(row_to_uncheck)
	if row_to_update:
		set_check_and_uncheck(row_to_update,parent,1,payment_date)
	if row_to_uncheck:
		set_check_and_uncheck(row_to_uncheck,parent,0,"")

def set_check_and_uncheck(list_of_payment_id,parent,value,payment_date):
	for i in list_of_payment_id:
		customer_agreement = frappe.get_doc("Customer Agreement",parent)
		for row in customer_agreement.payments_record:
				if row.payment_id in list_of_payment_id:
					row.update({
							'check_box':value,
							'payment_date':payment_date
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



# @frappe.whitelist()
# def update_payments_child_table_of_customer_agreement_on_submit(list_of_row_to_update_on_submit,payment_date):
# 	list_of_row_to_update_on_submit = json.loads(list_of_row_to_update_on_submit)
# 	for i in list_of_row_to_update_on_submit:
# 		update_child_table_of_agreement(i['parent'],i['list_of_payment_id'],payment_date)
# 	return "SuccesFully Update"	


# def update_child_table_of_agreement(parent,payment_id_list,payment_date):
# 	customer_agreement = frappe.get_doc("Customer Agreement",parent)
# 	for row in customer_agreement.payments_record:
# 		if row.payment_id in payment_id_list: 
# 			row.update({
# 					'check_box_of_submit':1,
# 					'check_box':1,
# 					'payment_date':payment_date
# 			})
# 			row.save(ignore_permissions = True)




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