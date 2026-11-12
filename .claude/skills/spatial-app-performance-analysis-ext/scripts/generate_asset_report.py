#!/usr/bin/env python3
"""Generate or incrementally augment a Spatial performance analysis report."""
from __future__ import annotations

import argparse
import html
import json
import pathlib
import webbrowser
from typing import Any


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def card(label: str, value: Any, note: str) -> str:
    return (
        '<div class="card"><div class="k">'
        + esc(label)
        + '</div><div class="v">'
        + esc(value)
        + '</div><div class="u">'
        + esc(note)
        + "</div></div>"
    )


def asset_block(data: dict[str, Any]) -> str:
    draws = data["draws"]
    mapping = draws["asset_mapping"]
    coverage = draws["asset_mapped_count"] / max(draws["count"], 1) * 100
    assets = "".join(
        "<tr><td><code>"
        + esc(row["name"])
        + "</code></td><td>"
        + str(row["draw_count"])
        + "</td></tr>"
        for row in mapping["top_assets"]
    )
    top_draws = "".join(
        "<tr><td>"
        + str(row["chunk_index"])
        + "</td><td>"
        + f"{row['triangles']:,}"
        + "</td><td>"
        + f"{row['index_count']:,}"
        + "</td><td>"
        + str(row["instance_count"])
        + "</td><td>"
        + esc(", ".join(row["asset_candidates"]) or "unmapped")
        + "</td><td>"
        + esc(row["mapping_confidence"])
        + "</td></tr>"
        for row in draws["top"]
    )
    textures = "".join(
        "<tr><td>"
        + str(image.get("chunk_index", "n/a"))
        + "</td><td>"
        + str(image.get("resource_id", "n/a"))
        + "</td><td>"
        + esc(", ".join(image.get("debug_names", [])) or "unnamed")
        + "</td><td>"
        + f"{image.get('width', 'n/a')} x {image.get('height', 'n/a')}"
        + "</td><td>"
        + str(image.get("mip_levels", "n/a"))
        + "</td><td>"
        + str(image.get("array_layers", "n/a"))
        + "</td><td>"
        + str(image.get("samples", "n/a"))
        + "</td><td>"
        + str(image.get("declared_size", "n/a"))
        + "</td><td>"
        + esc(image.get("format", "n/a"))
        + "</td></tr>"
        for image in data.get("images", {}).get("top_textures", [])
    )
    return f"""
<div class="callout warn"><b>Incremental asset attribution:</b>
This section is added to the existing Spatial performance analysis report. It does not replace the live,
RenderDoc, cross-source, root-cause, A/B, or limitations sections. The XML contains
{mapping["debug_object_name_count"]} debug object names; {draws["asset_mapped_count"]}/{draws["count"]}
indexed draws have asset candidates ({coverage:.1f}%).</div>
<div class="grid3">
{card("Debug Utils named resources", mapping["named_resource_count"], "ResourceId to ObjectName")}
{card("asset-mapped draws", f"{draws['asset_mapped_count']}/{draws['count']}", f"{coverage:.1f}% coverage")}
{card("unique asset names", mapping["unique_asset_name_count"], "from XML object names")}
</div>
<h3>5.1 Top asset candidates</h3>
<table><tr><th>Debug Name</th><th>draw count</th></tr>{assets}</table>
<h3>5.2 Top draws by asset</h3>
<table><tr><th>chunk</th><th>triangles</th><th>indexCount</th><th>instances</th><th>asset candidates</th><th>confidence</th></tr>{top_draws}</table>
<h3>5.3 Top Texture / Image</h3>
<table><tr><th>chunk</th><th>ResourceId</th><th>Debug Name</th><th>size</th><th>mips</th><th>layers</th><th>samples</th><th>declared size</th><th>format</th></tr>{textures}</table>
<p class="muted">Top Texture is sorted by the declared memory requirement in
<code>vkCreateImage</code>. It is not resident VRAM and is not GPU sampling time.</p>
<p class="muted">Texture debug names are unavailable when the capture has no
<code>vkSetDebugUtilsObjectNameEXT</code> entry for the corresponding image
ResourceId; "unnamed" is an explicit data limitation, not an inferred asset name.</p>
"""


def incremental(renderdoc: pathlib.Path, baseline: pathlib.Path, output: pathlib.Path) -> None:
    report = baseline.read_text(encoding="utf-8")
    token = "{{ASSET_ATTRIBUTION}}"
    if token not in report:
        raise RuntimeError(
            "Baseline is not an unfilled performance-analysis template: missing "
            "{{ASSET_ATTRIBUTION}}. Use an untouched template or provide a "
            "report generated with the asset placeholder preserved."
        )
    data = json.loads(renderdoc.read_text(encoding="utf-8"))
    report = report.replace(token, asset_block(data), 1)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")


def load_live_data(
    fastperf: pathlib.Path, report_data: pathlib.Path | None
) -> tuple[dict[str, Any], pathlib.Path | None]:
    live = json.loads(fastperf.read_text(encoding="utf-8"))
    candidate = report_data
    if candidate is None:
        sibling = fastperf.with_name("report-data.json")
        if sibling.is_file():
            candidate = sibling
        else:
            for parent in fastperf.parents:
                sibling = parent / "report-data.json"
                if sibling.is_file():
                    candidate = sibling
                    break
    if candidate is not None:
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        report = json.loads(candidate.read_text(encoding="utf-8"))
        for key in ("spr_frame_types", "spr_stats"):
            if key in report:
                live[key] = report[key]
    return live, candidate


