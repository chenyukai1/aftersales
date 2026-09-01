"""灌入演示用的 Mock 数据（与前端 Demo 的数据一致），并生成 Administrator 的 API Key。"""
import frappe


def _ensure(doc_def):
    try:
        frappe.get_doc(doc_def).insert(ignore_if_duplicate=True, ignore_permissions=True)
    except frappe.DuplicateEntryError:
        pass


SUPPLIERS = [
    "杭州液压密封件厂",
    "安徽合叉液压有限公司",
    "张家港货叉制造股份",
    "杭州转向传动科技",
    "天能电池集团",
    "无锡智能电控",
    "宁波灯具制造",
    "杭州制动器厂",
    "江苏威博",
    "华昌液压",
]

VEHICLES = [
    # (发货日期, 杭叉型号, 序列号, 车架号, 事倍达型号, 货叉尺寸, 颜色, 特殊配置, 线下改单)
    ("2026-01-15", "CPD20", "SN-20260115001", "HC-2026-0115-001", "SBD-20B", "920×100×35", "黄色", "无", 0),
    ("2026-02-03", "CPD30", "SN-20260203002", "HC-2026-0203-002", "SBD-30E", "1070×122×40", "黄色", "侧移器", 0),
    ("2026-02-27", "CPD35", "SN-20260227003", "HC-2026-0227-003", "SBD-35T", "1220×150×45", "灰色", "加长货叉(1500mm)", 1),
    ("2026-03-18", "CPD25", "SN-20260318004", "HC-2026-0318-004", "SBD-25L", "1100×125×40", "红色", "无", 0),
    ("2026-04-09", "CPD50", "SN-20260409005", "HC-2026-0409-005", "SBD-50X", "1300×160×50", "灰色", "侧移器+软包夹", 1),
    ("2026-05-12", "CPD30", "SN-20260512006", "HC-2026-0512-006", "SBD-30E", "1070×122×40", "黄色", "挡货架", 0),
    ("2026-06-06", "CPD20E", "SN-20260606007", "HC-2026-0606-007", "SBD-20B", "920×100×35", "蓝色", "无", 0),
    ("2026-06-28", "CPD45", "SN-20260628008", "HC-2026-0628-008", "SBD-45T", "1250×150×45", "灰色", "双货叉", 1),
    ("2026-07-17", "CPD30", "SN-20260717009", "HC-2026-0717-009", "SBD-30E", "1070×122×40", "黄色", "侧移器", 0),
    ("2026-08-02", "CPD25", "SN-20260802010", "HC-2026-0802-010", "SBD-25L", "1100×125×40", "红色", "无", 1),
]

PARTS_REG = [
    # (序列号, 车架号, 车型, 货叉尺寸, 订单号, 跟踪状态, 生产日期, 备注)
    ("SN-20260203002", "HC-2026-0203-002", "CPD30", "1070×122×40", "SO-2026020302", "已装机", "2026-01-28", "随车原装"),
    ("SN-20260227003", "HC-2026-0227-003", "CPD35", "1220×150×45", "SO-2026022703", "已装机", "2026-02-20", "加长货叉随车"),
    ("SN-20260409005", "HC-2026-0409-005", "CPD50", "1300×160×50", "SO-2026040905", "已发货", "2026-04-05", "软包夹补发"),
    ("SN-20260606007", "HC-2026-0606-007", "CPD20E", "920×100×35", "SO-2026060607", "生产中", "2026-05-30", "客户追加挡货架"),
    ("SN-20260717009", "HC-2026-0717-009", "CPD30", "1070×122×40", "SO-2026071709", "已登记", "2026-07-10", "售后补发货叉"),
    ("SN-20260802010", "HC-2026-0802-010", "CPD25", "1100×125×40", "SO-2026080210", "已登记", "2026-07-25", "线下改单补录"),
    ("SN-20260203002", "HC-2026-0203-002", "CPD30", "1070×122×40", "SO-2026020302-B", "已发货", "2026-02-15", "密封圈补发(售后)"),
]

