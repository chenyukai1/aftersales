"""售后管理平台 全功能端到端回归测试（模块化，输出 PASS/FAIL）。"""
import os

os.chdir("/home/frappe/frappe-bench/sites")
import frappe
import frappe.utils.scheduler as scheduler
from frappe.model.workflow import apply_workflow

frappe.init(site="dev.localhost", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(f"{name} {detail}")
    print(f"{'✅ PASS' if cond else '❌ FAIL'} {name} {detail}")


def section(title):
    print(f"\n========== {title} ==========")


# ========== 0. 基础设施 ==========
section("0. 基础设施")
check("DocType 数量(≥17)", frappe.db.count("DocType", {"module": "after_sales"}) >= 17, f"={frappe.db.count('DocType', {'module': 'after_sales'})}")
check("角色(4自定义)", all(frappe.db.exists("Role", r) for r in ("After Sales", "After Sales Manager")), "After Sales/Manager")
check("演示用户(3)", len(frappe.get_all("User", filters={"email": ["in", ("shouhou@demo.local", "caigou@demo.local", "zhiliang@demo.local")]})) == 3)
check("Workflow 配置", frappe.db.exists("Workflow", "售后登记-一级审批"))
check("Scheduler 启用", not scheduler.is_scheduler_disabled())
check("Print Format(2)", all(frappe.db.exists("Print Format", f) for f in ("售后登记表", "供应商索赔清单")))
check("售后设置单例", frappe.db.exists("DocType", "After Sales Settings"))

# 确保改进记录存在（幂等创建，供改进-再发比对测试）
if not frappe.db.exists("Improvement Record", {"part_code": "31101166"}):
    frappe.get_doc(
        {
            "doctype": "Improvement Record",
            "part_code": "31101166",
            "part_name": "PU双轮 80*70mm 带轴承 (REACH认证)",
            "fault_phenomenon": "承重轮异常磨损",
            "improvement_date": "2026-08-15",
            "improvement_desc": "更换轴承油脂配方",
            "change_request_no": "ECN-2026-008",
            "status": "验证中",
        }
    ).insert(ignore_permissions=True)
    frappe.db.commit()
    print("ℹ️ 改进记录已补建")

# ========== 1. 售后登记 → 审批 → 联动 ==========
section("1. 售后登记 → 审批 → 自动联动")
sr = frappe.get_doc(
    {
        "doctype": "Service Request",
        "feedback_date": "2026-09-01",
        "customer": "吉安吉翔/江西雷翼",
        "contact_person": "大程",
        "service_type": "特殊申请",
        "after_sale_type": "批量隐患",
        "fault_description": "端到端回归测试：液压站批量异响",
        "chassis_no": "HC-2026-0203-002",
        "parts": [
            {"old_part_code": "31101130", "new_part_code": "31101130", "erp_qty": 1, "gift_qty": 0, "need_return": "是"},
            {"old_part_code": "31101166", "new_part_code": "31101166", "erp_qty": 1, "gift_qty": 0, "need_return": "否"},
        ],
    }
).insert(ignore_permissions=True)
check("1.1 创建草稿", sr.workflow_state == "草稿" and sr.docstatus == 0, sr.name)
apply_workflow(sr, "提交审批")
sr.reload()
check("1.2 提交审批→待审批", sr.workflow_state == "待审批" and sr.docstatus == 0)
apply_workflow(sr, "审批通过")
sr.reload()
check("1.3 审批通过→已通过", sr.workflow_state == "已通过" and sr.docstatus == 1)
check("1.4 OA联动(特殊申请→Y)", sr.oa_status == "Y", f"={sr.oa_status}")
co = frappe.db.exists("Claim Order", {"service_request": sr.name})
check("1.5 自动创建索赔单", bool(co), co or "")
rc = frappe.db.exists("Old Part Recall", {"service_request": sr.name, "part_code": "31101130"})
check("1.6 自动创建追回(需寄回)", bool(rc), rc or "")
qc = frappe.db.exists("Quality Issue Closure", {"service_request": sr.name})
check("1.7 批量隐患自动创建闭环", bool(qc), qc or "")
cmts = frappe.get_all("Comment", filters={"reference_doctype": "Service Request", "reference_name": sr.name, "comment_type": "Info"}, fields=["content"])
check("1.8 改进-再发比对提醒", any("改进-再发" in c["content"] for c in cmts), "31101166 命中改进记录")

# ========== 2. 索赔单 → 出库 ==========
section("2. 索赔单 → Delivery Note 出库")
co_doc = frappe.get_doc("Claim Order", co)
check("2.1 索赔单状态草稿", co_doc.status == "草稿", co_doc.status)
dn = frappe.get_attr("aftersales.after_sales.doctype.claim_order.claim_order.make_delivery_note")(co)
dn_name = dn.get("delivery_note") if isinstance(dn, dict) else dn
check("2.2 生成出库单", bool(dn_name), dn_name or "")
dn_doc = frappe.get_doc("Delivery Note", dn_name)
check("2.3 服务单号写入出库单", dn_doc.custom_service_request == sr.name, dn_doc.custom_service_request)
check("2.4 索赔单状态回写", frappe.db.get_value("Claim Order", co, "status") == "已生成出库")

# ========== 3. 旧件追回调度 ==========
section("3. 旧件追回调度")
rc_doc = frappe.get_doc("Old Part Recall", rc)
rc_doc.ship_date = "2026-08-20"  # 发货超7天
rc_doc.save(ignore_permissions=True)
result = frappe.get_attr("aftersales.after_sales.doctype.old_part_recall.old_part_recall.run_recall_scheduler")()
check("3.1 调度运行", isinstance(result, dict), str(result))
rc_doc.reload()
check("3.2 已提醒+次数", rc_doc.status == "已提醒" and rc_doc.remind_count >= 1, f"status={rc_doc.status} count={rc_doc.remind_count}")
rc_doc.bad_part_arrived = "2026-09-01"
rc_doc.save(ignore_permissions=True)
check("3.3 坏件到货→已追回", rc_doc.status == "已追回", rc_doc.status)

# ========== 4. 索赔清单 ==========
section("4. 供应商索赔清单")
cl = frappe.get_attr("aftersales.after_sales.doctype.claim_list.claim_list.generate_monthly_claim_list")("2026-09")
check("4.1 清单生成", bool(cl.get("claim_list")), cl.get("claim_list") or "无数据")
cl_doc = frappe.get_doc("Claim List", cl["claim_list"])
check("4.2 清单明细≥1", cl_doc.item_count >= 1, f"={cl_doc.item_count}")
check("4.3 清单无「需提供旧件」项", not any(i.claim_requirement == "需提供旧件" for i in cl_doc.items))
cl_doc.status = "已发送采购"
cl_doc.save(ignore_permissions=True)
check("4.4 状态流转", cl_doc.status == "已发送采购")

# ========== 5. 质量闭环推进 ==========
section("5. 质量闭环（吹哨→原因→评审→落地→闭环）")
qc_doc = frappe.get_doc("Quality Issue Closure", qc)
check("5.1 定性批量隐患", qc_doc.issue_classification == "一周内新增≥3起（批量隐患）", qc_doc.issue_classification)
check("5.2 批量标记", qc_doc.is_batch_issue == 1)
check("5.3 批量行动项6条", len([a for a in qc_doc.actions if a.action_type == "批量处理"]) == 6)
qc_doc.whistleblower = "售后"
qc_doc.whistle_level = "红色"
qc_doc.save(ignore_permissions=True)
check("5.4 吹哨红色动作2条", len([a for a in qc_doc.actions if a.action_type == "吹哨处理"]) == 2)
qc_doc.root_cause = "密封件材质缺陷"
qc_doc.improvement_plan = "更换密封件材质"
qc_doc.save(ignore_permissions=True)
check("5.5 原因分析中", qc_doc.status == "原因分析中", qc_doc.status)
qc_doc.review_result = "通过"
qc_doc.review_date = "2026-09-01"
qc_doc.save(ignore_permissions=True)
check("5.6 评审通过→方案落地中", qc_doc.status == "方案落地中", qc_doc.status)
check("5.7 落地步骤8条", len([a for a in qc_doc.actions if a.action_type == "落地步骤"]) == 8)
qc_doc.change_request_no = "ECN-2026-999"
qc_doc.closed_date = "2026-09-15"
qc_doc.save(ignore_permissions=True)
check("5.8 完整闭环", qc_doc.status == "完整闭环", qc_doc.status)

# ========== 6. 批量隐患监控 ==========
section("6. 批量隐患监控")
bscan = frappe.get_attr("aftersales.after_sales.batch_issue_monitor.scan_batch_issues")()
check("6.1 扫描运行", isinstance(bscan, dict))
check("6.2 命中31101130", any(g["part_code"] == "31101130" and g["count"] >= 3 for g in bscan["groups"]), str([(g["part_code"], g["count"]) for g in bscan["groups"]]))

# ========== 7. 资料归档 ==========
section("7. 故障资料自动归档")
from frappe.utils.file_manager import save_file

part_row = frappe.db.get_value("Service Part Item", {"parent": sr.name}, "name")
f = save_file("回归测试视频.mp4", b"fake-video-data" * 100, "Service Part Item", part_row, is_private=0)
check("7.1 归档目录(售后资料/车型/月份/部件)", f.folder and f.folder.startswith("Home/售后资料/"), f.folder)
check("7.2 文件重命名(服务单号_部件)", f.file_name.startswith(sr.name), f.file_name)

# ========== 8. 打印模板 ==========
section("8. 打印模板")
html1 = frappe.get_print("Service Request", sr.name, print_format="售后登记表", as_pdf=False)
check("8.1 售后登记表打印", bool(html1) and "售后登记表" in html1)
html2 = frappe.get_print("Claim List", cl["claim_list"], print_format="供应商索赔清单", as_pdf=False)
check("8.2 索赔清单打印", bool(html2) and "供应商索赔清单" in html2)

# ========== 9. 通知 ==========
section("9. 通知模块")
from aftersales.after_sales.notify import notify

before = frappe.db.count("Notification Log")
notify("回归测试通知", "通知模块验证", doctype="Service Request", name=sr.name)
after = frappe.db.count("Notification Log")
check("9.1 系统通知生成", after > before, f"+{after-before}")

# ========== 10. 权限矩阵 ==========
section("10. 权限矩阵")
perm = {p.role: (p.read, p.write, p.create) for p in frappe.get_doc("DocType", "Service Request").permissions}
check("10.1 售后rwc", perm.get("After Sales") == (1, 1, 1), str(perm.get("After Sales")))
check("10.2 采购只读", perm.get("Purchase User") == (1, 0, 0), str(perm.get("Purchase User")))
perm_cl = {p.role: (p.read, p.write, p.create) for p in frappe.get_doc("DocType", "Claim List").permissions}
check("10.3 采购清单rw", perm_cl.get("Purchase User") == (1, 1, 0), str(perm_cl.get("Purchase User")))
perm_qc = {p.role: (p.read, p.write, p.create) for p in frappe.get_doc("DocType", "Quality Issue Closure").permissions}
check("10.4 质量闭环rwc", perm_qc.get("Quality Manager") == (1, 1, 1), str(perm_qc.get("Quality Manager")))

frappe.db.commit()
print("\n" + "=" * 50)
print(f"总计: {len(PASS)} PASS / {len(FAIL)} FAIL")
if FAIL:
    print("失败项:")
    for f in FAIL:
        print("  ❌", f)
frappe.destroy()
