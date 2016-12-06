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
	data = get_data(filters)
	return columns, data

def get_data(filters):
	now_date = datetime.now().date()
	if filters:
		result = frappe.db.sql("""select 
								t1.due_date,
								t2.customer,
								t1.payment_id,
								t3.receivables,
								t1.monthly_rental_amount,
								CASE WHEN t1.due_date < '{0}' AND DATEDIFF('{0}',t1.due_date) > 3
								THEN format((DATEDIFF('{0}',t1.due_date) - 3) * t1.monthly_rental_amount * 0.02,2) ELSE 0 END AS late_fees,
								"a",
								replace(t1.payment_id,concat(t2.name,"-Payment "),'') as payment_id_number,
								replace(t2.name,"BK-",'') as agreement_number
								from `tabPayments Record`t1,`tabCustomer Agreement`t2,
								`tabCustomer`t3
								where t1.parent = t2.name and t3.name = t2.customer
									and t2.name in  (select name from `tabCustomer Agreement`
												where agreement_status = "Open")
									and t1.check_box_of_submit != 1
									{1}
									order by agreement_number,t1.due_date  """ .format(now_date,get_condtion(filters.get("from_date"),filters.get("to_date"))),as_list=1)

		total = ["","",""]
		receivables = 0
		monthly_rental_amount = 0
		total_due = 0
		late_fees = 0
		customer_list = []
		for l in result:
			late_fees += float(l[5])
			monthly_rental_amount += float(l[4])
			# total_due += (float(l[5]) + float(l[4]) + float(l[3]))
			# l[6] = "{0:.2f}".format(float(l[5]) + float(l[4]) + float(l[3]))
			if l[1] in customer_list:
				l[3] = 0
			else:
				customer_list.append(l[1])	
			total_due += (float(l[5]) + float(l[4]) + float(l[3]))
			l[6] = "{0:.2f}".format(float(l[5]) + float(l[4]) + float(l[3]))
			receivables += float(l[3])
			if float(l[3]) == 0: # for display purpose
				l[3] = ""

		total.append("{0:.2f}".format(receivables))		
		total.append("{0:.2f}".format(monthly_rental_amount))
		total.append("{0:.2f}".format(late_fees))
		total.append("{0:.2f}".format(total_due))
		result.append(total)
		return result
	else:
		return []	


def get_condtion(from_date,to_date):
	print from_date,to_date

	cond = ""
	if  from_date and to_date:
		cond = "and t1.due_date BETWEEN '{0}' AND '{1}' ".format(from_date,to_date)

	elif from_date:
		cond = "and t1.due_date >= '{0}' ".format(from_date)

	elif to_date:
		cond = "and t1.due_date < '{0}' ".format(to_date)

	return cond	


def get_colums():
	print "future_payments columns"
	columns = [("Due Date") + ":Date:100"] + [("Customer") + ":Link/Customer:100"] + \
			  [("Payment Id") + ":Data:170"] + \
			  [("Receivables") + ":Data:90"] + \
			  [("Rental Payment") + ":Data:100"] + [("Late Fees") + ":Data:80"] + \
			  [("Total Due") + ":Data:90"]	
	return columns