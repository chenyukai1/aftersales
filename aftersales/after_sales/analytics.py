"""质量分析看板（M5 质量闭环"分析端"）。

为页面 /app/quality-dashboard 提供聚合数据：
- 索赔概览：登记总量 / 已通过 / 索赔单数 / 索赔率
- 故障 TOP：按故障大类 / 部件 / 现象分组 Top 10
- 供应商对比：索赔明细按供应商汇总（单量 / 数量）
- 月度趋势：近 12 个月售后登记量
全部只读聚合，不写任何数据。
"""
import frappe
from frappe.utils import add_months, getdate, today


@frappe.whitelist()
def get_dashboard_data():
    """看板一次性取数（页面加载调用）。"""
    return {
        "overview": _overview(),
        "fault_by_category": _fault_top("fault_category", "故障大类"),
        "fault_by_part": _fault_top("fault_part", "故障部件"),
        "fault_by_phenomenon": _fault_top("fault_phenomenon", "故障现象"),
        "supplier_stats": _supplier_stats(),
        "monthly_trend": _monthly_trend(),
        "generated_at": frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M"),
    }


def _overview():
    """索赔概览：已通过登记为分母，有索赔单的登记为分子。"""
    total = frappe.db.count("Service Request")
    approved = frappe.db.count("Service Request", {"workflow_state": "已通过"})
    # 有索赔单的已通过登记（去重）
    claimed = frappe.db.sql(
        """
        select count(distinct co.service_request)
        from `tabClaim Order` co
        where co.service_request is not null
          and co.docstatus < 2
        """,
    )[0][0] or 0
    parts = frappe.db.sql(
        """
        select sum(cpi.qty)
        from `tabClaim Order Item` cpi
        join `tabClaim Order` co on cpi.parent = co.name
        where co.docstatus < 2
        """,
    )[0][0] or 0
    rate = round(claimed * 100.0 / approved, 1) if approved else 0.0
    return {
        "total_requests": total,
        "approved_requests": approved,
        "claimed_requests": claimed,
        "claim_rate": rate,
        "claim_parts_qty": int(parts),
    }


def _fault_top(field, label, limit=10):
    """故障 TOP：按指定字段分组统计（含空值归"未填写"）。"""
    if not frappe.db.has_column("Service Request", field):
        return []
    rows = frappe.db.sql(
        f"""
        select coalesce(sr.`{field}`, '未填写') as name, count(*) as cnt
        from `tabService Request` sr
        group by sr.`{field}`
        order by cnt desc
        limit {int(limit)}
        """,
        as_dict=True,
    )
    return [{"label": label, "items": rows}]


def _supplier_stats(limit=15):
    """供应商对比：索赔明细按供应商汇总。"""
    rows = frappe.db.sql(
        """
        select coalesce(cpi.supplier, '未指定') as supplier,
               count(distinct co.name) as order_cnt,
               sum(cpi.qty) as qty
        from `tabClaim Order Item` cpi
        join `tabClaim Order` co on cpi.parent = co.name
        where co.docstatus < 2
        group by cpi.supplier
        order by qty desc
        limit {0}
        """.format(int(limit)),
        as_dict=True,
    )
    return rows


def _monthly_trend(months=12):
    """近 N 个月售后登记量（按创建月份）。"""
    start = getdate(add_months(today(), -(months - 1))).strftime("%Y-%m-01")
    rows = frappe.db.sql(
        """
        select date_format(sr.creation, '%%Y-%%m') as ym, count(*) as cnt
        from `tabService Request` sr
        where date(sr.creation) >= %(start)s
        group by ym order by ym
        """,
        {"start": start},
        as_dict=True,
    )
    return rows
