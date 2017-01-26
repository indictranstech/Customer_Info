frappe.pages['import_payments'].on_page_load = function(wrapper) {
	payment_import_tool = new PaymentImportTool(wrapper);
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
			args: {
				method: 'customer_info.customer_info.page.import_payments.import_payments.upload',
			},
			onerror: function(r) {
				me.onerror(r);
			},
			callback: function(attachment, r) {
				if(r.message.error) {
					me.onerror(r);
				} else {
					r.messages = ["<h5 style='color:green'>" + __("Import Successful!") + "</h5>"].
						concat(r.message.messages)
					me.write_messages(r.messages);
				}
			},
			is_private: true
		});
	},
	write_messages: function(data) {
		this.page.main.find(".import-log").removeClass("hide");
		var parent = this.page.main.find(".import-log-messages").empty();
		// TODO render using template!
		for (var i=0, l=data.length; i<l; i++) {
			var v = data[i];
			var $p = $('<p></p>').html(frappe.markdown(v)).appendTo(parent);
			if(v.substr(0,5)=='Error') {
				$p.css('color', 'red');
			} else if(v.substr(0,8)=='Inserted') {
				$p.css('color', 'green');
			} else if(v.substr(0,7)=='Updated') {
				$p.css('color', 'green');
			} else if(v.substr(0,5)=='Valid') {
				$p.css('color', '#777');
			}
		}
	},
	onerror: function(r) {
		if(r.message) {
			// bad design: moves r.messages to r.message.messages
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

			r.messages = ["<h4 style='color:red'>" + __("Import Failed") + "</h4>"]
				.concat(r.messages);

			r.messages.push("Please correct and import again.");

			frappe.show_progress(__("Importing"), 1, 1);

			this.write_messages(r.messages);
		}
	}
})