SPARE_PARTS = [
    # (K3编码, E10品号, 品名, 供应商, 索赔需求)
    ("K3-000101", "45.310.0101", "起升油缸密封圈", "杭州液压密封件厂", "需提供旧件"),
    ("K3-000102", "45.310.0102", "多路阀总成", "安徽合叉液压有限公司", "需提供旧件"),
    ("K3-000103", "45.210.0103", "货叉 1070×122×40", "张家港货叉制造股份", "仅需清单"),
    ("K3-000104", "45.210.0104", "货叉 1220×150×45", "张家港货叉制造股份", "仅需清单"),
    ("K3-000105", "45.410.0105", "转向桥总成", "杭州转向传动科技", "需提供旧件"),
    ("K3-000106", "45.510.0106", "蓄电池 48V/540Ah", "天能电池集团", "仅需清单"),
    ("K3-000107", "45.610.0107", "电控单元 ECU", "无锡智能电控", "需提供旧件"),
    ("K3-000108", "45.310.0108", "液压泵总成", "安徽合叉液压有限公司", "需提供旧件"),
    ("K3-000109", "45.510.0109", "警示灯组件", "宁波灯具制造", "仅需清单"),
    ("K3-000110", "45.410.0110", "制动器总成", "杭州制动器厂", "需提供旧件"),
    # 真实业务样例（来自 2026-01-04 售后日志）
    ("31101166", "31.101.0166", "PU双轮 80*70mm 带轴承 (REACH认证)", "江苏威博", "供应商预赔无需清单&资料"),
    ("31101130", "31.101.0130", "液压站总成 (VIBO) 2.0T", "江苏威博", "每月提供售后清单"),
    ("31501014", "31.501.0014", "00842 油缸总成 (活塞杆直径Ø35)", "华昌液压", "需资料"),
    ("31201128", "31.201.0128", "承重轮组件", "江苏威博", "需提供旧件"),
    ("31502033", "31.502.0033", "液压站总成 (VIBO) 3.0T", "江苏威博", "每月提供售后清单"),
]

# 售后选项默认值（下拉字段选项源，用户可在后台「售后选项」中自行增删）
AFTER_SALES_OPTIONS = [
    # (选项类别, 选项值, 排序)
    ("服务类型", "普通索赔", 1), ("服务类型", "特殊申请", 2), ("服务类型", "附带索赔", 3),
    ("售后类型", "已改善项", 1), ("售后类型", "待改进项", 2), ("售后类型", "批量隐患", 3), ("售后类型", "人为因素", 4),
    ("处理措施", "索赔配件", 1), ("处理措施", "赔钱", 2), ("处理措施", "赠送", 3),
    ("ERP录入", "OK", 1), ("ERP录入", "——", 2), ("ERP录入", "看详情", 3),
    ("OA状态", "N", 1), ("OA状态", "Y", 2), ("OA状态", "撤销", 3),
    ("坏件寄回", "是", 1), ("坏件寄回", "否", 2),
    ("状态客户", "已接单", 1), ("状态客户", "已发货", 2), ("状态客户", "完成", 3),
    ("状态部门", "索赔件已发", 1), ("状态部门", "坏件已退回", 2), ("状态部门", "完成", 3),
    ("发货方式", "顺丰寄付", 1), ("发货方式", "顺丰到付", 2), ("发货方式", "中通", 3),
    ("发货方式", "圆通", 4), ("发货方式", "韵达", 5), ("发货方式", "德邦", 6), ("发货方式", "随车", 7),
    ("索赔需求", "需提供旧件", 1), ("索赔需求", "仅需清单", 2), ("索赔需求", "供应商预赔无需清单&资料", 3),
    ("索赔需求", "每月提供售后清单", 4), ("索赔需求", "需资料", 5),
    ("客户回访", "待回访", 1), ("客户回访", "已回访", 2),
    ("售后波段", "A", 1), ("售后波段", "B", 2), ("售后波段", "C", 3),
]

CUSTOMERS = [
    "零星客户",
    "吉安吉翔/江西雷翼",
    "杭州杭叉电子商务有限公司",
]

