"""应用安装时创建自定义 DocType（用 Frappe 自身的 DocType API，避免手写 JSON 的版本兼容问题）。"""
import frappe

MODULE = "after_sales"


def _field(fieldname, label, fieldtype="Data", **kw):
    d = {"fieldname": fieldname, "label": label, "fieldtype": fieldtype}
    d.update(kw)
    return d


def _make_doctype(
    name,
    fields,
    *,
    autoname=None,
    naming_rule=None,
    search_fields="",
    title_field=None,
    istable=False,
):
    if frappe.db.exists("DocType", name):
        return None
    doc = frappe.get_doc(
        {
            "doctype": "DocType",
            "name": name,
            "module": MODULE,
            "fields": fields,
            "permissions": [
                {
                    "role": "System Manager",
                    "read": 1, "write": 1, "create": 1, "delete": 1,
                    "email": 1, "print": 1, "export": 1, "report": 1, "share": 1,
                }
            ],
            "search_fields": search_fields,
            "title_field": title_field,
            "sort_field": "modified",
            "sort_order": "DESC",
            "track_changes": 1,
            "allow_rename": 1,
            "istable": istable,
            "naming_rule": naming_rule or "Expression (old style)",
            "autoname": autoname,
        }
    )
    doc.insert(ignore_if_duplicate=True)
    return doc


def create_vehicle_delivery():
    return _make_doctype(
        "Vehicle Delivery",
        [
            _field("delivery_date", "发货日期", "Date", reqd=1, in_list_view=1),
            _field("hangcha_model", "杭叉型号", in_list_view=1),
            _field("serial_no", "序列号", reqd=1, unique=1, in_list_view=1),
            _field("chassis_no", "车架号", reqd=1, unique=1, in_list_view=1),
            _field("shibeida_model", "事倍达型号", in_list_view=1),
            _field("fork_size", "货叉尺寸", in_list_view=1),
            _field("product_color", "产品颜色", "Select", options="黄色\n灰色\n红色\n蓝色\n其他", in_list_view=1),
            _field("special_config", "特殊配置"),
            _field("offline_change", "线下改单", "Check", in_list_view=1),
        ],
        autoname="VD-.YYYY.-.#####",
        search_fields="chassis_no, serial_no, hangcha_model, shibeida_model",
    )


def create_special_part_registration():
    return _make_doctype(
        "Special Part Registration",
        [
            _field("serial_no", "序列号", in_list_view=1),
            _field("chassis_no", "车架号", in_list_view=1),
            _field("vehicle_model", "车型", in_list_view=1),
            _field("fork_size", "货叉尺寸", in_list_view=1),
            _field("order_no", "订单号", in_list_view=1),
            _field(
                "tracking_status", "配件跟踪登记", "Select",
                options="已登记\n已发货\n生产中\n已装机\n完结", default="已登记", in_list_view=1,
            ),
            _field("production_date", "生产日期", "Date"),
            _field("remark", "备注", "Small Text"),
        ],
        autoname="SR-.YYYY.-.#####",
        search_fields="chassis_no, serial_no, order_no",
    )


def create_spare_part():
    return _make_doctype(
        "Spare Part",
        [
            _field("k3_code", "K3编码", reqd=1, unique=1, in_list_view=1),
            _field("e10_code", "E10品号", in_list_view=1),
            _field("part_name", "配件品名", in_list_view=1),
            _field("supplier", "供应商", "Link", options="Supplier", in_list_view=1),
            _field(
                "claim_requirement", "索赔需求", "Select",
                options="需提供旧件\n仅需清单\n供应商预赔无需清单&资料\n每月提供售后清单\n需资料",
                in_list_view=1,
            ),
            _field("erp_item", "ERP物料", "Link", options="Item", in_list_view=1),
        ],
        autoname="SP-.#####",
        search_fields="k3_code, e10_code, part_name",
    )


def create_fault_category():
    return _make_doctype(
        "Fault Category",
        [
            _field("category_name", "大类名称", reqd=1, in_list_view=1),
        ],
        naming_rule="Set by user",
        title_field="category_name",
        search_fields="category_name",
    )


def create_fault_part():
    return _make_doctype(
        "Fault Part",
        [
            _field("part_name", "部件名称", reqd=1, in_list_view=1),
            _field("category", "所属大类", "Link", options="Fault Category", reqd=1, in_list_view=1),
        ],
        naming_rule="Set by user",
        search_fields="part_name",
    )


