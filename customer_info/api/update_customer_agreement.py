from __future__ import unicode_literals
import json
import frappe
from datetime import datetime
from frappe.utils import nowdate, nowtime
from datetime import datetime, timedelta,date
from frappe.utils import nowdate, getdate,add_months,add_days,get_last_day
from frappe.utils import date_diff,flt

'''
	1.For given customer it will updates late_fees, for each agreement.  
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

'''
	1. Get Open Agreement for given customer and iterate
	2. Calcualte late-fees for each payment. 
	3. Add it to total_due.
	4. Calculate amount_of_payment_left. 
	5. Save for each agreement.
 
'''
@frappe.whitelist()
def update_late_fees(customer):
	try:
		now_date = datetime.now().date()
		firstDay_of_month = date(now_date.year, now_date.month, 1)
		last_day_of_month = get_last_day(now_date)
		first_day_of_this_month = date(now_date.year, now_date.month, 1)

		customer_agreements = frappe.db.sql("""select name from `tabCustomer Agreement`
										where agreement_status = "Open" and late_fees_updated="No" and customer = '{0}'""".format(customer),as_list=1)
		for agreement in customer_agreements:
			total_late_fees = 0
			amount_of_payment_left = []
			agreement_doc =frappe.get_doc("Customer Agreement",agreement[0])
			total_due =0.0
			for row in agreement_doc.payments_record:	
				
				if row.check_box_of_submit == 0 and getdate(row.due_date) >= firstDay_of_month and getdate(row.due_date) <= now_date:
					if date_diff(now_date,row.due_date) > 3:
						no_of_late_days = date_diff(now_date,row.due_date) - 3
						row.late_fees_calculated = "{0:.2f}".format(float(no_of_late_days * agreement_doc.monthly_rental_payment * (agreement_doc.late_fees_rate/100)))
						total_late_fees = float(total_late_fees) + float(row.late_fees_calculated)
						if no_of_late_days:
							payment_amt = float(agreement_doc.monthly_rental_payment) + float(row.late_fee_for_payment)
							total_due = round((total_due + payment_amt),2)

				if (row.pre_select_uncheck == 0 and row.check_box_of_submit == 0 and getdate(row.due_date) < first_day_of_this_month):
					if date_diff(now_date,row.due_date) > 3:
						no_of_late_days = date_diff(now_date,row.due_date) - 3
						row.late_fees_calculated = "{0:.2f}".format(float(no_of_late_days * agreement_doc.monthly_rental_payment * (agreement_doc.late_fees_rate/100)))
						total_late_fees = float(total_late_fees) + float(row.late_fees_calculated)
						if no_of_late_days:
							payment_amt = float(agreement_doc.monthly_rental_payment) + float(row.late_fee_for_payment)
							total_due = round((total_due + payment_amt),2)
				
				if row.check_box_of_submit == 0:
					amount_of_payment_left.append(row.monthly_rental_amount)					

			agreement_doc.amount_of_payment_left = sum(amount_of_payment_left)
			agreement_doc.late_fees = total_late_fees
			agreement_doc.total_due = "{0:.2f}".format(round(total_due,2))
			agreement_doc.save(ignore_permissions = True)
			frappe.db.commit()
	except Exception,e:
		raise e