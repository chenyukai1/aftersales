"""Quality Issue Closure（质量问题闭环）Controller。

依据《售后质量问题闭环流程图（终稿）2026-08-27》：
1. 问题输入与定性判断：a安全法规类 / b设计缺陷 / c一周内≥3起批量隐患 / d新故障现象 / e新车型验证期(12个月) / f改进项-再发 / g以上均不是
2. 吹哨分级：红色（售后去现场车拿回 / 工厂停产核查库存隔离召回评估）、黄色（拆总成原车拿回 / 核查相同问题）、橙色（赔新件视情况去现场）、绿色（登记观察）
3. 批量问题处理：b/c 类触发（确认覆盖范围→核查库存→风险隔离→处置决策→售后方案→落实改进）
4. 原因分析与评审：找真因→有无方案→质量部+研发输出改进方案→评审（通过/不通过/暂不启用）
5. 方案落地：工厂验证→8D报告→改进报告→变更申请→采购下单→生产→市场反馈→完整闭环
"""
import frappe
from frappe.model.document import Document
from frappe.utils import today

# 问题定性 → 是否触发批量处理（终稿：b 设计缺陷、c 批量隐患 需触发批量问题处理流程）
BATCH_ISSUE_CLASSIFICATIONS = ("设计缺陷", "一周内新增≥3起（批量隐患）")

# 吹哨等级 → 处理动作模板（售后 / 工厂）
WHISTLE_ACTIONS = {
    "红色": [
        ("吹哨处理", "去现场、原车拿回（售后）", "售后部"),
        ("吹哨处理", "停生产、核查库存、隔离、召回评估（工厂）", "工厂"),
    ],
    "橙色": [
        ("吹哨处理", "赔新件、视情况去现场（售后）", "售后部"),
    ],
    "黄色": [
        ("吹哨处理", "拆总成、原车拿回（售后）", "售后部"),
        ("吹哨处理", "核查有无相同问题、判断风险、对问题定性（工厂）", "工厂"),
    ],
    "绿色": [
        ("吹哨处理", "登记、观察市场反馈，同类问题增多再启动闭环", "售后部"),
    ],
}

# 批量处理动作模板（终稿 3 阶段）
BATCH_ACTIONS = [
    ("批量处理", "确认覆盖范围（受影响车型/批次）", "质量部"),
    ("批量处理", "核查库存（供应商、厂内、经销商）", "采购部"),
    ("批量处理", "风险隔离（不流出）", "工厂"),
    ("批量处理", "处置决策（返工、停产等）", "总经办"),
    ("批量处理", "决策售后处理方案", "售后部"),
    ("批量处理", "落实改进", "质量部"),
]

# 落地步骤模板（终稿 5 阶段）
LANDING_ACTIONS = [
    ("落地步骤", "工厂内部验证改进有效性", "工厂"),
    ("落地步骤", "质量部输出 8D 报告", "质量部"),
    ("落地步骤", "售后部输出改进报告（对外版）", "售后部"),
    ("落地步骤", "研发部输出变更申请（有变更编号）", "研发部"),
    ("落地步骤", "总经办推进变更流程", "总经办"),
    ("落地步骤", "采购部下单采购新配件", "采购部"),
    ("落地步骤", "生管部排单、制造部生产", "生管部"),
    ("落地步骤", "售后部跟进市场反馈", "售后部"),
]