def create_fault_phenomenon():
    return _make_doctype(
        "Fault Phenomenon",
        [
            _field("phenomenon", "故障现象", reqd=1, in_list_view=1),
            _field("part", "所属部件", "Link", options="Fault Part", reqd=1, in_list_view=1),
            _field("category", "所属大类", "Link", options="Fault Category", in_list_view=1),
        ],
        autoname="FPH-.#####",
        search_fields="phenomenon, part",
    )


def create_after_sales_option():
    """售后选项配置：所有下拉字段的选项源，用户可在后台自行增删（枚举可编辑）。"""
    return _make_doctype(
        "After Sales Option",
        [
            _field(
                "option_type", "选项类别", "Select",
                options="服务类型\n售后类型\n处理措施\nERP录入\nOA状态\n坏件寄回\n状态客户\n状态部门\n发货方式\n索赔需求\n客户回访\n售后波段",
                reqd=1, in_list_view=1,
            ),
            _field("option_value", "选项值", reqd=1, in_list_view=1),
            _field("sort_order", "排序", "Int", in_list_view=1),
            _field("is_active", "启用", "Check", default=1, in_list_view=1),
        ],
        autoname="ASO-.#####",
        search_fields="option_type, option_value",
        title_field="option_value",
    )


def create_service_part_item():
    """售后配件明细（child table）：故障部件 / 三包新件 / 坏件追回 / 发货信息。"""
    return _make_doctype(
        "Service Part Item",
        [
            # 故障部件
            _field("section_fault", "故障部件", "Section Break"),
            _field("batch_no", "坏件批次号"),
            _field("usage_duration", "使用时长"),
            _field("old_part_code", "老配件编码", in_list_view=1),
            _field("old_part_name", "老配件名称", in_list_view=1),
            _field("fault_part_supplier", "故障部件供应商", "Link", options="Supplier"),
            _field(
                "claim_requirement", "索赔需求", "Select",
                options="需提供旧件\n仅需清单\n供应商预赔无需清单&资料\n每月提供售后清单\n需资料",
            ),
            _field("need_return", "坏件需要寄回", "Select", options="是\n否", in_list_view=1),
            # 三包新件
            _field("section_new_part", "三包新件", "Section Break"),
            _field("new_part_code", "新配件编码", in_list_view=1),
            _field("new_part_name", "新配件名称", in_list_view=1),
            _field("erp_qty", "ERP发货数量", "Int", in_list_view=1),
            _field("gift_qty", "本单赠送数量", "Int", in_list_view=1),
            _field("actual_claim_qty", "本单实际索赔数量", "Int", in_list_view=1),
            _field("erp_new_code", "新配件编码录ERP"),
            # 坏件追回
            _field("section_recall", "坏件追回", "Section Break"),
            _field("return_focus", "坏件需要重点关注"),
            _field("bad_part_arrived", "坏件到货日期", "Date"),
            _field("returned_to_factory", "退回工厂日期", "Date"),
            _field("return_remark", "坏件退回备注", "Small Text"),
            _field("factory_claim_date", "向工厂索赔日期", "Date"),
            _field("supplier_claim_date", "工厂已向供应商索赔日期", "Date"),
            _field("unclaimed_remark", "未赔备注", "Small Text"),
            # 发货信息
            _field("section_ship", "发货信息", "Section Break"),
            _field("ship_date", "发货日期", "Date"),
            _field(
                "ship_method", "发货方式", "Select",
                options="顺丰寄付\n顺丰到付\n中通\n圆通\n韵达\n德邦\n随车",
            ),
            _field("tracking_no", "快递/物流/随车单号"),
            _field("recipient", "收件人"),
            _field("phone", "电话"),
            _field("address", "寄件地址", "Small Text"),
            _field("ship_region", "发货区域"),
            # 故障资料（自动归档：售后资料/{车型}/{YYYY-MM}/{部件}）
            _field("section_files", "故障资料（图片/视频，拖拽上传自动归档）", "Section Break"),
            _field("fault_photo", "故障图片", "Attach Image"),
            _field("fault_video", "故障视频", "Attach"),
        ],
        istable=1,
        search_fields="old_part_code, new_part_code, batch_no",
    )


