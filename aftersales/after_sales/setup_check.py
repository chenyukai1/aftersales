# -*- coding: utf-8 -*-
"""
上线就绪检查器（setup_check）
=============================
用途：在「准备上线 / 交接演示」前跑一遍，快速了解系统就绪度——
哪些已就绪(✅)、哪些缺数据但可先用 mock 演示(⚠️)、哪些会阻塞真实业务(🔴)。

用法（容器内）：
    bench --site dev.localhost execute \
        frappe.get_attr('aftersales.after_sales.setup_check.run')

说明：只读检查，不修改任何数据，可重复执行。
"""
import frappe


# 核心业务 DocType（应全部存在）
CORE_DOCTYPES = [
    "Service Request", "Service Part Item",          # M0 登记
    "Claim Order", "Claim Order Item",               # M1 自动出库
    "Old Part Recall", "Old Part Recall Reminder",   # M2 坏件追回
    "Claim List", "Claim List Item",                 # M3 索赔清单
    "Spare Part",                                    # 配件主档
    "Vehicle Delivery",                              # 整车主档
    "Special Part Registration",                     # 特殊配件
    "After Sales Option",                            # 可编辑枚举
    "Fault Category", "Fault Part", "Fault Phenomenon",  # 故障字典
    "Quality Issue Closure", "Quality Issue Action",     # M5 质量闭环
    "Improvement Record",                            # 改进记录
    "After Sales Settings",                          # 售后设置
]

WORKFLOWS = ["售后登记-一级审批"]
PRINT_FORMATS = [("售后登记表", "Service Request"), ("供应商索赔清单", "Claim List")]
ROLES = ["After Sales", "After Sales Manager", "Purchase User", "Quality Manager"]
DEMO_USERS = [
    ("shouhou@demo.local", "售后登记（After Sales）"),
    ("zhuguan@demo.local", "售后主管审批（After Sales Manager）"),
    ("caigou@demo.local", "采购查看（Purchase User）"),
    ("zhiliang@demo.local", "质量闭环（Quality Manager）"),
]

# 主档数据检查：DocType → (说明, 空值判定字段)
MASTER_CHECKS = [
    ("Spare Part", "配件价格表(登记自动带出/出库/索赔的底座)", ["k3_code", "part_name"]),
    ("Spare Part", "   └ 已绑 ERP 物料 erp_item（M1 出库需真实物料）", ["erp_item"]),
    ("Vehicle Delivery", "整车发货记录(输铭牌带出车辆/客户)", ["chassis_no"]),
    ("Vehicle Delivery", "   └ 已填购车客户 customer(带出客户/对接人)", ["customer"]),
    ("Customer", "客户档案", ["customer_name"]),
    ("Customer", "   └ 已配主联系人 customer_primary_contact", ["customer_primary_contact"]),
    ("Customer", "   └ 已配主地址 customer_primary_address(带出收货/区域)", ["customer_primary_address"]),
    ("Supplier", "供应商档案", ["name"]),
    ("Fault Category", "故障大类字典(三级下拉)", ["name"]),
    ("Fault Part", "故障部件字典", ["name"]),
    ("Fault Phenomenon", "故障现象字典", ["name"]),
    ("After Sales Option", "可编辑枚举选项(服务类型/索赔需求等)", ["option_value"]),
]


def _has_field(doctype, fieldname):
    try:
        return fieldname in {f.fieldname for f in frappe.get_meta(doctype).fields}
    except Exception:
        return False


def _count(dt):
    try:
        return frappe.db.count(dt)
    except Exception:
        return 0


def _count_filled(dt, fieldname):
    """统计 dt 中 fieldname 非空的记录数（字段不存在返回 None）。"""
    if not _has_field(dt, fieldname):
        return None
    try:
        return frappe.db.count(dt, filters=[(fieldname, "is", "set")])
    except Exception:
        return None


def _line(mark, text):
    return f"  {mark} {text}"