def full(
    renderdoc: pathlib.Path,
    fastperf: pathlib.Path,
    output: pathlib.Path,
    report_data: pathlib.Path | None,
) -> None:
    data = json.loads(renderdoc.read_text(encoding="utf-8"))
    live, report_data_path = load_live_data(fastperf, report_data)
    frame_types = live.get("spr_frame_types", {})
    stats = live.get("spr_stats", {})
    live_summary = live.get("summary", {})
    app_fps = live_summary.get("appFps", {})
    sys_fps = live_summary.get("sysFps", {})
    gpu_usage = live_summary.get("gpuUsage", {})
    title = "Spatial Performance x RenderDoc Analysis Report"
    identity = "RenderDoc XML + Perfetto/FastPerf; evidence-bounded analysis"
    summary = (
        "This report preserves the distinction between a RenderDoc single frame "
        "and a Perfetto time window. Asset attribution is structural evidence, "
        "not same-frame GPU causality."
    )
    live_html = (
        '<div class="grid">'
        + card("App FPS average", app_fps.get("avg", "n/a"), "FastPerf live window")
        + card("App FPS minimum", app_fps.get("min", "n/a"), "FastPerf live window")
        + card("System FPS average", sys_fps.get("avg", "n/a"), "FastPerf live window")
        + card("GPU usage average", f"{gpu_usage.get('avg', 'n/a')}%", "FastPerf live window")
        + card("Spatial Late", frame_types.get("Late", "n/a"), "live window")
        + card("Spatial Miss", frame_types.get("Miss", "n/a"), "live window")
        + card("Average frame", f"{stats.get('avg_frame_ms', 'n/a')} ms", "SpatialRuntime")
        + card("Average GPU frame", f"{stats.get('avg_gpu_ms', 'n/a')} ms", "live telemetry")
        + "</div>"
    )
    renderdoc_html = (
        '<div class="grid">'
        + card("Indexed draws", data["draws"]["count"], "RenderDoc single frame")
        + card("Raw triangles", f"{data['draws']['raw_triangles_upper_bound']:,}", "upper bound")
        + card("Instanced triangles", f"{data['draws']['instanced_triangles_upper_bound']:,}", "upper bound")
        + card("Compute dispatch", data["dispatch"]["count"], "Vulkan API events")
        + card("Pipeline barriers", data["barriers"]["api_count"], "API event count")
        + "</div>"
    )
    template = pathlib.Path(__file__).resolve().parents[1] / "assets" / "joint-report-template.html"
    report = template.read_text(encoding="utf-8")
    replacements = {
        "{{TITLE}}": title,
        "{{IDENTITY}}": identity,
        "{{TAGS}}": '<span class="tag">candidate</span><span class="tag">RenderDoc XML</span><span class="tag">Perfetto/FastPerf</span>',
        "{{SUMMARY}}": summary,
        "{{CROSS_SOURCE_SUMMARY}}": '<div class="callout warn">RenderDoc and Perfetto are not verified to share a frame or timestamp key.</div>',
        "{{LIVE_METRICS}}": live_html,
        "{{RENDERDOC_METRICS}}": renderdoc_html,
        "{{RENDERDOC_TABLE}}": "<p>See the RenderDoc counters above and the asset section below.</p>",
        "{{TOP_TEXTURES}}": "",
        "{{CROSS_SOURCE_TABLE}}": "<p>Mechanism support only until same-window GPU timing or A/B evidence is available.</p>",
        "{{ASSET_ATTRIBUTION}}": asset_block(data),
        "{{ROOT_CAUSE}}": "<p>Conclusion level: candidate. Do not infer GPU causality from counts alone.</p>",
        "{{ACTIONS}}": "<p>Run reduced-content, texture-size, and GPU-timing A/B experiments.</p>",
        "{{VALIDATION}}": "<p>Repeat the same capture and compare FPS, Late/Miss, GPU frame time, and resource counters.</p>",
        "{{PROVENANCE}}": (
            f"<p>RenderDoc source: <code>{esc(data['source']['path'])}</code>. "
            f"FastPerf source: <code>{esc(fastperf)}</code>. "
            f"Report data source: <code>{esc(report_data_path or 'not provided')}</code>.</p>"
        ),
        "{{CONCLUSION_LEVEL}}": "candidate",
    }
    for token, value in replacements.items():
        report = report.replace(token, value)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--renderdoc", required=True, type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    parser.add_argument("--baseline", type=pathlib.Path)
    parser.add_argument("--fastperf", type=pathlib.Path)
    parser.add_argument("--report-data", type=pathlib.Path)
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the generated HTML with the system default browser.",
    )
    args = parser.parse_args()
    if args.baseline:
        incremental(args.renderdoc, args.baseline, args.out)
    elif args.fastperf:
        full(args.renderdoc, args.fastperf, args.out, args.report_data)
    else:
        parser.error("provide either --baseline for incremental mode or --fastperf for full mode")
    if args.open_browser:
        browser_url = args.out.resolve().as_uri()
        if not webbrowser.open(browser_url):
            raise RuntimeError(
                f"Could not open the generated report in the default browser: {args.out}"
            )
    print(args.out)


if __name__ == "__main__":
    main()