def create_service_request():
    """售后登记主表：服务内容 + 车辆信息 + 配件明细(child) + 公式统计区。"""
    return _make_doctype(
        "Service Request",
        [
            # 服务内容
            _field("section_service", "服务内容", "Section Break"),
            _field("feedback_date", "反馈日期", "Date", reqd=1, in_list_view=1),
            _field(
                "oa_status", "OA", "Select",
                options="N\nY\n撤销",
            ),
            _field(
                "erp_recorded", "ERP录入", "Select",
                options="OK\n——\n看详情",
            ),
            _field("customer", "客户简称", "Link", options="Customer", in_list_view=1),
            _field("contact_person", "对接人", in_list_view=1),
            _field(
                "service_type", "服务类型", "Select",
                options="普通索赔\n特殊申请\n附带索赔",
                reqd=1, in_list_view=1,
            ),
            _field("fault_description", "故障描述（全过程跟踪）", "Text Editor"),
            _field(
                "handling_action", "处理措施", "Select",
                options="索赔配件\n赔钱\n赠送",
            ),
            _field(
                "after_sale_type", "售后类型", "Select",
                options="已改善项\n待改进项\n批量隐患\n人为因素",
            ),
            # 配件明细
            _field("section_parts", "故障部件 / 三包新件 / 发货", "Section Break"),
            _field("parts", "配件明细", "Table", options="Service Part Item"),
            # 车辆信息
            _field("section_vehicle", "车辆信息", "Section Break"),
            _field("chassis_no", "车辆铭牌", reqd=1, in_list_view=1),
            _field("vehicle_model", "车型", in_list_view=1),
            _field("special_part_tracking", "特殊配件跟踪"),
            _field("exception_reason", "异常售后必填项（使用环境/运输货品等）", "Small Text"),
            _field("special_config", "车辆下单时的特殊配置"),
            _field("manufacture_date", "出厂日期", "Date"),
            _field("days_since_manufacture", "出厂天数", "Int"),
            _field(
                "after_sale_band", "售后波段", "Select",
                options="A\nB\nC",
            ),
            # 公式统计区
            _field("section_stats", "统计 / 状态", "Section Break"),
            _field(
                "customer_status", "状态（客户）", "Select",
                options="已接单\n已发货\n完成",
            ),
            _field(
                "department_status", "状态（部门）", "Select",
                options="索赔件已发\n坏件已退回\n完成",
            ),
            _field("claim_month", "索赔月份"),
            _field("claim_week", "索赔周数"),
            _field("manufacture_month", "出厂月份"),
            _field(
                "customer_callback", "客户回访", "Select",
                options="待回访\n已回访",
            ),
        ],
        autoname="service.YYYY.MM.####",
        search_fields="chassis_no, customer, feedback_date",
    )


def create_claim_order_item():
    """索赔单明细（child table）。"""
    return _make_doctype(
        "Claim Order Item",
        [
            _field("part_code", "配件编码", in_list_view=1),
            _field("part_name", "配件名称", in_list_view=1),
            _field("erp_item", "ERP物料", "Link", options="Item", in_list_view=1),
            _field("qty", "数量", "Int", default=1, in_list_view=1),
            _field("supplier", "供应商", "Link", options="Supplier", in_list_view=1),
            _field("claim_requirement", "索赔需求", "Select", options="需提供旧件\n仅需清单\n供应商预赔无需清单&资料\n每月提供售后清单\n需资料"),
        ],
        istable=1,
        search_fields="part_code, part_name",
    )


def create_claim_order():
    """索赔单：由售后登记提交后自动创建，负责生成 ERP 出库单（Delivery Note）。"""
    return _make_doctype(
        "Claim Order",
        [
            _field("section_main", "索赔信息", "Section Break"),
            _field("service_request", "售后登记", "Link", options="Service Request", reqd=1, in_list_view=1),
            _field("customer", "客户简称", "Link", options="Customer", in_list_view=1),
            _field("claim_date", "索赔日期", "Date", reqd=1, in_list_view=1),
            _field(
                "status", "状态", "Select",
                options="草稿\n已生成出库\n已出库", default="草稿", in_list_view=1,
            ),
            _field("delivery_note", "出库单", "Link", options="Delivery Note"),
            _field("remark", "备注"),
            _field("section_items", "索赔明细", "Section Break"),
            _field("items", "索赔明细", "Table", options="Claim Order Item"),
        ],
        autoname="CLM-.YYYY.-.####",
        search_fields="service_request, customer",
    )


