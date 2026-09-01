"""清理回归测试残留数据（service2026090009 及其联动）。"""
import os

os.chdir("/home/frappe/frappe-bench/sites")
import frappe

frappe.init(site="dev.localhost", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()

sr_name = "service2026090009"
# 删除联动记录
for dt in ("Quality Issue Closure", "Old Part Recall"):
    for d in frappe.get_all(dt, filters={"service_request": sr_name}):
        frappe.delete_doc(dt, d.name, force=1)
for d in frappe.get_all("Claim Order", filters={"service_request": sr_name}):
    dn = frappe.db.get_value("Claim Order", d.name, "delivery_note")
    if dn:
        frappe.delete_doc("Delivery Note", dn, force=1)
    frappe.delete_doc("Claim Order", d.name, force=1)
# 删除售后单
frappe.delete_doc("Service Request", sr_name, force=1)
frappe.db.commit()
print("已清理 service2026090009 及其联动记录")

frappe.destroy()
