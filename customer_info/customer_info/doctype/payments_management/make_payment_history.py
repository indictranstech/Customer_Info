import datetime
from datetime import datetime,date
import frappe

def make_payment_history(values,customer,receivables,receivables_collected,payment_date,total_charges,payment_ids,payments_ids_list,rental_payment,total_amount,late_fees,payment_type,merchandise_status,payoff_cond=None):
	payment_date = datetime.strptime(payment_date, '%Y-%m-%d')
	payments_history = frappe.new_doc("Payments History")
	payments_history.cash = float(values['amount_paid_by_customer'])
	payments_history.bank_card = float(values['bank_card'])
	payments_history.bank_transfer = float(values['bank_transfer'])
	payments_history.bonus = float(values['bonus']) if values['bonus'] else 0
	payments_history.discount = float(values['discount'])
	payments_history.rental_payment = rental_payment
	payments_history.late_fees = late_fees
	payments_history.customer = customer
	payments_history.receivables = float(receivables)
	payments_history.receivables_collected = float(receivables_collected)
	payments_history.payment_date = payment_date.date()
	payments_history.total_charges = float(total_charges)
	payments_history.payment_type = payment_type
	payments_history.merchandise_status = merchandise_status
	payments_history.total_payment_received = float(total_amount)
	payments_history.payoff_cond = payoff_cond if payoff_cond else ""


	for i in payment_ids:
		if payments_history.payments_ids:
			payments_history.payments_ids = payments_history.payments_ids + str(i) + ','
		else:
			payments_history.payments_ids = '"' + str(i) + ','
	
	payments_history.save(ignore_permissions = True)


	if payment_type == "Payoff":
		total_transaction_amount = float(total_amount)
	else:
		total_transaction_amount = float(rental_payment) + float(late_fees) -float(receivables)-float(values['bonus'])-float(values['discount'])
	
	pmt = "Split"

	if float(values['amount_paid_by_customer']) == 0 and float(values['bank_transfer']) == 0 and float(values['bank_card']) > 0:
		pmt = "Credit Card"
	elif float(values['amount_paid_by_customer']) > 0 and float(values['bank_transfer']) == 0 and float(values['bank_card']) == 0:
		pmt = "Cash"
	elif float(values['amount_paid_by_customer']) == 0 and float(values['bank_transfer']) > 0 and float(values['bank_card']) == 0:
		pmt = "Bank Transfer"	
		

	id_list = tuple([x.encode('UTF8') for x in list(payments_ids_list) if x])
	cond = ""	
	if len(id_list) == 1:
		cond ="where payment_id = '{0}' ".format(id_list[0]) 
	elif len(id_list) > 1:	
		cond = "where payment_id in {0} ".format(id_list)  	
	
	frappe.db.sql("""update `tabPayments Record` 
					set payment_history = '{0}',pmt = '{2}',total_transaction_amount = {3}
					{1} """.format(payments_history.name,cond,pmt,total_transaction_amount))