def create_dn_custom_field():
    """Delivery Note 增加「售后服务单号」自定义字段（业务规范：服务单号必须进出库单备注栏）。"""
    if frappe.db.exists("Custom Field", "Delivery Note-custom_service_request"):
        return
    frappe.get_doc(
        {
            "doctype": "Custom Field",
            "dt": "Delivery Note",
            "fieldname": "custom_service_request",
            "label": "售后服务单号",
            "fieldtype": "Data",
            "insert_after": "title",
            "read_only": 1,
            "in_list_view": 1,
        }
    ).insert()


def create_old_part_recall_reminder():
    """追回提醒历史（child table）。"""
    return _make_doctype(
        "Old Part Recall Reminder",
        [
            _field("remind_date", "提醒日期", "Date", reqd=1, in_list_view=1),
            _field("remind_by", "提醒人"),
            _field("note", "备注"),
        ],
        istable=1,
    )


def create_quality_issue_action():
    """质量闭环行动项（child table）：吹哨处理 / 批量处理 / 落地步骤。"""
    return _make_doctype(
        "Quality Issue Action",
        [
            _field("action_type", "行动类型", "Select", options="吹哨处理\n批量处理\n落地步骤", in_list_view=1),
            _field("description", "行动内容", reqd=1, in_list_view=1),
            _field("owner_department", "责任部门", in_list_view=1),
            _field("owner_person", "责任人"),
            _field(
                "status", "状态", "Select",
                options="未开始\n进行中\n已完成", default="未开始", in_list_view=1,
            ),
            _field("due_date", "截止日期", "Date"),
        ],
        istable=1,
    )


def create_quality_issue_closure():
    """质量问题闭环（终稿流程图 2026-08-27）：定性判断 → 吹哨分级 → 批量处理 → 原因分析 → 方案评审 → 方案落地。"""
    return _make_doctype(
        "Quality Issue Closure",
        [
            # 问题信息
            _field("section_issue", "问题信息", "Section Break"),
            _field("service_request", "售后登记", "Link", options="Service Request", in_list_view=1),
            _field("issue_title", "问题标题", in_list_view=1),
            _field("feedback_date", "反馈日期", "Date", in_list_view=1),
            _field("chassis_no", "车辆铭牌"),
            _field("customer", "客户简称", "Link", options="Customer"),
            _field("fault_part", "故障部件"),
            _field("fault_description", "故障描述", "Text"),
            # 问题定性（终稿 1 阶段）
            _field("section_classify", "问题定性判断", "Section Break"),
            _field(
                "issue_classification", "问题定性", "Select",
                options="安全法规类\n设计缺陷\n一周内新增≥3起（批量隐患）\n新故障现象\n新车型验证期问题（12个月）\n改进项-再发\n以上均不是",
                in_list_view=1,
            ),
            _field("is_batch_issue", "批量问题（b/c 类触发批量处理）", "Check"),
            # 吹哨分级（终稿 2 阶段）
            _field("section_whistle", "吹哨分级与处理", "Section Break"),
            _field("whistleblower", "吹哨人", "Select", options="售后\n工厂"),
            _field(
                "whistle_level", "吹哨等级", "Select",
                options="红色\n橙色\n黄色\n绿色",
                help="红色→黄色→绿色，重要紧急程度依次降低",
            ),
            _field("whistle_action_summary", "吹哨处理动作", "Text"),
            # 闭环状态与原因分析（终稿 4 阶段）
            _field("section_closure", "闭环状态", "Section Break"),
            _field(
                "status", "状态", "Select",
                options="待定性\n已定性\n原因分析中\n方案评审中\n方案落地中\n完整闭环\n阶段性闭环\n已搁置",
                default="待定性", in_list_view=1,
            ),
            _field("root_cause", "真因分析", "Small Text"),
            _field("root_cause_found", "是否找到真因", "Select", options="已找到\n未找到"),
            _field("has_solution", "是否有解决方案", "Select", options="有方案\n无方案"),
            _field("improvement_plan", "改进方案", "Small Text"),
            _field(
                "review_result", "方案评审结果", "Select",
                options="通过\n不通过\n暂不启用（成本/故障率低）",
            ),
            _field("review_date", "评审日期", "Date"),
            _field("8d_report", "8D 报告", "Attach"),
            _field("improvement_report", "改进报告（对外版）", "Attach"),
            _field("change_request_no", "变更编号（研发）"),
            _field("closed_date", "闭环日期", "Date"),
            _field("remark", "备注"),
            # 行动项（吹哨/批量/落地）
            _field("section_actions", "行动项（吹哨处理/批量处理/落地步骤）", "Section Break"),
            _field("actions", "行动项", "Table", options="Quality Issue Action"),
        ],
        autoname="QC-.YYYY.-.####",
        search_fields="issue_title, service_request, chassis_no",
    )


