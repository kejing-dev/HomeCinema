---
name: spatial-app-performance-analysis-ext
description: 'Extend PICO Spatial app performance analysis with routed RenderDoc/Perfetto joint analysis and power-pressure analysis. Use whenever the request concerns app power, energy, battery drain, current/voltage, heat or thermal pressure, battery life, power optimization, pre/post-launch comparison, Client versus shared SpatialRuntime attribution, or RenderDoc/Vulkan XML analysis. Use Perfetto/FastPerf and, when available, battery and thermal evidence; report proxy pressure rather than calibrated watts without electrical evidence. For .rdc input, explain that it is not directly supported and request a manual XML export from RenderDoc.'
license: 'Apache-2.0'
---

# Spatial Performance Analysis Extension

Use this skill as an extension to, not a replacement for, `spatial-app-performance-analysis`.

## When to Use

- Extended performance analysis with internal tooling

## When NOT to Use

- Public performance analysis — use `spatial-app-performance-analysis`

## Analysis Modes and Routing

This extension supports two independent evidence modes and one explicit combined mode. Do not mix their scopes or upgrade a mechanism signal into a causal conclusion without aligned evidence.

### Routing priority

Route by the user's objective before routing by the available artifact:

1. A power, energy, battery, thermal, heat, current, voltage, battery-life, or
   power-optimization objective always activates `power_pressure`.
2. A RenderDoc XML or Vulkan-structure objective activates `renderdoc_joint`.
3. If both objectives are present, activate `combined` and run the two pipelines
   independently before joining them.
4. If a power objective has no trace or FastPerf yet, use the base
   `spatial-app-performance-analysis` skill only for context confirmation and
   Perfetto/FastPerf capture, then return here for `power_pressure`.
5. If the request is only about jank, Binder, memory, scheduling, or frame
   correctness and contains no power/thermal objective, use the base skill.

Power intent includes direct and indirect wording such as power consumption,
current draw, voltage, battery drop, heat, temperature, thermal, power, energy,
battery drain, battery life, "lower power consumption", "save battery", and
"FPS is fine but power draw is high". Equivalent Chinese phrasings map to the
same route; see the internal `AGENTS.md` routing examples.

### `renderdoc_joint`

Route here when the request includes a RenderDoc XML export, Vulkan `draw`/`dispatch`/pipeline/descriptor/barrier/resource analysis, or a request to cross-check a single-frame capture against Perfetto/FastPerf.

- Primary evidence: RenderDoc XML plus optional Perfetto/FastPerf.
- Scope: one captured frame or RenderDoc capture history versus a live time series.
- Entry script: `scripts/analyze_renderdoc_xml.py`.
- Report: `spatial-performance-x-renderdoc-report.html`.

Direct `.rdc` analysis is not supported. Ask for a manual XML export from RenderDoc and do not infer metrics from the binary.

### `power_pressure`

Route here for any explicit power, energy, battery, or thermal objective,
including requests to lower power despite meeting an FPS target, explain
battery drain or heat, compare pre-launch/post-launch or steady-state behavior,
or attribute pressure between a target Client and shared `SpatialRuntime`.
Mentions of GPU/CPU frequency, DrawCall, Triangle, Vertex, Mesh/Texture memory,
CPU/GPU time, or frame timing strengthen this route but are not required when
power intent is explicit.

- Primary evidence: Perfetto Trace and FastPerf; RenderDoc is optional and not required.
- Scope: baseline, launch, and optional steady-state windows.
- Entry scripts: `scripts/analyze_power_phases.py` and `scripts/generate_phase_power_report_v2.py`.
- Measurement mode: `trace_proxy`; never report calibrated Watt/mWh without current/voltage evidence.
- If electrical evidence is absent, label results as proxy pressure and list battery current/voltage or charge-counter sampling as the next validation.
- If the device is charging, allow performance-pressure analysis but prohibit battery-drain or battery-life conclusions; request an unplugged rerun.
- Use generic conclusions such as "target Client" and "shared Runtime"; package names belong in provenance and case-specific data.
- Report output is mandatory after analysis and must be rendered from `assets/power-report-template.html`. The generator must fail if the template or its `{{REPORT_TITLE}}` / `{{REPORT_CONTENT}}` tokens are missing.

The quick default is 10 seconds with the target application stopped, followed by 20 seconds after launch. For release comparison, use a 30-second baseline and at least 30-60 seconds of steady state, repeated across runs.

### `combined`

Route here only when both RenderDoc structure analysis and power-pressure analysis are requested or supplied. Run the two evidence pipelines independently, then join them with an evidence matrix. A RenderDoc single frame and a Perfetto time series are `not_comparable` unless a shared frame or timestamp key is verified.

## Mode Selection Rules

