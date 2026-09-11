"""超时自动提醒：每日扫描异常滞留并统一通知（站内铃铛 + 企微预留）。

新增两类扫描（旧件追回的 7 天提醒/周提醒/60 天超时已由
old_part_recall.run_recall_scheduler 负责，此处不重复）：

1. 回访超时：customer_callback = 待回访 且 反馈日期距今超过
   CALLBACK_TIMEOUT_DAYS 天 → 提醒登记人 + 售后主管
2. 审批滞留：workflow_state = 待审批 且 最后修改时间距今超过
   APPROVAL_STALE_DAYS 天 → 提醒售后主管

去重：同一单据同一提醒当天只发一次（按 Notification Log 查重）。
通知走 notify.notify()：设置里勾选企微后自动同步推送群机器人。
"""
import frappe
from frappe.utils import add_days, getdate, nowdate, now_datetime, cint

from aftersales.after_sales.notify import notify

CALLBACK_TIMEOUT_DAYS = 3   # 回访超时天数
APPROVAL_STALE_DAYS = 2     # 审批滞留天数
NOTIFY_ROLE = "After Sales Manager"


def run_daily_reminders():
    """调度入口：daily_long 每日执行。"""
    callback_cnt = _scan_callback_timeout()
    approval_cnt = _scan_approval_stale()
    return {"callback_timeout": callback_cnt, "approval_stale": approval_cnt}


def _already_notified_today(subject, doctype, name):
    """当天同单同标题已提醒过则跳过（幂等去重）。"""
    return bool(
        frappe.db.exists(
            "Notification Log",
            {
                "subject": subject,
                "document_type": doctype,
                "document_name": name,
                "creation": [">=", now_datetime().replace(hour=0, minute=0, second=0, microsecond=0)],
            },
        )
    )


def _scan_callback_timeout():
    today = getdate(nowdate())
    deadline = add_days(today, -CALLBACK_TIMEOUT_DAYS)
    rows = frappe.get_all(
        "Service Request",
        filters={"customer_callback": "待回访", "feedback_date": ["<", deadline]},
        fields=["name", "owner", "customer", "feedback_date"],
    )
    cnt = 0
    for r in rows:
        days = (today - getdate(r.feedback_date)).days if r.feedback_date else CALLBACK_TIMEOUT_DAYS
        subject = f"回访超时提醒：{r.name} 已待回访 {days} 天"
        if _already_notified_today(subject, "Service Request", r.name):
            continue
        users = [r.owner] if r.owner else []
        notify(
            subject=subject,
            message=f"客户「{r.customer or '-'}」的售后登记 {r.name} 反馈日期 {r.feedback_date}，"
            f"已超过 {CALLBACK_TIMEOUT_DAYS} 天未回访，请及时跟进。",
            doctype="Service Request",
            name=r.name,
            users=users,
            roles=[NOTIFY_ROLE],
            priority="High",
        )
        cnt += 1
    return cnt


def _scan_approval_stale():
    cutoff = add_days(now_datetime(), -APPROVAL_STALE_DAYS)
    rows = frappe.get_all(
        "Service Request",
        filters={"workflow_state": "待审批", "modified": ["<", cutoff]},
        fields=["name", "owner", "customer", "modified"],
    )
    cnt = 0
    for r in rows:
        subject = f"审批滞留提醒：{r.name} 待审批已超 {APPROVAL_STALE_DAYS} 天"
        if _already_notified_today(subject, "Service Request", r.name):
            continue
        notify(
            subject=subject,
            message=f"售后登记 {r.name}（客户 {r.customer or '-'}）自 {r.modified:%Y-%m-%d %H:%M} "
            f"起处于「待审批」，请尽快处理。",
            doctype="Service Request",
            name=r.name,
            roles=[NOTIFY_ROLE],
            priority="Medium",
        )
        cnt += 1
    return cnt
