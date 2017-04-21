frappe.ui.form.on("Customer",{
    refresh:function(frm){
        $("[data-fieldname='customer_name']").hide()
        setTimeout(function(){ $('input[data-fieldname="company_phone_1"]').attr("placeholder","+370...");
        $('input[data-fieldname="company_phone_2"]').attr("placeholder","+370..."); }, 100);
        if(!cur_frm.doc.__islocal){
            cur_frm.add_custom_button(__('Payments Management'),function(){
                go_to_payments_management();
            });
            $($(".btn-xs")[0]).attr("data-fieldname","payments_management")
        }
        if(frappe.route_options){
            if(frappe.route_options["from_late_and_future"]  == "yes"){
                frappe.route_options = null;
                $("[data-fieldname='payments_management']").click()
            }
        }
    },        
    onload:function(frm){
        if(cur_frm.doc.customer_type == "Individual"){
            cur_frm.set_df_property("first_name", "reqd",true);
        }
        this.get_url(frm)
    },
    customer_type:function(frm){
        if(cur_frm.doc.customer_type == "Company"){
           cur_frm.set_df_property("first_name", "reqd",false);
           cur_frm.set_df_property("company_title", "reqd",true);
           cur_frm.doc.customer_group = "Commercial"
           refresh_field('customer_group')      
        }
        if(cur_frm.doc.customer_type == "Individual"){
           cur_frm.set_df_property("first_name", "reqd",true);
           cur_frm.set_df_property("company_title", "reqd",false);
           cur_frm.doc.customer_group = "Individual"
           refresh_field('customer_group')      
        }    
    },
    company_title: function(frm){
        if(cur_frm.doc.customer_type == "Company" && cur_frm.doc.company_title){
            cur_frm.doc.customer_name = cur_frm.doc.company_title
            refresh_field("customer_name")
        }
    },
    first_name: function(frm){
        if(cur_frm.doc.customer_type == "Individual"){
            cur_frm.doc.customer_name = cur_frm.doc.first_name
            refresh_field("customer_name")
            var n = cur_frm.doc.first_name;    
            if(n.slice(-1) == "s" || n.slice(-1) == "S"){
                cur_frm.doc.gender = "M"
                refresh_field("gender")
            }
            else{
                cur_frm.doc.gender = "F"
                refresh_field("gender")
            }
        }
        else{
            cur_frm.doc.gender = ""
            refresh_field('gender')
        }    
    },
    last_name: function(frm){
        if(cur_frm.doc.customer_type == "Individual" && cur_frm.doc.first_name){
            cur_frm.doc.customer_name = cur_frm.doc.first_name +" "+ cur_frm.doc.last_name
            refresh_field("customer_name")
        }
    },
    birthdate: function(frm){
        if(cur_frm.doc.birthdate){
            var d = moment().format('YYYY-MM-DD')
            var current_date = new Date(d)
            var b_date = new Date(cur_frm.doc.birthdate)
            if(b_date >= current_date){
                msgprint(__("'Birth Date' Not Greater Or Equal To Current Date"))
                cur_frm.doc.birthdate = ""
                refresh_field('birthdate')
            }
        } 
        if(cur_frm.doc.birthdate){
            var birthdate = new Date(cur_frm.doc.birthdate)
            var current_date = new Date();
            var diff = current_date - birthdate; // This is the difference in milliseconds
            var age = Math.floor(diff/31536000000); // Divide by 1000*60*60*24*365
            cur_frm.doc.age = age + " " +" Years"
            refresh_field('age');
        }
        else{
            cur_frm.doc.age = ""
            refresh_field('age')
        }    
    },
    customer_is_interested_in: function(frm){
        this.get_url(frm)
    },
    prersonal_code: function(frm){
        valid_personal_code("Personal Code");
    },
    company_code:function(frm){
        valid_personal_code("Company Code");
    }
})




get_url = function(frm){
    if(cur_frm.doc.customer_is_interested_in){
        var html='';
        html+=repl('<div class="row">\
                    <label class="control-label" style="margin-left: 16px;">Visit URL</label></div>\
                    <div class="row">\
                    <a target="_blank" href=%(link)s style="margin-left:26px">%(show_link)s</a>\
                    </div>', {
                        link: cur_frm.doc.customer_is_interested_in,
                        show_link: cur_frm.doc.customer_is_interested_in.slice(0,40)

                    })

        $(cur_frm.fields_dict.click_here.wrapper).html(html);
    }
}


go_to_payments_management = function(frm){
    frappe.model.open_mapped_doc({
        method: "customer_info.customer_info.doctype.payments_management.payments_management.get_payments_management",
        frm: cur_frm
    })
}

function valid_personal_code(code_label){
    if(cur_frm.doc.customer_type == "Individual"){
        var tempVal = cur_frm.doc.prersonal_code;
        var regex = !/^[0-9]{1,11}$/.test(tempVal)
        var digits = 11
    }
    else if(cur_frm.doc.customer_type == "Company"){
        var tempVal = cur_frm.doc.company_code;
        var regex = !/^[0-9]{1,9}$/.test(tempVal)
        var digits = 7
    }

    if(!/^\d+$/.test(tempVal)){
        console.log("code_label",code_label)
        code_label == "Company Code" ? msgprint("Company code should consist of 7 or 9 digits"):
        msgprint(__("Enter Digits From [0-"+digits+"] Only"))
    }
    else if (regex){
        code_label == "Company Code" ? msgprint(__(code_label+" Length Not Greater Than 9 Digits")):
        msgprint(__(code_label+" Length Not Greater Than "+digits+" Digits"))    
    }
    else if (tempVal.length < digits) {
        code_label == "Company Code" ? msgprint(__(code_label+" Should Be Of 7 or "+digits+" Digits")):
        msgprint(__(code_label+" Should Be Of "+digits+" Digits"))
    }
    else if (tempVal.length == 8 && code_label == "Company Code") {
        msgprint(code_label+" should be of 7 digits or 9 digits")
    }
}