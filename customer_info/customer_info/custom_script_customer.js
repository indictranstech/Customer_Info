frappe.ui.form.on("Customer","onload",function(frm){
    if(cur_frm.doc.customer_type == "Individual"){
        cur_frm.set_df_property("first_name", "reqd",true);
    }
})

frappe.ui.form.on("Customer","customer_type",function(frm){
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
})

frappe.ui.form.on("Customer","first_name",function(frm){
    if(cur_frm.doc.customer_type == "Individual"){
        cur_frm.doc.customer_name = cur_frm.doc.first_name
        refresh_field("customer_name")
    } 
    if(cur_frm.doc.first_name){
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
})

frappe.ui.form.on("Customer","last_name",function(frm){
    if(cur_frm.doc.customer_type == "Individual"){
        cur_frm.doc.customer_name = cur_frm.doc.first_name +" "+ cur_frm.doc.last_name
        refresh_field("customer_name")
    }
})

frappe.ui.form.on("Customer","company_title",function(frm){
    if(cur_frm.doc.customer_type == "Company"){
        cur_frm.doc.customer_name = cur_frm.doc.company_title
        refresh_field("customer_name")
    }
})

frappe.ui.form.on("Customer","birthdate",function(frm){
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
        var cur = new Date();
        var diff = cur-birthdate; // This is the difference in milliseconds
        var age = Math.floor(diff/31536000000); // Divide by 1000*60*60*24*365
        cur_frm.doc.age = age + " " +" Years"
        refresh_field('age');
    }
    else{
        cur_frm.doc.age = ""
        refresh_field('age')
    } 
})