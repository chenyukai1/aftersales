"""Service Request（售后登记）Controller：自动带出、公式计算、状态机。

公式字段规则（对齐 STAXX 内销售后日志填写说明）：
- 车辆铭牌 → 车型 / 特殊配件跟踪 / 特殊配置 / 出厂日期（数据源：Vehicle Delivery，仅杭叉订单）
- 出厂天数 = 今日 - 出厂日期；售后波段 = A(≤3月) / B(4-9月) / C(≥10月)
- 老/新配件编码 → 名称 / 故障部件供应商 / 索赔需求（数据源：Spare Part）
- 本单实际索赔数量 = ERP发货数量 - 本单赠送数量
- 发货日期 = 反馈日期；索赔月份/周数、出厂月份按日期取
- 状态（客户）：已接单 → 已发货 → 完成；状态（部门）：索赔件已发 → 坏件已退回 → 完成
"""
import frappe
from frappe.model.document import Document
from frappe.utils import today, getdate, add_days, formatdate


class ServiceRequest(Document):
    def validate(self):
        self.calc_vehicle_fields()
        self.calc_stats()
        self.calc_parts()

    def on_submit(self):
        """提交后：自动创建索赔单（草稿）+ 旧件追回提醒 + 批量隐患自动发起质量闭环 + 改进-再发比对。"""
        self.create_claim_order()
        self.create_recalls()
        self.trigger_quality_closure()
        self.check_recurrence()

    def check_recurrence(self):
        """改进-再发比对：命中改进记录且在改进日期后出厂 → 记录评论提醒。"""
        from aftersales.after_sales.batch_issue_monitor import check_improvement_recurrence

        try:
            result = check_improvement_recurrence(self.name)
            for r in result.get("recurrences", []):
                self.add_comment(
                    "Info",
                    f"⚠️ 改进-再发提醒：{r['part_code']} 在 {r['improvement_date']} 已改进"
                    f"（{r['desc'][:30]}），本次再发建议闭环定性为「改进项-再发」",
                )
        except Exception:
            frappe.log_error(f"改进-再发比对失败：{self.name}", "after_sales.recurrence")

    def trigger_quality_closure(self):
        """售后类型=批量隐患 → 自动创建质量闭环（终稿 c 类）。"""
        if self.after_sale_type != "批量隐患":
            return
        from aftersales.after_sales.doctype.quality_issue_closure.quality_issue_closure import (
            create_from_service_request,
        )

        try:
            create_from_service_request(self.name)
        except Exception:
            frappe.log_error(f"自动创建质量闭环失败：{self.name}", "after_sales.closure")

    def create_claim_order(self):
        """无需录 ERP（erp_recorded=——）场景跳过。"""
        if self.erp_recorded == "——":
            return
        parts = [p for p in self.parts if p.new_part_code]
        if not parts:
            return
        if frappe.db.exists("Claim Order", {"service_request": self.name}):
            return
        co = frappe.get_doc(
            {
                "doctype": "Claim Order",
                "service_request": self.name,
                "customer": self.customer,
                "claim_date": self.feedback_date,
                "status": "草稿",
                "items": [
                    {
                        "part_code": p.new_part_code,
                        "part_name": p.new_part_name,
                        "erp_item": frappe.db.get_value(
                            "Spare Part", {"k3_code": p.new_part_code}, "erp_item"
                        )
                        or "",
                        "qty": p.erp_qty or 1,
                        "supplier": p.fault_part_supplier,
                        "claim_requirement": p.claim_requirement,
                    }
                    for p in parts
                ],
            }
        )
        co.insert(ignore_permissions=True)

    def create_recalls(self):
        """配件「坏件需要寄回=是」→ 自动创建旧件追回（待提醒）。"""
        for p in self.parts:
            if p.need_return != "是":
                continue
            if frappe.db.exists(
                "Old Part Recall",
                {"service_request": self.name, "part_code": p.new_part_code},
            ):
                continue
            frappe.get_doc(
                {
                    "doctype": "Old Part Recall",
                    "service_request": self.name,
                    "chassis_no": self.chassis_no,
                    "customer": self.customer,
                    "part_code": p.new_part_code,
                    "part_name": p.new_part_name,
                    "supplier": p.fault_part_supplier,
                    "ship_date": p.ship_date or self.feedback_date,
                    "trigger_type": "坏件需寄回",
                    "status": "待提醒",
                }
            ).insert(ignore_permissions=True)

    # ---------- 车辆信息带出与公式 ----------
    def calc_vehicle_fields(self):
        if not self.chassis_no:
            return
        vehicle = frappe.db.get_value(
            "Vehicle Delivery",
            {"chassis_no": self.chassis_no},
            ["hangcha_model", "special_config", "delivery_date", "shibeida_model"],
            as_dict=True,
        )
        if vehicle:
            if not self.vehicle_model:
                self.vehicle_model = vehicle.hangcha_model or vehicle.shibeida_model
            if not self.special_config:
                self.special_config = vehicle.special_config or ""
            if not self.manufacture_date:
                self.manufacture_date = vehicle.delivery_date
        # 出厂天数 & 波段
        if self.manufacture_date:
            days = (getdate(today()) - getdate(self.manufacture_date)).days
            self.days_since_manufacture = days
            if days <= 90:
                self.after_sale_band = "A"
            elif days <= 270:
                self.after_sale_band = "B"
            else:
                self.after_sale_band = "C"
        # 出厂月份
        if self.manufacture_date:
            self.manufacture_month = formatdate(self.manufacture_date, "YYYY-MM")

    def calc_stats(self):
        # 索赔月份 / 周数（按反馈日期）
        if self.feedback_date:
            self.claim_month = formatdate(self.feedback_date, "YYYY-MM")
            self.claim_week = self._iso_week(self.feedback_date)
        # 状态（客户）：公式计算（Select 字段无默认值会被自动填充首项，故直接赋值覆盖）
        if self.feedback_date:
            if self._all_parts_shipped():
                self.customer_status = "完成"
            elif self.erp_recorded == "OK":
                self.customer_status = "已发货"
            else:
                self.customer_status = "已接单"
        # 状态（部门）
        if self.feedback_date:
            if self._all_returned_to_factory():
                self.department_status = "完成"
            elif self._any_part_shipped():
                self.department_status = "索赔件已发"
            else:
                self.department_status = "索赔件已发"

    def calc_parts(self):
        for row in self.parts:
            # 老配件编码 → 名称 / 供应商 / 索赔需求（公式带出，直接覆盖）
            if row.old_part_code:
                sp = frappe.db.get_value(
                    "Spare Part",
                    {"k3_code": row.old_part_code},
                    ["part_name", "supplier", "claim_requirement"],
                    as_dict=True,
                )
                if sp:
                    row.old_part_name = sp.part_name or ""
                    row.fault_part_supplier = sp.supplier or ""
                    row.claim_requirement = sp.claim_requirement or ""
                else:
                    row.old_part_name = row.old_part_name or "需完善配件价格表"
            # 新配件编码 → 名称
            if row.new_part_code:
                sp = frappe.db.get_value(
                    "Spare Part",
                    {"k3_code": row.new_part_code},
                    ["part_name"],
                    as_dict=True,
                )
                row.new_part_name = (sp.part_name if sp else "需完善配件价格表") or "需完善配件价格表"
                row.erp_new_code = row.new_part_code
            # 实际索赔数量 = ERP发货 - 赠送
            if row.erp_qty is not None and row.gift_qty is not None:
                row.actual_claim_qty = int(row.erp_qty or 0) - int(row.gift_qty or 0)
            # 发货日期 = 反馈日期
            if self.feedback_date and not row.ship_date:
                row.ship_date = self.feedback_date

    # ---------- 内部工具 ----------
    def _all_parts_shipped(self):
        if not self.parts:
            return False
        return all(row.tracking_no for row in self.parts)

    def _any_part_shipped(self):
        return any(row.tracking_no for row in self.parts)

    def _all_returned_to_factory(self):
        if not self.parts:
            return False
        return all(row.supplier_claim_date for row in self.parts)

    @staticmethod
    def _iso_week(date_str):
        try:
            return str(getdate(date_str).isocalendar()[1])
        except Exception:
            return ""


