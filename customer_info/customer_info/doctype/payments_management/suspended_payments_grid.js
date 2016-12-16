{% include 'customer_info/customer_info/doctype/payments_management/payments_details.js' %};

suspended_payments = Class.extend({
	init:function(frm,agreement_data){
		this.agreement_data = agreement_data;
		this.init_for_render_payments();
	},
	init_for_render_payments:function(){
		var me = this;
		$(cur_frm.fields_dict.suspended_payments_grid.wrapper).append("<table width='100%>\
  		<tr>\
		    <td valign='top' width='100%'>\
		      <div id='suspended_payments_grid' style='width:100%;height:200px;''></div>\
		    	</td>\
  			</tr>\
		</table>");
		me.render_suspended_agreement();
	},
	render_suspended_agreement:function(){
		var me = this;
		var suspended_payments_grid;
		var buttonFormat_detail = function (row, cell, value, columnDef, dataContext) {
			return "<input type='button' value='Detail' agreement = "+dataContext['agreement_no']+" class='detail-suspended' style='height:20px;padding: 0px;width: 70px;'; />";    
		}
		/*var buttonFormat_suspension = function (row, cell, value, columnDef, dataContext) {
			var id = "mybutton" + String(row);
			if(dataContext['suspenison']){
				return "<input type='button' value = "+dataContext['suspenison']+" id= "+id+" class='suspenison' style='height:20px;padding: 0px;width: 70px;'; />";		    
			}
			else{
				return "<input type='button' value = 'Call/Commitment' id= "+id+" class='suspenison' style='height:20px;padding: 0px;width: 100px;'; />";		
			}
		}*/

		/*var late_fees_editable = function(row, cell, value, columnDef, dataContext){
			var id = "late_fee"+ String(row)
			console.log(dataContext['late_fees'],"dataContext['late_fees']")
			return "<a class='late_fees' value="+dataContext['late_fees']+">" + dataContext['late_fees'] + "</a>";
		}*/

		/*var campaign_discount = function(row, cell, value, columnDef, dataContext){
			var id = "campaign_discount"+ String(row)
			console.log(dataContext['campaign_discount'],"dataContext['campaign_discount']")
			if(dataContext['campaign_discount'].split("-")[3] == "Yes"){			
				return "<a class='campaign_discount' value="+dataContext['campaign_discount']+">" + dataContext['campaign_discount'].split("-")[0] + "</a>";
			}
			else{
				return "<a class='campaign_discount' value="+dataContext['campaign_discount']+">" + 0.00 + "</a>";
			}
		}*/

		me.suspended_columns = [
		    {id: "agreement_no", name: "Agreement No", field: "agreement_no",width: 80,toolTip: "Agreement No"},
		    {id: "agreement_period", name: "Agreement Period", field: "agreement_period",width: 80,toolTip: "Agreement Period"},
		    {id: "product", name: "Product", field: "product",width: 120,toolTip: "Product"},
		    {id: "number_of_payments", name: "# of Payments", field: "number_of_payments",width: 70,toolTip: "# of Payments"},
		    {id: "monthly_rental_payment", name: "Rental Payments", field: "monthly_rental_payment",width: 90,toolTip: "Rental Payments"},
		    {id: "current_due_date", name: "Current Due Date", field: "current_due_date",width: 90,toolTip: "Current Due Date"},
		    {id: "next_due_date", name: "Next Due Date", field: "next_due_date",width: 90,toolTip: "Next Due Date"},
		    {id: "payments_left", name: "Payments left", field: "payments_left",width: 70,toolTip: "Payments left"},
		    {id: "balance", name: "Balance", field: "balance",width: 70,toolTip: "Balance"},
		    {id: "late_fees", name: "Late Fees", field: "late_fees",width: 50,toolTip: "Late Fees"},//,formatter:late_fees_editable},
		    {id: "total_dues", name: "Total Dues", field: "total_dues",width: 50,toolTip: "Total Dues"},
		    {id: "Campaign discount", name: "Campaign discount", field: "campaign_discount",width: 50,toolTip: "Campaign discount"},//,formatter:campaign_discount},
		    {id: "payments_made", name: "Payments Made", field: "payments_made",width: 50,toolTip: "Payments Made"},
		    {id: "detail", name: "Detail", field: "detail",formatter: buttonFormat_detail,toolTip: "Detail"},
		    {id: "suspenison", name: "Call/Commitment", field: "suspenison"}//,formatter: buttonFormat_suspension,toolTip: "Call/Commitment"}
	  	];

	  	me.suspended_options = {
	    	enableCellNavigation: true,
	    	enableColumnReorder: false,
	  	};
	  	me.make_grid();
	},
	make_grid:function(){
		var me = this;
		console.log("inisde make_grid")
		var grid_data = [];
		/*var index = 0;*/
		for (var i = 0; i<me.agreement_data.list_of_agreement.length; i++) {
	          	grid_data[i] = {
	          	id : me.agreement_data.list_of_agreement[i][0],	
	          	/*serial:i,*/	
	            agreement_no: me.agreement_data.list_of_agreement[i][0],
	            agreement_period: me.agreement_data.list_of_agreement[i][1],
	            product: me.agreement_data.list_of_agreement[i][2],
	            number_of_payments: me.agreement_data.list_of_agreement[i][3],
	            monthly_rental_payment: me.agreement_data.list_of_agreement[i][4],
	            current_due_date: me.agreement_data.list_of_agreement[i][5],
	            next_due_date: me.agreement_data.list_of_agreement[i][6],
	            payments_left: me.agreement_data.list_of_agreement[i][7],
	            balance: me.agreement_data.list_of_agreement[i][8],
	            late_fees: me.agreement_data.list_of_agreement[i][9],
	            total_dues: me.agreement_data.list_of_agreement[i][10],
	            payments_made: me.agreement_data.list_of_agreement[i][11],
	            suspenison: me.agreement_data.list_of_agreement[i][12],
	            campaign_discount: me.agreement_data.list_of_agreement[i][13],
	        };
	    }

	    dataView_suspended = new Slick.Data.DataView();  

		suspended_payments_grid = new Slick.Grid("#suspended_payments_grid", dataView_suspended, me.suspended_columns, me.suspended_options);
	      
	    // for row header filters
	    var columnFilters = []
	    function filter(item) {
		    for (var columnId in columnFilters) {
		      if (columnId !== undefined && columnFilters[columnId] !== "") {
		        var c = suspended_payments_grid.getColumns()[suspended_payments_grid.getColumnIndex(columnId)];
		        if (item[c.field] != columnFilters[columnId]) {
		          return false;
		        }
		      }
		    }
	    	return true;
	  	}	

	    dataView_suspended.onRowCountChanged.subscribe(function (e, args) {
	      suspended_payments_grid.updateRowCount();
	      suspended_payments_grid.render();
	    });

	    dataView_suspended.onRowsChanged.subscribe(function (e, args) {
	      suspended_payments_grid.invalidateRows(args.rows);
	      suspended_payments_grid.render();
	    });

	    $(suspended_payments_grid.getHeaderRow()).delegate(":input", "change keyup", function (e) {
	      var columnId = $(this).data("columnId");
	      if (columnId != null) {
	        columnFilters[columnId] = $.trim($(this).val());
	        dataView_suspended.refresh();
	      }
	    });

	    suspended_payments_grid.onHeaderRowCellRendered.subscribe(function(e, args) {
	        $(args.node).empty();
	        $("<input type='text'>")
	           .data("columnId", args.column.id)
	           .val(columnFilters[args.column.id])
	           .appendTo(args.node);
	    });
	    suspended_payments_grid.init();
	    //dataView.setFilter(filter);
	   	
	   	//

	    dataView_suspended.beginUpdate();
	    dataView_suspended.setItems(grid_data);
	    dataView_suspended.endUpdate();


		suspended_payments_grid.onClick.subscribe(function (e, args) {
	        var item = dataView_suspended.getItem(args.row);
	        if($(e.target).hasClass("detail-suspended")) {
	            index = parseInt(index) + 1;
	        	 var flag = "Suspended Agreement"
	        	new Payments_Details(item, index,flag)
	        }
	        /*if($(e.target).hasClass("suspenison")) {
	        	var id = $(e.target).attr('id')
	        	//new manage_suspenison(id,item)
	        	new call_commit(id,item)
	        }
	        if($(e.target).hasClass("late_fees")) {
	        	var id = $(e.target).attr('id')
	        	//new manage_suspenison(id,item)
	        	new edit_late_fees(id,item)
	        }
	        if($(e.target).hasClass("campaign_discount")) {
	        	var id = $(e.target).attr('id')
	        	//new manage_suspenison(id,item)
	        	new edit_campaign_discount(id,item)
	        }*/
	    });
	}
})