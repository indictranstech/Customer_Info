from __future__ import unicode_literals
import frappe
import json
from frappe.utils import flt, cstr, cint, date_diff
from frappe.utils.csvutils import UnicodeWriter
import pdfkit
from customer_info.customer_info.doctype.payments_management.payments_management import set_values_in_agreement_on_submit,set_values_in_agreement_temporary 

@frappe.whitelist()
def get_payments_details(customer,from_date,to_date,agreement,data_limit):

	if customer and from_date and to_date:
		cond = "where customer = '{0}' and (payment_date BETWEEN '{1}' AND '{2}') and refund = 'No' ".format(customer,from_date,to_date)

	elif customer and from_date:
		cond = "where customer = '{0}' and payment_date >= '{1}' and refund = 'No' ".format(customer,from_date)

	elif customer and to_date:
		cond = "where customer = '{0}' and payment_date < '{1}' and refund = 'No' ".format(customer,to_date)

	elif from_date and to_date:
		cond = "where (payment_date BETWEEN '{0}' AND '{1}')  and refund = 'No' ".format(from_date,to_date)

	elif customer:
		cond = "where customer = '{0}'  and refund = 'No' ".format(customer)

	elif from_date:
		cond = "where payment_date >= '{0}' and refund = 'No' ".format(from_date)

	elif to_date:
		cond = "where payment_date <= '{0}' and refund = 'No' ".format(to_date)

	else:
		cond = " where refund = 'No' "

	_cond = "limit 50" if not agreement	and not from_date and not to_date and not customer else " "
	if data_limit and not agreement and not from_date and not to_date and not customer:
		if data_limit != "All":
			_cond = "limit {0}".format(data_limit.split('-')[1])
		else:
			_cond = " "


	data = frappe.db.sql("""select payment_date,customer,payoff_cond,
								format(rental_payment+campaign_discount,2) as rental_payments,
								format(1*late_fees,2) as late_fees,receivables,
								CASE WHEN payoff_cond = "Rental Payment" 
								THEN format(rental_payment+late_fees-receivables-bonus-discount,2) ELSE format(total_payment_received,2) END AS total_payment_received,
	    						format(bank_transfer,2) as bank_transfer,format(cash,2) as cash,receivables_collected,format(bank_card,2) as bank_card,
								balance,format(discount, 2) as discount,format(campaign_discount, 2) as campaign_discount,format(bonus,2) as bonus,concat(name,'') as refund,payments_ids,
								late_fees_updated,payment_type,merchandise_status,
								case when special_associate = "Automatic" then special_associate else owner end as associate
								from `tabPayments History` {0}
								order by payment_date desc {1} """.format(cond,_cond),as_dict=1)


	filter_data = []
	filter_payments_history = []
	for row in data:
		if agreement and row['payments_ids'] and agreement in [i.split('-P')[0] for i in str(row['payments_ids'])[1::].split(',')[0:-1]]:
			filter_data.append(row)
			filter_payments_history.append(row['refund'])

	filter_payments_history = [name.encode('utf-8') for name in filter_payments_history]

	if agreement:
		if filter_payments_history:
			if len(filter_payments_history) == 1:
				cond += " and name = '{0}' ".format(filter_payments_history[0])
			elif len(filter_payments_history) > 1:
				cond += " and name in {0}".format(tuple(filter_payments_history))

		data = filter_data

	total = frappe.db.sql("""select "payment_date" as payment_date,"customer" as customer,"payoff_cond" as payoff_cond,
						format(sum(rental_payment),2) as rental_payment,
						format(sum(1*late_fees),2) as late_fees,format(sum(receivables),2) as receivables,"total_payment_received" as total_payment_received,
						format(sum(bank_transfer),2) as bank_transfer,format(sum(cash),2) as cash ,sum(receivables_collected) as receivables_collected,format(sum(bank_card),2) as bank_card,
						format(sum(balance),2) as balance,format(sum(discount),2) as discount,format(sum(campaign_discount),2) as campaign_discount, format(sum(bonus),2) as bonus
						from `tabPayments History` {0}""".format(cond,_cond),as_dict=1)
	total_payment_received = []

	for row in data:
		if row.get("associate") == "Administrator":
			row['associate'] = frappe.db.get_value("User",{'first_name':row['associate']},"first_name")
		elif row.get("associate") == "Automatic":
			pass
		else:		
			row['associate'] = frappe.db.get_value("User",{'email':row['associate']},"first_name")
		total_payment_received.append(row['total_payment_received'].replace(",",""))

	total[0]["payment_date"] = "Total"
	total[0]["customer"] = "-"
	total[0]["payoff_cond"] = "-"
	total[0]['total_payment_received'] = "{0:.2f}".format(sum(map(float,total_payment_received)))

	return {"data":data,"total":total}