FAULT_DICT = [
    ("动力系统", [
        ("发动机", ["无法启动", "启动困难", "怠速不稳", "功率不足", "异响"]),
        ("驱动电机", ["不运转", "运转无力", "异响", "过热报警", "无法换向"]),
        ("蓄电池", ["掉电过快", "无法充电", "充电不识别", "鼓包漏液", "电压异常"]),
    ]),
    ("液压系统", [
        ("液压泵", ["无压力", "压力不足", "异响", "漏油", "温升过高"]),
        ("多路阀", ["阀杆卡滞", "内泄漏", "操作沉重", "异响", "复位不良"]),
        ("起升油缸", ["起升缓慢", "起升后下滑", "漏油", "缸筒划伤", "异响"]),
        ("油管接头", ["渗油", "爆管", "接头松脱", "老化裂纹"]),
    ]),
    ("转向系统", [
        ("转向桥总成", ["转向沉重", "跑偏", "异响", "主销松旷", "轮毂过热"]),
        ("动力转向器", ["转向失灵", "漏油", "异响", "左右转向轻重不一致"]),
        ("方向盘", ["自由行程过大", "回正不良", "抖动", "卡滞"]),
    ]),
    ("制动系统", [
        ("制动器", ["制动失灵", "制动力不足", "制动拖滞", "异响", "跑偏"]),
        ("制动油路", ["漏油", "油管破裂", "油路进气", "制动油液变质"]),
        ("制动踏板", ["踏板行程过大", "踏板回位不良", "踏板发软"]),
    ]),
    ("电气系统", [
        ("电控单元ECU", ["无输出", "报故障码", "通信中断", "程序丢失", "偶发断电"]),
        ("线束", ["断路", "短路", "插接件松动", "绝缘破损", "进水氧化"]),
        ("仪表盘", ["无显示", "显示异常", "背光不亮", "按键失灵", "报警乱闪"]),
        ("照明灯光", ["灯不亮", "灯光闪烁", "亮度不足", "灯罩进水"]),
        ("喇叭", ["无声", "声音嘶哑", "长鸣不止"]),
    ]),
    ("车身与属具", [
        ("货叉", ["叉体变形", "叉尖磨损", "裂纹", "定位销松脱"]),
        ("挡货架", ["变形", "焊接裂纹", "螺栓松脱"]),
        ("门架", ["升降卡滞", "异响", "倾斜发抖", "导轨磨损", "链条松弛"]),
        ("护顶架", ["变形", "固定螺栓缺失", "锈蚀穿孔"]),
    ]),
]


def _seed_suppliers():
    group = "All Supplier Groups"
    if not frappe.db.exists("Supplier Group", group):
        frappe.get_doc(
            {"doctype": "Supplier Group", "supplier_group_name": group}
        ).insert(ignore_permissions=True)
    for name in SUPPLIERS:
        if not frappe.db.exists("Supplier", {"supplier_name": name}):
            frappe.get_doc(
                {"doctype": "Supplier", "supplier_name": name, "supplier_group": group}
            ).insert(ignore_permissions=True)


def _seed_vehicles():
    for row in VEHICLES:
        if frappe.db.exists("Vehicle Delivery", {"chassis_no": row[3]}):
            continue
        frappe.get_doc(
            {
                "doctype": "Vehicle Delivery",
                "delivery_date": row[0],
                "hangcha_model": row[1],
                "serial_no": row[2],
                "chassis_no": row[3],
                "shibeida_model": row[4],
                "fork_size": row[5],
                "product_color": row[6],
                "special_config": row[7],
                "offline_change": row[8],
            }
        ).insert(ignore_permissions=True)


def _seed_parts_reg():
    for row in PARTS_REG:
        if frappe.db.exists("Special Part Registration", {"order_no": row[4], "serial_no": row[0]}):
            continue
        frappe.get_doc(
            {
                "doctype": "Special Part Registration",
                "serial_no": row[0],
                "chassis_no": row[1],
                "vehicle_model": row[2],
                "fork_size": row[3],
                "order_no": row[4],
                "tracking_status": row[5],
                "production_date": row[6],
                "remark": row[7],
            }
        ).insert(ignore_permissions=True)


