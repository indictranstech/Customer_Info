import datetime
from datetime import datetime,date
import frappe

#def make_payment_history(values,customer,receivables,receivables_collected,payment_date,total_charges,payment_ids,payments_ids_list,rental_payment,total_amount,late_fees,payment_type,merchandise_status,late_fees_updated_status,payoff_cond=None,discount_amount=None,new_bonus=None):
def make_payment_history(args,payment_ids,payments_ids_list,payment_type,merchandise_status,late_fees_updated_status,payoff_cond=None,discount_amount=None,campaign_discount_of_agreements=None):
	payment_date = datetime.strptime(args['payment_date'], '%Y-%m-%d')
	payments_history = frappe.new_doc("Payments History")
	payments_history.cash = float(args['values']['amount_paid_by_customer'])
	payments_history.bank_card = float(args['values']['bank_card'])
	payments_history.bank_transfer = float(args['values']['bank_transfer'])
	payments_history.bonus = float(args['values']['bonus']) if args['values']['bonus'] else 0
	payments_history.new_bonus = args['new_bonus']
	payments_history.discount = float(args['values']['discount'])
	payments_history.campaign_discount = float(discount_amount) if discount_amount else 0
	payments_history.campaign_discount_of_agreements = campaign_discount_of_agreements if campaign_discount_of_agreements else ""
	payments_history.rental_payment = args['rental_payment']
	payments_history.late_fees = args['late_fees']
	payments_history.customer = args['customer']
	payments_history.receivables = float(args['receivables'])
	payments_history.receivables_collected = float(args['add_in_receivables'])
	payments_history.payment_date = payment_date.date()
	payments_history.total_charges = float(args['total_charges'])
	payments_history.payment_type = payment_type
	payments_history.merchandise_status = merchandise_status
	payments_history.total_payment_received = float(args['total_amount'])
	payments_history.payoff_cond = payoff_cond if payoff_cond else ""
	payments_history.late_fees_updated = late_fees_updated_status

	if payment_type == "Payoff Payment" or payment_type == "Normal Payment":
		for i in payment_ids:
			if payments_history.payments_ids:
				payments_history.payments_ids = payments_history.payments_ids + str(i) + ','
			else:
				payments_history.payments_ids = '"' + str(i) + ','
	
	payments_history.save(ignore_permissions = True)


	# if payment_type == "Payoff":
	# 	total_transaction_amount = float(total_amount)
	# else:
	# 	total_transaction_amount = float(rental_payment) + float(late_fees) -float(receivables)-float(values['bonus'])-float(values['discount'])
	if payment_type == "Payoff Payment" or payment_type == "Normal Payment":	
		bonus = float(args['values']['bonus']) if args['values']['bonus'] else 0
		total_transaction_amount = float(args['values']['amount_paid_by_customer']) + float(args['values']['bank_card']) + float(args['values']['bank_transfer']) + float(bonus)
		if payment_type == "Payoff Payment":
			total_calculated_payment_amount = float(args['total_amount'])
		else:	
			total_calculated_payment_amount = float(args['rental_payment'])+float(args['late_fees'])-float(args['receivables'])-float(bonus) - float(args['values']['discount'])
		pmt = "Split"

		if float(args['values']['amount_paid_by_customer']) == 0 and float(args['values']['bank_transfer']) == 0 and float(args['values']['bank_card']) > 0:
			pmt = "Credit Card"
		elif float(args['values']['amount_paid_by_customer']) > 0 and float(args['values']['bank_transfer']) == 0 and float(args['values']['bank_card']) == 0:
			pmt = "Cash"
		elif float(args['values']['amount_paid_by_customer']) == 0 and float(args['values']['bank_transfer']) > 0 and float(args['values']['bank_card']) == 0:
			pmt = "Bank Transfer"	
		elif float(args['values']['amount_paid_by_customer']) == 0 and float(args['values']['bank_transfer']) == 0 and float(args['values']['bank_card']) == 0 and float(args['values']['discount']) == 0:
			pmt = "Bonus"		

		id_list = tuple([x.encode('UTF8') for x in list(payments_ids_list) if x])
		cond = ""	
		if len(id_list) == 1:
			cond ="where payment_id = '{0}' ".format(id_list[0]) 
		elif len(id_list) > 1:	
			cond = "where payment_id in {0} ".format(id_list)  	
		
		frappe.db.sql("""update `tabPayments Record` 
						set payment_history = '{0}',pmt = '{2}',total_transaction_amount = '{3}'
						{1} """.format(payments_history.name,cond,pmt,str(total_transaction_amount)+"/"+str(total_calculated_payment_amount)))