@frappe.whitelist()
def create_csv(customer,from_date,to_date,agreement,data_limit):
	data_list = get_payments_details(customer,from_date,to_date,agreement,data_limit)['data']
	for row in data_list:
			row["payments_ids"] = update_dict_by_payment_ids(row) if row.get("payments_ids") else ""
	data = data_list
	w = UnicodeWriter()
	w = add_header(w)
	w = add_data(w, data)
	# write out response as a type csv
	frappe.response['result'] = cstr(w.getvalue())
	frappe.response['type'] = 'csv'
	frappe.response['doctype'] = "Payment Received Report"


def update_dict_by_payment_ids(row):
	dict_of_payments_ids = []
	__dict_of_payments_ids = []
	if row.payment_type != "Modification Of Receivables":
		formatted_list_of_payment_ids = str(row.payments_ids[1:-1]).split(",")
		if row.payoff_cond != "Rental Payment":
			late_fees = ""
			rental_payment = 0
			total = ""
			payment_id = ""
			payments_ids = []
			for d in formatted_list_of_payment_ids:
				payment_id = d.split("/")[0].split("-P")[0],
				payments_ids.append(d.split("/")[0]),
				late_fees = "-",
				rental_payment = float(d.split("/")[2]),
				total = "-"
	   		__dict_of_payments_ids.append({
	   			"payments_id":str(payment_id)+"-"+row.payoff_cond,
				"payment_id_list": str(payments_ids),
				"due_date":"-",
				"rental_payment":rental_payment,
				"late_fees":late_fees,
				"total": total
	   		})
			return __dict_of_payments_ids

		else:
			if row.late_fees_updated == "Yes":
				for index,data in enumerate(formatted_list_of_payment_ids):
					if index == 0:
			   			dict_of_payments_ids.append({
			   				"late_fees": row.updated_late_fees,
			   				"payments_id":data.split("/")[0],
							"due_date":data.split("/")[1],
							"rental_payment":data.split("/")[2],
							"total": float(float(row.updated_late_fees) if row.updated_late_fees else 0 + float(data.split("/")[2])) 
			   			})	
			   		else:
			   			dict_of_payments_ids.append({	
			   				"late_fees":0,
			   				"payments_id":data.split("/")[0],
							"due_date":data.split("/")[1],
							"rental_payment":data.split("/")[2],
							"total": float(0 + float(data.split("/")[2])) 
			   			})
			else:
		   		for d in formatted_list_of_payment_ids:
		   			dict_of_payments_ids.append({
			   			"payments_id":d.split("/")[0],
						"due_date":d.split("/")[1] if d.split("/")[1] else "",
						"rental_payment":d.split("/")[2],
						"late_fees":float(get_late_fees(d.split("/")[0].split("-P")[0],d.split("/")[1],d.split("/")[3],d.split("/")[2])),
						"total": float(float(get_late_fees(d.split("/")[0].split("-P")[0],d.split("/")[1],d.split("/")[3],d.split("/")[2])) + float(d.split("/")[2]))
			   		})
			return dict_of_payments_ids


def get_late_fees(agreement_name,date1,date2,rental_payment):
	date_diffirence = date_diff(date2,date1)
	late_fees_amount = 0
	agreement_doc = frappe.get_doc("Customer Agreement",agreement_name)
	if flt(date_diffirence) > 3:
		late_fees_amount = (float(date_diffirence) - 3) * float(rental_payment) * (float(agreement_doc.late_fees_rate)/100)
	if float(date_diffirence) > 3 and late_fees_amount:
		return late_fees_amount
	else:
		return 0

def add_header(w):
	w.writerow(["Payment Received Report"])
	return w

