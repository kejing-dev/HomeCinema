---
name: spatial-app-performance-workflow
description: 'Orchestrate PICO performance work through the fastest supported path: use direct SpatialPerfTrace capture for manual operation, and the unified Craft entry `pico-cli workflow start performance-workflow` for automatic capture, Trace analysis, coding repair, end-to-end diagnosis, and Workflow Run observation. Use `spatial-app-performance-analysis` for manual Trace SQL or evidence interpretation without orchestration.'
license: 'Apache-2.0'
---

# Spatial App Performance Workflow

This Skill owns the Host-side performance loop: choose the least costly supported path, collect
decisions, perform bounded checks, start the operation, observe it, and verify the handoff. Direct
SpatialPerfTrace capture is the fast path when the user will operate an already-running app. The
installed Workflow descriptor and schemas remain authoritative for the Craft path; this Skill must
not duplicate that contract.

## When to Use

- Managed performance analysis workflow with Craft JSON output

## When NOT to Use

- Ad-hoc performance diagnosis — use `spatial-app-performance-analysis`

## Route

Use the direct capture path or the single Craft Workflow `performance-workflow`:

| User goal                                   | Route          |
| ------------------------------------------- | -------------- |
| Capture while the user operates an app      | direct capture |
| Capture with Workflow-controlled app run    | `capture`      |
| Analyze an existing Trace                   | `analysis`     |
| Modify code and revalidate performance      | `codings`      |
| Diagnose, repair, and revalidate end to end | `diagnose-e2e` |

For manual Trace SQL, built-in queries, or evidence interpretation without orchestration, use
`spatial-app-performance-analysis` and do not start a Workflow.

## Talk to the user first

Use natural language, not schema names or internal Profiler IDs. Ask for the decisions that affect
the run, then translate the answers into the current descriptor/schema. Do not call a missing
property by its implementation name; ask for the project directory, capture configuration, script,
command, device, scenario, or duration that it represents.

For capture, present one coherent choice:

- manual operation: use direct capture; the user confirms a bounded sampling window;
- automatic app run: use the Craft `capture` route; the user provides how the app should be
  started/run and for how long.

When both modes are available, show both and let the user choose. Do not choose a mode or invent a
default on the user's behalf. If only one mode is supported, say so before collecting the remaining
inputs. Do not route manual operation through a no-op App Run just to satisfy the Craft contract when
direct capture is available.

Before starting, show the selected route, device, app, operation mode, duration/timeout, and any
source or device mutation. Resolve project/workspace and configuration locations silently when the
environment makes them unambiguous. Separate user decisions from detected values and defaults. A
detected/default value is not approved until the user confirms it.

### How to check

Use this order and stop as soon as the answer is determined:

1. Discover the installed Workflow only when the selected path uses Craft, and read its descriptor,
   input schema, and supported capabilities.
2. Run the environment/daemon checks needed for the selected path.
3. Validate only user-provided or path-resolved locations, devices, and configuration files.
4. For the Craft path, compare the resolved inputs with the schema and identify missing, ambiguous,
   or side-effecting decisions. For direct capture, perform the equivalent option and capability
   check from the installed command help.
5. Ask the user only for those unresolved decisions; do not search the project for substitutes.
6. After confirmation, construct the schema-valid input and start the Run.

Use read-only checks where possible. Treat command output, installed help, and the current
descriptor/schema as evidence; do not infer support from filenames, old examples, or a previous
Workflow version.

## Do not

Avoid these general failure modes:

- Do not use broad, unbounded exploration to compensate for missing input. Inspect only the
  declared sources and ask for the smallest missing decision or value.
- Do not spend time inspecting unrelated project material before a time-sensitive operation. Keep
  checks proportional to the selected route and stop once its prerequisites are known.
- Do not repeat a check whose evidence is still valid. Re-run it only after an environment change,
  a new failure signal, or an explicit request to refresh the result.
- Do not make users choose implementation details. Translate internal contracts into plain-language
  decisions and keep implementation identifiers inside the adapter or Workflow boundary.
- Do not turn an observed value into permission. Separate detected state, an explicit default, and
  a user-approved choice; never silently resolve an ambiguous target, duration, mode, or side effect.
- Do not widen the operation's scope to recover from an observation problem. Preserve existing
  sessions, selected resources, and user constraints unless a change is confirmed.
- Do not bypass the selected workflow because another path looks convenient. Explain a capability
  gap and obtain consent before changing the execution path.
- Do not infer success from process completion alone. Verify the expected terminal state, output
  presence and validity, and its association with the requested operation before handing it off.

### How to ask

Ask in decision order, not implementation order:

1. What result is wanted: capture, analysis, repair/revalidation, or coding?
2. For capture, should the app be started automatically, or will the user operate an already
   running app? If automatic, use the Craft capture route and ask for the start/run command or
   script and its expected duration. If manual, use direct capture and ask only for the bounded
   sampling window; invite an optional operation description.
3. Which app and device should be used?
4. Are there any project, output, permission, or mutation constraints the user wants to control?

