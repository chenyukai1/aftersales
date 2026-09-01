"""故障资料自动归档：上传的图片/视频按 车型/月份/部件 自动归类。

对齐需求讨论 47:56/54:18：故障视频/图片支持拖拽上传，系统根据车型、月份、部件
自动分类归档，售后与采购共同调用。

归档目录：Home/售后资料/{车型}/{YYYY-MM}/{部件}/
文件重命名：{服务单号}_{部件}_{4位随机}.{扩展名}
"""
import frappe

ARCHIVE_ROOT = "Home/售后资料"


def _ensure_folder(path):
    """逐级创建文件夹层级（File is_folder=1），返回完整路径。"""
    parts = [p for p in path.strip("/").split("/") if p]
    parent = "Home"
    for i, seg in enumerate(parts):
        if i == 0:
            continue  # Home 为系统根目录，已存在
        if not frappe.db.exists("File", {"is_folder": 1, "file_name": seg, "folder": parent}):
            frappe.get_doc(
                {
                    "doctype": "File",
                    "file_name": seg,
                    "is_folder": 1,
                    "folder": parent,
                }
            ).insert(ignore_permissions=True)
        parent = f"{parent}/{seg}"
    return parent


def archive_file_on_upload(file_doc, method):
    """File 上传/更新事件：仅处理关联到售后配件明细（Service Part Item）的文件。"""
    if file_doc.is_folder:
        return
    # 已归档的文件跳过（避免递归）
    if file_doc.folder and file_doc.folder.startswith(ARCHIVE_ROOT + "/"):
        return
    if file_doc.attached_to_doctype != "Service Part Item":
        return

    row = frappe.db.get_value(
        "Service Part Item",
        file_doc.attached_to_name,
        ["parent", "new_part_code", "new_part_name"],
        as_dict=True,
    )
    if not row:
        return
    sr = frappe.db.get_value(
        "Service Request",
        row.parent,
        ["name", "vehicle_model", "feedback_date"],
        as_dict=True,
    )
    if not sr:
        return

    month = str(sr.feedback_date or "")[:7] or "未知月份"
    vehicle = sr.vehicle_model or "未知车型"
    part = row.new_part_name or row.new_part_code or "未知部件"
    folder_path = _ensure_folder(f"{ARCHIVE_ROOT}/{vehicle}/{month}/{part}")

    # 重命名：{服务单号}_{部件}_{随机4位}.{扩展名}
    orig_name = file_doc.file_name or (file_doc.file_url or "").split("/")[-1] or "file"
    ext = f".{orig_name.rsplit('.', 1)[1]}" if "." in orig_name else ""
    new_name = f"{sr.name}_{part}_{frappe.generate_hash(length=4)}{ext}"

    file_doc.folder = folder_path
    file_doc.file_name = new_name
    file_doc.save(ignore_permissions=True)
