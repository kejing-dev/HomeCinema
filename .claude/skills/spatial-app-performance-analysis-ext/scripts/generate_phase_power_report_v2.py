#!/usr/bin/env python3
"""Generate a polished two-phase Spatial power-pressure report."""
from __future__ import annotations

import argparse
import html
import json
import pathlib
from typing import Any


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def num(value: Any, digits: int = 1) -> str:
    if value is None:
        return "\u672a\u91c7\u96c6"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return esc(value)
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.{digits}f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.{digits}f}k"
    return f"{value:,.{digits}f}"


def raw(value: Any) -> str:
    if value is None:
        return "\u672a\u91c7\u96c6"
    try:
        return f"{float(value):,.1f}"
    except (TypeError, ValueError):
        return esc(value)


def pct(before: Any, after: Any) -> str:
    try:
        before, after = float(before), float(after)
        if before == 0:
            return "n/a"
        change = (after / before - 1) * 100
        return f"{change:+.0f}%"
    except (TypeError, ValueError):
        return "n/a"


def change_html(before: Any, after: Any) -> str:
    try:
        before_number, after_number = float(before), float(after)
    except (TypeError, ValueError):
        return '<span class="change na">\u4e0d\u53ef\u6bd4\u8f83<small>\u6570\u636e\u7f3a\u5931</small></span>'
    if before_number == 0:
        if after_number == 0:
            return '<span class="change flat">不变 · 0</span>'
        return f'<span class="change increase">新增 +{raw(after_number)}<small>基线为 0</small></span>'
    change = (after_number / before_number - 1) * 100
    if after_number < before_number:
        return f'<span class="change decrease">减少 {abs(change):.0f}%<small>Δ {raw(after_number - before_number)}</small></span>'
    if after_number > before_number:
        return f'<span class="change increase">增长 {change:.0f}%<small>Δ +{raw(after_number - before_number)}</small></span>'
    return '<span class="change flat">不变 · 0%</span>'


def phase_cpu(phase: dict[str, Any], process: str, key: str) -> Any:
    row = next((x for x in phase["cpu"] if x["process"] == process), {})
    return row.get(key)


def process_value(phase: dict[str, Any], process: str, key: str) -> str:
    row = next((x for x in phase["cpu"] if x["process"] == process), {})
    if not row.get("present"):
        return "\u672a\u8fd0\u884c\uff08\u65e0\u8fdb\u7a0b\uff09"
    return num(row.get(key))


def app_fps_value(data: dict[str, Any]) -> str:
    value = data.get("summary", {}).get("appFps", {}).get("avg")
    if value in (None, 0):
        return "\u672a\u8fd0\u884c"
    return raw(value)


def kpi(label: str, value: str, change: str, note: str, tone: str = "neutral") -> str:
    return (
        f'<div class="kpi"><div class="label">{esc(label)}</div>'
        f'<div class="val">{value}</div><span class="delta {tone}">{esc(change)}</span>'
        f'<div class="kpi-note">{esc(note)}</div></div>'
    )