@frappe.whitelist()
def fetch_vehicle_info(chassis_no):
    """前端调用：按车辆铭牌带出车辆信息。"""
    row = frappe.db.get_value(
        "Vehicle Delivery",
        {"chassis_no": chassis_no},
        ["hangcha_model", "shibeida_model", "special_config", "delivery_date"],
        as_dict=True,
    )
    if not row:
        return {"found": False, "message": "未找到该铭牌的车辆发货记录，请人工补录"}
    days = (getdate(today()) - getdate(row.delivery_date)).days if row.delivery_date else None
    band = "A" if days and days <= 90 else ("B" if days and days <= 270 else ("C" if days is not None else None))
    return {
        "found": True,
        "vehicle_model": row.hangcha_model or row.shibeida_model,
        "special_config": row.special_config or "",
        "manufacture_date": row.delivery_date,
        "days_since_manufacture": days,
        "after_sale_band": band,
    }


@frappe.whitelist()
def fetch_part_info(part_code):
    """前端调用：按配件编码带出名称/供应商/索赔需求。"""
    row = frappe.db.get_value(
        "Spare Part",
        {"k3_code": part_code},
        ["part_name", "supplier", "claim_requirement"],
        as_dict=True,
    )
    if not row:
        return {"found": False, "message": "未找到该编码的配件，请先在配件主档维护（或提示完善配件价格表）"}
    return {"found": True, "part_name": row.part_name, "supplier": row.supplier, "claim_requirement": row.claim_requirement}