1. First detect the objective: power/energy/battery/thermal -> `power_pressure`;
   RenderDoc/Vulkan structure -> `renderdoc_joint`; both -> `combined`;
   neither -> base `spatial-app-performance-analysis`.
2. `.rdc` input: stop the RenderDoc path and request a manual XML export, but
   preserve a separately activated `power_pressure` path when power is requested.
3. A power objective does not require Client/Runtime comparison, FPS failure, or
   an existing trace; those are evidence and attribution options.
4. A DrawCall-only, triangle-only, or Vulkan-structure-only request without a
   power objective stays on `renderdoc_joint` or the base skill; do not infer
   power from geometry counters.
5. Ordinary jank, Binder, memory, or scheduling symptoms without an extension
   objective stay in the base skill. If analysis discovers a distinct power
   objective, return through this table and activate `power_pressure`.

### Routing examples

| User request                                                     | Route                                                                   |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------- |
| "Analyze this app's power consumption / battery drain / heat"    | `power_pressure`; base skill captures evidence if absent                |
| "FPS is 90 but battery life is poor, how do I optimize?"         | `power_pressure`                                                        |
| "Compare pre-launch vs post-launch CPU/GPU and battery pressure" | `power_pressure`                                                        |
| "Show me DrawCall, Triangle, Pipeline"                           | `renderdoc_joint` if XML/Vulkan evidence exists; otherwise base capture |
| "RenderDoc XML + Perfetto, decide whether resources drive power" | `combined`                                                              |
| "Analyze frame drops and Binder blocking"                        | base skill                                                              |
| "Analyze power from a `.rdc` file"                               | preserve `power_pressure`; request XML for the RenderDoc branch         |

## Collection Method Preflight

Before device collection or analysis, confirm the collection method and evidence scope. Record the decisions in `provenance.json` or an equivalent provenance section:

| Decision          | Required value                                                                  |
| ----------------- | ------------------------------------------------------------------------------- |
| Mode              | `renderdoc_joint`, `power_pressure`, or `combined`                              |
| Collection source | Existing artifacts, base `capture_perf_data.py`, or manual RenderDoc XML export |
| Artifact binding  | Same device, build, run, phase, and collection window where applicable          |
| Power phases      | `baseline`, `launch`, and optional `steady_state` with durations                |
| Process scope     | Target Client package and shared Runtime process                                |
| Report            | Canonical output name and template path                                         |

For `power_pressure`, prefer the local `capture_perf_data.py` script from the base Skill bundle because it collects FastPerf and Perfetto Trace together for one window. This is a Python script, not a `pico-cli` subcommand; resolve and invoke its absolute path explicitly. Do not silently combine `perf live run` and an unrelated `trace record` into a complete report; if they are different windows, label them separately.

### Mandatory power collection entry

When collection is required for `power_pressure`, invoke the base Skill bundle's local `capture_perf_data.py` first. Do not use direct `pico-cli perf live run`, `perf live start`, or standalone `perf trace record` as the default collection path or as a preliminary substitute.

The expected local script path is:

```text
<plugin-cache>/pico-spatial-agentic-tools/<version>/skills/spatial-app-performance-analysis/scripts/capture_perf_data.py
```

If that path is unavailable, report the collector as unavailable and do not pretend that a manually assembled live/Trace pair is equivalent. A direct CLI smoke test may be collected separately, but it must not be used as the canonical power capture without an explicit limitation.

The one-click collector currently binds these artifacts for one capture window:

```text
fast-perf.json
trace-perf.perfetto-trace
collector-summary.json
```

`report-data.json` and the extension-level `provenance.json` are not guaranteed outputs of the current collector. The extension must create provenance and must mark `report-data.json` as missing unless it is actually supplied. Do not claim that an artifact is bound to the session merely because a similarly named file exists elsewhere.

For the quick two-window workflow, run the same collector once with the target stopped and once after launching the target. Preserve each collector output directory and label the result `separate_capture_windows`; do not call it a continuous Trace. A continuous baseline-to-launch-to-steady-state Trace requires a collector that supports an explicit launch callback or time anchor and must not be simulated by concatenating two files.

Before executing collection, print a collection plan containing:

```text
mode=power_pressure
collector=capture_perf_data.py
baseline_duration=10s
launch_duration=20s
target_package=<package>
runtime_process=com.pico.spatial.runtime
output_root=<session-output>
expected_artifacts=fast-perf.json, trace-perf.perfetto-trace, collector-summary.json
```

If the user explicitly requests a direct CLI smoke test, keep it outside the power-analysis session and do not use its results for the final power HTML report.

The quick default is:

```text
baseline: target stopped, 10 s
launch: target launched, 20 s
```

This is a startup-inclusive quick comparison. For release-quality comparison, use a 30-second baseline, a separate launch window, and 30-60 seconds of steady state, repeated across runs.

Prefer one continuous Perfetto Trace with explicit time anchors:

