from __future__ import unicode_literals
import frappe
import datetime
import frappe.defaults
from frappe import _
from datetime import datetime,date
from frappe.utils import date_diff
from frappe.model.document import Document


@frappe.whitelist(allow_guest = True)
def product_status_change(self,method):
	now = datetime.now()
	date = now.strftime("%d-%m-%Y")
	status = ""
	vat = ""
	monthly_rental = ""
	agreement = ""
	sac = ""	
	if self.old_status != self.merchandise_status:
		status = " Product Status Changed from {0} To {1} ON - '{2}' ".format(self.old_status,self.merchandise_status,date)
		self.old_status = self.merchandise_status

	if self.old_agreement_period != self.period:
		agreement  = "Agreement Period Month Changed from {0} To {1} ON - '{2}'".format(self.old_agreement_period,self.period,date)
		self.old_agreement_period = self.period

	if self.old_purchase_price_with_vat != self.purchase_price_with_vat:	
		vat ="Purchase Price with vat Changed from {0} To {1} ON - {2} ".format(self.old_purchase_price_with_vat,self.purchase_price_with_vat,date)
		self.old_purchase_price_with_vat = self.purchase_price_with_vat

	if self.old_90d_sac_price != self.s90d_sac_price:
		sac = "90d SAC Price Changed from {0} To {1} ON - {2} ".format(self.old_90d_sac_price,self.s90d_sac_price,date)
		self.old_90d_sac_price = self.s90d_sac_price

	if self.old_monthly_rental_payment != self.monthly_rental_payment:
		monthly_rental = "Monthly Rental Payment Changed from {0} To {1} ON - {2} ".format(self.old_monthly_rental_payment,self.monthly_rental_payment,date)
		self.old_monthly_rental_payment = self.monthly_rental_payment

	if status or agreement or vat or sac or monthly_rental:
		comment = """<p>{0}</p> <p>{1}</p> <p>{2}</p> <p>{3}</p> <p>{4}</p>""".format(status,agreement,vat,sac,monthly_rental)
		#self.add_comment("Comment", comment)					


@frappe.whitelist(allow_guest = True)
def add_comment_for_customer_creation(self,method):
	comment = """Customer {0} is made on the {1}  """.format(self.name,datetime.now().date())
	self.add_comment("Comment",comment)
	if self.bonus and self.assign_manual_bonus and self.bonus == self.assign_manual_bonus:
		associate = frappe.session.user	if frappe.session.user == "Administrator" else frappe.db.get_value("User",{"email":frappe.session.user},"username")	
		comment = "{0} - [{1}] Bonus Modified From 0 To {2}".format(datetime.now().date(),associate,self.bonus)
		self.add_comment("Comment",comment)
		frappe.db.set_value("Customer", self.name, "summary_of_notes", comment)


@frappe.whitelist(allow_guest = True)
def add_comment_for_change_receivables(self,method):
	if self.company_code or self.prersonal_code:
		validate_code(self)
	if (self.old_receivables == 0 or self.old_receivables) and self.receivables and self.old_receivables != self.receivables:
		#comment = """Receivables change from  {0} to {1} on {2} """.format(self.old_receivables,self.receivables,datetime.now().date())
		associate = frappe.session.user	if frappe.session.user == "Administrator" else frappe.db.get_value("User",{"email":frappe.session.user},"username")	
		comment = "{0} - [{1}] Receivables changed from {2} to {3}".format(datetime.now().date(),associate,self.old_receivables,self.receivables)
		self.add_comment("Comment",comment)
		self.old_receivables = self.receivables
		summary_of_notes = self.summary_of_notes+"\n"+comment if self.summary_of_notes else comment
		self.summary_of_notes = summary_of_notes

def validate_code(self):
	if self.customer_type == "Individual":
		check_code(self.prersonal_code,"Personal Code",11)
	elif self.customer_type == "Company":
		check_code(self.company_code,"Company Code",7)


def check_code(code,code_label,digits):			
	msg = "Company code should consist of 7 or 9 digits" if code_label == "Company Code" else "Enter Digits From [0-"+str(digits)+"] Only"
	try:
		val = int(code)
		if len(code) < digits and code_label == "Personal Code":
			frappe.throw(code_label+" Should Be Of "+str(digits)+" Digits")  
		elif len(code) > digits and code_label == "Personal Code":
			frappe.throw(code_label+" Length Not Greater Than "+str(digits)+" Digits")	
		
		elif (len(code) < 7 or len(code) == 8) and code_label == "Company Code":
			frappe.throw(code_label+" Should Be Of 7 or 9 Digits")  
		elif len(code) > 9 and code_label == "Company Code":
			frappe.throw(code_label+" Length Not Greater Than 9 Digits")

	except ValueError:
   		frappe.throw(msg)
