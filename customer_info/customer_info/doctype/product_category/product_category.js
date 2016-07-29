frappe.ui.form.on("Product Category",{
	category_name:function(frm){
		if(cur_frm.doc.category_name){
		    frappe.call({
		        method: "customer_info.customer_info.doctype.product_category.product_category.get_category_name",
		        args: {
		            "name":cur_frm.doc.category_name
		        },
		       	callback: function(r){
		       		if(r.message){
		     			msgprint(r.message)
		     			cur_frm.doc.category_name = ""
		     			refresh_field("category_name")
		       		}
		       	}  	
		    });
		}
	},	
	period:function(frm){
		if(cur_frm.doc.period){
		    frappe.call({
		        method: "frappe.client.get_value",
		        args: {
		            doctype: "Period",
		            fieldname: "period",
		            filters: { name: cur_frm.doc.period },
		        },
		       	callback: function(res){
		          	if (res && res.message){
		          		cur_frm.doc.period_value = res.message['period']
		          		refresh_field("period_value");
		           	}
		       	}  	
		    });
		}    
	},
	ratio:function(frm){
	    if(cur_frm.doc.ratio){
		    frappe.call({
		        method: "frappe.client.get_value",
		        args: {
		            doctype: "Ratio",
		            fieldname: "ratio",
		            filters: { name: cur_frm.doc.ratio },
		        },
		       	callback: function(res){
		          	if (res && res.message){
		          		cur_frm.doc.ratio_value = res.message['ratio']
		          		refresh_field("ratio_value");
		           	}
		       	}  	
		    });
		}    
	},
	/*validate:function(frm){	
		if(cur_frm.doc.__islocal){
			return frappe.call({
				method: "customer_info.customer_info.doctype.product_category.product_category.new_item_group",
				args: {
					"category_name":cur_frm.doc.category_name
				}
			})
		}	
	}*/	
})