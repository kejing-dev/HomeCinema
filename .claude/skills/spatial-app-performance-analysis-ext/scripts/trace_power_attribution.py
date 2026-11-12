#!/usr/bin/env python3
"""Extract trace-proxy power attribution metrics from a PICO perf session."""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
from typing import Any


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
    if result.returncode != 0:
        return []
    try:
        payload = json.loads(result.stdout)
        return payload.get("data", {}).get("rows", []) or []
    except (json.JSONDecodeError, AttributeError):
        return []


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def phase_sql(start: int, end: int, column: str = "ts") -> str:
    return f"{column} > {start - 1}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--runtime-process", default="com.pico.spatial.runtime")
    parser.add_argument("--pico-cli", default="pico-cli")
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()

    package = sql_string(args.package)
    runtime = sql_string(args.runtime_process)
    bounds = query(
        args.session,
        "SELECT MIN(ts) AS start_ts, MAX(ts) AS last_ts FROM OpenXRClientSpatialFrames",
        args.pico_cli,
    )
    if not bounds or bounds[0].get("start_ts") is None:
        raise SystemExit("Trace does not contain sched_slice bounds")
    trace_start = int(bounds[0]["start_ts"])
    trace_end = int(bounds[0]["last_ts"])
    duration = max(trace_end - trace_start, 1)
    phase_width = duration // 3
    phase_defs = []

    processes = query(
        args.session,
        f"SELECT upid, pid, name FROM process WHERE name IN ({package}, {runtime})",
        args.pico_cli,
    )
    process_map = {row["name"]: row for row in processes if row.get("name")}
    client = process_map.get(args.package)
    server = process_map.get(args.runtime_process)

    cpu_rows = []
    for process_name, upid in ((args.package, client["upid"] if client else -1), (args.runtime_process, server["upid"] if server else -1)):
        rows = query(
            args.session,
            f"""
            SELECT COUNT(*) AS sched_slices, SUM(dur) / 1000000.0 AS running_ms,
                   AVG(dur) / 1000000.0 AS avg_slice_ms,
                   MAX(dur) / 1000000.0 AS max_slice_ms
            FROM sched_slice s
            WHERE utid IN (SELECT utid FROM thread WHERE upid = {upid})
            """,
            args.pico_cli,
        )
        if rows:
            cpu_rows.append({"process_name": process_name, **rows[0]})
    cpu_total = {
        row["process_name"]: {
            "running_ms": float(row.get("running_ms") or 0),
            "sched_slices": int(row.get("sched_slices") or 0),
            "avg_slice_ms": float(row.get("avg_slice_ms") or 0),
            "max_slice_ms": float(row.get("max_slice_ms") or 0),
        }
        for row in cpu_rows
    }

    counter_names = [
        "CPU Utilization",
        "GPU Utilization",
        "GPU Memory",
        "Texture2D Memory",
        "Mesh Memory",
        "Triangle Count",
        "Vertex Count",
        "Draw Call Count",
        "3D Mesh Draw Call Count",
        "frameRate",
        "frameDrop",
    ]
    escaped_names = ", ".join(sql_string(name) for name in counter_names)
    counters_total = []
    for process_name, upid in ((args.package, client["upid"] if client else -1), (args.runtime_process, server["upid"] if server else -1)):
        rows = query(
            args.session,
            f"""
            SELECT pct.name AS counter_name,
                   pct.unit, AVG(c.value) AS avg_value,
                   MIN(c.value) AS min_value, MAX(c.value) AS max_value,
                   COUNT(*) AS samples
            FROM counter c
            JOIN process_counter_track pct ON pct.id = c.track_id
            WHERE pct.upid = {upid}
              AND pct.name IN ({escaped_names})
            GROUP BY pct.name, pct.unit
            ORDER BY pct.name
            """,
            args.pico_cli,
        )
        counters_total.extend({"process_name": process_name, **row} for row in rows)

    frequency_rows = query(
        args.session,
        """
        SELECT AVG(c.value) AS avg_mhz, MIN(c.value) AS min_mhz,
               MAX(c.value) AS max_mhz, COUNT(*) AS samples
        FROM counter c
        JOIN gpu_counter_track gct ON gct.id = c.track_id
        WHERE gct.type = 'gpu_frequency'
        """,
        args.pico_cli,
    )
    spatial = {
        "frame_types": query(
            args.session,
            "SELECT CASE WHEN name GLOB 'Late Frame *' THEN 'Late' WHEN name GLOB 'Miss Frame *' THEN 'Miss' WHEN name GLOB 'Early Frame *' THEN 'Early' ELSE 'Other' END AS frame_type, COUNT(*) AS count, AVG(dur) / 1000000.0 AS avg_ms FROM SpatialRuntimeAbnormalFrames GROUP BY frame_type",
            args.pico_cli,
        ),
        "frame_timing": query(
            args.session,
            "SELECT AVG(dur) / 1000000.0 AS avg_ms, MAX(dur) / 1000000.0 AS max_ms, COUNT(*) AS frames FROM OpenXRClientSpatialFrames",
            args.pico_cli,
        ),
    }

    result = {
        "schema_version": 1,
        "mode": "spatial_power_attribution",
        "measurement": {
            "mode": "trace_proxy",
            "direct_watts_available": False,
            "limitation": "Perfetto trace provides resource-pressure proxies, not calibrated device power.",
        },
        "session": args.session,
        "target": {
            "package": args.package,
            "client_process": client,
            "spatial_runtime_process": server,
            "runtime_process_name": args.runtime_process,
        },
        "trace_bounds": {"start_ts": trace_start, "end_ts": trace_end, "duration_ms": duration / 1_000_000},
        "performance_constraint": {
            "target_fps": 90,
            "source": "fast-perf.json is analyzed separately; SpatialFrames are included per phase",
        },
        "phases": [
            {
                "id": "phase_analysis",
                "id": "phase_analysis",
                "status": "blocked",
                "reason": "The historical trace has incompatible/wrapped timestamp domains; reliable baseline/launch/workload windows cannot be derived.",
                "cpu": {},
                "counters": [],
                "gpu_frequency": {},
                "spatial": {},
            }
        ],
        "trace_level": {
            "cpu": cpu_total,
            "counters": counters_total,
            "gpu_frequency": frequency_rows[0] if frequency_rows else {},
            "spatial": spatial,
        },
        "limitations": [
            "The trace has no application-launch marker or pre-launch baseline; early/middle/late windows are trace-relative proxies.",
            "No calibrated voltage/current/power source is present in this trace.",
            "The trace does not expose sched_waking/cpu_idle tables needed for complete wakeup and idle-residency analysis.",
            "SpatialRuntime is a shared service; process-level increment is an attribution candidate, not exclusive app power.",
            "The profiler query service returns empty results for two-sided nanosecond predicates in this session; phase metrics therefore use a safe lower-bound query and are not treated as exact phase differences.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
