frappe.ui.form.on("Claim List", {
	refresh: function (frm) {
		if (frm.is_new()) {
			frm.add_custom_button(__("生成上月清单"), function () {
				frm.call({
					method: "aftersales.after_sales.doctype.claim_list.claim_list.generate_monthly_claim_list",
					callback: function (r) {
						if (r.message) {
							frappe.show_alert({
								message: __("清单已生成：{0} 项 / {1} 家供应商", [r.message.item_count, r.message.supplier_count]),
								indicator: "green",
							});
						}
					},
				});
			}).addClass("btn-primary");
		}
	},
});
