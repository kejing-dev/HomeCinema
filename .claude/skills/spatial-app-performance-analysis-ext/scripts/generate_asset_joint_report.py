#!/usr/bin/env python3
"""Backward-compatible entry point; use generate_asset_report.py."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> None:
    script = Path(__file__).with_name("generate_asset_report.py")
    sys.argv[0] = str(script)
    runpy.run_path(str(script), run_name="__main__")
    raise SystemExit(0)


if __name__ == "__main__":
    main()

import argparse
import html
import json
import pathlib
import re
from typing import Any


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def metric(data: dict[str, Any], path: list[str], default: Any = "n/a") -> Any:
    value: Any = data
    for key in path:
        if not isinstance(value, dict):
            return default
        value = value.get(key, default)
    return value


def card(label: str, value: Any, note: str = "") -> str:
    return (
        f'<div class="card"><div class="k">{esc(label)}</div>'
        f'<div class="v">{esc(value)}</div><div class="u">{esc(note)}</div></div>'
    )


def asset_section(renderdoc: dict[str, Any]) -> str:
    draws = renderdoc["draws"]
    mapping = draws["asset_mapping"]
    rows = "".join(
        f"<tr><td><code>{esc(row['name'])}</code></td><td>{row['draw_count']}</td></tr>"
        for row in mapping["top_assets"]
    )
    top_draws = "".join(
        "<tr>"
        f"<td>{row['chunk_index']}</td><td>{row['triangles']:,}</td>"
        f"<td>{row['index_count']:,}</td><td>{row['instance_count']}</td>"
        f"<td>{esc(', '.join(row['asset_candidates']) or '未映射')}</td>"
        f"<td>{esc(row['mapping_confidence'])}</td>"
        "</tr>"
        for row in draws["top"]
    )
    top_textures = "".join(
        "<tr>"
        f"<td>{image.get('chunk_index', 'n/a')}</td>"
        f"<td>{image.get('resource_id', 'n/a')}</td>"
        f"<td>{esc(', '.join(image.get('debug_names', [])) or '未命名')}</td>"
        f"<td>{image.get('width', 'n/a')} × {image.get('height', 'n/a')}</td>"
        f"<td>{image.get('mip_levels', 'n/a')}</td>"
        f"<td>{image.get('array_layers', 'n/a')}</td>"
        f"<td>{image.get('samples', 'n/a')}</td>"
        f"<td>{image.get('declared_size', 'n/a')}</td>"
        f"<td>{esc(image.get('format', 'n/a'))}</td>"
        "</tr>"
        for image in renderdoc.get("images", {}).get("top_textures", [])
    )
    texture_block = f"""
<h3>5.3 Top Texture / Image</h3>
<table><tr><th>chunk</th><th>ResourceId</th><th>Debug Name</th><th>尺寸</th><th>mips</th><th>layers</th><th>samples</th><th>declared size</th><th>format</th></tr>{top_textures}</table>
<p class="muted">Top Texture 按 RenderDoc XML 中 <code>vkCreateImage</code> 的 declared memory requirement size 排序；这不是实际驻留显存，也不能单独代表 GPU 带宽或纹理采样耗时。</p>
"""
    coverage = draws["asset_mapped_count"] / max(draws["count"], 1) * 100
    return f"""
<div class="callout warn"><b>增量关联结果：</b>本节只增加资产级信息，不替换原有 Perfetto/FastPerf、RenderDoc、跨源验证、根因判断和 A/B 章节。Detail.xml 中的
<code>vkSetDebugUtilsObjectNameEXT</code> 提供了 {mapping['debug_object_name_count']} 个对象命名记录；按 ResourceId 和 chunk 顺序重建绑定状态后，
{draws['asset_mapped_count']}/{draws['count']} 个 indexed draw 获得资产候选（{coverage:.1f}%）。</div>
<div class="grid3">
{card("Debug Utils named resources", mapping["named_resource_count"], "ResourceId → ObjectName")}
{card("asset-mapped draws", f"{draws['asset_mapped_count']}/{draws['count']}", f"{coverage:.1f}% coverage")}
{card("unique asset names", mapping["unique_asset_name_count"], "来自 XML 对象名")}
</div>
<h3>5.1 高频资产候选</h3>
<table><tr><th>资产 Debug Name</th><th>关联 draw 数</th></tr>{rows}</table>
<h3>5.2 最大 draw 的资产关联</h3>
<table><tr><th>chunk</th><th>triangles upper bound</th><th>indexCount</th><th>instances</th><th>资产候选</th><th>置信度</th></tr>{top_draws}</table>
{texture_block}
<p class="muted">关联置信度为 <code>high</code> 表示 draw 的当前绑定 ResourceId 可直接反查到 Debug Utils 对象名；这不等同于已证明该资产是实时异常帧的唯一根因。RenderDoc 单帧与 Perfetto 连续窗口仍按原报告规则视为未做同帧对齐。</p>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--renderdoc", required=True, type=pathlib.Path)
    parser.add_argument("--baseline", required=True, type=pathlib.Path)
    parser.add_argument("--live", type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()
    renderdoc = json.loads(args.renderdoc.read_text(encoding="utf-8"))
    report = args.baseline.read_text(encoding="utf-8")
    section = asset_section(renderdoc)
    if "{{ASSET_ATTRIBUTION}}" in report:
        report = report.replace("{{ASSET_ATTRIBUTION}}", section)
    else:
        match = re.search(r"<h2>5\.", report)
        if not match:
            raise RuntimeError("Baseline report has no section 5 insertion point")
        insertion = "<h2>5. 资产级 RenderDoc 关联</h2>" + section + "\n"
        report = report[:match.start()] + "__ASSET_SECTION__\n" + report[match.start():]

        def renumber(match: re.Match[str]) -> str:
            number = int(match.group(1))
            return f"<h2>{number + 1}." if number >= 5 else match.group(0)

        report = re.sub(r"<h2>(\d+)\.", renumber, report)
        report = report.replace("__ASSET_SECTION__", insertion)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
