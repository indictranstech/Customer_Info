# Copyright (c) 2013, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
# from numpy import irr
from datetime import datetime, timedelta,date
from frappe.utils import flt, get_datetime, get_time, getdate
import json
# from customer_info.customer_info.report.customer_agreements_report.financial import xirr

def execute(filters=None):
	columns, data = [], []
	columns = get_colums()
	data = get_data(filters)
	return columns, data

def get_data(filters):
	if filters:
		cond_dict = []
		filters = dict(filters)
		now_date = datetime.now().date()
		filters_keys = filters.keys()
		cond   = ""
		for key in filters_keys:
			if key =='agreement_period':
				cond = cond + " and ca.agreement_period = {0}".format(str(filters[key]))
			if key == 'agreement_status':
				cond = cond + " and ca.agreement_status = '{0}'".format(str(filters[key]))
			if key == 'agreement_close_reason' and filters['agreement_close_reason']:
				cond = cond + " and ca.agreement_closing_suspending_reason = '{0}'".format(str(filters[key]))
		if 'agreement_start_date_from' and 'agreement_start_date_to' in filters_keys:
				if filters['agreement_start_date_from'] != now_date and filters['agreement_start_date_to'] != now_date:
					cond = cond + "and ca.date BETWEEN '{0}' and '{1}'".format(str(filters['agreement_start_date_from']),str(filters['agreement_start_date_to']))
		if 'agreement_close_date_from' and 'agreement_close_date_to' in filters_keys:
				if filters['agreement_close_date_from'] != now_date and filters['agreement_close_date_to'] != now_date:
					cond = cond + "and ca.agreement_close_date BETWEEN '{0}' and '{1}'".format(str(filters['agreement_close_date_from']),str(filters['agreement_close_date_to']))
		
		result = frappe.db.sql("""select
					cus.first_name,
					cus.last_name,
					cus.prersonal_code,
					cus.city,
					cus.name,
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
					format((ca.s90d_sac_price - item.wholesale_price)/item.wholesale_price * 100,2),
					format((ca.monthly_rental_payment * ca.agreement_period -item.wholesale_price)/item.wholesale_price * 100,2),
					format(ca.monthly_rental_payment * ca.agreement_period,2),
					case when ca.agreement_status = "Closed"  then format(ca.real_agreement_income,2)
					else format(ca.payments_made,2) end as real_agreement_income,
					case when ca.agreement_status = "Closed" then ca.agreement_close_date
					when ca.agreement_status = "Suspended" then ca.suspended_from
					else "-" end as agreement_closing_suspension_date,
					case when ca.agreement_closing_suspending_reason = "Early buy offer" then
					concat(ca.early_buy_discount_percentage,"% ",ca.agreement_closing_suspending_reason)
					else ca.agreement_closing_suspending_reason end as agreement_closing_suspension_reason,
					case when ca.agreement_close_date then ceil((DATEDIFF(ca.agreement_close_date,ca.date)/30)) else ceil(DATEDIFF(CURDATE(),ca.date)/30) end as active_agreement_months,
					format(ca.payments_made - item.wholesale_price,2),
					format((ca.payments_made - item.wholesale_price)/item.wholesale_price * 100,2),
					format(ca.payments_left,2) as remaining_months_till_the_end_of_agreement,
					ca.campaign_discount_code,
					case when ca.without_advance_payment = 1 then "Yes" else "No" end as without_advance_payment ,
					ca.irr,
					ca.xirr,
					ca.tirr
					from `tabCustomer Agreement` ca ,`tabCustomer` cus,`tabItem` item
					where ca.customer = cus.name and ca.product = item.name {0} """.format(cond),as_list=1,debug=1)

		for row in result:
			if row[29] and row[29] != "Wholesale price is not set":
				if row[28] != "" or row[29]!="0.000000":
					try:
						row[29] =round(float(row[29]),2)
						# row[28] = str(row[28]) + "%"
					except Exception,e:
						row[29] =row[29]
			
			if row[30] and row[30] != "Wholesale price is not set":
				if row[30] != "" or row[30]!="0.000000" :
					try:
						row[30] =round(float(row[30]),2)
						# row[29] = str(row[29]) + "%"
					except Exception,e:
						row[30] =row[30]
		result = get_customer_status(result)
		result = calculate_real_agreement_income(result)
		irr_average = get_irr_averages(result)
		xirr_averages = get_xirr_averages(result)
		if xirr_averages or irr_average:
			last_row = [u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'', u'',u'',u'',u'', u'Weighted average',irr_average,xirr_averages]
			result.append(last_row)
		
		return result
	else:	
		now_date = datetime.now().date()
		result = frappe.db.sql("""select
					cus.first_name,
					cus.last_name,
					cus.prersonal_code,
					cus.city,
					cus.name,
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
					format((ca.s90d_sac_price - item.wholesale_price)/item.wholesale_price * 100,2),
					format((ca.monthly_rental_payment * ca.agreement_period -item.wholesale_price)/item.wholesale_price * 100,2),
					format(ca.monthly_rental_payment * ca.agreement_period,2),
					case when ca.agreement_status = "Closed"  then format(ca.real_agreement_income,2)
					else format(ca.payments_made,2) end as real_agreement_income,
					case when ca.agreement_status = "Closed" then ca.agreement_close_date
					when ca.agreement_status = "Suspended" then ca.suspended_from
					else "-" end as agreement_closing_suspension_date,
					case when ca.agreement_closing_suspending_reason = "Early buy offer" then
					concat(ca.early_buy_discount_percentage,"% ",ca.agreement_closing_suspending_reason)
					else ca.agreement_closing_suspending_reason end as agreement_closing_suspension_reason,
					case when ca.agreement_close_date then ceil((DATEDIFF(ca.agreement_close_date,ca.date)/30)) else ceil(DATEDIFF(CURDATE(),ca.date)/30) end as active_agreement_months,
					format(ca.payments_made - item.wholesale_price,2),
					format((ca.payments_made - item.wholesale_price)/item.wholesale_price * 100,2),
					format(ca.payments_left,2) as remaining_months_till_the_end_of_agreement,
					ca.campaign_discount_code,
					case when ca.without_advance_payment = 1 then "Yes" else "No" end as without_advance_payment ,
					ca.irr,
					ca.xirr,
					ca.tirr
					from `tabCustomer Agreement` ca ,`tabCustomer` cus,`tabItem` item
					where ca.customer = cus.name and ca.product = item.name""",as_list=1)

		for row in result:
			if row[30] and row[31] != "Wholesale price is not set":
				if row[30] != "" or row[31]!="0.000000":
					try:
						row[30] =round(float(row[30]),2)
						# row[28] = str(row[28]) + "%"
					except Exception,e:
						row[30] =row[30]
			
			if row[31] and row[31] != "Wholesale price is not set":
				if row[31] != "" or row[31]!="0.000000" :
					try:
						row[31] =round(float(row[31]),2)
						# row[29] = str(row[29]) + "%"
					except Exception,e:
						row[31] =row[31]
		result = get_customer_status(result)
		result = calculate_real_agreement_income(result)
		irr_average = get_irr_averages(result)
		xirr_averages = get_xirr_averages(result)
		if xirr_averages or irr_average:
			last_row = [u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'',u'', u'',u'',u'',u'', u'Weighted average',irr_average,xirr_averages]
			result.append(last_row)
		return result
		
		