Ask one compact question when several answers are independent, and summarize the choices in plain
language before requesting final confirmation. Never ask the user to choose between internal route
IDs or schema property names.

A capture clarification should sound like: “Should I start the app for you, or will you operate the
already-running app? How long should the sampling window be? If I start it, please provide the
command or script. The current device and app are …; confirm or change them.”

## Bounded preflight

Run the environment gate before an environment-dependent `pico-cli` command. Reuse a successful
`pico-env-doctor` result within the same unchanged Host session; rerun it after setup changes or a
new failure signal. Do not repair or install without authorization.

For a time-sensitive capture, validate only the exact paths and devices already selected. Do not
recursively search the project for possible configs, scripts, or context files. If a required input
is missing or ambiguous, ask the user; do not guess a nearby file. Start promptly after confirmation.

The minimum read-only performance checks are:

```bash
pico-cli perf doctor check
pico-cli perf daemon status --envelope
```

Verify the internal Craft entry once per Host session or after an install/build change when the Craft
path is selected:

```bash
pico-cli workflow list --format json
pico-cli workflow describe performance-workflow --format json
```

When more than one device is available, require an explicit serial. Treat emulator evidence as
emulator evidence, not proof of real-device frame-rate quality.

## Start

### Manual operation fast path

When the user will operate an already-running app, use the direct capture lifecycle after confirming
the app, device, channels, output location, and duration. Start the capture, keep it active for the
confirmed window, then stop that exact capture and retain its returned capture identity:

```bash
pico-cli perf spatial-trace start \
  --channel perfetto,fast-perf \
  --package <package-name> \
  --device <serial> \
  --output-dir <output-dir>
pico-cli perf spatial-trace status <capture-id>
pico-cli perf spatial-trace stop <capture-id>
```

The direct path does not install or launch the app. Do not start the sampling window until the user
has confirmed they are ready to operate the app. Validate the final manifest and non-empty channel
artifacts before handing them to `spatial-app-performance-analysis`.

If the completed manifest contains a readable `fast-perf` report, read its summary and include a
short overall result immediately. Report only metrics that are present, such as app/system FPS,
CPU load, GPU load/frequency/temperature, sample coverage, and any diagnosis or status supplied by
the report. Present this as a capture summary, not as a root-cause analysis or a device-quality
verdict. If the report is missing, incomplete, or contains no summary, say so and provide the report
path; do not synthesize metrics from zero values or from the process exit code.

### Craft Workflow path

Build a nested input object from the current Workflow schema and start only after user confirmation:

```bash
pico-cli workflow start performance-workflow --input <input.json>
```

Do not expose `performance.workflow.*` IDs as Host-facing route choices. Do not mix fields from
different routes or infer build, test, app-run, or capture commands from a guessed project layout.

For a Craft capture, the user-facing input must already resolve:

- how the app is driven (automatic command/script or manual mode if supported);
- a bounded duration (an operation description is optional);
- the selected device and app;
- any project/configuration details that could not be resolved from the current environment.

## Observe

The Craft Run ID and Profiler Workflow Session ID are different identifiers. For the unified Craft
entry, observe the Craft Run:

```bash
pico-cli workflow wait <craft-run-id>
pico-cli workflow run read <craft-run-id>
pico-cli workflow result read <craft-run-id>
pico-cli workflow events read <craft-run-id>
pico-cli workflow snapshot read <craft-run-id>
pico-cli workflow cancel <craft-run-id>
```

Do not pass a Craft Run ID to Profiler-native status/stop commands. The current compatibility
adapter starts and observes the Profiler-native session on Craft's behalf. Craft cancellation
requests native workflow stop and waits for native `cancelled` before completing the Craft Run.

Use the Profiler-native path only when the Craft adapter lacks a required capability and the user
explicitly accepts that fallback. Keep its Workspace, Workflow Session ID, and Trace Session ID
separate:

```bash
# Discover active native Workflow Sessions in one Workspace.
pico-cli perf workflow sessions --workspace <workspace> --status running

# A known native Workflow Session ID is sufficient for status and stop.
pico-cli perf workflow status <profiler-session-id>
pico-cli perf workflow stop <profiler-session-id>
```

## Verify and hand off

Do not report success from exit code alone. Confirm that the Run reached the expected terminal state,
the result is not an unreported partial/inconclusive state, and declared artifacts exist and are
non-empty. For capture or analysis, verify that the artifact belongs to the selected app, device,
Trace/build identity, and requested window. Preserve evidence gaps.

Hand a produced Trace or analysis artifact to `spatial-app-performance-analysis` for interpretation.
That Skill owns evidence reasoning; this Skill owns orchestration and handoff.

If the Workflow fails before producing a valid artifact, report the orchestration/environment error
and the smallest recovery action. Do not infer a performance conclusion from a failed or empty run.

Do not assume an option, field, route, or capability that is absent from the installed descriptor,
schema, help, or result. Record the observed compatibility limitation and stop at that boundary.
