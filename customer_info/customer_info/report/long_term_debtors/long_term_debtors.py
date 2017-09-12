#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2013, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from datetime import datetime, timedelta,date
from datetime import datetime, timedelta,date
from frappe.utils import flt, get_datetime, get_time, getdate
from frappe.utils import date_diff


def execute(filters=None):
	columns, data = [], []
	columns = get_colums()
	data = get_data()
	return columns, data


def get_data():
	now_date = datetime.now().date()
	result = frappe.db.sql("""select
								ca.name,
								ca.migrated_agreement_id,
								ca.agreement_status,
								cus.first_name,
								cus.last_name,
								cus.prersonal_code,
								cus.company_phone_1,
								cus.company_email_id_1,
								(select ad.city from `tabAddress` ad where ad.customer = cus.name and ad.is_primary_address=1),
								(select concat(ad.address_line1,"\n",IF(ad.address_line2 IS NULL,"",ad.address_line2)) from `tabAddress` ad where ad.customer = cus.name and ad.is_primary_address=1),
								cus.spouse_first_name,
								cus.spouse_last_name,
								cus.spouse_contact_no,
								ca.date,
								ca.agreement_period,
								(select t1.due_date from `tabPayments Record` t1 where t1.parent=ca.name order by t1.due_date desc limit 1),
								ca.current_due_date,
								concat(ca.product_category," ",ca.product),
								(select format(sum(CASE WHEN t1.due_date < '{0}' AND DATEDIFF('{0}',t1.due_date) > 3  THEN t1.monthly_rental_amount ELSE 0 END),2) AS late_payments from `tabPayments Record` t1 where t1.parent=ca.name and t1.check_box_of_submit = 0),
								(select sum(t1.monthly_rental_amount) AS balance from `tabPayments Record` t1 where t1.parent=ca.name and t1.check_box_of_submit = 0),
								ca.late_fees,
								(select format(sum(CASE WHEN t1.due_date < '{0}' AND DATEDIFF('{0}',t1.due_date) > 3  THEN (DATEDIFF('{0}',t1.due_date) - 3) * t1.monthly_rental_amount * (ca.late_fees_rate/100)+t1.monthly_rental_amount ELSE 0 END),2) AS late_payments from `tabPayments Record` t1 where t1.parent=ca.name and t1.check_box_of_submit = 0 and t1.no_of_payments <> "Payment 1"),
								ca.late_fees_rate,
								cus.name,
								cus.receivables
								from `tabCustomer Agreement` ca ,`tabCustomer` cus
								where ca.customer = cus.name and ca.debtor = "Yes"
								""".format(now_date),as_list=1,debug=1)
	for row in result:
			row= calculate_late_fee(row)

	for row in result:
		Oldest_agreement = frappe.db.sql("""select name from `tabCustomer Agreement` ca
												where customer = '{0}'
												order by ca.date limit 1""".format(row[23]),as_list=1)[0][0]
		if Oldest_agreement and row[0] == Oldest_agreement:
			row[23] = row[24]
			print "Agree----",row[0]
			print "row18",row[19],"row23",row[24],"row22",row[23]
			if float(row[24]) > 0.0:
				row[18] ="{0:.2f}".format(float(str(row[19])) - float(str(row[24]))) if row[24] and row[19] else row[19]
			else: 
				# print "float",float(row[23])
				row[19] = "{0:.2f}".format(float(str(row[19])) + abs(float(str(row[24])))) if row[24] and row[19] else row[19]
				print "row18",row[19],"row23",row[24],"row22",row[23]		
		else:
			row[23] = ""
	return result

def calculate_late_fee(row):
	now_date = datetime.now().date()
	late_fees_list = []
	late_fees = 0.0
	no_of_late_days = 0
	for days in frappe.get_doc("Customer Agreement",row[0]).payments_record:
		no_of_late_days_new = 0
		no_of_late_days_new += date_diff(now_date,days.due_date)
		late_fees_rate = frappe.get_doc("Customer Agreement",row[0]).late_fees_rate
		monthly_rental_amount =	frappe.get_doc("Customer Agreement",row[0]).payments_record[1].monthly_rental_amount
		if no_of_late_days_new > 180 and days.check_box_of_submit == 0 :
			no_of_late_days = 180
			late_fees_list.append(float(no_of_late_days * monthly_rental_amount * (late_fees_rate/100)))
		elif no_of_late_days_new > 0 and no_of_late_days_new < 180 and days.check_box_of_submit == 0: 
			no_of_late_days = no_of_late_days_new
			late_fees_list.append(float(no_of_late_days * monthly_rental_amount * (late_fees_rate/100)))
	row[20] = "{0:.2f}".format(sum(late_fees_list))
	return row


def get_colums():
	columns = [
			("Sutarties nr") + ":Link/Customer Agreement:80",
			("Migracinis sutarties nr.") + ":Data:70",
			("Sutarties statusas"),			
			("Kliento vardas") + ":Data:130",
			("Pavardė") + ":Data:100",
			("Asmens kodas") + ":Data:100",
			("Telefono numeris") + ":Data:100",
			("El. pašto adresas") + ":Data:80",
			("Miestas") + ":Data:90",
			("Adresas") + ":Data:80",
			("Sutuoktinio vardas") + ":Data:90",
			("Sutuoktinio pavardė") + ":Data:90",
			("Sutuoktinio telefono nr.") + ":Data:90",
			("Sutarties sudarymo data") + ":Date:90",
			("Sutarties terminas") + ":Data:90",
			("Sutarties pabaigos data") + ":Date:90",
			("Seniausio neapmokėto mokėjimo data") + ":Date:90",
			("Prekė") + ":Data:90",
			("Vėluojančių mokėjimų suma, EUR") + ":Data:90",	
			("Bendra skola iki sutarties pabaigos be delspinigių, EUR") + ":Data:90",
			("Delspinigių suma, EUR") + ":Data:90",
			("Mokėtina suma su delspinigiais, EUR") + ":Data:100",
			("Delspinigių dydis už kiekvieną praleistą dieną pagal sutartį, %")+ ":Data:100",
			("Permoka+/Nepriemoka-") + ":Data:100"
			]
	return columns


# def get_colums():
# 	columns = [
# 			("Agreement Number") + ":Link/Customer Agreement:80",
# 			("Migrated agreement ID") + ":Data:70",
# 			("Customer Name") + ":Data:130",
# 			("Surname") + ":Float:100",
# 			("Personal Code") + ":Data:100",
# 			("Phone") + ":Data:100",
# 			("Email Id") + ":Data:80",
# 			("City") + ":Data:90",
# 			("Address") + ":Float:80",
# 			("Spouse First Name") + ":Data:90",
# 			("Spouse Last Name") + ":Data:90",
# 			("Spouse Contact No") + ":Data:90",
# 			("Agreement Start Date") + ":Date:90",
# 			("Agreement period") + ":Data:90",
# 			("Agreement Close Date") + ":Date:90",
# 			("Oldest due date") + ":Date:90",
# 			("Product") + ":Data:90",
# 			("Late Payments") + ":Data:90",
# 			("Total amount of unpaid and to be paid payments") + ":Data:90",
# 			("Late Fees") + ":Data:90",
# 			("Late Payments + Late Fees") + ":Data:100",
# 			("Late Fees Rate %")+ ":Data:100",
# 			#("Permoka+/Nepriemoka-") + ":Data:100"
# 			("Receivables")+":Data:100"
# 			]
# 	return columns