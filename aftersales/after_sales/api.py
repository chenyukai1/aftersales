"""查询 API（契约与 Mock 版一致：POST /api/method/aftersales.after_sales.api.get_vehicle_info 等）。"""
import frappe


def _find_by(doctype, filters):
    names = frappe.get_all(doctype, filters=filters, limit=1, pluck="name")
    return names[0] if names else None


def _result(status, data=None, message=None):
    return {"status": status, "data": data, "message": message}


@frappe.whitelist()
def get_vehicle_info(key=None, chassis_no=None, serial_no=None):
    """入参：车架号或序列号（key 或 chassis_no / serial_no）。
    返回：{status, data:{vehicle, parts_registration, count}, message}"""
    key = (key or chassis_no or serial_no or "").strip()
    if not key:
        return _result("error", message="参数缺失：请提供 车架号 或 序列号")

    name = _find_by("Vehicle Delivery", {"chassis_no": key}) or _find_by(
        "Vehicle Delivery", {"serial_no": key}
    )
    if not name:
        return _result("not_found", message=f'未找到车架号或序列号为 "{key}" 的整车发货记录')

    vehicle = frappe.get_doc("Vehicle Delivery", name).as_dict()
    parts = frappe.get_all(
        "Special Part Registration",
        filters={"chassis_no": vehicle["chassis_no"]},
        fields=["*"],
    )
    return _result("success", data={"vehicle": vehicle, "parts_registration": parts, "count": len(parts)})


@frappe.whitelist()
def get_part_info(key=None, k3_code=None):
    """入参：K3 编码。返回：{status, data:{part}, message}"""
    key = (key or k3_code or "").strip()
    if not key:
        return _result("error", message="参数缺失：请提供 K3 编码")

    name = _find_by("Spare Part", {"k3_code": key})
    if not name:
        return _result("not_found", message=f'未找到 K3 编码为 "{key}" 的配件记录')

    return _result("success", data={"part": frappe.get_doc("Spare Part", name).as_dict()})