class QualityIssueClosure(Document):
    def validate(self):
        self.update_status()
        self.apply_whistle_actions()
        self.apply_batch_actions()
        self.apply_landing_actions()

    # ---------- 状态机 ----------
    def update_status(self):
        """根据字段自动推进闭环状态（终稿 4/5 阶段）。

        注意：Select 字段 review_result 无默认值时会被 Frappe 自动填充首项「通过」，
        因此「通过」分支必须以 review_date 有值为准（评审动作完成才算）。
        """
        reviewed = self.review_result == "通过" and self.review_date
        if self.review_result == "暂不启用（成本/故障率低）":
            self.status = "已搁置"
        elif self.review_result == "不通过":
            self.status = "原因分析中"  # 重新分析真因（重启闭环流程）
        elif reviewed:
            self.status = "方案落地中"
        elif self.root_cause or self.improvement_plan:
            self.status = "原因分析中"  # 已进入原因分析（以文本内容为准，避免 Select 自动填充干扰）
        elif self.issue_classification:
            self.status = "已定性"
        # 完整闭环判定：评审通过（有评审日期）+ 变更编号 + 闭环日期
        if reviewed and self.change_request_no and self.closed_date:
            self.status = "完整闭环"

    # ---------- 吹哨动作 ----------
    def apply_whistle_actions(self):
        if not self.whistle_level:
            return
        template = WHISTLE_ACTIONS.get(self.whistle_level, [])
        existing = {a.description for a in self.actions}
        for action_type, desc, dept in template:
            if desc not in existing:
                self.append(
                    "actions",
                    {
                        "action_type": action_type,
                        "description": desc,
                        "owner_department": dept,
                        "status": "未开始",
                    },
                )
        self.whistle_action_summary = "；".join(d for _, d, _ in template)

    # ---------- 批量处理 ----------
    def apply_batch_actions(self):
        if not self.is_batch_issue:
            return
        existing = {a.description for a in self.actions}
        for action_type, desc, dept in BATCH_ACTIONS:
            if desc not in existing:
                self.append(
                    "actions",
                    {
                        "action_type": action_type,
                        "description": desc,
                        "owner_department": dept,
                        "status": "未开始",
                    },
                )

    # ---------- 方案落地动作（评审通过且有评审日期后） ----------
    def apply_landing_actions(self):
        if not (self.review_result == "通过" and self.review_date):
            return
        existing = {a.description for a in self.actions}
        for action_type, desc, dept in LANDING_ACTIONS:
            if desc not in existing:
                self.append(
                    "actions",
                    {
                        "action_type": action_type,
                        "description": desc,
                        "owner_department": dept,
                        "status": "未开始",
                    },
                )


@frappe.whitelist()
def create_from_service_request(service_request, classification=None):
    """从售后登记创建质量闭环（Service Request 提交自动触发 / 页面按钮）。"""
    if frappe.db.exists("Quality Issue Closure", {"service_request": service_request}):
        return {"created": False, "message": "该售后单已存在质量闭环记录"}

    sr = frappe.get_doc("Service Request", service_request)
    classification = classification or _auto_classify(sr)
    if not classification:
        return {"created": False, "message": "无匹配的自动定性，请人工选择问题定性后创建"}

    doc = frappe.get_doc(
        {
            "doctype": "Quality Issue Closure",
            "service_request": sr.name,
            "issue_title": _make_title(sr),
            "feedback_date": sr.feedback_date,
            "chassis_no": sr.chassis_no,
            "customer": sr.customer,
            "fault_part": _first_part_name(sr),
            "fault_description": (sr.fault_description or "")[:200],
            "issue_classification": classification,
            "is_batch_issue": 1 if classification in BATCH_ISSUE_CLASSIFICATIONS else 0,
            "status": "待定性",
        }
    )
    doc.insert(ignore_permissions=True)
    doc.validate()  # 触发状态机与行动项模板
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    # 通知质量部：新闭环待分析
    try:
        from aftersales.after_sales.notify import notify

        notify(
            subject=f"新质量闭环：{doc.issue_title or doc.name}（{classification}）",
            message=(
                f"售后单 {sr.name} 已触发质量闭环，定性：{classification}。"
                f"{'批量问题，需同步启动批量处理。' if doc.is_batch_issue else ''}"
            ),
            doctype="Quality Issue Closure",
            name=doc.name,
            priority="High" if doc.is_batch_issue else "Medium",
        )
    except Exception:
        frappe.log_error(f"闭环创建通知失败：{doc.name}", "after_sales.closure")
    return {"created": True, "closure": doc.name, "classification": classification}


def _auto_classify(sr):
    """售后类型 → 问题定性（仅自动映射明确场景，其余人工选择）。"""
    after_sale_type = sr.after_sale_type or ""
    if after_sale_type == "批量隐患":
        return "一周内新增≥3起（批量隐患）"
    if after_sale_type == "待改进项":
        return "改进项-再发"
    return None


def _make_title(sr):
    parts = [sr.chassis_no, sr.fault_description or ""]
    title = (sr.fault_description or "")[:30]
    return f"{sr.chassis_no} {title}" if sr.chassis_no else title


def _first_part_name(sr):
    if sr.parts:
        return sr.parts[0].new_part_name or sr.parts[0].new_part_code or ""
    return ""


@frappe.whitelist()
def mark_complete(closure):
    """标记完整闭环（方案落地完成）。"""
    doc = frappe.get_doc("Quality Issue Closure", closure)
    if not (doc.review_result == "通过" and doc.review_date):
        frappe.throw("方案未完成评审（缺少评审日期），不能标记完整闭环")
    doc.closed_date = today()
    doc.status = "完整闭环"
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": doc.status}