def create_claim_list_item():
    """索赔清单明细（child table）。"""
    return _make_doctype(
        "Claim List Item",
        [
            _field("service_request", "售后登记", "Link", options="Service Request", in_list_view=1),
            _field("part_code", "配件编码", in_list_view=1),
            _field("part_name", "配件名称", in_list_view=1),
            _field("qty", "数量", "Int", default=1, in_list_view=1),
            _field("supplier", "供应商", "Link", options="Supplier", in_list_view=1),
            _field("claim_requirement", "索赔需求", "Select", options="需提供旧件\n仅需清单\n供应商预赔无需清单&资料\n每月提供售后清单\n需资料"),
            _field("chassis_no", "车辆铭牌"),
            _field("fault_summary", "故障简述"),
            _field("claim_month", "索赔月份"),
            _field("claim_week", "索赔周数"),
            _field("factory_claim_date", "向工厂索赔日期", "Date"),
            _field("supplier_claim_date", "工厂已向供应商索赔日期", "Date"),
            _field("remark", "备注"),
        ],
        istable=1,
        search_fields="part_code, part_name, service_request",
    )


def create_claim_list():
    """供应商索赔清单：每月自动生成「无需实物」索赔项，同步采购处理。"""
    return _make_doctype(
        "Claim List",
        [
            _field("month", "索赔月份", "Data", reqd=1, in_list_view=1),
            _field(
                "status", "状态", "Select",
                options="草稿\n已发送采购\n已核对", default="草稿", in_list_view=1,
            ),
            _field("supplier_count", "供应商数", "Int", in_list_view=1),
            _field("item_count", "明细数", "Int", in_list_view=1),
            _field("total_qty", "总数量", "Int", in_list_view=1),
            _field("generated_on", "生成日期", "Date"),
            _field("remark", "备注"),
            _field("section_items", "清单明细", "Section Break"),
            _field("items", "清单明细", "Table", options="Claim List Item"),
        ],
        # 命名由 generate_monthly_claim_list 显式指定（CL-YYYY-MM），不设 autoname
        search_fields="month, status",
        title_field="month",
    )


def create_old_part_recall():
    """旧件追回：坏件需要寄回的配件，发货一周后按周提醒，直至已追回或超 60 天终止。"""
    return _make_doctype(
        "Old Part Recall",
        [
            _field("section_main", "追回信息", "Section Break"),
            _field("service_request", "售后登记", "Link", options="Service Request", in_list_view=1),
            _field("chassis_no", "车辆铭牌", in_list_view=1),
            _field("customer", "客户简称", "Link", options="Customer", in_list_view=1),
            _field("part_code", "配件编码", in_list_view=1),
            _field("part_name", "配件名称", in_list_view=1),
            _field("supplier", "配件供应商", "Link", options="Supplier", in_list_view=1),
            _field("ship_date", "发货日期", "Date", in_list_view=1),
            _field(
                "trigger_type", "触发类型", "Select",
                options="坏件需寄回\n新品验证\n特定品号", default="坏件需寄回", in_list_view=1,
            ),
            _field(
                "status", "状态", "Select",
                options="待提醒\n已提醒\n已追回\n超时终止", default="待提醒", in_list_view=1,
            ),
            _field("first_remind_date", "首次提醒日期", "Date"),
            _field("last_remind_date", "最近提醒日期", "Date"),
            _field("remind_count", "已提醒次数", "Int"),
            _field("bad_part_arrived", "坏件到货日期", "Date"),
            _field("returned_to_factory", "退回工厂日期", "Date"),
            _field("remark", "备注"),
            _field("section_history", "提醒历史", "Section Break"),
            _field("reminders", "提醒历史", "Table", options="Old Part Recall Reminder"),
        ],
        autoname="RCL-.YYYY.-.####",
        search_fields="part_code, part_name, chassis_no, service_request",
    )


