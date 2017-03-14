# Copyright (c) 2013, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = get_colums(), get_data(filters)
	return columns, data

def get_data(filters=None):
	result = frappe.db.sql("""	select
							(select COALESCE(sum(new_agreement_bonus),0) from `tabCustomer Agreement` where agreement_status="Open" {0} ) as new_agreement_bonus,
							COALESCE(sum(IF(bonus_type = "Early Bonus", add_bonus_to_this_payment*1, 0)),0) as early_bonus,
							COALESCE(sum(IF(bonus_type = "On Time Bonus", add_bonus_to_this_payment*2, 0)),0) as on_time
							from `tabPayments Record` where add_bonus_to_this_payment = 1
							and check_box_of_submit = 1
							and parent in (select name from `tabCustomer Agreement` where agreement_status="Open")
							{1} """.format(get_condtion_for_date(filters.get('from_date'),filters.get('to_date')),get_condtion(filters.get('from_date'),filters.get('to_date'))),as_list=1)

	result[0].extend(frappe.db.sql("""select
											COALESCE(sum(IF(bonus_type = "Adding Manual Bonus",amount,0)),0) as manual_bonus,
											0,
											COALESCE(sum(IF(bonus_type = "Used Bonus",amount,0)),0) as used_bonus,
											0,
											0
											from `tabBonus Records` where
											parent in (select name from `tabCustomer` where customer_group = "Individual") 
											{0} """.format(get_condtion(filters.get('from_date'),filters.get('to_date'))),as_list=1)[0])

	if result:
		result[0][4] = result[0][0]+result[0][1]+result[0][2]+result[0][3]
		result[0][6] = result[0][0]+result[0][1]+result[0][2]+result[0][3] - result[0][5]
		result[0][7] = frappe.db.sql("""select sum(cancelled_bonus) from `tabCustomer` where customer_group ='Individual' """,as_list=1)[0][0]
		return result
	

def get_condtion_for_date(from_date,to_date):
	cond = ""
	if  from_date and to_date:
		cond = "and date BETWEEN '{0}' AND '{1}' ".format(from_date,to_date)

	elif from_date:
		cond = "and date >= '{0}' ".format(from_date)

	elif to_date:
		cond = "and date < '{0}' ".format(to_date)

	return cond


def get_condtion(from_date,to_date):
	cond = ""
	if  from_date and to_date:
		cond = "and payment_date BETWEEN '{0}' AND '{1}' ".format(from_date,to_date)

	elif from_date:
		cond = "and payment_date >= '{0}' ".format(from_date)

	elif to_date:
		cond = "and payment_date < '{0}' ".format(to_date)

	return cond	


def get_colums():
	columns =  [("New agreement bonus") + ":Float:150",
				("Early payments bonus") + ":Float:150",
				("Payment on time bonus") + ":Float:150",
				("Assign manual bonus") + ":Float:150",
				("Total bonus accumulated") + ":Float:160",
				("Used bonus") + ":Float:90",
				("Active bonus") + ":Float:90",
				("Cancelled bonus") + ":Float:150"
				]
	return columns