```text
0-10 s target stopped -> launch marker -> 20 s launch -> 30-60 s steady state
```

If the collector cannot launch the target mid-trace, separate baseline and launched Traces are allowed, but the report must mark `separate_capture_windows` and lower the comparison confidence.

## Trace Field Discovery and Completeness

After loading each Trace, discover fields before running metric queries. Check standard, counter, process, thread, and PICO custom sources, including:

```text
gpu_track
counter_track
counter
process_counter_track
thread_counter_track
TargetAppMetricCounterStates
SpatialRuntimeMetricCounterStates
```

Search all discovered track and metric names for:

```text
Draw, Mesh, Triangle, Vertex, Texture, Memory, Particle, Shadow, Animation
```

For every discovered metric, record its source table, track ID, `upid`, PID, process name, phase, and sample count. Resolve ownership through `process_counter_track.upid`; do not infer that a metric belongs to the Client or Runtime from its table name alone. An empty standard GPU table does not prove that 3D metrics are absent.

The analysis output must distinguish:

- `available`: collected, queried, and comparable.
- `not_recorded`: the Trace contains no such metric.
- `not_queried`: the field was discovered but the analyzer has not queried it.
- `not_reported`: analysis has the value but the HTML does not render it; this is a report-generation error.
- `not_comparable`: both phases have data but scope, alignment, or units differ.
- `not_running`: the target process was absent in that phase.
- `new_value_from_zero`: baseline is zero; show the absolute new value and do not calculate infinity.

Before publishing HTML, assert that every discovered and queried power/render metric is rendered with its value or explicit status, source, process ownership, and phase window. If a field exists but is not rendered, fail report generation instead of displaying a generic `n/a`.

## Power-Pressure Command Examples

Analyze separate baseline and launched Trace sessions:

```powershell
# First load each file and retain the returned UUID:
pico-cli perf trace load <baseline>\trace-perf.perfetto-trace
pico-cli perf trace load <launched>\trace-perf.perfetto-trace

# Pass the loaded session UUIDs below, not the .perfetto-trace paths:
python scripts/analyze_power_phases.py `
  --baseline-session <baseline-trace-session> `
  --launched-session <launched-trace-session> `
  --package <target-client-package> `
  --runtime-process com.pico.spatial.runtime `
  --baseline-fastperf <baseline>\fast-perf.json `
  --launched-fastperf <launched>\fast-perf.json `
  --out <session-output>\power\two-phase-analysis.json
```

The analyzer validates both session IDs with `SELECT 1` before metric extraction. Passing a Trace file path, an unloaded UUID, or a failed query is a hard input error with the CLI diagnostic; it must not be reported as a missing process or missing metric.

Generate the evidence-bounded HTML report:

```powershell
python scripts/generate_phase_power_report_v2.py `
  --analysis <session-output>\power\two-phase-analysis.json `
  --baseline-fastperf <baseline>\fast-perf.json `
  --launched-fastperf <launched>\fast-perf.json `
  --out <session-output>\power\spatial-power-attribution-report.html
