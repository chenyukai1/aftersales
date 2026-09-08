"""售后通知模块：系统内通知（Notification Log）+ 企业微信 Webhook 推送。

通知渠道配置（After Sales Settings 单例）：
- enable_inapp_notify：系统内通知（铃铛 + Notification Log）
- enable_wecom_notify + wecom_webhook：企业微信群机器人推送
"""
import frappe
import requests

try:
    requests.packages.urllib3.disable_warnings()
except Exception:
    pass


def _settings():
    if frappe.db.exists("After Sales Settings"):
        return frappe.get_single("After Sales Settings")
    return frappe._dict()


def notify(subject, message, doctype=None, name=None, roles=None, users=None, priority="Medium"):
    """统一通知入口：系统内通知 + 可选企微推送。

    :param subject: 通知标题
    :param message: 通知内容
    :param doctype/name: 关联单据
    :param roles: 接收角色（如 After Sales Manager）
    :param users: 或指定接收用户
    :param priority: High/Medium/Low
    """
    st = _settings()
    inapp = st.get("enable_inapp_notify", 1) if st else 1
    wecom = (st.get("enable_wecom_notify") and st.get("wecom_webhook")) if st else None

    # 1) 系统内通知
    if inapp:
        _inapp(subject, message, doctype, name, roles, users, priority)
    # 2) 企微推送
    if wecom:
        _wecom(wecom, subject, message, doctype, name)


def _inapp(subject, message, doctype, name, roles, users, priority):
    """Notification Log（铃铛通知）。roles/users 至少一个。"""
    try:
        log = frappe.get_doc(
            {
                "doctype": "Notification Log",
                "for_user": (users or [None])[0] if users else None,
                "type": "Alert",
                "subject": subject,
                "email_content": message,
                "document_type": doctype,
                "document_name": name,
                "read": 0,
                "priority": priority,
            }
        )
        log.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"系统通知发送失败: {e}", "after_sales.notify")


def _wecom(webhook, subject, message, doctype, name):
    """企业微信群机器人推送（文本消息）。"""
    try:
        content = f"{subject}\n{message}"
        if doctype and name:
            content += f"\n单据：{doctype} {name}"
        resp = requests.post(webhook, json={"msgtype": "text", "text": {"content": content}}, timeout=10)
        if resp.status_code != 200:
            frappe.log_error(f"企微推送失败: {resp.status_code} {resp.text[:200]}", "after_sales.notify")
    except Exception as e:
        frappe.log_error(f"企微推送异常: {e}", "after_sales.notify")


# ============================================================
# 外部系统接口（预留）：OA / 采购 / ERP 对接统一出口
# ============================================================
OUTBOUND_EVENTS = (
    "service_request.approved",   # 售后登记审批通过（OA 状态已回写）
    "delivery_note.created",       # M1 自动出库单已生成
    "claim_list.generated",        # M3 供应商索赔清单已生成
)


def send_outbound(event, payload=None, doctype=None, name=None):
    """向外部系统推送业务事件（预留接口，mock 友好）。

    配置 After Sales Settings → 「外部系统接口（预留）」：
      outbound_enabled 勾选 + outbound_webhook 填接收地址 → 启用真实推送；
      否则 = mock 模式（直接返回，不发任何请求，不影响现有流程）。

    payload 建议传 dict（单据摘要），由接收方系统按 event 解析。
    """
    st = _settings()
    enabled = bool(st and st.get("outbound_enabled") and st.get("outbound_webhook"))
    if not enabled:
        # mock 模式：仅返回待推送内容摘要，便于调试，不外发
        return {
            "mock": True,
            "event": event,
            "doctype": doctype,
            "name": name,
            "payload": payload or {},
            "hint": "After Sales Settings 勾选「启用外部推送」并填 Webhook URL 后自动转为真实推送",
        }
    body = {
        "source": "aftersales",
        "event": event,
        "doctype": doctype or "",
        "name": name or "",
        "payload": payload or {},
        "ts": frappe.utils.now_datetime().isoformat(),
    }
    try:
        resp = requests.post(st.outbound_webhook, json=body, timeout=10)
        ok = resp.status_code < 300
        if not ok:
            frappe.log_error(
                f"外部推送失败 event={event} status={resp.status_code} resp={resp.text[:200]}",
                "after_sales.outbound",
            )
        return {"ok": ok, "status": resp.status_code, "event": event}
    except Exception as e:
        frappe.log_error(f"外部推送异常 event={event}: {e}", "after_sales.outbound")
        return {"ok": False, "error": str(e), "event": event}
