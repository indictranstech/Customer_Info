frappe.ui.form.on("Item", {
    product_category: function(frm){
        if(cur_frm.doc.product_category){
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Product Category",
                    fieldname: ["period_value","ratio_value","period"],
                    filters: { name: cur_frm.doc.product_category },
                },
             	callback: function(res){
                    if(res && res.message){
                        cur_frm.doc.period = res.message['period_value']
                        cur_frm.doc.ratio = res.message['ratio_value']
                        cur_frm.doc.agreement_period = res.message['period']
                        refresh_field(["period","ratio","agreement_period"]);
                        cur_frm.doc.purchase_price_with_vat ? calculation_for_monthly_rental_and_90d(frm):""
                    }
             	}  	
            });
            cur_frm.doc.item_group = cur_frm.doc.product_category
            refresh_field("item_group")

        }           
    },
    serial_number: function(frm){
        cur_frm.doc.item_code = cur_frm.doc.brand + "-" +cur_frm.doc.serial_number
        cur_frm.doc.item_name = cur_frm.doc.item_code
        refresh_field(["item_code","item_name"])    
    },
    purchase_price_with_vat: function(frm){
        if(cur_frm.doc.period && cur_frm.doc.ratio){
            this.calculation_for_monthly_rental_and_90d(frm)
        }
        else{
            msgprint("Please Enter Value Of Agreement Period For Update Monthly Rental Payment")  
        }
    },
    period: function(frm){
        if(cur_frm.doc.purchase_price_with_vat && cur_frm.doc.ratio){
            this.calculation_for_monthly_rental_and_90d(frm)
        }
        else{
            msgprint("Please Enter Value Of Purchase Price with Vat")  
        }
        /*cur_frm.doc.old_agreement_period = cur_frm.doc.period
        refresh_field("old_agreement_period")*/
    },
    ratio:function(frm){
        if(cur_frm.doc.purchase_price_with_vat && cur_frm.doc.period){
            this.calculation_for_monthly_rental_and_90d(frm)
        }
        else{
            msgprint("Please Enter Value Of Purchase Price with Vat")
        }
    },
    insurance_fee: function(frm){
        if(cur_frm.doc.monthly_rental_payment){
            cur_frm.doc.total = cur_frm.doc.monthly_rental_payment + cur_frm.doc.insurance_fee
            refresh_field("total")
        }
    },
    merchandise_status: function(frm){
        if(cur_frm.doc.merchandise_status && cur_frm.doc.__islocal){
            cur_frm.doc.old_status = cur_frm.doc.merchandise_status
            refresh_field("old_status")
        }
        if(!cur_frm.doc.__islocal && cur_frm.doc.merchandise_status == "Stolen"){
            cur_frm.set_value("sold_date",frappe.datetime.nowdate())
        }
    },
    s90d_sac_price: function(frm){
        if(cur_frm.doc.s90d_sac_price && cur_frm.doc.__islocal){
            cur_frm.doc.old_90d_sac_price = cur_frm.doc.s90d_sac_price
            refresh_field("old_90d_sac_price")
        }
        if(cur_frm.doc.monthly_rental_payment && cur_frm.doc.__islocal){
            cur_frm.doc.old_monthly_rental_payment = cur_frm.doc.monthly_rental_payment
            refresh_field("old_monthly_rental_payment")
        }
        if(cur_frm.doc.period && cur_frm.doc.__islocal){
            cur_frm.doc.old_agreement_period = cur_frm.doc.period
            refresh_field("old_agreement_period")
        }
    },
    validate: function(frm){
        if (cur_frm.doc.serial_number){
            cur_frm.set_df_property("serial_number","read_only",1)
            refresh_field("serial_number")
        }
        if (cur_frm.doc.brand){
            cur_frm.set_df_property("brand","read_only",1)
            refresh_field("brand")
        }
        if (cur_frm.doc.product_category){
            cur_frm.set_df_property("product_category","read_only",1)
            refresh_field("product_category")
        }
        if (cur_frm.doc.monthly_rental_payment && !cur_frm.doc.insurance_fee){
            cur_frm.doc.total = cur_frm.doc.monthly_rental_payment
            refresh_field("total")
        }
        if (cur_frm.doc.__islocal){
            cur_frm.set_value("sold_date",frappe.datetime.nowdate())
            cur_frm.set_value("old_sold_date",frappe.datetime.nowdate())
        }
        cur_frm.doc.stock_uom = "Unit"
        refresh_field("stock_uom")
    },
    onload:function(frm){
        if (cur_frm.doc.serial_number){
            cur_frm.set_df_property("serial_number","read_only",1)
            refresh_field("serial_number")
        }
        if (cur_frm.doc.brand){
            cur_frm.set_df_property("brand","read_only",1)
            refresh_field("brand")
        }
        if (cur_frm.doc.product_category){
            cur_frm.set_df_property("product_category","read_only",1)
            refresh_field("product_category")
        }
    },
    refresh:function(frm){
        $('[data-fieldname="stock_uom"]').hide()
        $('[data-fieldname="item_group"]').hide()
    }
});

