# Copyright (c) 2013, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from numpy import irr
from datetime import datetime, timedelta,date
from frappe.utils import flt, get_datetime, get_time, getdate
from customer_info.customer_info.report.customer_agreements_report.financial import xirr

def execute(filters=None):
	columns, data = [], []
	columns = get_colums()
	data = get_data()
	return columns, data

def get_data():
	now_date = datetime.now().date()
	result = frappe.db.sql("""select
				cus.first_name,
				cus.last_name,
				cus.prersonal_code,
				ca.name,
				ca.agreement_status,
				ca.date,
				ca.agreement_close_date,
				ca.product_category,
				item.brand,
				format(ca.monthly_rental_payment,2),
				format(ca.agreement_period,2),
				format(ca.s90d_sac_price,2),
				item.purchase_price_with_vat,
				format((ca.s90d_sac_price - item.purchase_price_with_vat)/item.purchase_price_with_vat * 100,2),
				format((ca.monthly_rental_payment * ca.agreement_period -item.purchase_price_with_vat)/item.purchase_price_with_vat * 100,2),
				format(ca.monthly_rental_payment * ca.agreement_period,2),
				format(ca.payments_made,2),
				case when ca.agreement_status = "Closed" then ca.agreement_close_date
				when ca.agreement_status = "Suspended" then ca.suspended_from
				else "-" end as agreement_closing_suspension_date,
				case when ca.agreement_closing_suspending_reason = "Early buy offer" then
				concat(ca.early_buy_discount_percentage,"% ",ca.agreement_closing_suspending_reason)
				else ca.agreement_closing_suspending_reason end as agreement_closing_suspension_reason,

				case when ca.agreement_close_date then period_diff(date_format(ca.agreement_close_date, "%Y%m"), date_format(ca.date, "%Y%m")) else period_diff(date_format(now(), "%Y%m"), date_format(ca.date, "%Y%m")) end as active_agreement_months,

				format(ca.payments_made - item.purchase_price_with_vat,2),
				format((ca.payments_made - item.purchase_price_with_vat)/item.purchase_price_with_vat * 100,2),
				format(ca.payments_left,2) as remaining_months_till_the_end_of_agreement,
				ca.campaign_discount_code,
				ca.irr,
				ca.xiir
				from `tabCustomer Agreement` ca ,`tabCustomer` cus,`tabItem` item
				where ca.customer = cus.name and ca.product = item.name""",as_list=1,debug=1)

	return result
	
	"""
	for row in result:
	
		#  IIR Calculations 
	
		print row[3]
		if frappe.get_doc("Customer Agreement",row[3]).agreement_status == "Open":
			if row[12] and float(row[12])>0:
				submitted_payments_rental_amount = [-float(row[12])]
				submitted_payments_rental_amount.extend([payment.get("monthly_rental_amount") for payment in frappe.get_doc("Customer Agreement",row[24]).payments_record if payment.get("check_box_of_submit") == 1])
				submitted_payments_rental_amount.extend([payment.get("monthly_rental_amount") for payment in frappe.get_doc("Customer Agreement",row[24]).payments_record if payment.get("check_box_of_submit") == 0 and getdate(payment.get("due_date")) > getdate(now_date)])
				row[24] = round(irr(submitted_payments_rental_amount),5) if len(submitted_payments_rental_amount) > 1 else ""
				print row[24]	
		elif frappe.get_doc("Customer Agreement",row[24]).agreement_status == "Closed":
			if row[12] and float(row[12]) > 0 and row[18] =="Contract Term is over":
				submitted_payments_rental_amount = [-float(row[12])]
				submitted_payments_rental_amount.extend([payment.get("monthly_rental_amount") for payment in frappe.get_doc("Customer Agreement",row[24]).payments_record if payment.get("check_box_of_submit") == 1])
				row[24] = round(irr(submitted_payments_rental_amount),5) if len(submitted_payments_rental_amount) > 1 else ""
			
			if row[12] and float(row[12]) > 0 and row[18] =="90d SAC":
				payments_rental_amount =[]
				submitted_payments_rental_amount = [-float(row[12])]
				customer_agreement_doc = frappe.get_doc("Customer Agreement",row[3])
				payments_record_doc = customer_agreement_doc.payments_record
				if payments_record_doc:
					for payment_r in payments_record_doc:
						payment_type = frappe.db.get_value("Payments History",{"name":payment_r.payment_history},"payment_type")
						payoff_cond = frappe.db.get_value("Payments History",{"name":payment_r.payment_history},"payoff_cond")
						if payment_type =="Normal Payment" and payoff_cond =="Rental Payment" and payment_r.check_box_of_submit ==1:
							payments_rental_amount.append(payment_r.monthly_rental_amount)
					payments_rental_amount.append(customer_agreement_doc.s90d_sac_price)
					submitted_payments_rental_amount.extend(payments_rental_amount)				
					row[24] = round(irr(submitted_payments_rental_amount),5) if len(submitted_payments_rental_amount) > 1 else ""

			if row[12] and float(row[12]) > 0 and row[18] =="30% Early buy offer":
				payments_rental_amount =[]
				submitted_payments_rental_amount = [-float(row[12])]
				customer_agreement_doc = frappe.get_doc("Customer Agreement",row[3])
				payments_record_doc = customer_agreement_doc.payments_record
				if payments_record_doc:
					payment_history =''
					for payment_r in payments_record_doc:
						payment_type = frappe.db.get_value("Payments History",{"name":payment_r.payment_history},"payment_type")
						payoff_cond = frappe.db.get_value("Payments History",{"name":payment_r.payment_history},"payoff_cond")
						if payment_type =="Normal Payment" and payoff_cond =="Rental Payment" and payment_r.check_box_of_submit ==1:
							payments_rental_amount.append(payment_r.monthly_rental_amount)
						if payment_type =="Payoff Payment" and payoff_cond =="Early buy-30" and payment_r.check_box_of_submit ==1:
							payment_history = payment_r.payment_history
					Total_payoff_amount = frappe.db.get_value("Payments History",{"name":payment_history},"total_payment_received")
					payments_rental_amount.append(float(Total_payoff_amount)) if Total_payoff_amount else ""
					submitted_payments_rental_amount.extend(payments_rental_amount)
					row[24] = round(irr(submitted_payments_rental_amount),5) if len(submitted_payments_rental_amount) > 1 else ""
			else:
				row[24] = ""
		else:
			row[24] = ""
		
		#  XIIR Calculations 
	
		if frappe.get_doc("Customer Agreement",row[3]).agreement_status == "Open":
			if row[12] and float(row[12])>0:
				submitted_payments_rental_amount = []
				print "Row[3]",row[3]
				agreement_doc = frappe.get_doc("Customer Agreement",row[3])
				payments = agreement_doc.payments_record
				if payments:
					purchase_date = frappe.db.get_value("Item",{"name":agreement_doc.product},"purchase_date")
					submitted_payments_rental_amount.append((purchase_date,-float(row[12])))
					print "\nsubmitted_payments_rental_amount",submitted_payments_rental_amount
					for payment_r in payments:
						if payment_r.check_box_of_submit == 1:
							submitted_payments_rental_amount.append((payment_r.payment_date,payment_r.monthly_rental_amount))
						if payment_r.check_box_of_submit == 0 and payment_r.due_date > getdate(now_date):
							submitted_payments_rental_amount.append((payment_r.due_date,payment_r.monthly_rental_amount))	
					print "Row[3]",row[3]
					print "\nsubmitted_payments_rental_amount",submitted_payments_rental_amount
					try:
						row[25] = xirr(submitted_payments_rental_amount,0.1)
						print "row[25]",row[25]
					except Exception,e:
						row[25] = ""
 		
 		elif frappe.get_doc("Customer Agreement",row[3]).agreement_status == "Closed":
 			if row[12] and float(row[12]) > 0 and row[18] =="Contract Term is over":
 				submitted_payments_rental_amount = []
				agreement_doc = frappe.get_doc("Customer Agreement",row[3])
				payments = agreement_doc.payments_record
				if payments:
					purchase_date = frappe.db.get_value("Item",{"name":agreement_doc.product},"purchase_date")
					submitted_payments_rental_amount.append((purchase_date,-float(row[12])))
					for payment_r in payments:
						if payment_r.check_box_of_submit == 1:
							submitted_payments_rental_amount.append((payment_r.payment_date,payment_r.monthly_rental_amount))
					try:
						row[25] = xirr(submitted_payments_rental_amount,0.1)
					except Exception,e:
						row[25] = ""
 			
 			if row[12] and float(row[12]) > 0 and row[18] =="90d SAC":
 				submitted_payments_rental_amount = []
 				pay_off_date = ""
				agreement_doc = frappe.get_doc("Customer Agreement",row[3])
				payments = agreement_doc.payments_record
 				if payments:
 					purchase_date = frappe.db.get_value("Item",{"name":agreement_doc.product},"purchase_date")
					submitted_payments_rental_amount.append((purchase_date,-float(row[12])))
 					for payment_r in payments_record_doc:
						payment_type = frappe.db.get_value("Payments History",{"name":payment_r.payment_history},"payment_type")
						payoff_cond = frappe.db.get_value("Payments History",{"name":payment_r.payment_history},"payoff_cond")
						if payment_type == "Normal Payment" and payoff_cond == "Rental Payment" and payment_r.check_box_of_submit ==1:
							submitted_payments_rental_amount.append((payment_r.payment_date,payment_r.monthly_rental_amount))
						if payment_type == "Payoff Payment" and  payoff_cond == "90d SAC":
							pay_off_date = payment_r.payment_date
					submitted_payments_rental_amount.append((pay_off_date,agreement_doc.s90d_sac_price))
				   	try:
						row[25] = xirr(submitted_payments_rental_amount,0.1)
					except Exception,e:
						row[25] = ""

 			if row[12] and float(row[12]) > 0 and row[18] =="30% Early buy offer":
 				submitted_payments_rental_amount = []
 				payment_history = ""
				Total_payoff_amount =""
				payment_date =''
				agreement_doc = frappe.get_doc("Customer Agreement",row[3])
				payments = agreement_doc.payments_record
 				if payments:
 					purchase_date = frappe.db.get_value("Item",{"name":agreement_doc.product},"purchase_date")
					submitted_payments_rental_amount.append((purchase_date,-float(row[12])))
 					for payment_r in payments_record_doc:
						payment_type = frappe.db.get_value("Payments History",{"name":payment_r.payment_history},"payment_type")
						payoff_cond = frappe.db.get_value("Payments History",{"name":payment_r.payment_history},"payoff_cond")
						if payment_type == "Normal Payment" and payoff_cond == "Rental Payment" and payment_r.check_box_of_submit ==1:
							submitted_payments_rental_amount.append((payment_r.payment_date,payment_r.monthly_rental_amount))
 						if payment_type =="Payoff Payment" and payoff_cond =="Early buy-30" and payment_r.check_box_of_submit ==1:
							payment_history = payment_r.payment_history
					Total_payoff_amount = frappe.db.get_value("Payments History",{"name":payment_history},"total_payment_received")
					payment_date = frappe.db.get_value("Payments History",{"name":payment_history},"payment_date")
					submitted_payments_rental_amount.append((payment_date,Total_payoff_amount))
					try:
						row[25] = xirr(submitted_payments_rental_amount,0.1)
					except Exception,e:
							row[25] = ""
			else:
				row[25] = ""
 		else:
			row[25] = ""
				
	return result
"""

