from __future__ import unicode_literals
import json
import frappe
from datetime import datetime
from frappe.utils import nowdate, nowtime
from datetime import datetime, timedelta,date
from frappe.utils import nowdate, getdate,add_months,add_days,get_last_day
from frappe.utils import date_diff,flt

"""
update customer agreement
"""
@frappe.whitelist()
def update_customer_agreement(customer):
	cust_doc = frappe.get_doc("Customer",customer)
	if cust_doc:
		try:
			# cust_doc.save(ignore_permissions=True)
			# frappe.db.commit()
			update_late_by_api(customer)
			return "Agreement is successfully updated"
		except Exception, e:
			raise e
	else:
			return "%Invalid Customer#"



@frappe.whitelist()
def update_late_by_api(customer):
	now_date = datetime.now().date()
	firstDay_of_month = date(now_date.year, now_date.month, 1)
	last_day_of_month = get_last_day(now_date)

	# Step - 1 : Get All  Customer Agreement
	customer_agreements = frappe.db.sql("""select name from `tabCustomer Agreement`
										where agreement_status = "Open" and late_fees_updated="No" and customer = '{0}'""".format(customer),as_list=1)

	# Step - 2 : Globally declare all payment list

	payments = {}
	payments_sorted = []
	customer_bonus = []
	payments_detalis_list = []
	payment_ids_list = []
	# print " 1 **********",payment_ids_list
	monthly_rental_amount = []
	merchandise_status = ""
	add_bonus_of_one_eur = []
	add_bonus_of_two_eur = []
	late_payments = []
	late_fees = []
	total_late_fees=0
	firstDay_this_month = date(now_date.year, now_date.month, 1)
	args = {'values':{}}


	# # Step - 3 : Find out pending payment's from all customer open agreements.
	for agreement in customer_agreements:
		total_late_fees=0
		agreement_doc =frappe.get_doc("Customer Agreement",agreement[0])
		for row in agreement_doc.payments_record:
			print "___________",row
			print "firstDay_of_month",firstDay_of_month
			if row.check_box_of_submit == 0 and getdate(row.due_date) >= firstDay_of_month and getdate(row.due_date) <= now_date:
				print "1 scinirio__________-"
				if date_diff(now_date,row.due_date) > 3:
					no_of_late_days = date_diff(now_date,row.due_date) - 3
					late_payments.append(row.monthly_rental_amount)
					row.late_fees_payment = "{0:.2f}".format(float(no_of_late_days * agreement_doc.monthly_rental_payment * (agreement_doc.late_fees_rate/100)))
					total_late_fees=float(total_late_fees)+float(row.late_fees_payment)
			if (row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and getdate(row.due_date) < firstDay_this_month):
				print "ABBN ",row.due_date,now_date
				print "______________"
				if date_diff(now_date,row.due_date) > 3:
					no_of_late_days = date_diff(now_date,row.due_date) - 3
					late_payments.append(row.monthly_rental_amount)
					row.late_fees_payment = "{0:.2f}".format(float(no_of_late_days * agreement_doc.monthly_rental_payment * (agreement_doc.late_fees_rate/100)))
					print "___row._",row.late_fees_payment
					total_late_fees=float(total_late_fees)+float(row.late_fees_payment)
					print "total_late_fees",total_late_fees
		agreement_doc.late_fees=total_late_fees
		agreement_doc.save(ignore_permissions = True)
	return "Agreement is successfully updated"
				


	
		 					
	






