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