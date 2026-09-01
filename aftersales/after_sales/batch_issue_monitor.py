"""批量隐患自动监控 + 改进-再发比对。

批量隐患口径（STAXX 填写说明 2026-09-01 校准）：
  一周内不同客户反馈 3 起相似故障且出厂批次相近；或 1 个客户连续反馈 3 起以上且出厂时间相近。
简化判定：近 7 天已提交售后单中，相同配件编码（new_part_code）≥3 起 → 提示批量隐患（ToDo 通知售后主管）。

改进-再发：售后登记提交时，配件命中改进记录（Improvement Record）且出厂时间在改进日期之后
→ 提示"改进-再发"，建议闭环定性 f 类。
"""
import frappe
from frappe.utils import today, getdate, add_days

BATCH_THRESHOLD = 3  # 一周内相似故障阈值
MONITOR_WINDOW_DAYS = 7


@frappe.whitelist()
def scan_batch_issues(days=MONITOR_WINDOW_DAYS):
    """扫描近 N 天已提交售后单，统计同部件故障数，≥阈值生成批量隐患提醒。

    返回：{date, groups: [{part_code, part_name, count, service_requests, customers}], created_todos}
    """
    since = str(add_days(getdate(today()), -days))
    srs = frappe.get_all(
        "Service Request",
        filters={"docstatus": 1, "feedback_date": [">=", since]},
        fields=["name", "customer"],
    )
    groups = {}
    for sr in srs:
        doc = frappe.get_doc("Service Request", sr.name)
        for p in doc.parts:
            if not p.new_part_code:
                continue
            key = p.new_part_code
            g = groups.setdefault(
                key,
                {"part_code": key, "part_name": p.new_part_name, "count": 0, "service_requests": set(), "customers": set()},
            )
            g["count"] += 1
            g["service_requests"].add(sr.name)
            if sr.customer:
                g["customers"].add(sr.customer)

    hits = []
    created = 0
    for key, g in groups.items():
        if g["count"] >= BATCH_THRESHOLD:
            g["service_requests"] = sorted(g["service_requests"])
            g["customers"] = sorted(g["customers"])
            hits.append(g)
            created += _create_batch_alert(g, since)

    frappe.db.commit()
    return {"date": str(today()), "window_days": days, "groups": hits, "created_todos": created}


def _create_batch_alert(group, since):
    """创建批量隐患提醒（ToDo 给售后主管 + 系统通知）。"""
    if frappe.db.exists(
        "ToDo",
        {
            "reference_type": "Service Request",
            "description": ["like", f"%{group['part_code']}%"],
            "status": ["!=", "Closed"],
        },
    ):
        return 0
    desc = (
        f"【批量隐患预警】近7天「{group['part_name']}」（{group['part_code']}）已收到 "
        f"{group['count']} 起相似故障（阈值 {BATCH_THRESHOLD} 起）\n"
        f"涉及售后单：{', '.join(group['service_requests'])}\n"
        f"涉及客户：{', '.join(group['customers']) or '-'}\n"
        f"请确认是否触发质量闭环（定性 c 类）"
    )
    todo = frappe.get_doc(
        {
            "doctype": "ToDo",
            "role": "After Sales Manager",
            "description": desc,
            "reference_type": "Service Request",
            "reference_name": group["service_requests"][0],
            "status": "Open",
            "priority": "High",
        }
    )
    todo.insert(ignore_permissions=True)
    # 系统内通知 + 企微推送（通知渠道由售后设置控制）
    from aftersales.after_sales.notify import notify

    try:
        notify(
            subject=f"批量隐患预警：{group['part_name']}（{group['part_code']}）",
            message=desc,
            doctype="Service Request",
            name=group["service_requests"][0],
            priority="High",
        )
    except Exception:
        frappe.log_error("批量隐患通知发送失败", "after_sales.batch_issue")
    return 1


@frappe.whitelist()
def check_improvement_recurrence(service_request):
    """售后登记提交时比对改进记录：命中且出厂时间在改进日期之后 → 提示"改进-再发"。"""
    sr = frappe.get_doc("Service Request", service_request)
    results = []
    for p in sr.parts:
        if not p.new_part_code:
            continue
        recs = frappe.get_all(
            "Improvement Record",
            filters={"part_code": p.new_part_code, "status": "验证中"},
            fields=["name", "improvement_date", "improvement_desc", "fault_phenomenon", "change_request_no"],
        )
        for r in recs:
            if getdate(sr.feedback_date) < getdate(r.improvement_date):
                continue  # 改进前出厂，不算再发
            results.append(
                {
                    "part_code": p.new_part_code,
                    "improvement": r.name,
                    "improvement_date": str(r.improvement_date),
                    "desc": r.improvement_desc,
                    "suggest_classification": "改进项-再发",
                }
            )
    return {"recurrences": results}
