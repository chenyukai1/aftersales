"""Claim List（供应商索赔清单）Controller：月度生成「无需实物」索赔项。

业务规则（对齐需求讨论 19:44/22:17 与 STAXX 填写说明）：
- 数据源：已提交售后登记的配件明细
- 筛选条件：索赔需求 ≠ "需提供旧件"（即无需实物退回：仅需清单 / 每月提供售后清单 / 需资料 / 供应商预赔无需清单&资料）
- 生成粒度：一张清单 = 一个索赔月份（明细含供应商，采购可按供应商筛选）
- 调度：每月自动生成上月清单；可手动触发指定月份
"""
import frappe
from frappe.model.document import Document
from frappe.utils import today, getdate, add_months

# 无需实物的索赔需求（需提供旧件的走 M2 追回流程，不进清单）
NO_PHYSICAL_CLAIM_REQUIREMENTS = ("仅需清单", "每月提供售后清单", "需资料", "供应商预赔无需清单&资料")


class ClaimList(Document):
    def validate(self):
        if not self.generated_on:
            self.generated_on = today()


def _last_month():
    return add_months(today(), -1)[:7]


def _collect_items(month):
    """收集指定月份已提交售后单中的「无需实物」索赔明细。"""
    items = []
    sr_list = frappe.get_all("Service Request", filters={"docstatus": 1}, fields=["name"])
    for sr_name in sr_list:
        doc = frappe.get_doc("Service Request", sr_name.name)
        if (doc.claim_month or "") != month:
            continue
        for p in doc.parts:
            if not p.new_part_code:
                continue
            req = p.claim_requirement or ""
            if req == "需提供旧件":
                continue  # 需实物 → 走追回流程
            if not req or req not in NO_PHYSICAL_CLAIM_REQUIREMENTS:
                # 未知索赔需求：仍纳入清单（宁可多不漏），备注标记
                pass
            items.append(
                {
                    "service_request": doc.name,
                    "part_code": p.new_part_code,
                    "part_name": p.new_part_name,
                    "qty": int(p.actual_claim_qty or p.erp_qty or 1),
                    "supplier": p.fault_part_supplier,
                    "claim_requirement": req or "未维护",
                    "chassis_no": doc.chassis_no,
                    "fault_summary": (doc.fault_description or "")[:50],
                    "claim_month": doc.claim_month,
                    "claim_week": doc.claim_week,
                    "factory_claim_date": p.factory_claim_date,
                    "supplier_claim_date": p.supplier_claim_date,
                }
            )
    return items


@frappe.whitelist()
def generate_monthly_claim_list(month=None, replace=True):
    """生成索赔清单。month 格式 YYYY-MM；默认上月。replace=True 时重新生成覆盖。"""
    month = (month or _last_month()).strip()
    items = _collect_items(month)
    if not items:
        return {"created": False, "claim_list": None, "message": f"{month} 无「无需实物」索赔项，未生成清单"}
    claim_list_name = "CL-" + month  # 如 CL-2026-09（月份即唯一键）

    existing = frappe.db.exists("Claim List", claim_list_name)
    if existing:
        if not replace:
            return {"created": False, "claim_list": claim_list_name, "message": f"{month} 清单已存在，未覆盖"}
        doc = frappe.get_doc("Claim List", claim_list_name)
        creating = False
    else:
        doc = frappe.get_doc(
            {
                "doctype": "Claim List",
                "name": claim_list_name,
                "month": month,
                "status": "草稿",
            }
        )
        creating = True

    doc.items = []
    for it in items:
        doc.append("items", it)

    suppliers = {i.supplier for i in doc.items if i.supplier}
    doc.supplier_count = len(suppliers)
    doc.item_count = len(doc.items)
    doc.total_qty = sum(int(i.qty or 0) for i in doc.items)
    doc.generated_on = today()
    # 注意：Frappe 16 中 get_doc(dict) 不会自动置 __islocal，新建必须用 insert()
    # 且必须通过 set_name 显式指定名字（dict 里的 name 会被默认命名机制覆盖）
    if creating:
        doc.insert(ignore_permissions=True, set_name=claim_list_name)
    else:
        doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {
        "created": creating,
        "claim_list": doc.name,
        "item_count": doc.item_count,
        "supplier_count": doc.supplier_count,
        "total_qty": doc.total_qty,
        "month": month,
    }


def run_monthly_scheduler():
    """每月自动生成上月索赔清单（幂等：已发送/已核对的不覆盖）。"""
    month = _last_month()
    existing = frappe.db.exists("Claim List", {"month": month})
    if existing:
        status = frappe.db.get_value("Claim List", existing, "status")
        if status in ("已发送采购", "已核对"):
            return {"skipped": True, "claim_list": existing, "message": f"{month} 清单已{status}，跳过"}
    return generate_monthly_claim_list(month=month, replace=True)