def after_install():
    for func in (
        create_vehicle_delivery,
        create_special_part_registration,
        create_spare_part,
        create_fault_category,
        create_fault_part,
        create_fault_phenomenon,
        create_after_sales_option,
        create_service_part_item,
        create_service_request,
        create_claim_order_item,
        create_claim_order,
    ):
        func()
    sync_dynamic_options()
    sync_spare_part_erp_item()
    create_dn_custom_field()
    create_old_part_recall_reminder()
    create_old_part_recall()
    create_claim_list_item()
    create_claim_list()
    create_quality_issue_action()
    create_quality_issue_closure()
    create_after_sales_manager_role()
    create_service_request_workflow()
    create_improvement_record()
    frappe.db.commit()


# 字段 → 配置表「选项类别」映射（sync_dynamic_options 使用）
FIELD_OPTION_MAP = {
    "Service Request": {
        "oa_status": "OA状态",
        "erp_recorded": "ERP录入",
        "service_type": "服务类型",
        "handling_action": "处理措施",
        "after_sale_type": "售后类型",
        "after_sale_band": "售后波段",
        "customer_status": "状态客户",
        "department_status": "状态部门",
        "customer_callback": "客户回访",
    },
    "Service Part Item": {
        "claim_requirement": "索赔需求",
        "ship_method": "发货方式",
    },
    "Spare Part": {
        "claim_requirement": "索赔需求",
    },
}


def sync_dynamic_options():
    """把「售后选项」配置表中的选项同步到各 Select 字段（幂等，可重复执行）。

    用户后台修改选项后，执行本函数即可让下拉字段的选项生效：
    bench --site dev.localhost execute "frappe.get_attr('aftersales.after_sales.setup.sync_dynamic_options')()"
    """
    if not frappe.db.exists("DocType", "After Sales Option"):
        return
    for doctype, fields in FIELD_OPTION_MAP.items():
        if not frappe.db.exists("DocType", doctype):
            continue
        dt = frappe.get_doc("DocType", doctype)
        changed = False
        for f in dt.fields:
            if f.fieldname in fields:
                values = frappe.get_all(
                    "After Sales Option",
                    filters={"option_type": fields[f.fieldname], "is_active": 1},
                    fields=["option_value"],
                    order_by="sort_order asc, creation asc",
                    limit_page_length=0,
                    pluck="option_value",
                )
                new_opts = "\n".join([v for v in values if v])
                if new_opts and f.options != new_opts:
                    f.options = new_opts
                    changed = True
        if changed:
            dt.save(ignore_permissions=True)
    frappe.db.commit()


def sync_spare_part_erp_item():
    """为已存在的 Spare Part DocType 补充 erp_item 字段（幂等）。"""
    if not frappe.db.exists("DocType", "Spare Part"):
        return
    dt = frappe.get_doc("DocType", "Spare Part")
    if not any(f.fieldname == "erp_item" for f in dt.fields):
        dt.append(
            "fields",
            {
                "fieldname": "erp_item",
                "label": "ERP物料",
                "fieldtype": "Link",
                "options": "Item",
                "in_list_view": 1,
            },
        )
        dt.save(ignore_permissions=True)
        frappe.db.commit()


def sync_service_part_item_attachments():
    """为已存在的 Service Part Item 补充故障资料附件字段（幂等）。"""
    if not frappe.db.exists("DocType", "Service Part Item"):
        return
    dt = frappe.get_doc("DocType", "Service Part Item")
    fields = [
        {"fieldname": "section_files", "label": "故障资料（图片/视频，拖拽上传自动归档）", "fieldtype": "Section Break"},
        {"fieldname": "fault_photo", "label": "故障图片", "fieldtype": "Attach Image"},
        {"fieldname": "fault_video", "label": "故障视频", "fieldtype": "Attach"},
    ]
    existing = {f.fieldname for f in dt.fields}
    added = False
    for f in fields:
        if f["fieldname"] not in existing:
            dt.append("fields", f)
            added = True
    if added:
        dt.save(ignore_permissions=True)
        frappe.db.commit()

# ---------- 角色与权限 ----------
ROLE_AFTER_SALES = "After Sales"
ROLE_PURCHASE = "Purchase User"
ROLE_QUALITY = "Quality Manager"

