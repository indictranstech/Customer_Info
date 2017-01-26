import frappe
from frappe.utils.csvutils import read_csv_content_from_uploaded_file
from frappe.utils import nowdate, getdate,add_months,add_days,get_last_day
from customer_info.customer_info.doctype.payments_management.payments_management import update_on_submit


@frappe.whitelist()
def upload():
	csv_rows = read_csv_content_from_uploaded_file()
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
			made_payments(d)
			
def made_payments(d):
	frappe.errprint(d['Agreement No'])
	agreement_doc = frappe.get_doc("Customer Agreement",d['Agreement No'])
	for row in agreement_doc.payments_record:
		if row.payment_id == d['Payment ID'] and getdate(row.due_date) == getdate(d['Payment due date']) and row.check_box == 0:
			row.update({
				"check_box":1,
				"payment_date":d['Payment date']
			})
			row.save(ignore_permissions = True)
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
	"receivables":0,
	}

	update_on_submit(args,"True")
	
	#frappe.errprint(frappe.get_traceback())
	return "Sucess"


