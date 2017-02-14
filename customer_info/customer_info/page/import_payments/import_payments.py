import frappe
from frappe.utils.csvutils import read_csv_content_from_uploaded_file
from frappe.utils import getdate
from customer_info.customer_info.doctype.payments_management.payments_management import update_on_submit


@frappe.whitelist()
def upload():
	csv_rows = read_csv_content_from_uploaded_file()
	ret = []
	error = False
	for index,line in enumerate(csv_rows):
		d = {key:'' for key in csv_rows[0]}
		if index > 0:
			d['Migrated agreement ID'] = line[0]
			d['Payment ID'] = line[1]
			d['Payment date'] = line[2]
			d['Payment due date'] = line[3]
			d['Cash'] = line[4]
			d['Credit card'] = line[5]
			d['Discount'] = line[6]
			d['Agreement No'] = line[7]
			d['Rental payment'] = line[8]
			d['Customer'] = line[9]
			ret.append(made_payments(d))
	return {"messages": ret,"error":error}		
							
def made_payments(d):
	agreement_doc = frappe.get_doc("Customer Agreement",d['Agreement No'])
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
	"late_fees":0,
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


