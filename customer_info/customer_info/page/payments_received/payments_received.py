from __future__ import unicode_literals
import frappe
import json
from frappe.utils import flt, cstr, cint
from frappe.utils.csvutils import UnicodeWriter


@frappe.whitelist()
def get_payments_details(customer,from_date,to_date):
	print customer,from_date,to_date

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

	
	return frappe.db.sql("""select payment_date,customer,rental_payment,
								late_fees,receivables,rental_payment+late_fees+receivables as total_payment_received,
								bank_transfer,cash,bank_card,
								balance,discount,bonus,concat(name,'') as refund,payments_ids
								from `tabPayments History` {0}
								order by customer """.format(cond),as_dict=1,debug=1)



@frappe.whitelist()
def create_csv(data):

	w = UnicodeWriter()
	w = add_header(w)
	w = add_data(w, data)
	# write out response as a type csv
	frappe.response['result'] = cstr(w.getvalue())
	frappe.response['type'] = 'csv'
	frappe.response['doctype'] = "Payment Received Report"

def add_header(w):
	w.writerow(["Payment Received Report"])
	return w

def add_data(w,data):
	data = json.loads(data)
	if len(data) > 0:
		w.writerow('\n')
		w.writerow(['Payment Received'])
		w.writerow(['', 'Payment Date','Customer', 'Rental Payment','Late Fees','Receivables','Total Rental Payment','Bank Transfer','Cash','Bank Card','Balance','Discount','Bonus'])
		for i in data:
			row = ['',i['payment_date'], i['customer'], i['rental_payment'],i['late_fees'],i['receivables'],i['total_payment_received'],i['bank_transfer'],i['cash'],i['bank_card'],i['balance'],i['discount'],i['bonus']]
			w.writerow(row)	
			w.writerow(['','Payment id','Due Date','Rental Payment','Late Fees','Total'])
			for j in i['payments_ids']:
				row = ['', j['payments_id'],j['due_date'],j['rental_payment'],j['late_fees'],j['total']]
				w.writerow(row)
	return w
	