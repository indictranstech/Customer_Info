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

// frappe.ui.form.on("Customer","customer_is_interested_in",function(frm){
//     if (cur_frm.doc.customer_is_interested_in) {
//         $(frm.fields_dict['click_here'].wrapper)
//             .html(repl('<div class="row">\
//                 <label class="control-label" style="margin-left: 16px;">Visit URL</label></div>\
//                 <div class="row">\
//                 <a target="_blank" href=%(link)s style="margin-left:26px">%(link)s%0A</a>%0A\
//                 </div>', {
//                     link: cur_frm.doc.customer_is_interested_in
//                 }))
//         refresh_field("click_here")                                        
//     }
//  /*   cur_frm.doc.set_df_property("customer_is_interested_in","hidden",1)*/
// })

frappe.ui.form.on("Customer", "customer_is_interested_in", function(frm,doctype,name) {
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
});
frappe.ui.form.on("Customer", "onload", function(frm,doctype,name) {
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
});


/*get_customer_is_interested_in = function(frm){
    if(cur_frm.doc.customer_is_interested_in.length > 40){
        return cur_frm.doc.customer_is_interested_in.slice(0,40)
    }
    else{
        return cur_frm.doc.customer_is_interested_in
    }
}*/