def _seed_spare_parts():
    for row in SPARE_PARTS:
        if frappe.db.exists("Spare Part", {"k3_code": row[0]}):
            continue
        frappe.get_doc(
            {
                "doctype": "Spare Part",
                "k3_code": row[0],
                "e10_code": row[1],
                "part_name": row[2],
                "supplier": row[3],
                "claim_requirement": row[4],
            }
        ).insert(ignore_permissions=True)


def _seed_fault_dict():
    for cat_name, parts in FAULT_DICT:
        cat_code = frappe.get_doc(
            {"doctype": "Fault Category", "category_name": cat_name}
        ).insert(ignore_permissions=True).name
        for part_name, faults in parts:
            part_code = frappe.get_doc(
                {"doctype": "Fault Part", "part_name": part_name, "category": cat_code}
            ).insert(ignore_permissions=True).name
            for f in faults:
                if frappe.db.exists("Fault Phenomenon", {"phenomenon": f, "part": part_code}):
                    continue
                frappe.get_doc(
                    {
                        "doctype": "Fault Phenomenon",
                        "phenomenon": f,
                        "part": part_code,
                        "category": cat_code,
                    }
                ).insert(ignore_permissions=True)


def _seed_options():
    for otype, ovalue, sort in AFTER_SALES_OPTIONS:
        if frappe.db.exists("After Sales Option", {"option_type": otype, "option_value": ovalue}):
            continue
        frappe.get_doc(
            {
                "doctype": "After Sales Option",
                "option_type": otype,
                "option_value": ovalue,
                "sort_order": sort,
                "is_active": 1,
            }
        ).insert(ignore_permissions=True)


def _seed_customers():
    group_name = "售后客户"
    if not frappe.db.exists("Customer Group", group_name):
        frappe.get_doc(
            {
                "doctype": "Customer Group",
                "customer_group_name": group_name,
                "is_group": 0,
            }
        ).insert(ignore_permissions=True)
    for name in CUSTOMERS:
        if not frappe.db.exists("Customer", {"customer_name": name}):
            frappe.get_doc(
                {
                    "doctype": "Customer",
                    "customer_name": name,
                    "customer_group": group_name,
                    "territory": "All Territories",
                }
            ).insert(ignore_permissions=True)


# 演示售后单（对齐 2026-01-04 真实样例结构）
SERVICE_SAMPLES = [
    {
        "feedback_date": "2026-09-01",
        "customer": "零星客户",
        "contact_person": "大程",
        "service_type": "特殊申请",
        "handling_action": "赠送",
        "after_sale_type": "人为因素",
        "fault_description": "特殊申请赠送一个PU轮，新车轮子失圆",
        "chassis_no": "HC-2026-0115-001",
        "parts": [
            {
                "old_part_code": "31101166",
                "new_part_code": "31101166",
                "erp_qty": 1,
                "gift_qty": 0,
                "need_return": "否",
                "ship_method": "顺丰寄付",
                "tracking_no": "SF1564365977181",
                "recipient": "叶根财",
            }
        ],
    },
    {
        "feedback_date": "2026-09-01",
        "customer": "吉安吉翔/江西雷翼",
        "contact_person": "大程",
        "service_type": "普通索赔",
        "after_sale_type": "已改善项",
        "fault_description": "油缸耐磨环脱落，堵住下降电磁阀，导致车子无法起升，更换液压站+油缸",
        "chassis_no": "HC-2026-0203-002",
        "parts": [
            {
                "old_part_code": "31101130",
                "new_part_code": "31101130",
                "erp_qty": 1,
                "gift_qty": 0,
                "need_return": "是",
                "recipient": "刘清华",
            },
            {
                "old_part_code": "31501014",
                "new_part_code": "31501014",
                "erp_qty": 1,
                "gift_qty": 0,
                "need_return": "是",
                "recipient": "刘清华",
            },
        ],
    },
]


