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
			update_customer_agreement(customer)
			return "%customer agreement are successfully updated {0}#".format(cust_doc.name)
		except Exception, e:
			raise e
	else:
			return "%Invalid Customer#"



@frappe.whitelist()
def update_customer_agreement(customer):
	now_date = datetime.now().date()
	firstDay_of_month = date(now_date.year, now_date.month, 1)
	last_day_of_month = get_last_day(now_date)

	# Step - 1 : Get All  Customer Agreement
	customer_agreements = frappe.db.sql("""select name from `tabCustomer Agreement`
										where agreement_status = "Open" and customer = '{0}'""".format(customer),as_list=1)
	
	print "________________customer_agreements____________",customer_agreements
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
	args = {'values':{}}


	# # Step - 3 : Find out pending payment's from all customer open agreements.
	for agreement in customer_agreements:
		print"__________________________________",agreement
		agreement_doc =frappe.get_doc("Customer Agreement",agreement[0])
		for row in agreement_doc.payments_record:
			if row.check_box_of_submit == 0:
				payments[row.payment_id] = row.due_date

	# Step - 4 : Sort Pending Payments
	for key, value in sorted(payments.iteritems(), key=lambda (k,v): (v,k)):
		payments_sorted.append(key)

	# Step - 6 : Process Pending Payments
	for payment in payments_sorted:
		print "______________________________________--",payment

	# Step -6(1) - Validate Agreement
		if frappe.db.exists("Customer Agreement", payment.split('-P')[0]):				
			customer_agreement = frappe.get_doc("Customer Agreement",payment.split('-P')[0])
			# Step -6(2) - Validate Payment
			for row in customer_agreement.payments_record:
		 		if row.payment_id == payment:											
		 			merchandise_status += str(customer_agreement.name)+"/"+str(customer_agreement.merchandise_status)+"/"+str(customer_agreement.agreement_closing_suspending_reason)+","

		 			if row.check_box_of_submit == 0 and row.payment_id == payment:	
		 				# step late_payments
		 				if (getdate(row.due_date) < firstDay_of_month or getdate(row.due_date) < now_date):
		 					if date_diff(now_date,row.due_date) > 3:
		 						no_of_late_days = date_diff(row.payment_date,row.due_date) - 3
		 						late_payments.append(row.monthly_rental_amount)
		 						if customer_agreement.late_fees_updated != "Yes":
		 							row.late_fees_payment = "{0:.2f}".format(float(no_of_late_days * customer_agreement.monthly_rental_payment * (customer_agreement.late_fees_rate/100)))
									print "+++++++++++++++++++++++++++late fess",row.late_fees_payment
		 						row.save(ignore_permissions = True)
		 						total_late_fees=float(total_late_fees)+float(row.late_fees_payment)

	# print "____________---",total_late_fees
				customer_agreement.late_fees=total_late_fees
				customer_agreement.save(ignore_permissions = True)
				return "customer agreement are successfully updated"
				
 

		 					
	





