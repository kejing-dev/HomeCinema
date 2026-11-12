#!/usr/bin/env python3
"""Generate an evidence-bounded HTML report for two-phase Spatial traces."""
from __future__ import annotations

import argparse
import html
import json
import pathlib
from typing import Any


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def fmt(value: Any, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)):
        return f"{value:,.{digits}f}"
    return esc(value)


def load_json(path: pathlib.Path | None) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path else {}


def fastperf_cards(data: dict[str, Any], label: str) -> str:
    summary = data.get("summary", {})
    app = summary.get("appFps", {})
    gpu = summary.get("gpuUsage", {})
    freq = summary.get("gpuFreq", {})
    return (
        f"<tr><td>{esc(label)}</td><td>{fmt(app.get('avg'))}</td>"
        f"<td>{fmt(summary.get('sysFps', {}).get('avg'))}</td>"
        f"<td>{fmt(gpu.get('avg'))}%</td><td>{fmt(freq.get('avg'))} MHz</td>"
        f"<td>{fmt(summary.get('appCpu', {}).get('avg'))}%</td></tr>"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", required=True, type=pathlib.Path)
    parser.add_argument("--baseline-fastperf", type=pathlib.Path)
    parser.add_argument("--launched-fastperf", type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()

    analysis = load_json(args.analysis)
    target_package = analysis.get("target", {}).get("package", "target app")
    baseline = analysis["phases"]["baseline"]["metrics"]
    launched = analysis["phases"]["launched"]["metrics"]
    delta = analysis["runtime_metric_delta"]
    baseline_frames = baseline["spatial_frames"]
    launched_frames = launched["spatial_frames"]
    rows = []
    labels = {
        "Draw Call Count": "DrawCall",
        "3D Mesh Draw Call Count": "3D Mesh DrawCall",
        "Particle Draw Call Count": "Particle DrawCall",
        "Shadow Draw Call Count": "Shadow DrawCall",
        "Triangle Count": "Triangle",
        "3D Mesh Triangle Count": "3D Mesh Triangle",
        "Vertex Count": "Vertex",
        "Mesh Memory": "Mesh Memory",
        "Texture2D Memory": "Texture2D Memory",
        "Skeletal Animation Count": "Skeletal Animation",
    }
    for name, label in labels.items():
        item = delta[name]
        unit = "bytes" if "Memory" in name else ""
        rows.append(
            f"<tr><td>{esc(label)}</td><td>{fmt(item['baseline_avg'])} {unit}</td>"
            f"<td>{fmt(item['launched_avg'])} {unit}</td>"
            f"<td class=\"{'up' if (item['delta'] or 0) > 0 else 'down'}\">"
            f"{fmt(item['delta'])} {unit}</td><td>{esc(item['status'])}</td></tr>"
        )

    def cpu_row(phase: dict[str, Any], process: str) -> tuple[str, str]:
        row = next((x for x in phase["cpu"] if x["process"] == process), {})
        return fmt(row.get("running_ms")), fmt(row.get("sched_slices"))

    html_text = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>Spatial 两阶段 Trace 功耗归因分析</title>
<style>
body{{margin:0;background:#0b1020;color:#e8eefc;font:15px/1.7 Arial,"Microsoft YaHei",sans-serif}}
main{{max-width:1240px;margin:auto;padding:32px}}h1{{font-size:30px}}
h2{{border-left:4px solid #56d9ff;padding-left:10px;margin-top:32px}}
.sub,.note,small{{color:#9eacc8}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
.card,table,.callout{{background:#121a2d;border:1px solid #2a3959;border-radius:10px}}
.card{{padding:14px}}.label{{color:#9eacc8;font-size:13px}}.value{{font-size:24px;font-weight:bold;margin:4px 0}}
table{{width:100%;border-collapse:collapse;margin:12px 0}}th,td{{padding:9px;border-bottom:1px solid #2a3959;text-align:left;vertical-align:top}}
th{{background:#192641}}.callout{{padding:15px;margin:14px 0}}.warn{{border-color:#775d27;background:#2a2415}}
.up{{color:#ffb454}}.down{{color:#7ee2a8}}code{{color:#b9eaff;background:#091222;padding:1px 4px}}
@media(max-width:800px){{.grid{{grid-template-columns:1fr}}main{{padding:18px}}}}
</style></head><body><main>
<h1>Spatial 两阶段 Trace 功耗归因分析</h1>
<div class="sub">Perfetto Trace + FastPerf · Client / SpatialRuntime · {esc(analysis['target']['package'])}</div>
<div class="callout warn"><b>口径：</b>本报告使用 <code>trace_proxy</code>。没有电压/电流校准，因此不输出 Watt 或 mWh；目标是识别 Client、共享 SpatialRuntime 和渲染链路的优化方向。</div>

<h2>1. 结论</h2>
<div class="callout">
启动 {esc(target_package)} 后，SpatialRuntime 的渲染指标发生明显变化：平均 DrawCall 为 <b>{fmt(delta['Draw Call Count']['launched_avg'])}</b>，
相对基线 <b>{fmt(delta['Draw Call Count']['delta'])}</b>；Triangle 为 <b>{fmt(delta['Triangle Count']['launched_avg'])}</b>，
变化 <b>{fmt(delta['Triangle Count']['delta'])}</b>；Mesh Memory 和 Texture2D Memory 分别变化
<b>{fmt(delta['Mesh Memory']['delta'])}</b>、<b>{fmt(delta['Texture2D Memory']['delta'])}</b> bytes。
这说明应用拉起后 Runtime 承担了新的/不同的场景工作负载，但不能仅凭 DrawCall 直接断言功耗或几何瓶颈。
</div>
<div class="grid">
<div class="card"><div class="label">Runtime DrawCall Δ</div><div class="value">{fmt(delta['Draw Call Count']['delta'])}</div><div class="note">平均值差分</div></div>
<div class="card"><div class="label">Runtime Triangle Δ</div><div class="value">{fmt(delta['Triangle Count']['delta'])}</div><div class="note">平均值差分</div></div>
<div class="card"><div class="label">Runtime Mesh Memory Δ</div><div class="value">{fmt(delta['Mesh Memory']['delta'])}</div><div class="note">bytes，平均值差分</div></div>
<div class="card"><div class="label">Runtime Texture2D Δ</div><div class="value">{fmt(delta['Texture2D Memory']['delta'])}</div><div class="note">bytes，平均值差分</div></div>
</div>

<h2>2. FastPerf 启动前后</h2>
<table><tr><th>阶段</th><th>App FPS</th><th>System FPS</th><th>GPU Usage</th><th>GPU Freq</th><th>App CPU</th></tr>
{fastperf_cards(load_json(args.baseline_fastperf), "启动前 10 秒")}
{fastperf_cards(load_json(args.launched_fastperf), "拉起后 20 秒")}
</table>
<p class="note">启动前 App FPS 为 0/缺失是预期现象，因为目标应用尚未运行；启动后窗口包含启动过程，不能等价为稳定态。</p>

<h2>3. SpatialRuntime 3D Render 指标差分</h2>
<table><tr><th>指标</th><th>启动前平均</th><th>启动后平均</th><th>Δ</th><th>证据状态</th></tr>
{''.join(rows)}
</table>

<h2>4. 帧、Client 与 Runtime 调度</h2>
<table><tr><th>指标</th><th>启动前</th><th>启动后</th><th>说明</th></tr>
<tr><td>Spatial frames</td><td>{fmt(baseline_frames.get('frames'))}</td><td>{fmt(launched_frames.get('frames'))}</td><td>Trace 窗口内数量</td></tr>
<tr><td>平均 frame duration</td><td>{fmt(baseline_frames.get('avg_ms'))} ms</td><td>{fmt(launched_frames.get('avg_ms'))} ms</td><td>启动后含异常帧</td></tr>
<tr><td>Late / Miss</td><td>{fmt(baseline_frames.get('late'))} / {fmt(baseline_frames.get('miss'))}</td><td>{fmt(launched_frames.get('late'))} / {fmt(launched_frames.get('miss'))}</td><td>Spatial frame evidence</td></tr>
<tr><td>Client CPUTime</td><td>{fmt(baseline['client_cpu_time'].get('avg_ms'))} ms</td><td>{fmt(launched['client_cpu_time'].get('avg_ms'))} ms</td><td>OpenXR Client per-frame trace</td></tr>
<tr><td>Client GPUTime</td><td>{fmt(baseline['client_gpu_time'].get('avg_ms'))} ms</td><td>{fmt(launched['client_gpu_time'].get('avg_ms'))} ms</td><td>OpenXR Client per-frame trace</td></tr>
<tr><td>Client sched running</td><td>{cpu_row(baseline, analysis['target']['package'])[0]} ms</td><td>{cpu_row(launched, analysis['target']['package'])[0]} ms</td><td>进程及其线程累计</td></tr>
<tr><td>Runtime sched running</td><td>{cpu_row(baseline, analysis['target']['runtime_process'])[0]} ms</td><td>{cpu_row(launched, analysis['target']['runtime_process'])[0]} ms</td><td>共享服务累计，非独占功耗</td></tr>
</table>

<h2>5. 优化方向</h2>
<ol>
<li><b>Client：</b>先用稳定态重复采集分离启动开销；检查每帧提交、资源更新、无效轮询和 CPUTime，避免为了维持 90 FPS 产生不必要的提交频率。</li>
<li><b>SpatialRuntime：</b>优先对比 Runtime DrawCall、Triangle、Mesh/Texture Memory 与 GPUTime；对持续高频但视觉收益低的网格、阴影、粒子、动画做 A/B 降级。</li>
<li><b>共享服务归因：</b>Runtime 是统一服务，报告中的 Runtime 增量是“由该场景触发的候选压力”，需要空场景/静态场景/目标场景三组重复 A/B 才能确认。</li>
<li><b>下一轮采集：</b>建议每阶段至少 30–60 秒，且增加启动后稳定态窗口；同时采集 Binder、wakeup、CPU idle/frequency 和电流校准数据。</li>
</ol>

<h2>6. 证据边界</h2>
<ul>
<li>本次只使用 Perfetto Trace 和 FastPerf，未使用 RenderDoc。</li>
<li>两段 Trace 是独立采集窗口，差异包含启动、温度和设备状态因素；不能视为严格同一时刻 A/B。</li>
<li>SpatialRuntime 总成本不能直接等同 {esc(target_package)} 独占功耗。</li>
<li>没有校准电流/电压，所有功耗结论均为相对压力方向，不是实际功率值。</li>
</ul>
<p class="note">Analysis JSON: <code>{esc(args.analysis)}</code></p>
</main></body></html>"""
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html_text, encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
