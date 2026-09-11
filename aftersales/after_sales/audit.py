"""操作日志：售后登记敏感字段改动留痕。

Frappe 自带 Version 记录所有字段变化但偏技术视角；本模块针对
业务敏感字段（索赔处理动作 / OA 状态 / 回访状态 / ERP 录入状态 /
异常原因）生成一条人类可读的「变更日志」Comment，便于追责。

通过 hooks doc_events 挂到 Service Request.on_update。
"""
import frappe

# 需要留痕的字段 -> 中文标签
SENSITIVE_FIELDS = {
    "handling_action": "索赔处理动作",
    "oa_status": "OA状态",
    "customer_callback": "回访状态",
    "erp_recorded": "ERP录入状态",
    "exception_reason": "异常原因",
}


def track_sensitive_changes(doc, method=None):
    """on_update 钩子：敏感字段发生变更时写入 Comment 留痕。"""
    before = doc.get_doc_before_save()
    if not before:
        return
    changes = []
    for fieldname, label in SENSITIVE_FIELDS.items():
        old = getattr(before, fieldname, None)
        new = getattr(doc, fieldname, None)
        if (old or "") != (new or ""):
            changes.append(f"{label}：{old or '(空)'} → {new or '(空)'}")
    if not changes:
        return
    user = frappe.session.user
    user_name = frappe.db.get_value("User", user, "full_name") or user
    content = "变更日志（{user}）：{changes}".format(
        user=user_name, changes="；".join(changes)
    )
    try:
        frappe.get_doc(
            {
                "doctype": "Comment",
                "comment_type": "Comment",
                "reference_doctype": doc.doctype,
                "reference_name": doc.name,
                "content": content,
                "published": 1,
            }
        ).insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"变更日志写入失败 {doc.doctype} {doc.name}: {e}", "after_sales.audit")