cur_frm.fields_dict['brand'].get_query = function(doc) {
	return {
		filters: {
			'category': cur_frm.doc.product_category 
		}
	}
}

calculation_for_monthly_rental_and_90d = function(frm){
    var b = (cur_frm.doc.purchase_price_with_vat * cur_frm.doc.ratio) / cur_frm.doc.period
	var c = roundNumber(b,2)
	var n = c.toString();
	var n1 = n.slice(-2)
	var aa = parseInt(n1[0])
	if(aa >= 5){
		var five = Math.floor(b) + 0.99
        if(five >= 0){
            cur_frm.doc.monthly_rental_payment = five
            refresh_field("monthly_rental_payment")
	    }
        else{
            cur_frm.doc.monthly_rental_payment = "0"
            refresh_field("monthly_rental_payment")
        }
    }
	else{
		var less = Math.floor(b) - 0.01
		if(less >= 0){
            cur_frm.doc.monthly_rental_payment = less
            refresh_field("monthly_rental_payment")
	    }
        else{
            cur_frm.doc.monthly_rental_payment = "0"
            refresh_field("monthly_rental_payment")
        }
    }
    if(cur_frm.doc.purchase_price_with_vat >= 1 && cur_frm.doc.purchase_price_with_vat <= 430.99){
        var div = (cur_frm.doc.purchase_price_with_vat * 15) / 100
        var de = cur_frm.doc.purchase_price_with_vat + div
        calculation_for_90d_sac(de)
    }            
    else if(cur_frm.doc.purchase_price_with_vat >= 431 && cur_frm.doc.purchase_price_with_vat <= 580.99){
        var div = (cur_frm.doc.purchase_price_with_vat * 12) / 100
        var de = cur_frm.doc.purchase_price_with_vat + div
        calculation_for_90d_sac(de)                  
    }
    else if(cur_frm.doc.purchase_price_with_vat >= 581){
        var div = (cur_frm.doc.purchase_price_with_vat * 10) / 100
        var de = cur_frm.doc.purchase_price_with_vat + div
        calculation_for_90d_sac(de)      
    }
}            

calculation_for_90d_sac = function(de){
    var deduc = de.toFixed(2)
    var str_deduc = deduc.toString()
    var slice_str_deduc = str_deduc.slice(-2)
    var int_slice_str_deduc = parseInt(slice_str_deduc)

    var floor = Math.floor(deduc)
    var str_floor = floor.toString();
    var slice_str_floor = str_floor.slice(-1)
    var int_str_floor = parseInt(slice_str_floor)

    var concade = slice_str_floor + "." + slice_str_deduc
    var float_concade = parseFloat(concade)


    if(float_concade >= 0.00 && float_concade <= 5.00){
      var minus = 5 - int_str_floor
      cur_frm.set_value("s90d_sac_price",(floor + minus))
      refresh_field("s90d_sac_price")
    }

    if(float_concade >= 5.01 && float_concade <= 9.99){
      var minus = 9 - int_str_floor
      cur_frm.set_value("s90d_sac_price",(floor + minus))
      refresh_field("s90d_sac_price")
    }      
}