from __future__ import unicode_literals
import frappe
import datetime
import frappe.defaults
from frappe.utils import date_diff
from frappe.model.document import Document


@frappe.whitelist(allow_guest = True)
def purchase_date_comment(self,method):
	if self.old_status != self.merchandise_status:
		now = datetime.datetime.now()
		date = now.strftime("%d-%m-%Y")	
		comment = " Product Status Changed from '{0}' To '{1}' ON - '{2}' ".format(self.old_status,self.merchandise_status,date)
		self.add_comment("Comment",comment)
		self.old_status = self.merchandise_status