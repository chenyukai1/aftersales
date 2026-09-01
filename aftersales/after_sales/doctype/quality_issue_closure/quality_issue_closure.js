frappe.ui.form.on("Quality Issue Closure", {
	refresh: function (frm) {
		// 评审通过后：标记完整闭环
		if (
			frm.doc.review_result === "通过" &&
			frm.doc.status !== "完整闭环" &&
			!frm.is_new()
		) {
			frm.add_custom_button(__("标记完整闭环"), function () {
				frm.call({
					method: "aftersales.after_sales.doctype.quality_issue_closure.quality_issue_closure.mark_complete",
					args: { closure: frm.doc.name },
					callback: function (r) {
						if (r.message) {
							frappe.show_alert({ message: __("状态：{0}", [r.message.status]), indicator: "green" });
							frm.reload_doc();
						}
					},
				});
			}).addClass("btn-primary");
		}
	},
});
