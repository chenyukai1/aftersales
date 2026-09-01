app_name = "aftersales"
app_title = "售后管理"
app_publisher = "ZCode Demo"
app_description = "售后管理平台演示：整车发货 / 配件登记 / 配件主档 / 故障字典 / 查询 API"
app_icon = "octicon package-dependencies"
app_color = "blue"

required_apps = ["frappe", "erpnext"]

# 安装应用后自动创建自定义 DocType
after_install = "aftersales.after_sales.setup.after_install"