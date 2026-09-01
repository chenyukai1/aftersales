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