def run(verbose=True):
    """执行全部检查，返回分级汇总 dict。"""
    out = []
    total = {"ok": 0, "warn": 0, "block": 0}

    def ok(t):
        total["ok"] += 1
        out.append(_line("✅", t))

    def warn(t):
        total["warn"] += 1
        out.append(_line("⚠️", t))

    def block(t):
        total["block"] += 1
        out.append(_line("🔴", t))

    # ---------- ① 基础结构 ----------
    out.append("\n【① 基础结构：DocType / 审批流 / 打印模板】")
    missing_dt = [d for d in CORE_DOCTYPES if not frappe.db.exists("DocType", d)]
    if missing_dt:
        block(f"缺少核心 DocType：{', '.join(missing_dt)}（请先跑 after_install / migrate）")
    else:
        ok(f"核心 DocType {len(CORE_DOCTYPES)} 个全部存在")

    for wf in WORKFLOWS:
        if frappe.db.exists("Workflow", wf):
            ok(f"审批流「{wf}」存在")
        else:
            block(f"审批流「{wf}」缺失（售后登记将无法提交审批）")

    for name, _dt in PRINT_FORMATS:
        if frappe.db.exists("Print Format", name):
            ok(f"打印模板「{name}」存在")
        else:
            warn(f"打印模板「{name}」缺失（不影响流程，仅打印按钮无模板）")

    # ---------- ② 角色 / 演示账号 ----------
    out.append("\n【② 角色与演示账号】")
    miss_role = [r for r in ROLES if not frappe.db.exists("Role", r)]
    ok("角色 After Sales / After Sales Manager / Purchase User / Quality Manager 就绪" if not miss_role
       else f"缺少角色：{', '.join(miss_role)}（跑 sync_roles_and_permissions）")
    for email, desc in DEMO_USERS:
        user = frappe.db.exists("User", email)
        if user:
            ok(f"演示账号 {email}（{desc}）")
        else:
            warn(f"演示账号 {email} 缺失（跑 seed）")

    # ---------- ③ 主档数据量 ----------
    out.append("\n【③ 主档数据量（数量 = 可用于自动带出的底座）】")
    warn_threshold = {
        "Spare Part": 3, "Vehicle Delivery": 3, "Customer": 2, "Supplier": 2,
    }
    for dt, desc, fields in MASTER_CHECKS:
        if not frappe.db.exists("DocType", dt):
            continue
        if len(fields) == 1 and fields[0] == "name":
            n = _count(dt)
            mark = ok if n >= (warn_threshold.get(dt, 1)) else warn
            mark(f"{desc}：{n} 条" + ("" if n else "（空 → 三级下拉无可选项）"))
        else:
            n = _count(dt)
            filled = _count_filled(dt, fields[-1])
            if filled is None:
                warn(f"{desc}：{n} 条（缺字段 {fields[-1]}，跳过非空统计）")
            else:
                if n and filled == n:
                    ok(f"{desc}：{n}/{n} 已填")
                elif filled and filled > 0:
                    warn(f"{desc}：{filled}/{n} 已填（未填的登记时需人工补）")
                elif n:
                    block(f"{desc}：0/{n} 已填（自动带出将失效，请补主档或导入）")
                else:
                    warn(f"{desc}：0 条（mock 演示建议先导入）")

    # ---------- ④ 售后设置 ----------
    out.append("\n【④ 售后设置（设置 → 售后设置）】")
    try:
        st = frappe.get_doc("After Sales Settings", "After Sales Settings")
    except Exception:
        st = None
    if not st:
        block("售后设置单不存在（跑 after_install）")
    else:
        wh = st.get("delivery_warehouse")
        if wh and frappe.db.exists("Warehouse", wh):
            ok(f"默认出库仓库：{wh}")
        elif wh:
            warn(f"默认出库仓库「{wh}」在系统不存在（检查仓库名或建仓）")
        else:
            warn("默认出库仓库未配置（自动出库 M1 将失败）")
        if st.get("wecom_webhook"):
            ok("企微 Webhook 已配置" + ("，且已开启企微推送" if st.get("enable_wecom_notify") else "（但未勾选“企业微信推送”）"))
        else:
            warn("企微 Webhook 未配置（通知仅走系统内；上线前填入群机器人地址即可）")
        if st.get("outbound_enabled") and st.get("outbound_webhook"):
            ok("外部系统接口：已启用并配置 URL")
        elif st.get("outbound_enabled"):
            warn("外部系统接口已勾选但未填 URL（实际不会外发）")
        else:
            ok("外部系统接口：mock 模式未启用（预留通道，无需处理）")

    # ---------- ⑤ 调度与测试 ----------
    out.append("\n【⑤ 调度与自动化】")
    scheduler = True
    try:
        from frappe.utils.scheduler import is_scheduler_disabled
        scheduler = not is_scheduler_disabled()
    except Exception:
        pass
    ok("Frappe 后台调度已启用" if scheduler else "⚠️ 后台调度未启用（追回提醒/索赔清单 cron 不会自动跑）")
    if frappe.db.exists("DocType", "Improvement Record"):
        ok("改进记录表（提交登记自动比对再发）就绪")
    if frappe.db.exists("DocType", "File"):
        ok("文件归档 hook 挂载（上传附件自动归档到 售后资料/）")

    # ---------- 汇总 ----------
    summary = f"\n═══ 检查完成：✅ {total['ok']}  |  ⚠️ {total['warn']}  |  🔴 {total['block']} ═══"
    out.append(summary)
    if total["block"]:
        out.append("存在 🔴 阻塞项：真实业务（审批/出库）无法闭环，请优先处理后再演示。")
    elif total["warn"]:
        out.append("无阻塞项：系统可完整演示；⚠️ 多为上线前需补真实数据/配置，mock 数据可先行。")
    else:
        out.append("全部就绪，可进入真实数据试点。")
    report = "\n".join(out)
    if verbose:
        print(report)
    return {"summary": summary, "total": total, "report": report}
