frappe.ui.form.on("Claim Order", {
	refresh: function (frm) {
		if (frm.doc.status === "草稿" && frm.doc.items && frm.doc.items.length) {
			frm.add_custom_button(__("生成出库单"), function () {
				frm.call({
					method: "aftersales.after_sales.doctype.claim_order.claim_order.make_delivery_note",
					args: { claim_order: frm.doc.name },
					callback: function (r) {
						if (r.message) {
							frappe.show_alert({
								message: __("出库单已生成：{0}", [r.message.delivery_note]),
								indicator: "green",
							});
							frm.reload_doc();
						}
					},
				});
			}).addClass("btn-primary");
		}
	},
});
