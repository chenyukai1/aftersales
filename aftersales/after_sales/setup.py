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
                options="需提供旧件\n仅需清单", in_list_view=1,
            ),
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


def after_install():
    for func in (
        create_vehicle_delivery,
        create_special_part_registration,
        create_spare_part,
        create_fault_category,
        create_fault_part,
        create_fault_phenomenon,
    ):
        func()
    frappe.db.commit()