# DocType 权限矩阵：角色 → 权限级别（r=读 w=写 c=创建）
PERMISSIONS_MATRIX = {
    "Service Request": {ROLE_AFTER_SALES: "rwc", ROLE_PURCHASE: "r", ROLE_QUALITY: "r"},
    "Service Part Item": {ROLE_AFTER_SALES: "rwc", ROLE_PURCHASE: "r", ROLE_QUALITY: "r"},
    "Claim Order": {ROLE_AFTER_SALES: "rwc", ROLE_PURCHASE: "r", ROLE_QUALITY: "r"},
    "Claim Order Item": {ROLE_AFTER_SALES: "rwc", ROLE_PURCHASE: "r", ROLE_QUALITY: "r"},
    "Old Part Recall": {ROLE_AFTER_SALES: "rwc", ROLE_PURCHASE: "r", ROLE_QUALITY: "r"},
    "Old Part Recall Reminder": {ROLE_AFTER_SALES: "rwc", ROLE_PURCHASE: "r", ROLE_QUALITY: "r"},
    "Claim List": {ROLE_AFTER_SALES: "rwc", ROLE_PURCHASE: "rw", ROLE_QUALITY: "r"},
    "Claim List Item": {ROLE_AFTER_SALES: "rwc", ROLE_PURCHASE: "rw", ROLE_QUALITY: "r"},
    "Spare Part": {ROLE_AFTER_SALES: "rw", ROLE_PURCHASE: "rw", ROLE_QUALITY: "r"},
    "Vehicle Delivery": {ROLE_AFTER_SALES: "rw", ROLE_PURCHASE: "r", ROLE_QUALITY: "r"},
    "Special Part Registration": {ROLE_AFTER_SALES: "rw", ROLE_PURCHASE: "r", ROLE_QUALITY: "r"},
    "After Sales Option": {ROLE_AFTER_SALES: "rw"},
    "Fault Category": {ROLE_AFTER_SALES: "rw", ROLE_PURCHASE: "r", ROLE_QUALITY: "r"},
    "Fault Part": {ROLE_AFTER_SALES: "rw", ROLE_PURCHASE: "r", ROLE_QUALITY: "r"},
    "Fault Phenomenon": {ROLE_AFTER_SALES: "rw", ROLE_PURCHASE: "r", ROLE_QUALITY: "r"},
    "Quality Issue Closure": {ROLE_AFTER_SALES: "rw", ROLE_PURCHASE: "r", ROLE_QUALITY: "rwc"},
    "Quality Issue Action": {ROLE_AFTER_SALES: "rwc", ROLE_PURCHASE: "r", ROLE_QUALITY: "rwc"},
    "File": {ROLE_AFTER_SALES: "r", ROLE_PURCHASE: "r", ROLE_QUALITY: "r"},
}


def _perm_row(role, level):
    """level: r=读 w=写 c=创建。注意 DocPerm 的 Check 字段默认值均为 1，必须显式置 0。"""
    return {
        "role": role,
        "read": 1,
        "write": 1 if "w" in level else 0,
        "create": 1 if "c" in level else 0,
        "delete": 0,
        "submit": 0,
        "amend": 0,
        "cancel": 0,
        "export": 1,
        "print": 1,
        "email": 1,
        "share": 1,
    }


def sync_roles_and_permissions():
    """创建售后角色并分配 DocType 权限（幂等，可重复执行）。

    角色：After Sales（新建） / Purchase User（复用 ERPNext）/ Quality Manager（复用）
    保留 System Manager 全权限，仅新增业务角色权限。
    """
    # 1) 创建售后角色
    if not frappe.db.exists("Role", ROLE_AFTER_SALES):
        frappe.get_doc(
            {
                "doctype": "Role",
                "role_name": ROLE_AFTER_SALES,
                "desk_access": 1,
                "is_custom": 1,
            }
        ).insert(ignore_permissions=True)

    # 2) 分配权限（先删除业务角色旧权限，再按矩阵重建，保证幂等且不残留）
    for doctype, role_perm in PERMISSIONS_MATRIX.items():
        if not frappe.db.exists("DocType", doctype):
            continue
        business_roles = list(role_perm.keys())
        placeholders = ",".join(["%s"] * len(business_roles))
        frappe.db.sql(
            f"DELETE FROM `tabDocPerm` WHERE parent=%s AND role IN ({placeholders})",
            (doctype, *business_roles),
        )
        dt = frappe.get_doc("DocType", doctype)
        for role, level in role_perm.items():
            dt.append("permissions", _perm_row(role, level))
        dt.save(ignore_permissions=True)
    frappe.db.commit()
    return {"role_created": frappe.db.exists("Role", ROLE_AFTER_SALES), "doctypes": len(PERMISSIONS_MATRIX)}