def get_colums():
	columns = [
				("Customer Name") + ":Data:100",
				("Surname") + ":Data:100",
				("Personal Code") + ":Data:100",
				("Agreement Number") + ":Link/Customer Agreement:150",
				("Agreement Status") + ":Data:100",
				("Agreement Start Date") + ":Date:100",
				("Agreement Close Date") + ":Date:100",
				("Product category") + ":Data:100",
				("Product model") + ":Data:100",
				("Rental Payment") + ":Data:100",
				("Agreement Period") + ":Data:100",
				("90d SAC Price") + ":Data:100",
				("Purchase price") + ":Data:100",
				("90d SAC profit %") + ":Data:100",
				("Planned agreement profit %") + ":Data:100",
				("Planned agreement incomes") + ":Data:100",
				("Real agreement incomes") + ":Data:100",
				("Agreement closing/suspension date") + ":Date:100",
				("Agreement closing suspension reason") + ":Data:100",
				("Active agreement months") + ":Data:100",
				("Real agreement profit (EUR)") + ":Data:100",
				("Real agreement profit %") + ":Data:100",
				("Remaining months till the end of agreement") + ":Data:100",
				("Campaign discount code") + ":Link/Campaign Discount Code:150",
				("IRR") + ":Data:100",
				("XIRR")+":Data:150",
			]
	return columns
