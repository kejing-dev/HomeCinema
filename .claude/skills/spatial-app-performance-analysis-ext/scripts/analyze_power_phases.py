#!/usr/bin/env python3
"""Analyze baseline and post-launch PICO traces for power-pressure attribution."""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import re
from typing import Any


SESSION_ID_PATTERN = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


class TraceQueryError(RuntimeError):
    pass


def validate_session_id(value: str, option_name: str) -> str:
    if not value:
        raise ValueError(f"{option_name} must be a loaded pico-cli trace session ID")
    path = pathlib.Path(value)
    if path.suffix.lower() in {".perfetto-trace", ".pftrace", ".json"} or path.exists():
        raise ValueError(
            f"{option_name} received a file path, not a loaded trace session ID: {value}. "
            "Run `pico-cli perf trace load <trace-file>` first and pass the returned UUID."
        )
    if not SESSION_ID_PATTERN.fullmatch(value):
        raise ValueError(
            f"{option_name} must be the UUID returned by `pico-cli perf trace load`, got: {value}"
        )
    return value


def query(session: str, sql: str, pico_cli: str) -> list[dict[str, Any]]:
    executable = shutil.which(pico_cli) or shutil.which(f"{pico_cli}.cmd") or pico_cli
    result = subprocess.run(
        [executable, "perf", "trace", "query", "--session", session, "--sql", sql],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        detail = (result.stderr or result.stdout or "").strip()
        raise TraceQueryError(
            f"Trace query returned non-JSON output for session {session}: {detail[:500]}"
        ) from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise TraceQueryError(
            f"Trace query failed for session {session} (exit {result.returncode}): {detail[:500]}"
        )
    if payload.get("success") is False or payload.get("error"):
        detail = payload.get("error") or payload.get("message") or "unknown query error"
        raise TraceQueryError(
            f"Trace query rejected for session {session}: {detail}. SQL: {sql[:300]}"
        )
    data = payload.get("data")
    if not isinstance(data, dict):
        raise TraceQueryError(
            f"Trace query response has no data object for session {session}. SQL: {sql[:300]}"
        )
    rows = data.get("rows")
    if rows is None:
        raise TraceQueryError(
            f"Trace query response has no rows field for session {session}. SQL: {sql[:300]}"
        )
    return rows or []


def validate_loaded_session(session: str, pico_cli: str, option_name: str) -> None:
    validate_session_id(session, option_name)
    query(session, "SELECT 1 AS session_probe", pico_cli)


def one(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return rows[0] if rows else {}


def phase_metrics(session: str, package: str, runtime: str, pico_cli: str) -> dict[str, Any]:
    processes = query(
        session,
        "SELECT upid, pid, name FROM process "
        f"WHERE name IN ({json.dumps(package)}, {json.dumps(runtime)})",
        pico_cli,
    )
    process_map = {row.get("name"): row for row in processes}
    cpu = []
    for name in (package, runtime):
        process = process_map.get(name)
        upid = process.get("upid", -1) if process else -1
        row = one(query(
            session,
            "SELECT COUNT(*) AS sched_slices, "
            "SUM(dur) / 1000000.0 AS running_ms, "
            "AVG(dur) / 1000000.0 AS avg_slice_ms, "
            "MAX(dur) / 1000000.0 AS max_slice_ms "
            f"FROM sched_slice WHERE utid IN (SELECT utid FROM thread WHERE upid = {int(upid)})",
            pico_cli,
        ))
        cpu.append({"process": name, "present": bool(process), **row})

    metrics = query(
        session,
        "SELECT name, COUNT(*) AS samples, AVG(value) AS avg_value, "
        "MIN(value) AS min_value, MAX(value) AS max_value "
        "FROM TargetAppMetricCounterStates GROUP BY name ORDER BY name",
        pico_cli,
    )
    metric_map = {row["name"]: row for row in metrics if row.get("name")}
    frames = one(query(
        session,
        "SELECT COUNT(*) AS frames, AVG(dur) / 1000000.0 AS avg_ms, "
        "MAX(dur) / 1000000.0 AS max_ms, "
        "SUM(CASE WHEN name LIKE 'Late Frame%' THEN 1 ELSE 0 END) AS late, "
        "SUM(CASE WHEN name LIKE 'Miss Frame%' THEN 1 ELSE 0 END) AS miss, "
        "SUM(CASE WHEN name LIKE 'Discard Frame%' THEN 1 ELSE 0 END) AS discard "
        "FROM OpenXRClientSpatialFrames",
        pico_cli,
    ))
    client_times = one(query(
        session,
        "SELECT COUNT(*) AS samples, AVG(dur) / 1000000.0 AS avg_ms, "
        "SUM(dur) / 1000000.0 AS total_ms FROM OpenXRClientSpatialCPUTime",
        pico_cli,
    ))
    gpu_times = one(query(
        session,
        "SELECT COUNT(*) AS samples, AVG(dur) / 1000000.0 AS avg_ms, "
        "SUM(dur) / 1000000.0 AS total_ms FROM OpenXRClientSpatialGPUTime",
        pico_cli,
    ))
    return {
        "processes": process_map,
        "cpu": cpu,
        "runtime_metrics": metric_map,
        "spatial_frames": frames,
        "client_cpu_time": client_times,
        "client_gpu_time": gpu_times,
    }


def number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--baseline-session",
        required=True,
        help="Loaded trace session UUID from `pico-cli perf trace load`, not a .perfetto-trace path",
    )
    parser.add_argument(
        "--launched-session",
        required=True,
        help="Loaded trace session UUID from `pico-cli perf trace load`, not a .perfetto-trace path",
    )
    parser.add_argument("--package", required=True)
    parser.add_argument("--runtime-process", default="com.pico.spatial.runtime")
    parser.add_argument("--baseline-fastperf", type=pathlib.Path)
    parser.add_argument("--launched-fastperf", type=pathlib.Path)
    parser.add_argument("--pico-cli", default="pico-cli")
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()

    try:
        validate_loaded_session(args.baseline_session, args.pico_cli, "--baseline-session")
        validate_loaded_session(args.launched_session, args.pico_cli, "--launched-session")
    except (ValueError, TraceQueryError) as exc:
        raise SystemExit(f"[INPUT ERROR] {exc}") from exc

    baseline = phase_metrics(args.baseline_session, args.package, args.runtime_process, args.pico_cli)
    launched = phase_metrics(args.launched_session, args.package, args.runtime_process, args.pico_cli)
    metric_names = [
        "Draw Call Count", "3D Mesh Draw Call Count", "Particle Draw Call Count",
        "Shadow Draw Call Count", "Triangle Count", "3D Mesh Triangle Count",
        "Particle Triangle Count", "Shadow Triangle Count", "Vertex Count",
        "3D Mesh Vertex Count", "Particle Vertex Count", "Shadow Vertex Count",
        "Mesh Memory", "Texture2D Memory", "Skeletal Animation Count",
    ]
    diff = {}
    for name in metric_names:
        before = number(baseline["runtime_metrics"].get(name, {}).get("avg_value"))
        after = number(launched["runtime_metrics"].get(name, {}).get("avg_value"))
        diff[name] = {
            "baseline_avg": before,
            "launched_avg": after,
            "delta": after - before if before is not None and after is not None else None,
            "status": "available" if before is not None and after is not None else "missing",
        }

    result = {
        "schema_version": 2,
        "mode": "spatial_power_attribution_two_phase",
        "measurement": {
            "type": "trace_proxy",
            "direct_watts_available": False,
            "purpose": "Find client/runtime optimization directions, not calibrated power.",
        },
        "target": {"package": args.package, "runtime_process": args.runtime_process},
        "phases": {
            "baseline": {
                "label": "application_not_running",
                "session": args.baseline_session,
                "fastperf": str(args.baseline_fastperf) if args.baseline_fastperf else None,
                "metrics": baseline,
            },
            "launched": {
                "label": "application_running",
                "session": args.launched_session,
                "fastperf": str(args.launched_fastperf) if args.launched_fastperf else None,
                "metrics": launched,
            },
        },
        "runtime_metric_delta": diff,
        "interpretation": {
            "runtime_increment_candidate": "Runtime process scheduling and render metrics increased/changed after launch; this is shared-service attribution evidence, not exclusive app power.",
            "draw_call_caveat": "DrawCall and geometry metrics are trace counters. They indicate workload direction but do not alone prove GPU power or a geometry bottleneck.",
            "comparison_caveat": "The two captures are separate windows. Differences include device thermal/state and startup effects; repeat steady-state A/B captures before release decisions.",
        },
        "limitations": [
            "No voltage/current calibration is present; no Watt or mWh is reported.",
            f"SpatialRuntime is a shared service; its total CPU/render cost cannot be assigned entirely to {args.package}.",
            "The baseline window is pre-launch and the launched window includes startup plus runtime activity, so startup and steady-state are not separated.",
            "No RenderDoc data is used; this report is based on Perfetto Trace and FastPerf only.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
