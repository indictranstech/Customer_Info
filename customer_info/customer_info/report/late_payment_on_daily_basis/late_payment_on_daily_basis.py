# Copyright (c) 2013, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import date_diff
from datetime import datetime, timedelta,date
from frappe.utils import flt, get_datetime, get_time, getdate

def execute(filters=None):
	columns, data = [], []
	columns = get_colums()
	data = get_data()
	return columns, data

def get_data():
	now_date = datetime.now().date()
	result = frappe.db.sql("""select t1.due_date, DATEDIFF('{0}',t1.due_date) as difference,
								t1.payment_id,t1.monthly_rental_amount,concat(t2.product," ",t2.product_category),
								concat(t3.first_name," ",t3.last_name) as customer,
								t3.company_phone_1,t3.bonus,
								CASE WHEN t1.due_date < '{0}' AND DATEDIFF('{0}',t1.due_date) > 3 
								THEN (DATEDIFF('{0}',t1.due_date) - 3) * t1.monthly_rental_amount * 0.02 ELSE 0 END AS late_fees,
								"a"																		
								from `tabPayments Record`t1,`tabCustomer Agreement`t2,
								`tabCustomer`t3		 
								where t1.parent = t2.name and t3.name = t2.customer 
								and t2.name in  (select name from `tabCustomer Agreement`
												where agreement_status = "Open") 
								and DATEDIFF('{0}',t1.due_date) >= 0
								and t1.check_box_of_submit != 1
								order by t1.due_date""" .format(now_date),as_list=1)
	for l in result:
		if float(l[8]):
			l[9] = l[8] + l[3]

	return result

def get_colums():
	columns = [("Due Date") + ":Date:80"] + [("Late Days") + ":Int:70"] + \
			  [("Payment Id") + ":Data:130"] + \
			  [("Rental Payment") + ":Float:100"] + [("Product") + ":Data:240"] + \
			  [("Customer") + ":Data:100"] + [("Phone") + ":Data:80"] + \
			  [("Bonus") + ":Float:90"] + [("Late Fees") + ":Float:80"] + \
			  [("Total Due") + ":Float:90"]	
	return columns