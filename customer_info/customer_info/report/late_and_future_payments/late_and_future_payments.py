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
	if filters:
		now_date = datetime.now().date()
		result = frappe.db.sql("""select t1.due_date, 
									CASE WHEN t1.due_date < '{1}' AND DATEDIFF('{1}',t1.due_date) > 0
									THEN DATEDIFF('{1}',t1.due_date) ELSE 0 END AS difference,
									t1.payment_id,
									t1.monthly_rental_amount,
									concat(t2.product," ",t2.product_category),
									t3.first_name AS customer,
									t3.last_name AS sur_name,
									t2.debtor as debtor,
									REPLACE(t3.company_phone_1,'+',''),
									t3.bonus,
									CASE WHEN t1.due_date < '{1}' AND DATEDIFF('{1}',t1.due_date) > 3 
									THEN (DATEDIFF('{1}',t1.due_date) - 3) * t1.monthly_rental_amount * (t2.late_fees_rate/100) ELSE 0 END AS late_fees,
									"a",
									CASE WHEN t2.contact_result = "WBI" AND t1.due_date < t2.suspension_date
									THEN concat(t2.contact_result," ",t2.suspension_date," ",format(t2.amount_of_contact_result,2))
									WHEN t2.contact_result = "Sent SMS/Email" AND t1.due_date < t2.suspension_date AND t1.due_date < '{1}'
									THEN concat(t2.contact_result," ",t2.suspension_date) ELSE " " END AS contact_result,
									t3.company_email_id_1																		
									from `tabPayments Record`t1,`tabCustomer Agreement`t2, `tabCustomer`t3		 
									where t1.parent = t2.name 
										and t3.name = t2.customer
										and t2.agreement_status = "Open"
										and DATEDIFF('{0}',t1.due_date) >= 0
										and CASE WHEN t2.suspension_date THEN t2.suspension_date <= '{0}'
											ELSE 1=1 END
										and t1.check_box_of_submit != 1
											order by t1.due_date""" .format(filters.get('date'),now_date),as_list=1)
		# for l in result:
		# 	if float(l[9]):
		# 		total_due = l[9] + l[3]
		# 		l[10] = "{0:.2f}".format(total_due)
		# 	else:
		# 		total_due = 0.00
		# 		l[10] = "{0:.2f}".format(total_due)
		# 	l[9] = "{0:.2f}".format(float(l[9]))
		# 	l[3] = "{0:.2f}".format(float(l[3]))
		# 	l[8] = "{0:.2f}".format(float(l[8]))
		for l in result:
			if float(l[10]):
				total_due = l[10] + l[3]
				l[11] = "{0:.2f}".format(total_due)
			else:
				total_due = 0.00
				l[11] = "{0:.2f}".format(total_due)
			l[10] = "{0:.2f}".format(float(l[10]))
			l[3] = "{0:.2f}".format(float(l[3]))
			l[9] = "{0:.2f}".format(float(l[9]))

		return result
	else:
		return []	

def get_colums():
	columns = [("Due Date") + ":Date:80"] + [("Late Days") + ":Int:70"] + \
			  [("Payment Id") + ":Data:150"] + \
			  [("Rental Payment") + ":Data:100"] + [("Product") + ":Data:200"] + \
			  [("Name") + ":Data:80"] + [("Surname") + ":Data:80"] + \
			  [("Debtor") + ":Data:80"] + \
			  [("Phone") + ":Data:80"] + \
			  [("Customer level bonus") + ":Data:90"] + [("Late Fees") + ":Data:80"] + \
			  [("Total Due") + ":Data:90"] + [("Contact Result") + ":Data:140"] + [("Email") + ":Data:140"]	
	return columns