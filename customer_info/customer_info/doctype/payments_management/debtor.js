Debtor = Class.extend({
	init:function(customer){
		this.customer = customer;
		this.render_dialog();
	},
	render_dialog:function(){
		var me = this;
		this.dialog = new frappe.ui.Dialog({
            title: "Debtor",
              fields: [
                  {"fieldtype": "Select" , "fieldname": "debtor" , "label": "Debtor","options":["","Yes","No"]},
                  {"fieldtype": "Small Text" , "fieldname": "comment" , "label": "Comment"},
                  {"fieldtype": "Section Break" , "fieldname": "section"},
                  {"fieldtype": "Button" , "fieldname": "add_comment" , "label": "Add Comment"},
                  {"fieldtype": "Column Break" , "fieldname": "column"},
                  {"fieldtype": "Column Break" , "fieldname": "column"},
                  {"fieldtype": "Column Break" , "fieldname": "column"},
                ],
                primary_action_label: "Update",
                primary_action: function(){
                    me.update_debtor()
                }
        });
        this.fd = this.dialog.fields_dict;
        this.fd.debtor.set_input(cur_frm.doc.debtor)
        this.dialog.show();
        this.add_comment();
	},
    update_debtor:function(){
        var me = this;
        frappe.call({    
            method: "customer_info.customer_info.doctype.payments_management.payments_management.update_debtor",
            args: {
                customer: me.customer,
                debtor: me.fd.debtor.$input.val()
            },
            callback: function(r) {
                if(r.message){
                    me.dialog.hide();
                    r.message == "Yes" ? $('button[data-fieldname="debtor_button"]').css('background','red'):$('button[data-fieldname="debtor_button"]').css('background','')
                    cur_frm.set_value("debtor",r.message)
                }
            }
        })
    },
    add_comment:function(){
        var me = this;
        me.dialog.fields_dict.add_comment.$input.click(function() {
            if(me.dialog.fields_dict.comment.$input.val()){
                if(me.fd.debtor.$input.val() == "Yes"){
                    cur_frm.set_value("notes_on_customer_payments", frappe.datetime.nowdate()+" "+"["+cur_frm.doc.username+"] "+"Marked as debtor:"+" "+me.dialog.fields_dict.comment.$input.val()+" ")
                }
                else if(me.fd.debtor.$input.val() == "No"){
                    cur_frm.set_value("notes_on_customer_payments", frappe.datetime.nowdate()+" "+"["+cur_frm.doc.username+"] "+"Removed debtor mark:"+" "+me.dialog.fields_dict.comment.$input.val()+" ")            
                }
                $('button[data-fieldname="add_notes"]').click();
                me.dialog.fields_dict.comment.set_input("");
            }
            me.dialog.hide();
        })
    }
})	