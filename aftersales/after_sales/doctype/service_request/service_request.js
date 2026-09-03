frappe.ui.form.on("Service Request", {
	refresh: function (frm) {
		frm.trigger("update_status_help");
		// 新建登记：反馈日期默认今天，减少人工填写
		if (frm.is_new() && !frm.doc.feedback_date) {
			frm.set_value("feedback_date", frappe.datetime.get_today());
		}
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
				// 车辆带出客户/对接人（空才覆盖），再联动收货信息
				if (v.customer && !frm.doc.customer) {
					frm.set_value("customer", v.customer);
				}
				if (v.customer_contact && !frm.doc.contact_person) {
					frm.set_value("contact_person", v.customer_contact);
				}
				if (frm.doc.customer) {
					fill_ship_from_customer(frm, frm.doc.customer);
				}
				frappe.show_alert({ message: "已带出车辆信息（车型/出厂日期/客户）", indicator: "green" });
			},
		});
	},

	customer: function (frm) {
		if (!frm.doc.customer) return;
		// 客户主档带出对接人，并预填配件行收件信息（空行才填）
		fill_ship_from_customer(frm, frm.doc.customer);
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
				const info = r.message;
				frappe.model.set_value(cdt, cdn, "old_part_name", info.part_name || "");
				frappe.model.set_value(cdt, cdn, "fault_part_supplier", info.supplier || "");
				frappe.model.set_value(cdt, cdn, "claim_requirement", info.claim_requirement || "");
				// 联动1：索赔需求=需提供旧件 → 坏件寄回自动"是"，其余"否"
				if (info.claim_requirement) {
					frappe.model.set_value(cdt, cdn, "need_return", info.claim_requirement === "需提供旧件" ? "是" : "否");
				}
				// 联动2：三包新件未填时默认与老件同码（同款换新，可再修改）
				if (!frappe.model.get_value(cdt, cdn, "new_part_code")) {
					frappe.model.set_value(cdt, cdn, "new_part_code", row.old_part_code);
				}
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

// 客户主档 → 对接人/收件人/电话/地址（预填主表 + 配件行发货信息，仅空值填充）
function fill_ship_from_customer(frm, customer) {
	frm.call({
		method: "aftersales.after_sales.doctype.service_request.service_request.fetch_customer_ship_info",
		args: { customer: customer },
		callback: function (r) {
			const info = (r.message || {});
			if (!info.found) {
				if (info.message) frappe.show_alert({ message: info.message, indicator: "orange" });
				return;
			}
			if (info.contact_person && !frm.doc.contact_person) {
				frm.set_value("contact_person", info.contact_person);
			}
			if (frm.doc.parts && frm.doc.parts.length) {
				frm.doc.parts.forEach((row) => {
					if (!row.recipient && info.recipient) {
						frappe.model.set_value(row.doctype, row.name, "recipient", info.recipient);
					}
					if (!row.phone && info.phone) {
						frappe.model.set_value(row.doctype, row.name, "phone", info.phone);
					}
					if (!row.address && info.address) {
						frappe.model.set_value(row.doctype, row.name, "address", info.address);
					}
				});
			}
			frappe.show_alert({ message: "已带出客户收货信息（对接人/收件人/电话/地址）", indicator: "green" });
		},
	});
}

function calc_claim_qty(frm, cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	const erp = row.erp_qty || 0;
	const gift = row.gift_qty || 0;
	frappe.model.set_value(cdt, cdn, "actual_claim_qty", erp - gift);
}