def svg_bars(items: list[tuple[str, float | None, float | None]], width: int = 900) -> str:
    height = 42 + len(items) * 34
    left, right = 190, 90
    rows = []
    for index, (label, before, after) in enumerate(items):
        y = 28 + index * 34
        before_pct = 100.0 if before not in (None, 0) else None
        after_pct = (after / before * 100.0) if before not in (None, 0) and after is not None else None
        max_pct = 100.0
        if after_pct is not None:
            max_pct = max(100.0, after_pct)
        chart_width = width - left - right
        bw = (before_pct or 0) / max_pct * chart_width
        aw = (after_pct or 0) / max_pct * chart_width
        before_text = f"{before_pct:.0f}%" if before_pct is not None else "n/a"
        after_text = f"{after_pct:.0f}%" if after_pct is not None else "n/a"
        rows.append(
            f'<text x="{left - 10}" y="{y + 5}" text-anchor="end">{esc(label)}</text>'
            f'<rect x="{left}" y="{y - 8}" width="{bw:.1f}" height="9" rx="4" fill="#31405f"/>'
            f'<rect x="{left}" y="{y + 5}" width="{aw:.1f}" height="9" rx="4" fill="#4da3ff"/>'
            f'<text x="{left + chart_width + 8}" y="{y - 1}" class="svg-value">{before_text}</text>'
            f'<text x="{left + chart_width + 8}" y="{y + 14}" class="svg-value after">{after_text}</text>'
        )
    return f'<svg class="chart" viewBox="0 0 {width} {height}" role="img">{"".join(rows)}</svg>'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", required=True, type=pathlib.Path)
    parser.add_argument("--baseline-fastperf", type=pathlib.Path)
    parser.add_argument("--launched-fastperf", type=pathlib.Path)
    parser.add_argument(
        "--template",
        type=pathlib.Path,
        default=pathlib.Path(__file__).resolve().parents[1] / "assets" / "power-report-template.html",
    )
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()

    analysis = json.loads(args.analysis.read_text(encoding="utf-8"))
    baseline = analysis["phases"]["baseline"]["metrics"]
    launched = analysis["phases"]["launched"]["metrics"]
    delta = analysis["runtime_metric_delta"]
    target = analysis["target"]
    package = target["package"]
    runtime = target["runtime_process"]
    before_fp = json.loads(args.baseline_fastperf.read_text(encoding="utf-8")) if args.baseline_fastperf else {}
    after_fp = json.loads(args.launched_fastperf.read_text(encoding="utf-8")) if args.launched_fastperf else {}

    def fp(data: dict[str, Any], group: str, field: str) -> Any:
        return data.get("summary", {}).get(group, {}).get(field)

    draw = delta["Draw Call Count"]
    triangle = delta["Triangle Count"]
    mesh_draw = delta["3D Mesh Draw Call Count"]
    texture = delta["Texture2D Memory"]
    gpu_before, gpu_after = fp(before_fp, "gpuUsage", "avg"), fp(after_fp, "gpuUsage", "avg")
    freq_before, freq_after = fp(before_fp, "gpuFreq", "avg"), fp(after_fp, "gpuFreq", "avg")
    app_before, app_after = fp(before_fp, "appCpu", "avg"), fp(after_fp, "appCpu", "avg")
    before_frames, after_frames = baseline["spatial_frames"], launched["spatial_frames"]
    runtime_before = phase_cpu(baseline, runtime, "running_ms")
    runtime_after = phase_cpu(launched, runtime, "running_ms")
    client_before = phase_cpu(baseline, package, "running_ms")
    client_after = phase_cpu(launched, package, "running_ms")

    metric_specs = [
        ("DrawCall", "Draw Call Count", "提交数量；需结合几何量和 GPUTime 判断"),
        ("3D Mesh DrawCall", "3D Mesh Draw Call Count", "网格提交数量"),
        ("Particle DrawCall", "Particle Draw Call Count", "粒子提交数量"),
        ("Shadow DrawCall", "Shadow Draw Call Count", "阴影提交数量"),
        ("Triangle", "Triangle Count", "总三角形处理量"),
        ("3D Mesh Triangle", "3D Mesh Triangle Count", "网格几何量，重点关注 LOD/裁剪"),
        ("Particle Triangle", "Particle Triangle Count", "粒子几何量"),
        ("Shadow Triangle", "Shadow Triangle Count", "阴影几何量"),
        ("Vertex", "Vertex Count", "总顶点处理量"),
        ("3D Mesh Vertex", "3D Mesh Vertex Count", "网格顶点量"),
        ("Particle Vertex", "Particle Vertex Count", "粒子顶点量"),
        ("Shadow Vertex", "Shadow Vertex Count", "阴影顶点量"),
        ("Mesh Memory", "Mesh Memory", "网格资源驻留"),
        ("Texture2D Memory", "Texture2D Memory", "纹理资源驻留"),
        ("Skeletal Animation", "Skeletal Animation Count", "骨骼动画实例数量"),
    ]
    metric_rows = []
    for label, key, explanation in metric_specs:
        item = delta[key]
        metric_rows.append(
            f'<tr><td class="metric">{esc(label)}</td>'
            f'<td>{raw(item["baseline_avg"])}</td><td>{raw(item["launched_avg"])}</td>'
            f'<td>{change_html(item["baseline_avg"], item["launched_avg"])}</td>'
            f'<td>{esc(explanation)}</td></tr>'
        )
    metric_rows_html = "".join(metric_rows)

    html_text = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>{esc(package)} 启动前后性能功耗报告</title>
