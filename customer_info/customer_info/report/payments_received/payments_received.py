# Copyright (c) 2013, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	columns = get_colums()
	data = get_data(filters)
	static_list = ["","Totals"]
	static_list.extend(get_totals(filters))
	data.append(static_list)
	return columns, data

def get_totals(filters):
	if filters:
		return frappe.db.sql("""select sum(rental_payment),sum(late_fees),sum(receivables),
							sum(rental_payment+late_fees+receivables),
							sum(bank_transfer),sum(cash),sum(bank_card),
							sum(balance),sum(discount) from `tabPayments History`
							where customer = '{0}'""".format(filters.get('customer')),as_list=1)[0]
	else:
		return frappe.db.sql("""select sum(rental_payment),sum(late_fees),sum(receivables),
							sum(rental_payment+late_fees+receivables),
							sum(bank_transfer),sum(cash),sum(bank_card),
							sum(balance),sum(discount) from `tabPayments History`""",as_list=1)[0]			


def get_data(filters):
	if filters:
		result = frappe.db.sql("""select payment_date,customer,rental_payment,
								late_fees,receivables,rental_payment+late_fees+receivables as total_payment_received,
								bank_transfer,cash,bank_card,
								balance,discount 
								from `tabPayments History` where customer = '{0}' order by customer """.format(filters.get('customer')),as_list=1)
		
		blank_list = ["","","","","","","","","","",""]
		result.append(blank_list)
		return result
	else:	
		result = frappe.db.sql("""select payment_date,customer,rental_payment,
								late_fees,receivables,rental_payment+late_fees+receivables as total_payment_received,
								bank_transfer,cash,bank_card,
								balance,discount 
								from `tabPayments History` order by customer """,as_list=1)
		
		blank_list = ["","","","","","","","","","",""]
		result.append(blank_list)
		return result

def get_colums():
	columns = [("Payment Date") + ":Date:90"] + [("Customer") + ":Link/Customer:150"] + \
	[("Rental Payment") + ":Currency:120"] + [("Late Fees") + ":Currency:120"] + \
	[("Receivables") + ":Currency:120"] + [("Total Payment Received") + ":Currency:120"] + \
	[("Bank Transfer") + ":Currency:120"] + \
	[("Cash") + ":Currency:120"] + [("Bank Card") + ":Currency:120"] + \
	[("Balance") + ":Currency:120"] + [("Discount") + ":Currency:120"]
	return columns