def _seed_service_samples():
    for row in SERVICE_SAMPLES:
        doc = frappe.get_doc(
            {
                "doctype": "Service Request",
                "feedback_date": row["feedback_date"],
                "customer": row["customer"],
                "contact_person": row.get("contact_person", ""),
                "service_type": row["service_type"],
                "handling_action": row.get("handling_action", ""),
                "after_sale_type": row.get("after_sale_type", ""),
                "fault_description": row.get("fault_description", ""),
                "chassis_no": row["chassis_no"],
                "parts": row["parts"],
            }
        )
        doc.insert(ignore_permissions=True)


def _seed_mock_items():
    """为配件主档创建 ERP 物料（mock：item_code=k3_code），并建立 erp_item 映射。

    仅处理数字开头的真实样例编码（如 31101130）；演示编码（K3-000xxx）不创建 Item。
    is_stock_item=0：不管理库存，保证演示环境出库不因库存不足失败。
    """
    item_group = "Products"
    if not frappe.db.exists("Item Group", item_group):
        frappe.get_doc(
            {"doctype": "Item Group", "item_group_name": item_group, "is_group": 0}
        ).insert(ignore_permissions=True)
    for sp in frappe.get_all("Spare Part", fields=["k3_code", "part_name"]):
        code = (sp.k3_code or "").strip()
        if not code or not code[0].isdigit():
            continue
        if not frappe.db.exists("Item", code):
            frappe.get_doc(
                {
                    "doctype": "Item",
                    "item_code": code,
                    "item_name": sp.part_name or code,
                    "item_group": item_group,
                    "stock_uom": "Nos",
                    "is_stock_item": 0,
                }
            ).insert(ignore_permissions=True)
        if not frappe.db.get_value("Spare Part", {"k3_code": code}, "erp_item"):
            frappe.db.set_value("Spare Part", {"k3_code": code}, "erp_item", code)


# 演示用户（售后/采购/质量部，密码均为 demo12345）
DEMO_USERS = [
    ("shouhou@demo.local", "售后演示", "After Sales"),
    ("caigou@demo.local", "采购演示", "Purchase User"),
    ("zhiliang@demo.local", "质量演示", "Quality Manager"),
]


def _seed_demo_users():
    for email, name, role in DEMO_USERS:
        if frappe.db.exists("User", email):
            continue
        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": name,
                "enabled": 1,
                "send_welcome_email": 0,
                "user_type": "System User",
                "roles": [{"role": role}],
            }
        )
        user.insert(ignore_permissions=True)
        frappe.utils.password.update_password(email, "demo12345")
        print(f"created user: {email} / {name} / {role}")


def _ensure_api_key():
    user = frappe.get_doc("User", "Administrator")
    if not user.api_key:
        user.api_key = frappe.generate_hash(length=15)
        user.api_secret = frappe.generate_hash(length=15)
        user.save(ignore_permissions=True)
        print("ADMIN_API_KEY=" + user.api_key)
        print("ADMIN_API_SECRET=" + user.api_secret)
    else:
        print("API key already exists (key=" + user.api_key + ")")


def run():
    _seed_suppliers()
    _seed_vehicles()
    _seed_parts_reg()
    _seed_spare_parts()
    _seed_fault_dict()
    _seed_options()
    _seed_customers()
    _seed_mock_items()
    _seed_service_samples()
    _seed_demo_users()
    _ensure_api_key()
    frappe.db.commit()
    print(
        "seed done => 供应商:%d 整车:%d 配件登记:%d 配件主档:%d 故障大类:%d 部件:%d 现象:%d 售后选项:%d 客户:%d 演示售后单:%d 物料映射:%d"
        % (
            frappe.db.count("Supplier", {"supplier_name": ["in", SUPPLIERS]}),
            frappe.db.count("Vehicle Delivery"),
            frappe.db.count("Special Part Registration"),
            frappe.db.count("Spare Part"),
            frappe.db.count("Fault Category"),
            frappe.db.count("Fault Part"),
            frappe.db.count("Fault Phenomenon"),
            frappe.db.count("After Sales Option"),
            frappe.db.count("Customer", {"customer_name": ["in", CUSTOMERS]}),
            frappe.db.count("Service Request"),
            frappe.db.count("Item", {"item_code": ["like", "3110%"]}),
        )
    )