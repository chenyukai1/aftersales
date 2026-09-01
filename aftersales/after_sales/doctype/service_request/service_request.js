frappe.ui.form.on("Service Request", {
	refresh: function (frm) {
		frm.trigger("update_status_help");
		// 已提交且未创建闭环时，可人工发起质量闭环（覆盖非批量隐患场景）
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__("发起质量闭环"), function () {
				frappe.prompt(
					[
						{
							label: __("问题定性"),
							fieldname: "classification",
							fieldtype: "Select",
							options: [
								"安全法规类",
								"设计缺陷",
								"一周内新增≥3起（批量隐患）",
								"新故障现象",
								"新车型验证期问题（12个月）",
								"改进项-再发",
							],
							reqd: 1,
						},
					],
					function (values) {
						frm.call({
							method: "aftersales.after_sales.doctype.quality_issue_closure.quality_issue_closure.create_from_service_request",
							args: { service_request: frm.doc.name, classification: values.classification },
							callback: function (r) {
								if (r.message && r.message.created) {
									frappe.show_alert({ message: __("质量闭环已创建：{0}", [r.message.closure]), indicator: "green" });
								} else {
									frappe.show_alert({ message: r.message && r.message.message, indicator: "orange" });
								}
							},
						});
					},
					__("发起质量闭环"),
					__("创建")
				);
			}).addClass("btn-primary");
		}
	},

	chassis_no: function (frm) {
		if (!frm.doc.chassis_no) return;
		frm.call({
			method: "aftersales.after_sales.doctype.service_request.service_request.fetch_vehicle_info",
			args: { chassis_no: frm.doc.chassis_no },
			callback: function (r) {
				if (!r.message || !r.message.found) {
					frappe.show_alert({ message: (r.message && r.message.message) || "未找到车辆记录", indicator: "orange" });
					return;
				}
				const v = r.message;
				frm.set_value("vehicle_model", frm.doc.vehicle_model || v.vehicle_model);
				frm.set_value("special_config", frm.doc.special_config || v.special_config || "");
				frm.set_value("manufacture_date", frm.doc.manufacture_date || v.manufacture_date);
				frm.set_value("days_since_manufacture", v.days_since_manufacture);
				frm.set_value("after_sale_band", v.after_sale_band);
				if (v.manufacture_date) {
					frm.set_value("manufacture_month", v.manufacture_date.substring(0, 7));
				}
				frappe.show_alert({ message: "已带出车辆信息（车型/出厂日期）", indicator: "green" });
			},
		});
	},

	feedback_date: function (frm) {
		if (frm.doc.feedback_date) {
			frm.set_value("claim_month", frm.doc.feedback_date.substring(0, 7));
		}
	},

	update_status_help: function (frm) {
		// 状态字段为公式自动计算，禁用手动编辑提示（保留覆盖能力）
	},
});

frappe.ui.form.on("Service Part Item", {
	old_part_code: function (frm, cdt, cdn) {
		const row = frappe.get_doc(cdt, cdn);
		if (!row.old_part_code) return;
		frm.call({
			method: "aftersales.after_sales.doctype.service_request.service_request.fetch_part_info",
			args: { part_code: row.old_part_code },
			callback: function (r) {
				if (!r.message || !r.message.found) {
					frappe.model.set_value(cdt, cdn, "old_part_name", "需完善配件价格表");
					return;
				}
				frappe.model.set_value(cdt, cdn, "old_part_name", r.message.part_name || "");
				frappe.model.set_value(cdt, cdn, "fault_part_supplier", r.message.supplier || "");
				frappe.model.set_value(cdt, cdn, "claim_requirement", r.message.claim_requirement || "");
			},
		});
	},

	new_part_code: function (frm, cdt, cdn) {
		const row = frappe.get_doc(cdt, cdn);
		if (!row.new_part_code) return;
		frm.call({
			method: "aftersales.after_sales.doctype.service_request.service_request.fetch_part_info",
			args: { part_code: row.new_part_code },
			callback: function (r) {
				if (!r.message || !r.message.found) {
					frappe.model.set_value(cdt, cdn, "new_part_name", "需完善配件价格表");
					return;
				}
				frappe.model.set_value(cdt, cdn, "new_part_name", r.message.part_name || "");
				frappe.model.set_value(cdt, cdn, "erp_new_code", row.new_part_code);
			},
		});
	},

	erp_qty: function (frm, cdt, cdn) {
		calc_claim_qty(frm, cdt, cdn);
	},
	gift_qty: function (frm, cdt, cdn) {
		calc_claim_qty(frm, cdt, cdn);
	},
});

function calc_claim_qty(frm, cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	const erp = row.erp_qty || 0;
	const gift = row.gift_qty || 0;
	frappe.model.set_value(cdt, cdn, "actual_claim_qty", erp - gift);
}
