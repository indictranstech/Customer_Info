from __future__ import unicode_literals
import json
import frappe
from datetime import datetime
from frappe.utils import nowdate, nowtime
from datetime import datetime, timedelta,date
from frappe.utils import nowdate, getdate,add_months,add_days,get_last_day
from frappe.utils import date_diff,flt

# Add agreement status as draft throug API
@frappe.whitelist()
def create_agreement_status_draft(customer,agreement_no):
	cust_doc = frappe.get_doc("Customer",customer)
	if cust_doc and agreement_no:
		try:
			create_draft_for_customer_agreement(customer,agreement_no)
			return "%Agreement status draft are successfully added for customer {0}#".format(cust_doc.name)
		except Exception, e:
			raise e
	else:
		return "%Invalid Customer Or Agreement-No #"

# Create Draft For Customer Agreement 				
@frappe.whitelist()
def create_draft_for_customer_agreement(customer,agreement_no):
	cust_doc = frappe.get_doc("Customer",customer)
	agreement_doc=frappe.get_doc("Customer Agreement",agreement_no)
	if customer and agreement_no:
		agreement_doc.save()
		frappe.db.set_value("Customer Agreement",agreement_doc.name,"agreement_status","Draft")
		frappe.db.set_value("Customer Agreement",agreement_doc.name,"old_agreement_status","Draft")
		