def add_data(w,data):
	if len(data) > 0:
		w.writerow('\n')
		w.writerow(['Payment Received'])
		w.writerow(['', 'Payment Date', 'Customer Name', 'Payment Type', 'Payment Amount',\
					 'Late Fees Amount', 'Receivables Amount','Discount Amount',\
					 'Campaign Discount Amount', 'Bonus Amount', 'Total Calculated Payment Amount',\
					  'Bank Transfer Amount', 'Receivables Collected', 'Cash Amount', 'Bank Card Amount'])
		for i in data:
			row = ['',i['payment_date'], i['customer'], i['payment_type'],i['rental_payments']\
				,i['late_fees'],i['receivables'],i['discount'],\
				i['campaign_discount'],i['bonus'],i['total_payment_received'],i['bank_transfer']\
				,i['receivables_collected'],i['cash'],i['bank_card']]
			w.writerow(row)	
			w.writerow(['','','Payment id','Due Date','Rental Payment','Late Fees','Total'])
			for j in i['payments_ids']:
				row = ['','', j['payments_id'],j['due_date'],j['rental_payment'],j['late_fees'],j['total']]
				w.writerow(row)
	return w

# @frappe.whitelist()
# def create_csv(data):
# 	w = UnicodeWriter()
# 	w = add_header(w)
# 	w = add_data(w, data)
# 	# write out response as a type csv
# 	frappe.response['result'] = cstr(w.getvalue())
# 	frappe.response['type'] = 'csv'
# 	frappe.response['doctype'] = "Payment Received Report"

# def add_header(w):
# 	w.writerow(["Payment Received Report"])
# 	return w

# def add_data(w,data):
# 	data = json.loads(data)
# 	if len(data) > 0:
# 		w.writerow('\n')
# 		w.writerow(['Payment Received'])
# 		w.writerow(['', 'Payment Date','Customer', 'Rental Payment','Late Fees','Receivables','Total Rental Payment','Bank Transfer','Cash','Bank Card','Balance','Discount','Bonus'])
# 		for i in data:
# 			row = ['',i['payment_date'], i['customer'], i['rental_payment'],i['late_fees'],i['receivables'],i['total_payment_received'],i['bank_transfer'],i['cash'],i['bank_card'],i['balance'],i['discount'],i['bonus']]
# 			w.writerow(row)	
# 			w.writerow(['','Payment id','Due Date','Rental Payment','Late Fees','Total','','Payment id','Due Date','Rental Payment','Late Fees','Total'])
# 			for j in i['payments_ids']:
# 				row = ['', j['payments_id'],j['due_date'],j['rental_payment'],j['late_fees'],j['total'],'', j['payments_id'],j['due_date'],j['rental_payment'],j['late_fees'],j['total']]
# 				w.writerow(row)
# 	return w
	 
