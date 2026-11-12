# Power-Pressure Methodology

## Purpose

This mode finds optimization directions for a Spatial application that already meets its frame-rate target but still creates unnecessary Client, shared Runtime, or device resource pressure. It is not a calibrated electrical power meter.

## Standard phases

| Phase | Default | Purpose |
|---|---:|---|
| `baseline` | 10 s | Target application stopped; characterize the shared Runtime/system floor. |
| `launch` | 20 s | Capture process creation, resource loading, and initial Client/Runtime workload. |
| `steady_state` | optional 30–60 s | Separate persistent workload from one-time startup cost. |

The 10-second baseline is suitable for fast diagnosis. Use longer and repeated windows for regression decisions.

## Collection preflight

Default to the base `capture_perf_data.py` one-click collector so FastPerf and Perfetto belong to the same capture window. Do not construct a complete phase report by silently mixing an unrelated live report and Trace recording.

Before collecting, confirm the target package, Runtime process, device/build identity, phase durations, and whether existing artifacts are reusable. Prefer one continuous Trace with explicit launch anchors. If separate Traces are unavoidable, record `separate_capture_windows` and do not present the comparison as strict same-run A/B.

## Evidence model

Collect and compare:

- Client process presence, sched running time, CPUTime, GPUTime, and frame timing.
- `com.pico.spatial.runtime` or the configured shared Runtime process.
- Runtime render metrics: Draw Call, 3D Mesh Draw Call, Particle Draw Call, Shadow Draw Call, Triangle, Vertex, Mesh Memory, Texture2D Memory, and animation counts when available.
- FastPerf App/System FPS, GPU utilization, GPU frequency, temperature, system CPU, and app CPU.
- Late/Miss/Discard frame evidence.

Use `baseline -> launch -> steady_state` labels. Never fabricate early/middle/late phases by repeating a cumulative query result.

After loading a Trace, discover all relevant metric sources before querying. Check `counter_track`, `counter`, `process_counter_track`, `thread_counter_track`, `TargetAppMetricCounterStates`, `SpatialRuntimeMetricCounterStates`, and PICO custom tables. Search track names for Draw, Mesh, Triangle, Vertex, Texture, Memory, Particle, Shadow, and Animation.

Resolve metric ownership through `process_counter_track.upid` and the `process` table. Store source table, track ID, PID/UPID, process name, phase, and sample count for every field. An empty standard GPU table does not establish that 3D metrics are absent.

The phase analyzer accepts loaded `pico-cli perf trace load` session UUIDs, not Trace file paths. It must probe each session with `SELECT 1` before extraction and fail with the CLI error, SQL context, and input hint if a query fails. A query failure must never be converted into `not_running` or an empty process map.

## Attribution rules

- Runtime process totals are shared-service pressure, not target-application-exclusive power.
- A target Client increment is a candidate attribution only when the process and workload are present in the target window and absent or materially lower in the baseline.
- DrawCall, Triangle, Vertex, memory, GPU utilization, or GPU frequency alone cannot prove GPU power or a geometry bottleneck.
- A stronger claim requires same-window GPU timing, controlled A/B, or calibrated current/voltage data.
- Startup windows include one-time loading and should not be presented as steady-state power.

## Controlled comparison

For shared Runtime attribution, prefer:

```text
empty scene -> static scene -> target scene
```

The comparison estimates:

```text
Runtime baseline ~= static scene - empty scene
target-induced candidate ~= target scene - static scene
```

This is an experimental attribution model, not an electrical decomposition.

## Required report language

Reports must state:

- `trace_proxy` measurement mode.
- No Watt/mWh output without electrical calibration.
- Shared Runtime attribution limitation.
- Separate capture-window limitation.
- Missing metrics as `not_recorded`, `not_queried`, `not_reported`, `not_running`, or `not_comparable`, not as invented zeroes.
- A baseline-zero metric as `new_value_from_zero` with an absolute delta, never infinity.
- The canonical output name `spatial-power-attribution-report.html` and template `assets/power-report-template.html`.

Before publishing, assert that every discovered and queried metric is present in the report with a value or explicit status. A discovered metric omitted from HTML is a report-generation error.

