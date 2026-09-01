frappe.ui.form.on("Old Part Recall", {
	refresh: function (frm) {
		if (!frm.is_new() && frm.doc.status !== "已追回" && frm.doc.status !== "超时终止") {
			frm.add_custom_button(__("登记坏件到货"), function () {
				frm.call({
					method: "aftersales.after_sales.doctype.old_part_recall.old_part_recall.mark_bad_part_arrived",
					args: { recall: frm.doc.name },
					callback: function (r) {
						if (r.message) {
							frappe.show_alert({ message: __("坏件已登记到货，状态：{0}", [r.message.status]), indicator: "green" });
							frm.reload_doc();
						}
					},
				});
			}).addClass("btn-primary");
		}
	},
});