<style>
:root{{--bg:#0f1420;--card:#182030;--card2:#1e2740;--line:#2a3450;--txt:#e6ecf5;
--sub:#93a1bd;--accent:#4da3ff;--purple:#7c5cff;--good:#37d39b;--down:#ff6b7d;
--warn:#ffb454;--grid:#243050;--chip:#233152}}
*{{box-sizing:border-box}} body{{margin:0;background:linear-gradient(180deg,#0c111c,#0f1420 260px);
color:var(--txt);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
line-height:1.6;font-size:15px}} .wrap{{max-width:1160px;margin:auto;padding:32px 22px 80px}}
header.hero{{background:linear-gradient(120deg,#16233f,#1a1d38 55%,#241a3a);border:1px solid var(--line);
border-radius:18px;padding:34px;position:relative;overflow:hidden}} header.hero:after{{content:"";position:absolute;
right:-60px;top:-60px;width:260px;height:260px;background:radial-gradient(circle,rgba(124,92,255,.35),transparent 70%)}}
.tag{{display:inline-block;background:var(--chip);color:var(--accent);border:1px solid var(--line);padding:3px 12px;
border-radius:999px;font-size:12px;letter-spacing:.4px;margin-bottom:14px}} h1{{margin:6px 0 4px;font-size:30px;letter-spacing:.4px}}
.mono,code{{font-family:ui-monospace,"SF Mono",Consolas,monospace}} h1 .mono{{color:var(--accent)}}
.subtitle,.note,.kpi-note{{color:var(--sub);font-size:13.5px}} .meta{{display:flex;flex-wrap:wrap;gap:8px 24px;
margin-top:20px;color:var(--sub);font-size:13px}} .meta b{{color:var(--txt)}} .verdict{{margin-top:22px;
background:rgba(255,180,84,.08);border:1px solid rgba(255,180,84,.35);border-radius:12px;padding:14px 18px}}
.verdict b{{color:var(--warn)}} section{{margin-top:38px}} h2{{font-size:21px;margin:0 0 6px;display:flex;align-items:center;gap:10px}}
h2 .num{{width:30px;height:30px;border-radius:8px;background:var(--accent);color:#06101f;display:grid;place-items:center;
font-size:15px;font-weight:700}} .lead{{color:var(--sub);margin:0 0 18px;font-size:14px}}
.grid{{display:grid;gap:16px}} .g4{{grid-template-columns:repeat(4,1fr)}} .g3{{grid-template-columns:repeat(3,1fr)}}
@media(max-width:820px){{.g4,.g3{{grid-template-columns:repeat(2,1fr)}}}} @media(max-width:520px){{.g4,.g3{{grid-template-columns:1fr}}}}
.kpi,.card,.chartbox{{background:var(--card);border:1px solid var(--line);border-radius:14px}}
.kpi{{padding:16px}} .kpi .label{{color:var(--sub);font-size:12.5px;margin-bottom:8px}} .val{{font-size:25px;font-weight:700}}
.delta{{display:inline-block;margin-top:8px;font-size:12px;padding:2px 9px;border-radius:999px;font-weight:600}}
.neutral{{background:rgba(147,161,189,.14);color:var(--sub)}} .up{{background:rgba(255,180,84,.14);color:var(--warn)}}
.down{{background:rgba(255,107,125,.14);color:var(--down)}} .good{{background:rgba(55,211,155,.14);color:var(--good)}}
.kpi-note{{margin-top:8px;font-size:11.5px}} .card{{padding:20px 22px}} table{{width:100%;border-collapse:collapse;font-size:13.5px}}
th,td{{padding:9px 10px;border-bottom:1px solid var(--line);text-align:right;vertical-align:top}} th:first-child,td:first-child{{text-align:left}}
thead th{{color:var(--sub);font-size:12px;font-weight:600}} tbody tr:hover{{background:rgba(77,163,255,.05)}}
.metric{{font-weight:600}} .chartbox{{padding:18px}} .chartbox h3{{margin:0;font-size:15px}} .chartbox .cap{{color:var(--sub);font-size:12px;margin:2px 0 8px}}
.change{{display:inline-flex;flex-direction:column;align-items:flex-end;gap:1px;padding:2px 8px;border-radius:7px;font-weight:700;white-space:nowrap}}
.change small{{font-size:10.5px;font-weight:500;opacity:.85}}
.change.decrease{{color:var(--good);background:rgba(55,211,155,.14)}}
.change.increase{{color:var(--down);background:rgba(255,107,125,.14)}}
.change.flat,.change.na{{color:var(--sub);background:rgba(147,161,189,.14)}}
.change-legend{{align-items:center;flex-wrap:wrap;margin:8px 0 12px}}
.change-legend i{{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:-1px}}
.legend-decrease{{background:var(--good)}} .legend-increase{{background:var(--down)}} .legend-neutral{{background:var(--sub)}}
.chart{{width:100%;height:auto;display:block}} svg text{{fill:#e6ecf5;font-size:12px}} svg .svg-value{{fill:#93a1bd;font-family:ui-monospace,Consolas,monospace}} svg .svg-value.after{{fill:#4da3ff}}
.legend{{display:flex;gap:16px;color:var(--sub);font-size:12px;margin:6px 2px}} .legend i{{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;vertical-align:-1px}}
.timeline{{position:relative;margin:8px 0;padding-left:8px}} .tl{{display:grid;grid-template-columns:100px 1fr;gap:16px;padding:12px 0;
border-left:2px solid var(--line);margin-left:8px;padding-left:20px;position:relative}} .tl:before{{content:"";position:absolute;left:-7px;top:18px;
width:12px;height:12px;border-radius:50%;background:var(--accent);border:2px solid var(--bg)}} .tl.hot:before{{background:var(--down)}}
.tl.warn:before{{background:var(--warn)}} .tl-time{{color:var(--accent);font:700 13px ui-monospace,Consolas,monospace}} .tl.hot .tl-time{{color:var(--down)}}
.tl.warn .tl-time{{color:var(--warn)}} .tl-desc{{color:var(--sub);font-size:13.5px}} .tl-desc b{{color:var(--txt)}} .callout{{padding:14px 18px;
border:1px solid var(--line);border-radius:12px;background:var(--card)}} .warning{{background:rgba(255,180,84,.08);border-color:rgba(255,180,84,.35)}}
ul.clean{{margin:8px 0;padding-left:20px}} ul.clean li{{margin:5px 0}} .foot{{margin-top:44px;color:var(--sub);font-size:12px;text-align:center;border-top:1px solid var(--line);padding-top:20px}}
</style></head><body><div class="wrap">
<header class="hero">
<span class="tag">PERFETTO 性能功耗分析 · 统一渲染架构 · TRACE PROXY</span>
<h1><span class="mono">{esc(package)}</span> 启动前后性能功耗报告</h1>
<div class="subtitle">Client 启动对共享渲染服务器 <span class="mono">{esc(runtime)}</span> 3D 负载、帧时序与整机功耗代理量的影响</div>
<div class="meta"><span>基线窗口：<b>启动前 10 s</b></span><span>启动后窗口：<b>拉起后 20 s</b></span>
<span>Client：<b>{esc(package)}</b></span><span>Runtime：<b>{esc(runtime)}</b></span></div>
<div class="verdict"><b>核心结论：</b>目标 Client 拉起后，Runtime 平均 Triangle <b>{pct(triangle["baseline_avg"], triangle["launched_avg"])}</b>、
Texture2D Memory <b>{pct(texture["baseline_avg"], texture["launched_avg"])}</b>，GPU 使用率 <b>{pct(gpu_before, gpu_after)}</b>，
GPU 平均频率 <b>{pct(freq_before, freq_after)}</b>。这是明显的渲染负载/功耗压力上升信号；但 DrawCall 本身 <b>{pct(draw["baseline_avg"], draw["launched_avg"])}</b>，
不能单独作为功耗结论。SpatialRuntime 为共享服务，以下 Runtime 增量是候选归因，不是目标应用独占功耗。</div>
</header>

<section><h2><span class="num">1</span>关键指标概览（启动前 → 启动后）</h2>
<p class="lead">启动后窗口包含应用启动过程；差分用于定位优化方向，不等价于严格同一时刻 A/B 或稳定态功耗测量。</p>
<div class="grid g4">
{kpi("Runtime DrawCall", f"{num(draw['baseline_avg'])} → {num(draw['launched_avg'])}", pct(draw["baseline_avg"], draw["launched_avg"]), "SpatialRuntime 平均值", "up" if (draw["delta"] or 0) > 0 else "down")}
{kpi("Runtime Triangle", f"{num(triangle['baseline_avg'])} → {num(triangle['launched_avg'])}", pct(triangle["baseline_avg"], triangle["launched_avg"]), "SpatialRuntime 平均值", "up")}
{kpi("Texture2D Memory", f"{num(texture['baseline_avg'])} → {num(texture['launched_avg'])}", pct(texture["baseline_avg"], texture["launched_avg"]), "bytes，平均值", "up")}
{kpi("GPU Usage", f"{raw(gpu_before)}% → {raw(gpu_after)}%", pct(gpu_before, gpu_after), "FastPerf 平均值", "up")}
</div></section>

<section><h2><span class="num">2</span>启动时间线与 FastPerf</h2>
<div class="timeline">
<div class="tl"><div class="tl-time">0–10 s</div><div class="tl-desc"><b>应用未运行</b>：App FPS {app_fps_value(before_fp)}，System FPS {raw(fp(before_fp, "sysFps", "avg"))}，GPU Usage {raw(gpu_before)}%，GPU Frequency {raw(freq_before)} MHz；Runtime 仍承担系统基础渲染。</div></div>
<div class="tl hot"><div class="tl-time">拉起时刻</div><div class="tl-desc"><b>Client 出现并建立 Spatial 渲染工作负载</b>：目标 Client 进程进入 launched Trace，Runtime 指标开始反映目标场景资源。</div></div>
<div class="tl warn"><div class="tl-time">0–20 s</div><div class="tl-desc"><b>启动后采集窗口</b>：App FPS {app_fps_value(after_fp)}，System FPS {raw(fp(after_fp, "sysFps", "avg"))}，GPU Usage {raw(gpu_after)}%，平均频率 {raw(freq_after)} MHz。</div></div>
</div>
<table><thead><tr><th>阶段</th><th>App FPS</th><th>System FPS</th><th>GPU Usage</th><th>GPU Frequency</th><th>App CPU</th></tr></thead><tbody>
<tr><td class="metric">启动前 10 s</td><td>{app_fps_value(before_fp)}</td><td>{raw(fp(before_fp, "sysFps", "avg"))}</td><td>{raw(gpu_before)}%</td><td>{raw(freq_before)} MHz</td><td>{raw(app_before)}%</td></tr>
<tr><td class="metric">拉起后 20 s</td><td>{app_fps_value(after_fp)}</td><td>{raw(fp(after_fp, "sysFps", "avg"))}</td><td>{raw(gpu_after)}%</td><td>{raw(freq_after)} MHz</td><td>{raw(app_after)}%</td></tr>
</tbody></table></section>

<section><h2><span class="num">3</span>SpatialRuntime 3D 渲染负载变化</h2>
<p class="lead">完整列出 SpatialRuntime 启动前后的 3D 渲染指标；“变化”按启动前为基准计算，正值表示启动后增加，负值表示减少。</p>
<div class="card" style="margin-top:16px"><table><thead><tr><th>指标</th><th>启动前平均</th><th>启动后平均</th><th>变化</th><th>解释</th></tr></thead><tbody>
<div class="legend change-legend"><span><i class="legend-decrease"></i>减少：绿色</span><span><i class="legend-increase"></i>增长：红色</span><span><i class="legend-neutral"></i>不变 / 不可比较：灰色</span><span>基线为 0：显示“新增 +N”，不计算百分比</span></div>
{metric_rows_html}
</tbody></table></div></section>

<section><h2><span class="num">4</span>帧时序与 Client / Runtime 进程压力</h2>
<div class="grid g3">
<div class="kpi"><div class="label">Spatial Late / Miss</div><div class="val">{raw(before_frames.get("late"))} / {raw(before_frames.get("miss"))} → {raw(after_frames.get("late"))} / {raw(after_frames.get("miss"))}</div><div class="kpi-note">启动后窗口出现明显异常帧</div></div>
<div class="kpi"><div class="label">Client CPU sched</div><div class="val">{process_value(baseline, package, "running_ms")} → {process_value(launched, package, "running_ms")} ms</div><div class="kpi-note">进程线程累计 running time</div></div>
<div class="kpi"><div class="label">Runtime CPU sched</div><div class="val">{process_value(baseline, runtime, "running_ms")} → {process_value(launched, runtime, "running_ms")} ms</div><div class="kpi-note">共享服务累计，不等于独占功耗</div></div>
</div>
<div class="card" style="margin-top:16px"><table><thead><tr><th>指标</th><th>启动前</th><th>启动后</th><th>证据边界</th></tr></thead><tbody>
<tr><td class="metric">Spatial frames</td><td>{raw(before_frames.get("frames"))}</td><td>{raw(after_frames.get("frames"))}</td><td>窗口内帧数量</td></tr>
<tr><td class="metric">平均 / 最大 frame duration</td><td>{raw(before_frames.get("avg_ms"))} / {raw(before_frames.get("max_ms"))} ms</td><td>{raw(after_frames.get("avg_ms"))} / {raw(after_frames.get("max_ms"))} ms</td><td>启动后包含启动抖动</td></tr>
<tr><td class="metric">Client CPUTime / GPUTime</td><td>{raw(baseline["client_cpu_time"].get("avg_ms"))} / {raw(baseline["client_gpu_time"].get("avg_ms"))} ms</td><td>{raw(launched["client_cpu_time"].get("avg_ms"))} / {raw(launched["client_gpu_time"].get("avg_ms"))} ms</td><td>OpenXR Client 每帧聚合</td></tr>
</tbody></table></div></section>

<section><h2><span class="num">5</span>功耗归因与优化方向</h2>
<div class="callout warning"><b>功耗口径：</b>当前没有电流/电压校准，只能把 GPU duty、GPU frequency、CPU running time、Runtime 3D 指标作为相对功耗压力代理量；不输出实际 Watt/mWh。</div>
<div class="grid g2" style="margin-top:16px"><div class="card"><h3>Client 侧</h3><ul class="clean"><li>拆分启动与稳定态，避免把一次性资源加载误判为持续功耗。</li><li>检查每帧提交、资源更新、轮询和同步等待，优先降低无效 Client CPUTime/GPUTime。</li><li>对动态对象更新频率、不可见对象提交做 A/B。</li></ul></div>
<div class="card"><h3>SpatialRuntime 侧</h3><ul class="clean"><li>Triangle 与纹理驻留增长是首要优化方向：LOD、裁剪、纹理压缩/分辨率和释放时机。</li><li>对阴影、粒子、骨骼动画、后处理做逐项开关实验，观察 GPUTime 和频率是否下降。</li><li>Runtime 是共享服务，应使用空场景/静态场景/目标场景重复 A/B，分离目标 Client 引入的 Runtime 增量。</li></ul></div></div></section>

<section><h2><span class="num">6</span>证据边界与下一轮采集</h2>
<ul class="clean"><li>本报告仅使用 Perfetto Trace + FastPerf，未使用 RenderDoc。</li><li>两段 Trace 是独立窗口，差异包含启动、温度和设备状态；不能作为严格同一时刻 A/B。</li><li>建议每阶段采集 30–60 秒，并额外切出启动后稳定态；补采 Binder、wakeup、CPU idle/frequency 和电流校准数据。</li><li>SpatialRuntime 总成本不能直接等同目标应用独占功耗。</li></ul>
</section>
<div class="foot">Generated from <span class="mono">two-phase-analysis.json</span> · trace_proxy · Report output is evidence-bounded</div>
</div></body></html>"""
    template = args.template.read_text(encoding="utf-8")
    required_tokens = ("{{REPORT_TITLE}}", "{{REPORT_CONTENT}}")
    missing_tokens = [token for token in required_tokens if token not in template]
    if missing_tokens:
        raise SystemExit(f"Power report template is missing required tokens: {', '.join(missing_tokens)}")
    body_start = html_text.find("<body>")
    body_end = html_text.rfind("</body>")
    if body_start < 0 or body_end < body_start:
        raise SystemExit("Generated power report body could not be extracted")
    report_content = html_text[body_start + len("<body>"):body_end]
    rendered = (
        template
        .replace("{{REPORT_TITLE}}", f"{package} 启动前后性能功耗报告")
        .replace("{{REPORT_CONTENT}}", report_content)
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(rendered, encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
