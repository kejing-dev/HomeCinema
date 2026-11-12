#!/usr/bin/env python3
"""Extract stable Vulkan counters from a RenderDoc-exported XML file."""
from __future__ import annotations

import argparse
import json
import pathlib
import xml.etree.ElementTree as ET
from collections import Counter
from typing import Any


def field(chunk: ET.Element, name: str, default: int | str | None = None) -> Any:
    for node in chunk.iter():
        if node is chunk or node.attrib.get("name") != name or not node.text:
            continue
        value = node.text.strip()
        try:
            return int(value, 0)
        except ValueError:
            return value
    return default


def resource_ids(chunk: ET.Element, name: str | None = None) -> list[int]:
    result = []
    for node in chunk.iter():
        if node.tag != "ResourceId" or (name is not None and node.attrib.get("name") != name):
            continue
        if node.text and node.text.strip().isdigit():
            result.append(int(node.text.strip()))
    return result


def object_names(chunks: list[ET.Element]) -> dict[int, list[str]]:
    result: dict[int, list[str]] = {}
    for chunk in chunks:
        if chunk.attrib.get("name") != "vkSetDebugUtilsObjectNameEXT":
            continue
        objects = resource_ids(chunk, "Object")
        names = [
            node.text.strip()
            for node in chunk.iter()
            if node.attrib.get("name") == "ObjectName" and node.text and node.text.strip()
        ]
        for object_id in objects:
            result.setdefault(object_id, []).extend(names)
    return {key: list(dict.fromkeys(value)) for key, value in result.items()}


def asset_names(names: list[str]) -> list[str]:
    result = []
    for name in names:
        if "Model:" in name or "EngineMesh" in name or "asset" in name.lower() or "mesh" in name.lower():
            result.append(name)
    return list(dict.fromkeys(result))


class RenderDocXmlError(ValueError):
    """Raised when the input is not a usable RenderDoc-exported XML file."""


def load_renderdoc_xml(xml_path: pathlib.Path) -> ET.Element:
    if not xml_path.exists():
        raise RenderDocXmlError(f"Input XML does not exist: {xml_path}")
    if not xml_path.is_file():
        raise RenderDocXmlError(f"Input XML is not a file: {xml_path}")
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as exc:
        raise RenderDocXmlError(f"Invalid XML: {xml_path}: {exc}") from exc
    return root


def renderdoc_chunks(root: ET.Element, xml_path: pathlib.Path) -> list[ET.Element]:
    chunks_node = root.find("chunks")
    if chunks_node is None:
        raise RenderDocXmlError(
            f"Input XML is not a RenderDoc export: missing <chunks> section in {xml_path}"
        )
    chunks = list(chunks_node)
    if not chunks:
        raise RenderDocXmlError(
            f"Input XML is not a usable RenderDoc export: <chunks> is empty in {xml_path}"
        )
    renderdoc_like_chunks = [
        chunk
        for chunk in chunks
        if chunk.attrib.get("name") or chunk.attrib.get("chunkIndex") is not None
    ]
    if not renderdoc_like_chunks:
        raise RenderDocXmlError(
            f"Input XML is not a RenderDoc export: chunks lack RenderDoc chunk metadata in {xml_path}"
        )
    return chunks


