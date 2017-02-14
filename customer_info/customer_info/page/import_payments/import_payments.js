frappe.pages['import_payments'].on_page_load = function(wrapper) {
	payment_import_tool = new PaymentImportTool(wrapper);
	frappe.breadcrumbs.add("Customer Info");
}

PaymentImportTool = Class.extend({
	init: function(parent) {
		this.page = frappe.ui.make_app_page({
			parent: parent,
			title: __("Payments Import Tool"),
			single_column: true
		});
		this.make();
		this.make_upload();
	},
	make: function() {
		var me = this;
		$(frappe.render_template("import_payments", this)).appendTo(this.page.main);
	},
	make_upload: function() {
		var me = this;
		frappe.upload.make({
			parent: this.page.main.find(".upload-area"),
			btn: this.page.main.find(".btn-import"),
			get_params: function() {
				return {
					update_due_date: me.page.main.find('[name="update_due_date"]').prop("checked")
				}
			},
			args: {
				method: 'customer_info.customer_info.page.import_payments.import_payments.upload',
			},
			callback: function(attachment, r) {
				me.page.main.find(".import-log").removeClass("hide");
				var parent = me.page.main.find(".import-log-messages").empty();
				if(!r.messages) r.messages = [];
				// replace links if error has occured
				if(r.exc || r.error) {
					r.messages = $.map(r.message.messages, function(v) {
						var msg = v.replace("Inserted", "Valid")
							.replace("Updated", "Valid").split("<");
						if (msg.length > 1) {
							v = msg[0] + (msg[1].split(">").slice(-1)[0]);
						} else {
							v = msg[0];
						}
						return v;
					});

					r.messages = ["<h4 style='color:red'>"+__("Import Failed!")+"</h4>"]
						.concat(r.messages)
				} else {
					r.messages = ["<h4 style='color:green'>"+__("Import Successful!")+"</h4>"].
						concat(r.message.messages)
				}
				console.log(r.messages)
				$.each(r.messages, function(i, v) {

					var $p = $('<p>').html(v).appendTo(parent);
					if(v.substr(0,5)=='Error') {
						$p.css('color', 'red');
					} else if(v.substr(0,8)=='Inserted') {
						$p.css('color', 'green');
					} else if(v.substr(0,7)=='Updated') {
						$p.css('color', 'green');
					} else if(v.substr(0,5)=='Valid') {
						$p.css('color', '#777');
					}
				});
			},
			is_private: false
		});
	}
})