# ---------- 审批流程（售后登记一级审批，对齐业务 OA 环节） ----------
ROLE_AFTER_SALES_MANAGER = "After Sales Manager"


def create_after_sales_manager_role():
    """售后主管角色（一级审批人）。"""
    if not frappe.db.exists("Role", ROLE_AFTER_SALES_MANAGER):
        frappe.get_doc(
            {
                "doctype": "Role",
                "role_name": ROLE_AFTER_SALES_MANAGER,
                "desk_access": 1,
                "is_custom": 1,
            }
        ).insert(ignore_permissions=True)


def create_service_request_workflow():
    """售后登记一级审批 Workflow（幂等）。

    草稿 → 提交 → 待审批 → 审批通过（docstatus=1，触发 on_submit 业务联动）/
                           驳回 → 草稿（可修改后重新提交）
    审批人角色：After Sales Manager（售后主管）
    """
    # workflow_state 字段修正（幂等）：Frappe 自动创建为 Link（按记录名校验状态名会失败），改为 Data
    if frappe.db.get_value("Custom Field", "Service Request-workflow_state", "fieldtype") != "Data":
        frappe.db.set_value("Custom Field", "Service Request-workflow_state", "fieldtype", "Data")
        frappe.db.set_value("Custom Field", "Service Request-workflow_state", "options", "")
        frappe.clear_cache(doctype="Service Request")
        frappe.db.commit()
    # 审批角色需要售后登记读写权限（幂等）
    sr_dt = frappe.get_doc("DocType", "Service Request")
    if ROLE_AFTER_SALES_MANAGER not in {p.role for p in sr_dt.permissions}:
        sr_dt.append("permissions", _perm_row(ROLE_AFTER_SALES_MANAGER, "rw"))
        sr_dt.save(ignore_permissions=True)

    if frappe.db.exists("Workflow", "售后登记-一级审批"):
        return
    frappe.get_doc(
        {
            "doctype": "Workflow",
            "workflow_name": "售后登记-一级审批",
            "document_type": "Service Request",
            "is_active": 1,
            "workflow_state_field": "workflow_state",
            "send_email_alert": 0,
            "states": [
                {"state": "草稿", "doc_status": "0", "allow_edit": "After Sales"},
                {"state": "待审批", "doc_status": "0", "allow_edit": "After Sales Manager"},
                {"state": "已通过", "doc_status": "1", "allow_edit": "System Manager"},
                {"state": "已驳回", "doc_status": "0", "allow_edit": "After Sales"},
            ],
            "transitions": [
                # 售后提交
                {"state": "草稿", "action": "提交审批", "next_state": "待审批", "allowed": "After Sales", "allow_self_approval": 1},
                # 主管审批
                {"state": "待审批", "action": "审批通过", "next_state": "已通过", "allowed": ROLE_AFTER_SALES_MANAGER, "allow_self_approval": 1},
                {"state": "待审批", "action": "驳回", "next_state": "已驳回", "allowed": ROLE_AFTER_SALES_MANAGER, "allow_self_approval": 1},
                # 驳回后修改重新提交
                {"state": "已驳回", "action": "重新提交", "next_state": "待审批", "allowed": "After Sales", "allow_self_approval": 1},
            ],
        }
    ).insert(ignore_permissions=True, ignore_links=True)


# ---------- 改进记录（供"改进-再发"比对） ----------
def create_improvement_record():
    """改进记录：维护改进日期、部件、现象、批次，供售后登记自动比对"改进-再发"。"""
    return _make_doctype(
        "Improvement Record",
        [
            _field("part_code", "配件编码", in_list_view=1),
            _field("part_name", "配件名称", in_list_view=1),
            _field("fault_phenomenon", "故障现象", in_list_view=1),
            _field("improvement_date", "改进日期", "Date", reqd=1, in_list_view=1),
            _field("improvement_desc", "改进说明", "Small Text", in_list_view=1),
            _field("vehicle_model", "涉及车型", "Link", options="Vehicle Delivery"),
            _field("batch_no", "涉及批次"),
            _field("supplier", "供应商", "Link", options="Supplier"),
            _field("change_request_no", "变更编号"),
            _field("status", "状态", "Select", options="已改进\n验证中", default="验证中"),
            _field("remark", "备注"),
        ],
        autoname="IMP-.YYYY.-.####",
        search_fields="part_code, part_name, fault_phenomenon",
    )
