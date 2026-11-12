# Collection Preflight

This checklist is mandatory before collecting evidence for `power_pressure`.

## Entry rule

Use the base Spatial performance skill bundle's local script:

```text
C:\Users\Admin\.trae\plugins\cache\local\pico-spatial-agentic-tools\1.0.0\skills\spatial-app-performance-analysis\scripts\capture_perf_data.py
```

This is not a `pico-cli` subcommand. Invoke it with Python using the resolved absolute path. Do not assume that `pico-cli --help` exposes it.

Do not start with direct `pico-cli perf live run`, `perf live start`, or standalone `perf trace record`. Those commands are lower-level smoke-test or recovery tools, not the default power-analysis collector.

## What the one-click collector guarantees

For each invocation, `capture_perf_data.py` starts and stops the live and Trace collectors together and writes a `perf-data-*` directory containing, when collection succeeds:

```text
fast-perf.json
trace-perf.perfetto-trace
collector-summary.json
```

The FastPerf and Trace artifacts are bound to the same invocation and capture window. The script does not currently guarantee `report-data.json` or the extension's `provenance.json`; the extension must collect or write those separately and must not invent them.

## Quick power workflow

The currently supported safe workflow is two explicit collector invocations:

```text
1. Stop target app.
2. capture_perf_data.py --duration 10
3. Launch target app.
4. capture_perf_data.py --duration 20
5. Keep both perf-data-* directories and mark separate_capture_windows.
```

This is a baseline-versus-launched comparison across separate windows. It is not a single continuous Trace and must carry a lower comparison confidence.

## Continuous workflow

A single Trace with an in-trace launch marker is preferred for release-quality analysis, but the current one-click script only supports one fixed-duration collector window. Do not pretend that two independent Trace files are one continuous Trace. Until the collector supports phase callbacks, use separate-window labeling or add a dedicated phase-aware collector before making strict same-run claims.

## Required preflight output

Before collection, state:

- selected mode;
- collector path and exact command;
- target package and Runtime process;
- phase durations;
- output root;
- expected artifacts;
- whether the run is same-window or `separate_capture_windows`;
- known limitations, including absent `report-data.json` or electrical calibration.

## Power evidence limitation

If the device is USB-powered or charging, permit CPU/GPU/frame/Runtime pressure analysis, but prohibit battery-drain, battery-life, or energy-per-session conclusions. Record readable battery voltage, temperature, charge state, and the USB/charging state as provenance; these values are contextual telemetry, not a calibrated power measurement.

## Artifact acceptance

Reject the collection for final power analysis if:

- the target package or device serial is not recorded;
- `fast-perf.json` is missing or invalid;
- `trace-perf.perfetto-trace` is missing or too small to load;
- baseline and launched windows cannot be identified;
- the app state at collection start is unknown.

Do not reject solely because `simpleperf` is disabled; record it as a limitation unless the requested analysis requires it.
