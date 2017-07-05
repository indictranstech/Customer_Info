from __future__ import unicode_literals
import json
import frappe
from datetime import datetime
from frappe.utils import nowdate, nowtime
from customer_info.customer_info.doctype.customer_agreement.customer_agreement import payments_done_by_api


"""
Addding receivables to customer for payment process
"""
@frappe.whitelist()
def add_receivables(customer,receivables):
	cust_doc = frappe.get_doc("Customer",customer)
	if cust_doc and float(receivables):
		try:
			cust_doc.receivables += float(receivables)
			cust_doc.save(ignore_permissions=True)
			frappe.db.commit()
			return "%Receivables are successfully added for customer {0}#".format(cust_doc.name)
		except Exception, e:
			raise e
	else:
			return "%Invalid Customer#"

"""
Addding flagged receivables to customer for payment process
"""
@frappe.whitelist()
def add_flagged_receivables(customer,flagged_receivables):
	cust_doc = frappe.get_doc("Customer",customer)
	if cust_doc and float(flagged_receivables):
		try:
			cust_doc.flagged_receivables += float(flagged_receivables)
			cust_doc.save(ignore_permissions=True)
			frappe.db.commit()
			#payments_done_by_api(customer)
			return "%Flagged Receivables are successfully added for customer {0}#".format(cust_doc.name)
		except Exception, e:
			raise e
	else:
			return "%Invalid Customer#"