// Service Request 列表增强：一键导出 Excel + 移动端友好
frappe.listview_settings["Service Request"] = {
	onload: function (listview) {
		listview.page.add_inner_button(__("导出 Excel"), function () {
			window.location.href =
				"/api/method/aftersales.after_sales.api.export_service_requests";
		});
	},
};
