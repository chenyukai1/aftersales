"""Service Part Item（售后配件明细，child table）Controller。

计算逻辑集中在父文档 ServiceRequest.validate() 中统一处理，
此处仅保留类定义供 Frappe 加载。
"""
from frappe.model.document import Document


class ServicePartItem(Document):
    pass
