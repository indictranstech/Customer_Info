# -*- coding: utf-8 -*-
from __future__ import unicode_literals

app_name = "customer_info"
app_title = "Customer Info"
app_publisher = "indictrans"
app_description = "Details Of Customers"
app_icon = "icon-truck"
app_color = "blue"
app_email = "jitendra.k@indictranstech.com"
app_version = "0.0.1"
app_license = "GNU General Public License"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/customer_info/css/customer_info.css"
# app_include_js = "/assets/customer_info/js/customer_info.js"

# include js, css files in header of web template
# web_include_css = "/assets/customer_info/css/customer_info.css"
# web_include_js = "/assets/customer_info/js/customer_info.js"

# Home Pages
# ----------
# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "customer_info.utils.get_home_page"

# Add Fixtures
fixtures =['Custom Field', "Property Setter","Custom Script","Letter Head","Print Format"]

doctype_js = {
    "Customer":["custom_scripts/customer.js"],
    "Item":["custom_scripts/item.js"],
    "Brand":["custom_scripts/brand.js"]
}

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "customer_info.install.before_install"
# after_install = "customer_info.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "customer_info.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events	
# doc_events = {
# 	"Contact": {
# 		"validate":"",
		# "on_update": "method",
		# "on_cancel": "method",
		# "on_trash": "method"
# 	}
# }
doc_events = {
	"Item": {
		"on_update": "customer_info.customer_info.custom_item.product_status_change"
	},
	"Customer":{
		"after_insert":"customer_info.customer_info.custom_item.add_comment_for_customer_creation",
		"validate":"customer_info.customer_info.custom_item.add_comment_for_change_receivables"
	},
	"Product Category": {
		"validate": "customer_info.customer_info.doctype.product_category.product_category.new_item_group"
	},
	# "Brand":{
	# 	"before_insert":"customer_info.customer_info.doctype.product_category.product_category.make_category_and_brand_name"	
	# }	
}
# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"customer_info.customer_info.doctype.customer_agreement.customer_agreement.reset_contact_result_of_sent_sms"
	],
	"hourly": [
		"customer_info.customer_info.doctype.customer_agreement.customer_agreement.payments_done_by_scheduler"			
	]
}

# scheduler_events = {
# 	"all": [
# 		"customer_info.tasks.all",
# 	],
# 	"daily": [
# 		"customer_info.tasks.daily"
# 	],
# 	"hourly": [
# 		"customer_info.tasks.hourly"
# 	],
# 	"weekly": [
# 		"customer_info.tasks.weekly"
# 	]
# 	"monthly": [
# 		"customer_info.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "customer_info.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "customer_info.event.get_events"
# }

