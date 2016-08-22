# Copyright (c) 2013, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json

def execute(filters=None):
	columns, data = [], []
	columns = get_colums()
	data = get_data(filters)
	# static_list = ["","Totals"]
	# static_list.extend(get_totals(filters))
	# data.append(static_list)
	return columns, data

def get_totals(filters):
	if filters:
		return frappe.db.sql("""select sum(rental_payment),sum(late_fees),sum(receivables),
							sum(rental_payment+late_fees+receivables),
							sum(bank_transfer),sum(cash),sum(bank_card),
							sum(balance),sum(discount),sum(bonus) from `tabPayments History`
							{0}""".format(get_conditions(filters)),as_list=1)[0]
	else:
		return frappe.db.sql("""select sum(rental_payment),sum(late_fees),sum(receivables),
							sum(rental_payment+late_fees+receivables),
							sum(bank_transfer),sum(cash),sum(bank_card),
							sum(balance),sum(discount),sum(bonus) from `tabPayments History`""",as_list=1)[0]			


def get_data(filters):
	if filters:
		result = frappe.db.sql("""select payment_date,customer,rental_payment,
								late_fees,receivables,rental_payment+late_fees+receivables as total_payment_received,
								bank_transfer,cash,bank_card,
								balance,discount,bonus,concat(name,'') 
								from `tabPayments History` 
								{0}
								order by customer """.format(get_conditions(filters)),as_list=1)
		
		# blank_list = ["","","","","","","","","","",""]
		# result.append(blank_list)
		return result
	else:	
		result = frappe.db.sql("""select payment_date,customer,rental_payment,
								late_fees,receivables,rental_payment+late_fees+receivables as total_payment_received,
								bank_transfer,cash,bank_card,
								balance,discount,bonus,concat(name,'')
								from `tabPayments History` order by customer """,as_list=1)
		
		# blank_list = ["","","","","","","","","","",""]
		# result.append(blank_list)
		return result

def get_conditions(filters):
	cond = ''
	if filters.get('customer') and filters.get('from_date') and filters.get('to_date'):
		cond = "where customer = '{0}' and (payment_date BETWEEN '{1}' AND '{2}') ".format(filters.get('customer'),filters.get('from_date'),filters.get('to_date'))

	elif filters.get('customer') and filters.get('from_date'):
		cond = "where customer = '{0}' and payment_date >= '{1}'".format(filters.get('customer'),filters.get('from_date'))

	elif filters.get('customer') and filters.get('to_date'):
		cond = "where customer = '{0}' and payment_date < '{1}'".format(filters.get('customer'),filters.get('to_date'))

	elif filters.get('from_date') and filters.get('to_date'):
		cond = "where (payment_date BETWEEN '{0}' AND '{1}') ".format(filters.get('from_date'),filters.get('to_date'))

	elif filters.get('customer'):
		cond = "where customer = '{0}' ".format(filters.get("customer"))

	elif filters.get('from_date'):
		cond = "where payment_date >= '{0}'".format(filters.get('from_date'))

	elif filters.get('to_date'):
		cond = "where payment_date <= '{0}'".format(filters.get("to_date"))	
	return cond


def get_colums():
	columns = [("Payment Date") + ":Date:90"] + [("Customer") + ":Data:118"] + \
	[("Rental Payment") + ":Currency:110"] + [("Late Fees") + ":Currency:75"] + \
	[("Receivables") + ":Currency:85"] + [("Total Payment Received") + ":Currency:160"] + \
	[("Bank Transfer") + ":Currency:90"] + \
	[("Cash") + ":Currency:80"] + [("Bank Card") + ":Currency:90"] + \
	[("Balance") + ":Currency:90"] + [("Discount") + ":Currency:90"] + \
	[("Bonus") + ":Currency:90"] + [("Refund") + ":Data:80"]
	return columns
		