def get_colums():
	columns = [
				("Customer Name") + ":Data:100",
				("Surname") + ":Data:100",
				("Personal Code") + ":Data:100",
				("City/Town") + ":Data:100",
				("Customer Status") + ":Data:100",
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
				("Without advance payment")+":Data:150",
				("IRR %") + ":Data:150",
				("XIRR %")+":Data:150",
				("TIRR %")+":Data:150"
			]
	return columns


def get_customer_status(result):
	'''
	"New" - when customer had no agreements before creating this agreement
	"Existing" - when customer had agreements before creating this agreement
	'''
	for row in result:
		agreements = frappe.db.sql("""select name from `tabCustomer Agreement`
					 where customer ='{0}' and  date < '{1}'""".format(row[4],row[7]),debug =1)
		if agreements:
			row[4] = 'Existing'
		else:
			row[4] = 'New'
	return result

def calculate_real_agreement_income(result):
	'''
	Real agreement profit EUR = Real agreements incomes - Wholesale price - Transportation costs
	'''
	for row in result:
		if row[21] and row[15]:
			realagreement_income = wholesale_price = transportation_costs = 0.0
			if row[21]: 
				realagreement_income =flt(row[21])
			if row[15]:
				wholesale_price = flt(row[15])
			if row[16]:
				transportation_costs = flt(row[16])
			if row[17]:
				transportation_costs = transportation_costs + flt(row[17])
			row[22] = round(realagreement_income - ( wholesale_price + transportation_costs),2) 
	return result

def get_irr_averages(result):
	'''
	irr_average = irr_average + round(row.wholsale price * row.IRR,2)
	wholesale_price_total = wholesale_price_total+ row.wholesale_price
	irr_average = irr_average/wholesale_price_total
	irr_average = round(irr_average,2)
	'''
	irr_average = 0.0
	wholesale_price_total = 0.0
	for row in result:
		if row[5] and row[30] !='Wholesale price is not set':
			irr_average = irr_average + round(flt(row[15]) * (flt(row[30])),2)
			wholesale_price_total = wholesale_price_total + flt(row[15])
	if wholesale_price_total != 0.0:
		return round(flt(irr_average/wholesale_price_total),2)
	else:
		return 0.0


def get_xirr_averages(result):
	'''
	xirr_average = xirr_average + round(row.wholsale price * row.XIRR,2)
	wholesale_price_total = wholesale_price_total+ row.wholesale_price
	xirr_average = xirr_average/wholesale_price_total
	xirr_average = round(xirr_average,2)
	'''
	xirr_average = 0.0
	wholesale_price_total = 0.0
	for row in result:
		if row[5] and row[31] !='Wholesale price is not set':
			xirr_average = xirr_average + round(flt(row[15]) * (flt(row[31])),2)
			wholesale_price_total = wholesale_price_total + flt(row[15])
	if wholesale_price_total != 0.0:
		return round(flt(xirr_average/wholesale_price_total),2)
	else:
		return 0.0