@frappe.whitelist()
def make_refund_payment(payments_ids,ph_name):
	payments_ids = json.loads(payments_ids)
	payment_history = frappe.get_doc("Payments History",ph_name)
	customer = frappe.get_doc("Customer",payment_history.customer)
	payments_id_list = []
	agreement_list = []
	merchandise_status_list= []
	campaign_discount_of_agreements_list = []
	if len(payments_ids) > 0:
		for i in payments_ids:
			frappe.db.sql("""update `tabPayments Record` set check_box = 0,pre_select_uncheck = 0,
								payment_date = "",check_box_of_submit = 0,payment_history = "",pmt="",associate="",
								total_transaction_amount = 0 
								where check_box_of_submit = 1 
								and payment_id = '{0}' """.format(i))
			payments_id_list.append(i)
			agreement_list.append(i.split("-P")[0])
		agreement_list =  list(set(agreement_list))
		if agreement_list:
			agreement_list = [x.encode('UTF8') for x in agreement_list if x]
		flag = "Make Refund"
		agreement_list.sort()

		merchandise_status = payment_history.merchandise_status
		if merchandise_status and payment_history.payment_type == "Normal Payment":
			merchandise_status_list = [x.encode('UTF8') for x in merchandise_status.split(",")[0:-1] if x]	
			merchandise_status_list.sort()


		campaign_discount_of_agreements = payment_history.campaign_discount_of_agreements
		if campaign_discount_of_agreements and payment_history.payment_type == "Normal Payment":
			
			campaign_discount_of_agreements_list = [x.encode('UTF8') for x in campaign_discount_of_agreements.split(",")[0:-1] if x]	
			campaign_discount_of_agreements_list.sort()
			campaign_discount_of_agreements_dict = { agreement.split("/")[0]:[agreement.split("/")[1],agreement.split("/")[2]] for agreement in campaign_discount_of_agreements_list}

		refund_bonus = []	
		for i,agreement in enumerate(agreement_list):
			customer_agreement = frappe.get_doc("Customer Agreement",agreement)
			set_values_in_agreement_on_submit(customer_agreement)
			item_doc = frappe.get_doc("Item",customer_agreement.product)
			if payment_history.payment_type == "Payoff Payment":
				payment_history.payoff_cond = ""
				item_doc.sold_date = item_doc.old_sold_date
				item_doc.old_sold_date = item_doc.old_sold_date
				item_doc.save(ignore_permissions=True)
				customer_agreement.agreement_status = "Open"
				customer_agreement.old_merchandise_status = customer_agreement.merchandise_status
				customer_agreement.merchandise_status = payment_history.merchandise_status
				customer_agreement.agreement_closing_suspending_reason = ""
				customer_agreement.save(ignore_permissions=True)

			if payment_history.payment_type == "Normal Payment" and agreement == merchandise_status_list[i].split("/")[0]:
				item_doc.sold_date = item_doc.old_sold_date
				item_doc.old_sold_date = item_doc.old_sold_date
				item_doc.save(ignore_permissions=True)
				customer_agreement.agreement_status = "Open"
				customer_agreement.old_merchandise_status = customer_agreement.merchandise_status
				customer_agreement.merchandise_status = merchandise_status_list[i].split("/")[1]
				customer_agreement.agreement_closing_suspending_reason = ""  							
				customer_agreement.save(ignore_permissions=True)


			if payment_history.payment_type == "Normal Payment":
				"""
				deduct assigned bonus and discount from specific agreement
				"""
				if customer_agreement.name == payment_history.assigned_bonus_and_discount:
					customer_agreement.assigned_bonus = float(customer_agreement.assigned_bonus) - float(payment_history.bonus)
					customer_agreement.assigned_discount = float(customer_agreement.assigned_discount) - float(payment_history.discount)

				# if campaign_discount_of_agreements_list and agreement == campaign_discount_of_agreements_list[i].split("/")[0]:
				# 	customer_agreement.discount = campaign_discount_of_agreements_list[i].split("/")[1]
				# 	customer_agreement.assigned_campaign_discount = customer_agreement.assigned_campaign_discount - float(campaign_discount_of_agreements_list[i].split("/")[1])
				# 	customer_agreement.discounted_payments_left = campaign_discount_of_agreements_list[i].split("/")[2]

				if campaign_discount_of_agreements_list and agreement in campaign_discount_of_agreements_dict.keys():
					customer_agreement.discount = float(campaign_discount_of_agreements_dict[agreement][0])
					customer_agreement.assigned_campaign_discount = customer_agreement.assigned_campaign_discount - float(campaign_discount_of_agreements_dict[agreement][0])
					customer_agreement.discounted_payments_left = float(campaign_discount_of_agreements_dict[agreement][1])
				customer_agreement.save(ignore_permissions=True)	
				refund_bonus.append(float(set_values_in_agreement_temporary(agreement,customer.bonus,flag,payments_id_list)))
		#customer.bonus = customer.bonus - sum(refund_bonus) + float(payment_history.bonus)
		customer.bonus = customer.bonus - float(payment_history.new_bonus) + float(payment_history.bonus)
		customer.used_bonus = float(customer.used_bonus) - float(payment_history.bonus)
		customer.refund_to_customer = float(payment_history.cash) + float(payment_history.bank_card) + float(payment_history.bank_transfer) - float(payment_history.bonus) - float(payment_history.discount)

	#customer.receivables = float(payment_history.rental_payment) - float(payment_history.late_fees) - float(payment_history.total_charges)
	#customer.receivables = payment_history.receivables
	customer.receivables = float(customer.receivables) + float(payment_history.receivables) - float(payment_history.receivables_collected)
	customer.old_receivables = payment_history.receivables
	customer.save(ignore_permissions=True)
	
	payment_history.refund = "Yes"
	payment_history.save(ignore_permissions=True)