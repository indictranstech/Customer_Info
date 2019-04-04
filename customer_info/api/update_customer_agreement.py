from __future__ import unicode_literals
import json
import frappe
from datetime import datetime
from frappe.utils import nowdate, nowtime
from datetime import datetime, timedelta,date
from frappe.utils import nowdate, getdate,add_months,add_days,get_last_day
from frappe.utils import date_diff,flt

'''
	1.For given customer it updates late fees for each agreement.  
'''
@frappe.whitelist()
def update_customer_agreement(customer):
	cust_doc = frappe.get_doc("Customer",customer)
	if cust_doc:
		try:
			update_late_fees(customer)
			return "% Agreement is successfully updated #"
		except Exception, e:
			raise e
	else:
		return "% Invalid Customer#"

@frappe.whitelist()
def update_late_fees(customer):
	try:
		now_date = datetime.now().date()
		firstDay_of_month = date(now_date.year, now_date.month, 1)
		last_day_of_month = get_last_day(now_date)
		first_day_of_this_month = date(now_date.year, now_date.month, 1)

		#1.Get All Open Agreement of Customer

		customer_agreements = frappe.db.sql("""select name from `tabCustomer Agreement`
										where agreement_status = "Open" and late_fees_updated="No" and customer = '{0}'""".format(customer),as_list=1)
		#1.Iterate open agreements.
		for agreement in customer_agreements:
			total_late_fees = 0
			agreement_doc =frappe.get_doc("Customer Agreement",agreement[0])

			for row in agreement_doc.payments_record:	
				
				if row.check_box_of_submit == 0 and getdate(row.due_date) >= firstDay_of_month and getdate(row.due_date) <= now_date:
					if date_diff(now_date,row.due_date) > 3:
						no_of_late_days = date_diff(now_date,row.due_date) - 3
						row.late_fee_for_payment = "{0:.2f}".format(float(no_of_late_days * agreement_doc.monthly_rental_payment * (agreement_doc.late_fees_rate/100)))
						total_late_fees = float(total_late_fees) + float(row.late_fee_for_payment)
				
				if (row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and getdate(row.due_date) < first_day_of_this_month):
					if date_diff(now_date,row.due_date) > 3:
						no_of_late_days = date_diff(now_date,row.due_date) - 3
						row.late_fee_for_payment = "{0:.2f}".format(float(no_of_late_days * agreement_doc.monthly_rental_payment * (agreement_doc.late_fees_rate/100)))
						total_late_fees = float(total_late_fees) + float(row.late_fee_for_payment)
			set_values_in_agreement(agreement_doc)
			agreement_doc.late_fees = total_late_fees
			agreement_doc.save(ignore_permissions = True)

	except Exception,e:
		raise e

@frappe.whitelist()
def set_values_in_agreement(customer_agreement):
	payment_made = []
	
	for row in customer_agreement.payments_record:
		if row.check_box_of_submit == 1:
			payment_made.append(row.monthly_rental_amount)				
	
	for index,row in enumerate(customer_agreement.payments_record):
		if row.check_box_of_submit == 0 and row.idx > 1 and row.idx < len(customer_agreement.payments_record):
			customer_agreement.current_due_date = row.due_date
			customer_agreement.next_due_date = customer_agreement.payments_record[index+1].due_date#get_next_due_date(row.due_date,1)
			break
		if row.check_box_of_submit == 0 and row.idx == 1:
			customer_agreement.current_due_date = customer_agreement.date
			customer_agreement.next_due_date = customer_agreement.payments_record[index+1].due_date#get_next_due_date(customer_agreement.due_date_of_next_month,0)
			break
		
		if row.check_box_of_submit == 0 and row.idx == len(customer_agreement.payments_record):
			customer_agreement.current_due_date = row.due_date
			customer_agreement.next_due_date = row.due_date
			break
	payment_made = map(float,payment_made)

	if customer_agreement.payments_record and customer_agreement.date:
		customer_agreement.payments_made = sum(payment_made)
		customer_agreement.number_of_payments = 0
		customer_agreement.discount_updated = "No"
		customer_agreement.late_fees_updated = "No"
		customer_agreement.payments_left = len(customer_agreement.payments_record) - len(payment_made)
		
	customer_agreement.balance = (len(customer_agreement.payments_record) - len(payment_made)) * customer_agreement.monthly_rental_payment
	customer_agreement.save(ignore_permissions=True)
