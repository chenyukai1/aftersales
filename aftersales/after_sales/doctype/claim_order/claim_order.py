"""Claim Order（索赔单）Controller：生成 ERP 出库单（Delivery Note）。

业务规则（对齐 STAXX 内销售后日志填写说明）：
- 售后登记提交后自动创建索赔单（草稿）；无需录 ERP（erp_recorded=——）的场景不创建
- 索赔单点「生成出库单」→ 创建 Delivery Note，**服务单号自动写入出库单备注栏**
- 出库单提交后：索赔单状态 → 已出库；售后登记 ERP录入 → OK
"""
import frappe
from frappe.model.document import Document
from frappe.utils import today

# 默认出库仓库（零配件仓）；真实环境可在设置中调整
DEFAULT_WAREHOUSE = "101 101零配件仓1 - 事倍达"
DEFAULT_PRICE_LIST = "Standard Selling"


class ClaimOrder(Document):
    def validate(self):
        if not self.claim_date:
            self.claim_date = today()
        if not self.customer and self.service_request:
            self.customer = frappe.db.get_value("Service Request", self.service_request, "customer")


@frappe.whitelist()
def make_delivery_note(claim_order):
    """根据索赔单生成 ERP 出库单（Delivery Note），服务单号写入备注栏。"""
    doc = frappe.get_doc("Claim Order", claim_order)
    if doc.status != "草稿":
        frappe.throw(f"当前状态「{doc.status}」不可生成出库单，仅草稿状态可操作")
    if not doc.items:
        frappe.throw("索赔单没有明细，无法生成出库单")
    if not doc.customer:
        frappe.throw("索赔单缺少客户，请先填写客户简称")

    missing = [i.part_code for i in doc.items if not i.erp_item]
    if missing:
        frappe.throw(
            "以下配件未映射 ERP 物料，请在「配件主档」维护 ERP物料 后重试："
            + ", ".join(missing)
        )

    company = frappe.db.get_single_value("Global Defaults", "default_company")
    dn = frappe.get_doc(
        {
            "doctype": "Delivery Note",
            "customer": doc.customer,
            "posting_date": today(),
            "posting_time": frappe.utils.nowtime(),
            "company": company,
            "currency": frappe.db.get_value("Company", company, "default_currency") or "CNY",
            "selling_price_list": DEFAULT_PRICE_LIST,
            "set_warehouse": DEFAULT_WAREHOUSE,
            "custom_service_request": doc.service_request,  # 服务单号进出库单（业务规范）
            "items": [
                {
                    "item_code": i.erp_item,
                    "item_name": i.part_name,
                    "qty": i.qty or 1,
                    "warehouse": DEFAULT_WAREHOUSE,
                }
                for i in doc.items
            ],
        }
    )
    dn.insert(ignore_permissions=True)

    doc.delivery_note = dn.name
    doc.status = "已生成出库"
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"delivery_note": dn.name, "status": "已生成出库"}


def update_delivery_note_status(dn, method):
    """Delivery Note 提交后回写：索赔单状态 → 已出库；售后登记 ERP录入 → OK。"""
    if not dn.name:
        return
    co = frappe.db.exists("Claim Order", {"delivery_note": dn.name})
    if co:
        frappe.db.set_value("Claim Order", co, "status", "已出库")
    service_request = getattr(dn, "custom_service_request", None)
    if not service_request and dn.remarks and "服务单号：" in dn.remarks:
        service_request = dn.remarks.split("服务单号：", 1)[1].strip()
    if service_request and frappe.db.exists("Service Request", service_request):
        frappe.db.set_value("Service Request", service_request, "erp_recorded", "OK")
    frappe.db.commit()
