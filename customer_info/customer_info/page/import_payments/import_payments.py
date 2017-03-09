import frappe
from frappe.utils.csvutils import read_csv_content_from_uploaded_file
from frappe.utils import getdate
import json
from customer_info.customer_info.doctype.payments_management.payments_management import update_on_submit
from customer_info.customer_info.doctype.payments_management.payments_management import update_payments_records_on_payoff_submit
from customer_info.customer_info.doctype.payments_management.payments_management import payoff_submit

@frappe.whitelist()
def upload(update_due_date = None):
	params = json.loads(frappe.form_dict.get("params") or '{}')
	csv_rows = read_csv_content_from_uploaded_file()
	ret = []
	error = False
	for index,line in enumerate(csv_rows):
		d = {key:'' for key in csv_rows[0]}
		if index > 0:
			d['Migrated agreement ID'] = line[0]
			d['Agreement No'] = line[8]
			d["Payoff"] = line[9]	
			d['Payment ID'] = d['Agreement No']+"-"+line[1] if not d["Payoff"] else ""
			d['Payment date'] = line[2]
			d['Payment due date'] = line[3]
			d['Cash'] = line[4]
			d['Credit card'] = line[5]
			d['Discount'] = line[6]
			d['Late Fees'] = line[7]
			ret.append(made_payments(d,params))

	return {"messages": ret,"error":error}		
							
def made_payments(d,params):
	error = ""
	agreement_doc = frappe.get_doc("Customer Agreement",d['Agreement No'])
	d['Rental payment'] = agreement_doc.monthly_rental_payment
	d['Customer'] = agreement_doc.customer

	if d['Late Fees']:
		agreement_doc.late_fees_updated = "Yes"
		agreement_doc.save(ignore_permissions=True)

	if d["Payoff"]:
		payoff_data = update_payments_records_on_payoff_submit(d['Payment date'],d['Agreement No'])
		error += payoff_payment(payoff_data,agreement_doc,d)

	else:
		if params['update_due_date']:
			for row in agreement_doc.payments_record:
				if row.payment_id == d['Payment ID'] and row.check_box == 0:
					row.due_date = d['Payment due date']
					row.save(ignore_permissions=True)
		agreement_doc.save(ignore_permissions=True)
		error += regular_payment(agreement_doc,d)

	return error


def regular_payment(agreement_doc,d):
	error = ""
	for row in agreement_doc.payments_record:
		if row.check_box == 1 and row.payment_id == d['Payment ID'] and getdate(row.due_date) == getdate(d['Payment due date']):
			error += "Payment ID {0} of {1} agreement already Processed".format(d['Payment ID'],d['Agreement No'])
		if row.payment_id == d['Payment ID'] and getdate(row.due_date) == getdate(d['Payment due date']) and row.check_box == 0:
			row.update({
				"check_box":1,
				"payment_date":d['Payment date']
			})
			row.save(ignore_permissions = True)
			error += "Payment Processed Successful for {0} of {1} agreement".format(d['Payment ID'],d['Agreement No'])
		if row.payment_id == d['Payment ID'] and getdate(row.due_date) != getdate(d['Payment due date']):
			error += "Payment due date {0} not match with Payment ID {1} of {2} agreement".format(d['Payment due date'],d['Payment ID'],d['Agreement No'])
	
	agreement_doc.save(ignore_permissions=True)
	
	args = {
	"values":{
		'amount_paid_by_customer':d['Cash'],
		'bank_card':d['Credit card'],
		'discount':d['Discount'],
		'bank_transfer':0,
		'bonus':0
	},
	"rental_payment":d['Rental payment'],
	"payment_date":d['Payment date'],
	"customer":d['Customer'],
	"total_charges":d['Rental payment'],
	"late_fees":d['Late Fees'],
	"bonus":0,
	"manual_bonus":0,
	"used_bonus":0,
	"new_bonus":0,
	"add_in_receivables":0,
	"receivables":0
	}
	flag = "from_import_payment"

	update_on_submit(args,flag)
	return error


def payoff_payment(payoff_data,agreement_doc,d):
	error = "Successful"
	balance = float(agreement_doc.payments_left) * agreement_doc.monthly_rental_payment
	discount = ((balance - float(agreement_doc.late_payment)) / 100) * float(agreement_doc.early_buy_discount_percentage)

	args = {
		"customer_agreement":d['Agreement No'],
		"agreement_status":"Closed",
		"condition": "90 day pay Off",
		"customer":d['Customer'],
		"receivables":0,
		"add_in_receivables":0,
		"values":{
			'amount_paid_by_customer':d['Cash'],
			'bank_card':d['Credit card'],
			'discount':d['Discount'],
			'bank_transfer':0,
			'bonus':0
		},
		"late_fees":0,
		"bonus":0,
		"manual_bonus":0,
		"used_bonus":0,
		"new_bonus":0,
		"payment_date":d['Payment date'],
		"data":payoff_data
	}

	if d["Payoff"] == "Early buy":
		args['condition'] = "90 day pay Off"
		args['rental_payment'] =  balance - (float(discount) + float(agreement_doc.late_payment))#Discounted_payment_amount
		args['total_amount'] = balance - float(discount)#Total_payoff_amount

	if d["Payoff"] == "90d SAC":
		args['condition'] = "pay off agreement"
		args['rental_payment'] = agreement_doc.s90d_sac_price#s90d_sac_price
		args['total_amount'] = agreement_doc.s90d_sac_price - agreement_doc.payments_made#s90_day_pay_Off
	flag = "from_import_payment"
	payoff_submit(args,flag)
	return error