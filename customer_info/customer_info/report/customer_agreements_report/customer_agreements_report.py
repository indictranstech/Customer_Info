# Copyright (c) 2013, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
# from numpy import irr
from datetime import datetime, timedelta,date
from frappe.utils import flt, get_datetime, get_time, getdate
# from customer_info.customer_info.report.customer_agreements_report.financial import xirr

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
				item.serial_number,
				format(ca.monthly_rental_payment,2),
				format(ca.agreement_period,2),
				format(ca.s90d_sac_price,2),
				item.wholesale_price,
				item.transportation_costs_incoming,
				item.transportation_costs_outgoing,
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

				case when ca.agreement_close_date then ceil((DATEDIFF(ca.agreement_close_date,ca.date)/30)) else ceil(DATEDIFF(CURDATE(),ca.date)/30) end as active_agreement_months,

				format(ca.payments_made - item.purchase_price_with_vat,2),
				format((ca.payments_made - item.purchase_price_with_vat)/item.purchase_price_with_vat * 100,2),
				format(ca.payments_left,2) as remaining_months_till_the_end_of_agreement,
				ca.campaign_discount_code,
				ca.irr,
				ca.xirr
				from `tabCustomer Agreement` ca ,`tabCustomer` cus,`tabItem` item
				where ca.customer = cus.name and ca.product = item.name""",as_list=1)


	for row in result:
		if row[26] and row[26] != "Wholesale price is not set":
			if row[26] != "" or row[27]!="0.000000":
				try:
					row[26] =round(float(row[26]),2)
					row[26] = str(row[26]) + "%"
				except Exception,e:
					row[26] =row[26]
		
		if row[27] and row[27] != "Wholesale price is not set":
			if row[27] != "" or row[27]!="0.000000" :
				try:
					row[27] =round(float(row[27]),2)
					row[27] = str(row[27]) + "%"
				except Exception,e:
					row[27] =row[27]
	return result
	
	
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
				("Serial number") + ":Data:100",
				("Rental Payment") + ":Data:100",
				("Agreement Period") + ":Data:100",
				("90d SAC Price") + ":Data:100",
				("Purchase price") + ":Data:100",
				("Transportation costs (incoming)") + ":Data:90",
				("Transportation costs (outgoing)") + ":Data:90",
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
				("IRR") + ":Data:150",
				("XIRR")+":Data:150",
			]
	return columns
