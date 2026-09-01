"""Old Part Recall（旧件追回）Controller + 周调度任务。

业务规则（对齐需求讨论 14:20/15:21 与 STAXX 填写说明）：
- 触发：售后登记配件「坏件需要寄回=是」自动创建（或新品验证/特定品号人工标记）
- 发货满 7 天进入提醒队列，按周提醒（距上次提醒 ≥ 7 天）
- 坏件到货登记 → 状态「已追回」停止提醒
- 发货起超过 60 天（2 个月）→ 自动「超时终止」
"""
import frappe
from frappe.model.document import Document
from frappe.utils import today, getdate, add_days

REMIND_START_DAYS = 7          # 发货满 7 天开始提醒
REMIND_INTERVAL_DAYS = 7       # 按周提醒
TIMEOUT_DAYS = 60              # 2 个月上限


class OldPartRecall(Document):
    def validate(self):
        if self.bad_part_arrived and self.status not in ("已追回", "超时终止"):
            self.status = "已追回"
        if not self.first_remind_date and self.last_remind_date:
            self.first_remind_date = self.last_remind_date


def _is_due(recall, today_date):
    """是否满足提醒条件：满 7 天且距上次提醒 ≥ 7 天。"""
    if not recall.ship_date:
        return False
    days_since_ship = (today_date - getdate(recall.ship_date)).days
    if days_since_ship < REMIND_START_DAYS:
        return False
    if not recall.last_remind_date:
        return True
    return (today_date - getdate(recall.last_remind_date)).days >= REMIND_INTERVAL_DAYS


def run_recall_scheduler():
    """Frappe Scheduler 每日执行：扫描追回提醒，处理提醒/超时/已追回。"""
    today_date = getdate(today())
    recalls = frappe.get_all(
        "Old Part Recall",
        filters={"status": ["in", ("待提醒", "已提醒")]},
        fields=["name"],
    )
    reminded, timedout, closed = 0, 0, 0
    for r in recalls:
        doc = frappe.get_doc("Old Part Recall", r.name)

        # 1) 坏件已到货 → 已追回
        if doc.bad_part_arrived:
            doc.status = "已追回"
            doc.save(ignore_permissions=True)
            closed += 1
            continue

        # 2) 超时：发货起 60 天
        if doc.ship_date and (today_date - getdate(doc.ship_date)).days > TIMEOUT_DAYS:
            doc.status = "超时终止"
            doc.save(ignore_permissions=True)
            timedout += 1
            continue

        # 3) 到期待提醒
        if _is_due(doc, today_date):
            doc.append("reminders", {"remind_date": str(today_date), "note": "系统按周提醒"})
            doc.last_remind_date = str(today_date)
            if not doc.first_remind_date:
                doc.first_remind_date = str(today_date)
            doc.remind_count = (doc.remind_count or 0) + 1
            doc.status = "已提醒"
            doc.save(ignore_permissions=True)
            reminded += 1
            # 系统/企微通知（追回第 N 次提醒）
            try:
                from aftersales.after_sales.notify import notify

                notify(
                    subject=f"旧件追回提醒（第 {doc.remind_count} 次）：{doc.part_name or doc.part_code}",
                    message=(
                        f"售后单 {doc.service_request} 的坏件 {doc.part_code}（{doc.part_name or ''}）尚未寄回，"
                        f"已发货 {doc.ship_date}，请跟进客户寄回。"
                    ),
                    doctype="Old Part Recall",
                    name=doc.name,
                    priority="High" if doc.remind_count >= 3 else "Medium",
                )
            except Exception:
                frappe.log_error(f"追回提醒通知失败：{doc.name}", "after_sales.recall")

    frappe.db.commit()
    frappe.log_error(
        f"旧件追回调度完成：提醒 {reminded}，已追回 {closed}，超时终止 {timedout}",
        "after_sales.recall",
    )
    return {"reminded": reminded, "closed": closed, "timedout": timedout}


@frappe.whitelist()
def mark_bad_part_arrived(recall, arrival_date=None):
    """登记坏件到货（页面按钮），状态自动转「已追回」。"""
    doc = frappe.get_doc("Old Part Recall", recall)
    doc.bad_part_arrived = arrival_date or today()
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": doc.status}