def run(xml_path: pathlib.Path) -> dict[str, Any]:
    root = load_renderdoc_xml(xml_path)
    chunks = renderdoc_chunks(root, xml_path)
    names = Counter(chunk.attrib.get("name", "") for chunk in chunks)
    draws = [chunk for chunk in chunks if chunk.attrib.get("name") == "vkCmdDrawIndexed"]
    dispatches = [chunk for chunk in chunks if chunk.attrib.get("name") == "vkCmdDispatch"]
    barriers = [chunk for chunk in chunks if chunk.attrib.get("name") == "vkCmdPipelineBarrier"]
    debug_names = object_names(chunks)
    draw_rows = []
    raw_indices = instanced_indices = instances = 0
    current_pipeline: int | None = None
    current_vertex_buffers: list[int] = []
    current_index_buffer: int | None = None
    current_descriptors: list[int] = []
    for chunk in draws:
        chunk_position = chunks.index(chunk)
        for state_chunk in chunks[:chunk_position]:
            state_name = state_chunk.attrib.get("name")
            if state_name == "vkCmdBindPipeline":
                pipeline_ids = resource_ids(state_chunk, "pipeline")
                if pipeline_ids:
                    current_pipeline = pipeline_ids[-1]
            elif state_name == "vkCmdBindVertexBuffers":
                current_vertex_buffers = resource_ids(state_chunk, "pBuffers")
            elif state_name == "vkCmdBindIndexBuffer":
                index_ids = resource_ids(state_chunk, "buffer")
                if index_ids:
                    current_index_buffer = index_ids[-1]
            elif state_name == "vkCmdBindDescriptorSets":
                current_descriptors = resource_ids(state_chunk, "pDescriptorSets")
        indices = int(field(chunk, "indexCount", 0) or 0)
        count = max(int(field(chunk, "instanceCount", 1) or 1), 1)
        bound_ids = (
            ([current_pipeline] if current_pipeline is not None else [])
            + current_vertex_buffers
            + ([current_index_buffer] if current_index_buffer is not None else [])
            + current_descriptors
        )
        bound_names = []
        for resource_id in bound_ids:
            bound_names.extend(debug_names.get(resource_id, []))
        candidates = asset_names(bound_names)
        row = {
            "chunk_index": int(chunk.attrib.get("chunkIndex", -1)),
            "index_count": indices,
            "instance_count": count,
            "triangles": (indices * count) // 3,
            "first_index": field(chunk, "firstIndex"),
            "first_instance": field(chunk, "firstInstance"),
            "pipeline_resource_id": current_pipeline,
            "vertex_buffer_resource_ids": current_vertex_buffers,
            "index_buffer_resource_id": current_index_buffer,
            "descriptor_set_resource_ids": current_descriptors,
            "bound_debug_names": list(dict.fromkeys(bound_names)),
            "asset_candidates": candidates,
            "mapping_confidence": "high" if candidates else "unmapped",
        }
        draw_rows.append(row)
        raw_indices += indices
        instanced_indices += indices * count
        instances += count
    images = []
    for chunk in chunks:
        if chunk.attrib.get("name") != "vkCreateImage":
            continue
        image_ids = resource_ids(chunk, "Image")
        image_id = image_ids[-1] if image_ids else None
        image_names = debug_names.get(image_id, []) if image_id is not None else []
        images.append({
            "chunk_index": int(chunk.attrib.get("chunkIndex", -1)),
            "resource_id": image_id,
            "debug_names": image_names,
            "width": field(chunk, "width"),
            "height": field(chunk, "height"),
            "depth": field(chunk, "depth"),
            "mip_levels": field(chunk, "mipLevels"),
            "array_layers": field(chunk, "arrayLayers"),
            "samples": field(chunk, "samples"),
            "format": field(chunk, "format"),
            "declared_size": field(chunk, "size"),
        })
    barrier_fields = {
        "memory_barrier_count": sum(int(field(chunk, "memoryBarrierCount", 0) or 0) for chunk in barriers),
        "buffer_memory_barrier_count": sum(int(field(chunk, "bufferMemoryBarrierCount", 0) or 0) for chunk in barriers),
        "image_memory_barrier_count": sum(int(field(chunk, "imageMemoryBarrierCount", 0) or 0) for chunk in barriers),
    }
    return {
        "source": {"path": str(xml_path), "size_bytes": xml_path.stat().st_size},
        "header": {
            "driver": (root.findtext("./header/driver") or ""),
            "app_name": (root.findtext(".//string[@name='AppName']") or ""),
            "engine_name": (root.findtext(".//string[@name='EngineName']") or ""),
        },
        "chunk_count": len(chunks),
        "api_counts": {name: names[name] for name in sorted(names) if name in {
            "vkCmdDrawIndexed", "vkCmdDispatch", "vkCmdPipelineBarrier",
            "vkCmdBindPipeline", "vkCmdBindDescriptorSets", "vkCmdBindVertexBuffers",
            "vkCmdBindIndexBuffer", "vkCreateGraphicsPipelines", "vkCreateComputePipelines",
            "vkCreateShaderModule", "vkCreateImage", "vkCreateBuffer", "vkQueueSubmit",
        }},
        "draws": {
            "count": len(draws),
            "raw_triangles_upper_bound": raw_indices // 3,
            "instanced_triangles_upper_bound": instanced_indices // 3,
            "instance_total": instances,
            "top": sorted(draw_rows, key=lambda row: row["triangles"], reverse=True)[:20],
            "asset_mapped_count": sum(bool(row["asset_candidates"]) for row in draw_rows),
            "asset_mapping": {
                "debug_object_name_count": sum(len(names) for names in debug_names.values()),
                "named_resource_count": len(debug_names),
                "unique_asset_name_count": len({
                    name for names in debug_names.values() for name in asset_names(names)
                }),
                "top_assets": [
                    {"name": name, "draw_count": count}
                    for name, count in Counter(
                        asset_name
                        for row in draw_rows
                        for asset_name in row["asset_candidates"]
                    ).most_common(30)
                ],
            },
        },
        "dispatch": {
            "count": len(dispatches),
            "group_totals": [sum(int(field(chunk, axis, 0) or 0) for chunk in dispatches) for axis in ("x", "y", "z")],
        },
        "barriers": {"api_count": len(barriers), **barrier_fields},
        "images": {
            "count": len(images),
            "declared_size_sum": sum(int(image["declared_size"] or 0) for image in images),
            "largest": sorted(images, key=lambda image: (int(image["width"] or 0) * int(image["height"] or 0)), reverse=True)[:20],
            "top_textures": sorted(
                images,
                key=lambda image: int(image["declared_size"] or 0),
                reverse=True,
            )[:20],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml", required=True, type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()
    try:
        result = run(args.xml)
    except RenderDocXmlError as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
