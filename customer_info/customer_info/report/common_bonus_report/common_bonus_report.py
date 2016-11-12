# Copyright (c) 2013, indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = get_colums(), get_data()
	return columns, data

def get_data(filters=None):
	#now_date = datetime.now().date()
	customer_bonus_info = frappe.db.sql("""select assign_manual_bonus,used_bonus,bonus,name 
											from `tabCustomer` 
								where customer_group ="Individual" """,as_list=1,debug=1)

	result = []
	for i in customer_bonus_info:
		customer_agreement_bonus_info = []
		customer_agreement_bonus_info = frappe.db.sql("""select sum(ag.new_agreement_bonus),sum(ag.payment_on_time_bonus),
									sum(ag.early_payments_bonus), 
									(sum(ag.payment_on_time_bonus)+ sum(ag.new_agreement_bonus)
										+sum(ag.early_payments_bonus) + {1}) as total	
									from `tabCustomer Agreement` ag 
									where customer ='{0}' """.format(i[3],i[0]),as_list=1,debug=1)[0]

		customer_agreement_bonus_info.extend(i)	
		result.append(customer_agreement_bonus_info)
		#i.extend(customer_agreement_bonus_info)	
		#i.append(sum(customer_agreement_bonus_info)+float(i[1]))

	#print "\n\n\n\n\n",result,"customer_bonus_info"	
	return result

# def get_condtion(from_date,to_date):
# 	print from_date,to_date

# 	cond = ""
# 	if  from_date and to_date:
# 		cond = "and t1.due_date BETWEEN '{0}' AND '{1}' ".format(from_date,to_date)

# 	elif from_date:
# 		cond = "and t1.due_date >= '{0}' ".format(from_date)

# 	elif to_date:
# 		cond = "and t1.due_date < '{0}' ".format(to_date)

# 	return cond	


def get_colums():
	print "future_payments columns"
	columns =  [("New agreement bonus") + ":Float:150"] + \
				[("Early payments bonus") + ":Float:150"] + [("Payment on time bonus") + ":Float:150"] + \
			[("Total bonus accumulated") + ":Float:160"] + [("Assign manual bonus") + ":Float:150"] + \
			[("Used bonus") + ":Float:90"] + \
			[("Active bonus") + ":Float:90"] + [("Customer") + ":Link/Customer:100"]
	return columns