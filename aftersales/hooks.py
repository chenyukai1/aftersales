app_name = "aftersales"
app_title = "售后管理"
app_publisher = "ZCode Demo"
app_description = "售后管理平台演示：整车发货 / 配件登记 / 配件主档 / 故障字典 / 查询 API"
app_icon = "octicon package-dependencies"
app_color = "blue"

required_apps = ["frappe", "erpnext"]

# 安装应用后自动创建自定义 DocType
after_install = "aftersales.after_sales.setup.after_install"

# 出库单提交后回写索赔单状态 / 售后登记 ERP录入状态
# 故障资料上传后自动归档（车型/月份/部件目录）
doc_events = {
    "Delivery Note": {
        "on_submit": "aftersales.after_sales.doctype.claim_order.claim_order.update_delivery_note_status",
    },
    "File": {
        "on_update": "aftersales.after_sales.archive.archive_file_on_upload",
    },
}

# 旧件追回：每日检查提醒 / 超时终止
# 批量隐患：每日扫描近7天相似故障
scheduler_events = {
    "daily_long": [
        "aftersales.after_sales.doctype.old_part_recall.old_part_recall.run_recall_scheduler",
        "aftersales.after_sales.batch_issue_monitor.scan_batch_issues",
    ],
    # 供应商索赔清单：每月 1 日凌晨 2 点自动生成上月清单
    "cron": {
        "0 2 1 * *": [
            "aftersales.after_sales.doctype.claim_list.claim_list.run_monthly_scheduler",
        ],
    },
}