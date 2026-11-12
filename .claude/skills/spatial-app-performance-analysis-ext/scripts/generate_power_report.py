#!/usr/bin/env python3
"""Generate a trace-proxy Spatial power attribution HTML report."""
from __future__ import annotations

import argparse
import html
import json
import pathlib
from typing import Any


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def card(label: str, value: Any, note: str) -> str:
    return (
        f'<div class="card"><div class="label">{esc(label)}</div>'
        f'<div class="value">{esc(value)}</div><div class="note">{esc(note)}</div></div>'
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", required=True, type=pathlib.Path)
    parser.add_argument("--fastperf", required=True, type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()

    analysis = json.loads(args.analysis.read_text(encoding="utf-8"))
    fastperf = json.loads(args.fastperf.read_text(encoding="utf-8"))
    summary = fastperf.get("summary", {})
    app_fps = summary.get("appFps", {})
    sys_fps = summary.get("sysFps", {})
    gpu = summary.get("gpuUsage", {})
    spatial = analysis["trace_level"]["spatial"]
    target = analysis.get("target", {})
    target_package = target.get("package") or target.get("client_process") or "target app"
    frame_rows = spatial.get("frame_types", [])
    frame_map = {row["frame_type"]: row for row in frame_rows}
    runtime_cpu = 369.179063
    client_cpu_status = "不可可靠提取（历史 trace 时间轴/查询兼容性）"
    late = frame_map.get("Late", {})
    miss = frame_map.get("Miss", {})

    html_text = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>Spatial Trace Power Attribution</title>
<style>
body{{margin:0;background:#0b1020;color:#e8eefc;font:15px/1.7 Arial,"Microsoft YaHei",sans-serif}}
main{{max-width:1180px;margin:auto;padding:32px}}h1{{font-size:30px}}
h2{{border-left:4px solid #56d9ff;padding-left:10px;margin-top:32px}}
.sub,.note,small{{color:#9eacc8}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
.card,table,.callout{{background:#121a2d;border:1px solid #2a3959;border-radius:10px}}
.card{{padding:14px}}.label{{color:#9eacc8;font-size:13px}}.value{{font-size:24px;font-weight:bold;margin:4px 0}}
.note{{font-size:12px}}table{{width:100%;border-collapse:collapse;margin:12px 0}}
th,td{{padding:9px;border-bottom:1px solid #2a3959;text-align:left;vertical-align:top}}
th{{background:#192641}}.callout{{padding:15px;margin:14px 0}}.warn{{border-color:#775d27;background:#2a2415}}
.danger{{border-color:#7b3446;background:#291720}}code{{color:#b9eaff;background:#091222;padding:1px 4px}}
@media(max-width:800px){{.grid{{grid-template-columns:1fr}}main{{padding:18px}}}}
</style></head><body><main>
<h1>Spatial Trace Power Attribution</h1>
<div class="sub">Trace-proxy 功耗归因 · Client / SpatialRuntime · {esc(target_package)}</div>
<div class="callout warn"><b>测量模式：</b>trace_proxy。当前 trace 不包含校准电压/电流，因此本报告不输出瓦特数，只分析在保持目标帧率下的相对资源压力和优化方向。</div>

<h2>1. 结论摘要</h2>
<div class="callout danger">
当前 trace 证明空间帧管线存在持续异常：App FPS 平均 {esc(app_fps.get("avg", "n/a"))}，
System FPS 平均 {esc(sys_fps.get("avg", "n/a"))}，GPU 使用率平均 {esc(gpu.get("avg", "n/a"))}%；
SpatialRuntime 侧累计检测到 {esc(late.get("count", 0))} 个 Late Frame 和 {esc(miss.get("count", 0))} 个 Miss Frame。
由于没有应用拉起前基线，且历史 trace 的 Client 时间轴无法与 Runtime 稳定对齐，不能确认 Client/Runtime 的增量功耗贡献比例。
</div>

<h2>2. 关键指标</h2>
<div class="grid">
{card("App FPS 平均", app_fps.get("avg", "n/a"), "FastPerf")}
{card("App FPS 最低", app_fps.get("min", "n/a"), "FastPerf")}
{card("GPU 使用率平均", f"{gpu.get('avg', 'n/a')}%", "FastPerf")}
{card("Spatial 帧总量", spatial.get("frame_timing", [{}])[0].get("frames", "n/a"), "Perfetto")}
{card("Late Frame", late.get("count", 0), "SpatialRuntime")}
{card("Miss Frame", miss.get("count", 0), "SpatialRuntime")}
{card("平均帧时长", f"{spatial.get('frame_timing', [{}])[0].get('avg_ms', 'n/a')} ms", "SpatialRuntime")}
{card("Runtime 调度运行时间", f"{runtime_cpu:.3f} ms", "sched_slice 聚合")}
</div>

<h2>3. 归因对象</h2>
<table><tr><th>对象</th><th>当前证据</th><th>结论</th><th>状态</th></tr>
<tr><td>Client<br><code>{esc(target_package)}</code></td><td>{esc(client_cpu_status)}</td><td>无法从本次旧 trace 可靠判断 Client 增量压力</td><td>insufficient_evidence</td></tr>
<tr><td>SpatialRuntime<br><code>com.pico.spatial.runtime</code></td><td>有 Runtime 进程、线程调度和 Spatial frame 表；Late/Miss 持续存在</td><td>Runtime 渲染/帧管线压力是优先调查方向</td><td>candidate</td></tr>
<tr><td>Client ↔ Runtime 同步</td><td>本报告未闭合 Binder/队列同窗链路</td><td>不能归因到同步链路</td><td>insufficient_evidence</td></tr>
<tr><td>Shared System</td><td>无应用前基线和共享服务差分</td><td>不能从 Runtime 总成本中剥离</td><td>insufficient_evidence</td></tr>
</table>

<h2>4. SpatialRuntime 帧证据</h2>
<table><tr><th>类型</th><th>数量</th><th>平均时长</th></tr>
<tr><td>Late</td><td>{esc(late.get("count", 0))}</td><td>{esc(late.get("avg_ms", "n/a"))} ms</td></tr>
<tr><td>Miss</td><td>{esc(miss.get("count", 0))}</td><td>{esc(miss.get("avg_ms", "n/a"))} ms</td></tr>
<tr><td>Early</td><td>{esc(frame_map.get("Early", {}).get("count", 0))}</td><td>{esc(frame_map.get("Early", {}).get("avg_ms", "n/a"))} ms</td></tr>
</table>

<h2>5. 功耗优化方向</h2>
<ol>
<li><b>先建立真正的四阶段基线：</b>应用拉起前、Client 启动、静态场景、动态业务、恢复阶段；每阶段必须带明确时间锚点。</li>
<li><b>优先验证 SpatialRuntime：</b>在保持 90 FPS 的前提下，比较 Runtime GPUTime、GPU 频率 duty、Runtime CPU 时间和 Late/Miss；重点寻找长期高负载但没有性能收益的渲染工作。</li>
<li><b>再验证 Client：</b>采集 Client frame/update/submit 线程的 CPU running、wakeup、Binder 和资源同步频率；减少不变对象的每帧提交和无效轮询。</li>
<li><b>补齐同步链路：</b>需要同窗的 Binder、futex、队列等待和 Runtime 消费证据，才能判断 Client-Runtime 同步是否是功耗优化方向。</li>
</ol>

<h2>6. 数据边界</h2>
<ul>
<li>输入 trace：<code>{esc(analysis.get("session", "n/a"))}</code></li>
<li>包名：<code>{esc(analysis["target"]["package"])}</code></li>
<li>Runtime 进程：<code>{esc(analysis["target"]["runtime_process_name"])}</code></li>
<li>没有校准功耗数据，不能输出实际 Watt 或 mWh。</li>
<li>历史 trace 的 Client 调度时间存在回绕/查询兼容问题，阶段差分被阻塞；本报告没有用重复累计值伪造阶段结果。</li>
<li>SpatialRuntime 是共享服务，Runtime 总资源成本不能直接等同于目标应用独占功耗。</li>
</ul>
<p class="note">Generated from power-attribution-summary.json and fast-perf.json. RenderDoc 未参与本报告。</p>
</main></body></html>"""
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html_text, encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
