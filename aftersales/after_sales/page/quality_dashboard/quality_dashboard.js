frappe.pages["quality-dashboard"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "质量分析看板",
		single_column: true,
	});

	page.main.addClass("qs-dashboard");

	// 刷新按钮
	page.set_primary_action("刷新", function () {
		load_data(page);
	});

	$(wrapper).find(".layout-main-section").html(`
		<div class="qs-updated text-muted" style="padding: 0 0 8px 4px; font-size: 12px;"></div>
		<div class="qs-kpis row"></div>
		<div class="row">
			<div class="col-sm-6"><div class="qs-card"><h5>故障大类 TOP10</h5><div class="qs-chart qs-fault-cat"></div></div></div>
			<div class="col-sm-6"><div class="qs-card"><h5>故障部件 TOP10</h5><div class="qs-chart qs-fault-part"></div></div></div>
		</div>
		<div class="row">
			<div class="col-sm-6"><div class="qs-card"><h5>供应商索赔对比</h5><div class="qs-chart qs-supplier"></div></div></div>
			<div class="col-sm-6"><div class="qs-card"><h5>近 12 个月登记趋势</h5><div class="qs-chart qs-trend"></div></div></div>
		</div>
		<div class="qs-card"><h5>故障现象 TOP10</h5><div class="qs-chart qs-phenomenon"></div>
			<table class="table table-bordered qs-supplier-table" style="margin-top:8px;"></table>
		</div>
		<style>
			.qs-dashboard .qs-card { background: var(--card-bg, #fff); border: 1px solid var(--border-color, #e2e6e9);
				border-radius: 8px; padding: 12px 16px; margin-bottom: 16px; }
			.qs-dashboard .qs-kpi { background: var(--card-bg, #fff); border: 1px solid var(--border-color, #e2e6e9);
				border-radius: 8px; padding: 14px 16px; margin-bottom: 16px; text-align: center; }
			.qs-dashboard .qs-kpi .num { font-size: 26px; font-weight: 600; }
			.qs-dashboard .qs-kpi .cap { color: var(--text-muted, #8d99a2); font-size: 12px; margin-top: 2px; }
			.qs-dashboard .qs-chart { min-height: 260px; }
		</style>
	`);

	load_data(page);
};

function load_data(page) {
	var $wrap = $(page.main);
	$wrap.find(".qs-updated").text("加载中…");
	frappe
		.call({
			method: "aftersales.after_sales.analytics.get_dashboard_data",
		})
		.then(function (r) {
			var d = r.message || {};
			$wrap.find(".qs-updated").text("数据生成时间：" + (d.generated_at || "-"));
			render_kpis($wrap, d.overview || {});
			render_bar($wrap.find(".qs-fault-cat"), d.fault_by_category);
			render_bar($wrap.find(".qs-fault-part"), d.fault_by_part);
			render_bar($wrap.find(".qs-phenomenon"), d.fault_by_phenomenon);
			render_supplier($wrap, d.supplier_stats || []);
			render_trend($wrap, d.monthly_trend || []);
		});
}

function render_kpis($wrap, ov) {
	var kpis = [
		{ num: ov.total_requests || 0, cap: "售后登记总数" },
		{ num: ov.approved_requests || 0, cap: "已通过（审批完成）" },
		{ num: ov.claimed_requests || 0, cap: "涉及索赔登记数" },
		{ num: (ov.claim_rate || 0) + "%", cap: "索赔率（已通过口径）" },
		{ num: ov.claim_parts_qty || 0, cap: "索赔配件总量" },
	];
	var html = kpis
		.map(function (k) {
			return '<div class="col-sm col-xs-6"><div class="qs-kpi"><div class="num">' + k.num + '</div><div class="cap">' + k.cap + "</div></div></div>";
		})
		.join("");
	$wrap.find(".qs-kpis").html(html);
}

function _bar_config(labels, datasets, type) {
	return new frappe.Chart(null, {
		data: { labels: labels, datasets: datasets },
		type: type || "bar",
		height: 260,
		barOptions: { spaceRatio: 0.35 },
		axisOptions: { xAxisMode: "tick", shortenYAxisNumbers: 1 },
		colors: ["#4f8ef7"],
	});
}

function render_bar($el, groups) {
	$el.empty();
	var items = groups && groups[0] ? groups[0].items : [];
	if (!items.length) {
		$el.html('<div class="text-muted" style="padding:40px;text-align:center;">暂无数据</div>');
		return;
	}
	_bar_config(
		items.map(function (i) {
			return i.name;
		}),
		[
			{
				name: "数量",
				values: items.map(function (i) {
					return i.cnt;
				}),
			},
		]
	).mount($el[0]);
}

function render_supplier($wrap, rows) {
	var $el = $wrap.find(".qs-supplier");
	$el.empty();
	// 表格
	var thead = "<thead><tr><th>供应商</th><th>索赔单数</th><th>配件数量</th></tr></thead>";
	var tbody = rows
		.map(function (r) {
			return "<tr><td>" + frappe.utils.escape_html(r.supplier) + "</td><td>" + r.order_cnt + "</td><td>" + r.qty + "</td></tr>";
		})
		.join("");
	$wrap.find(".qs-supplier-table").html(thead + "<tbody>" + (tbody || '<tr><td colspan="3" class="text-muted">暂无数据</td></tr>') + "</tbody>");
	if (!rows.length) {
		$el.html('<div class="text-muted" style="padding:40px;text-align:center;">暂无数据</div>');
		return;
	}
	_bar_config(
		rows.map(function (r) {
			return r.supplier;
		}),
		[
			{
				name: "配件数量",
				values: rows.map(function (r) {
					return r.qty;
				}),
			},
		]
	).mount($el[0]);
}

function render_trend($wrap, rows) {
	var $el = $wrap.find(".qs-trend");
	$el.empty();
	if (!rows.length) {
		$el.html('<div class="text-muted" style="padding:40px;text-align:center;">暂无数据</div>');
		return;
	}
	_bar_config(
		rows.map(function (r) {
			return r.ym;
		}),
		[
			{
				name: "登记量",
				values: rows.map(function (r) {
					return r.cnt;
				}),
			},
		],
		"line"
	).mount($el[0]);
}
