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
    _ensure_api_key()
    frappe.db.commit()
    print(
        "seed done => 供应商:%d 整车:%d 配件登记:%d 配件主档:%d 故障大类:%d 部件:%d 现象:%d"
        % (
            frappe.db.count("Supplier", {"supplier_name": ["in", SUPPLIERS]}),
            frappe.db.count("Vehicle Delivery"),
            frappe.db.count("Special Part Registration"),
            frappe.db.count("Spare Part"),
            frappe.db.count("Fault Category"),
            frappe.db.count("Fault Part"),
            frappe.db.count("Fault Phenomenon"),
        )
    )