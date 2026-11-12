# Performance Workflow command reference

This reference supplements `SKILL.md`. The internal Craft Catalog is authoritative for the
Host-facing entry; Profiler command help is authoritative only for the explicitly documented
fallback path.

## Manual capture fast path

When the user will operate an already-running app, prefer the direct SpatialPerfTrace lifecycle. It
avoids creating a synthetic App Run solely to keep a Craft capture alive:

```bash
pico-cli perf spatial-trace start \
  --channel perfetto,fast-perf \
  --package <package-name> \
  --device <serial> \
  --output-dir <output-dir>
pico-cli perf spatial-trace status <capture-id>
pico-cli perf spatial-trace stop <capture-id>
```

The Host confirms the capture window before starting, waits for the user-operated interval, and
verifies the final manifest and non-empty artifacts. This path does not install or launch the app.
When the manifest contains a readable `fast-perf` report, the Host should read its summary and
print the available overall metrics (for example FPS, CPU/GPU load, GPU frequency/temperature, and
diagnosis) before handing the artifacts to deeper analysis. Missing or partial summary data must be
reported as a limitation, not filled in by inference.

## Unified Craft entry

The Host-facing Workflow is:

```text
performance-workflow
```

Select the Profiler route through a validated nested input:

```json
{
  "workflow": "analysis | capture | codings | diagnose-e2e",
  "input": {
    "workspace": "<workspace-dir>",
    "package": "<package-name>",
    "agentProvider": "<native-agent-provider>",
    "agentModel": "<native-agent-model>"
  }
}
```

Start and observe it with Craft commands:

```bash
pico-cli workflow start performance-workflow --input <input.json>
pico-cli workflow wait <craft-run-id>
pico-cli workflow result read <craft-run-id>
pico-cli workflow cancel <craft-run-id>
```

`workflow` is an enum, not an arbitrary Profiler Workflow ID. Route-specific fields belong inside
`input`; do not use a flat mixture of capture, analysis, and coding fields.

The four accepted values map internally as follows, but the dotted IDs are not valid Host-facing
selectors:

| Craft input  | Internal Profiler ID                       |
| ------------ | ------------------------------------------ |
| `analysis`   | `performance.workflow.analysis`            |
| `capture`    | `performance.workflow.capture-performance` |
| `codings`    | `performance.workflow.codings`             |
| diagnose-e2e | `performance.workflow.diagnose-e2e`        |

The current adapter accepts a Trace path through `input.trace`. It does not yet accept a loaded
Profiler `trace-session-id`; use the Profiler-native fallback only when that distinction is needed.

For a direct Profiler-native workflow, retain its returned Workflow Session ID. Discover active
sessions within a Workspace, then query or stop a known session ID without repeating Workspace:

```bash
pico-cli perf workflow sessions --workspace <workspace> --status running
pico-cli perf workflow status <profiler-session-id>
pico-cli perf workflow stop <profiler-session-id>
```

## Profiler-native fallback options

The following options apply to `pico-cli perf workflow run` only when the unified Craft adapter does
not expose the required capability (for example, a loaded Trace session ID):

```text
--workspace <dir>                 required project Workflow Workspace
--package <package>               required target application package
--trace <path>                    existing Perfetto Trace path
--trace-session-id <id>           loaded Perfetto query session ID
--source-dir <path>               source project for coding/repair workflows
--device <serial>                 explicit Android device serial
--agent-provider <provider>       ACP provider, for example traex-acp or codex-acp
--agent-model <model>             default Agent model
--goal <text>                     analysis goal
--focus <topics>                  comma-separated topic IDs
--exclude-topics <topics>        comma-separated topic IDs
--target-fps <fps>                performance gate target
--fps-tolerance <fps>             performance gate tolerance
--wait                            wait for terminal state
--wait-timeout-ms <ms>            bounded wait timeout
```

Coding workflows may additionally need `--build-command`, `--test-command`, `--app-run-command`,
and the `--app-run-*` configuration options. SpatialPerfTrace capture can be configured with
`--spatial-perf-trace-config` and channel/capture duration options.

## Identifier rules

| Identifier          | Produced by                       | Used by                               |
| ------------------- | --------------------------------- | ------------------------------------- |
| Device serial       | device inspection                 | `--device`, capture, App Run          |
| Trace path          | `perf trace record` or user input | `--trace`                             |
| Trace session ID    | `perf trace load`                 | `--trace-session-id`, Trace query     |
| Workflow Session ID | `perf workflow run`               | `status`, `watch`, `stop`, `sessions` |

Never pass a Trace path where a Trace session ID is required, or a Trace session ID where a
Workflow Session ID is required.