```

The canonical power report name is `spatial-power-attribution-report.html`. The report must be rendered from `assets/power-report-template.html`; do not use ad hoc output names for the standard power mode. The scripts require already loaded Perfetto sessions. Use the base Skill bundle local `capture_perf_data.py` script to collect the Trace and FastPerf artifacts; it is not expected to appear as a `pico-cli` command.

## Combined-Mode Evidence Matrix

When both modes are requested, keep these relationships separate:

| Relationship                                                                                            | Classification rule     |
| ------------------------------------------------------------------------------------------------------- | ----------------------- |
| RenderDoc draw structure and same-window Perfetto GPU timing with verified frame key                    | `strong_cross_support`  |
| RenderDoc geometry/resource structure plausibly explains a live pressure signal without frame alignment | `mechanism_support`     |
| Runtime metric or power proxy exists independently of RenderDoc                                         | `independent_candidate` |
| Different capture window, scene, build, or missing provenance                                           | `not_comparable`        |

The combined report must not turn a RenderDoc draw count into a Watt value, or assign all shared Runtime cost to the target Client.

## Workflow

1. Collect one RenderDoc-exported `.xml` file. The filename and basename are not significant; accept any XML filename, including names matching `renderdoc*.xml`. Add `fast-perf.json`, Perfetto trace, `report-data.json`, `final-summary.md` plus `final-summary.meta.json`, or topic output pairs (`output-<topic>.md` plus `output-<topic>.meta.json`) when available.
2. Create a new `session-output-<timestamp>/` directory and record exact input paths, sizes, timestamps, package/build identity, API/driver, and live capture interval.
3. If the input is `.rdc`, stop the RenderDoc analysis path and state: "Direct .rdc analysis is not supported. Open the capture in RenderDoc, manually export XML, and provide the XML file." Do not invoke a converter, parse the binary as XML, or infer metrics from file size/header/embedded sections.
4. Run `scripts/analyze_renderdoc_xml.py --xml <capture.xml> --out <renderdoc-summary.json>`.
5. Extract `vkCmdDrawIndexed`, `vkCmdDispatch`, pipeline, descriptor, buffer, barrier, queue-submit, image, buffer, and shader counts. Compute raw triangles as `sum(indexCount)/3` and instanced triangle upper bound as `sum(indexCount * max(instanceCount,1))/3`.
6. Extract top draws, image dimensions/layers/samples/mips/format/declared size, declared image-size sum, and XR/render-target risks.
7. Read live values only from real Perfetto/FastPerf artifacts or delegate live analysis to the base Spatial skill. Never infer live values from RenderDoc.
8. Classify relationships as `strong_cross_support`, `mechanism_support`, `independent_candidate`, or `not_comparable`. A single RenderDoc frame and a Perfetto time series are not same-time aligned unless a shared frame/timestamp key is verified.
9. Do not call GPU geometry confirmed from draw count, triangle count, GPU usage, or texture memory alone. Require same-window GPU timing or controlled A/B evidence. Do not call GC or Binder causal without ownership and overlap evidence.
10. Generate a UTF-8 HTML report from `assets/joint-report-template.html`, including summary, live metrics, RenderDoc metrics, cross-source matrix, confidence, actions, A/B validation, provenance, limitations, and an incremental asset-attribution section. Use the descriptive output name `spatial-performance-x-renderdoc-report.html`; it makes the RenderDoc + live-performance relationship explicit. For a complete report, use `scripts/generate_asset_report.py --renderdoc <summary.json> --fastperf <fast-perf.json> --report-data <report-data.json> --out <spatial-performance-x-renderdoc-report.html>`. `fast-perf.json` supplies FastPerf samples, while `report-data.json` supplies PICO CLI aggregates such as `spr_frame_types` and `spr_stats`; when `--report-data` is omitted, auto-discover `report-data.json` beside `fast-perf.json`. For an incremental report, use `scripts/generate_asset_report.py --renderdoc <summary.json> --baseline <unfilled-baseline.html> --out <spatial-performance-x-renderdoc-report.html>`; the baseline must still contain `{{ASSET_ATTRIBUTION}}`. Never pre-fill or remove that placeholder. If it is missing, fail and explain instead of guessing an insertion point. Add `--open-browser` when the generated HTML should be opened with the system default browser after successful writing and validation.
11. Validate XML, JSON, and HTML; confirm actual current metrics appear in the report and that no replacement characters or stale reference numbers are used.

The `{{ASSET_ATTRIBUTION}}` token in `assets/joint-report-template.html` is a required insertion point. Keep it intact when creating a baseline. Use `generate_asset_report.py` rather than manually editing or pre-filling the asset section.

For a user-facing walkthrough with command examples, data-flow diagrams, asset mapping, browser opening, and troubleshooting, read `references/usage-guide.md`.

## Command examples

Generate the complete report and open it in the system default browser:

```powershell
python scripts/generate_asset_report.py `
  --renderdoc <session-output>\renderdoc-summary.json `
  --fastperf <session-output>\performance-data\perf-data-<timestamp>\fast-perf.json `
  --report-data <session-output>\performance-data\report-data.json `
  --out <session-output>\spatial-performance-x-renderdoc-report.html `
  --open-browser
```

If `report-data.json` is in the same directory as, or a parent directory of, `fast-perf.json`, it can be auto-discovered:

```powershell
python scripts/generate_asset_report.py `
  --renderdoc <session-output>\renderdoc-summary.json `
  --fastperf <session-output>\performance-data\perf-data-<timestamp>\fast-perf.json `
  --out <session-output>\spatial-performance-x-renderdoc-report.html `
  --open-browser
```

Add asset attribution incrementally to an unfilled baseline:

```powershell
python scripts/generate_asset_report.py `
  --renderdoc <session-output>\renderdoc-summary.json `
  --baseline <unfilled-baseline.html> `
  --out <session-output>\spatial-performance-x-renderdoc-report.html `
  --open-browser
```

The baseline must retain `{{ASSET_ATTRIBUTION}}`. The script fails rather than guessing an insertion point when that placeholder is absent.

## Output contract

Write under one new session directory:

- `renderdoc-summary.json`: machine-readable extraction.
- `spatial-performance-x-renderdoc-report.html`: evidence-bounded human report.
- `spatial-power-attribution-report.html`: canonical `power_pressure` HTML report when that mode is used.
- `provenance.json` or an equivalent provenance section.

Read `references/evidence-contract.md` before root-cause claims and `references/renderdoc-schema.md` when fields or Vulkan command families differ.
