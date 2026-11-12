---
name: pico-workflow-integrator
description: 'Integrates an existing workflow into pico-cli Domain or LangGraph Runtime. Use when onboarding, migrating, registering, or validating workflow code that already exists.'
license: 'Apache-2.0'
allowed-tools: 'Bash(git *) Bash(rg *) Bash(find *) Bash(npm *) Bash(node *) Read Edit Write'
---

# Integrate an existing pico-cli Workflow

Use this skill when the developer already has workflow code, a CLI-driven process, an Agent loop, a
LangGraph graph, or a legacy pico-cli Workflow and wants it integrated into the maintained Workflow
Foundation.

This is not the greenfield scaffolding path. In a SpatialCraft source checkout, route requests that
only describe a new process and have no existing implementation to the repository-local
`workflow/skills/pico-workflow-creator` guidance.

## When to Use

- Integrating an existing implementation into a maintained Workflow package
- Mapping existing source code to Workflow steps and handoffs

## When NOT to Use

- Creating a complete app — use `spatial-app-dev-workflow` for overall development and delivery; use `spatial-app-onboarding` for scaffold-only requests and `spatial-design-to-app` for scoped UI work
- Authoring a new Workflow package — use the workflow authoring guide

## Supported outcomes

The skill may produce one of four honest outcomes:

1. migrate the implementation to Domain `static-dag`;
2. migrate the implementation to Domain `module-kernel`;
3. adapt a reviewable graph to LangGraph codegen;
4. report a blocked or compatibility-only boundary without generating unsupported integration code.

Never create a new `node-module`, `agent-guided`, or `pico-managed` Workflow. Do not rewrite an
existing engine merely to force it into Domain. An independently executable process is not a
supported Workflow Runtime until the repository provides a maintained process adapter and protocol.

### Unsupported is a terminal result for the current request

Classify the requested execution model before making any repository change. If the request requires
an unsupported Runtime, return the fourth outcome above and stop the current implementation pass:

- do not continue to the integration map, package implementation, registration, build, or test steps;
- do not run implementation, build, test, formatting, scaffolding, or speculative compatibility
  probes after the unsupported classification; the classification is terminal for this pass;
- do not create, edit, delete, format, or stage repository files, including a proposed adapter;
- report the requested execution contract, the missing Runtime or adapter, and the evidence used;
- offer bounded choices such as keeping the process external, separately designing a maintained
  process adapter, or migrating to a supported Runtime; then wait for the user to choose.

Words such as “integrate”, “register”, or “make pico-cli start this existing process” authorize an
integration attempt, not a rewrite. Migrating or reimplementing the existing engine in Domain,
TypeScript LangGraph, or a Node wrapper changes the requested execution model and requires explicit
user approval. After that approval, begin a new implementation pass from the selected route and
preserve the original behavior through focused tests.

## 1. Establish the source and target

Before editing:

1. Read the current repository `AGENTS.md` files and inspect `git status --short`.
2. Identify the existing implementation root, its owner, build system, entry point, and tests.
3. Identify the SpatialCraft source checkout that will own the integration package and verify its
   current Workflow contracts exist.
4. Determine whether the requested result is:
   - an internal maintained package under `workflow/internal/<name>`;
   - an unregistered candidate under `workflow/candidates/<name>`;
   - an external installable package.
5. Treat external v1 package installation and arbitrary process execution as unsupported unless
   current source and tests prove those paths have landed.

Do not guess a repository path from examples or old plans. Do not move source ownership across
repositories unless the user explicitly requests it.

## 2. Inspect before choosing a Runtime

Read [the integration decision tree](references/integration-decision-tree.md), then inspect:

- public input, output, error, event, artifact, and snapshot behavior;
- ordering, fan-out, joins, branches, loops, retries, and terminal conditions;
- checkpoints, suspension, resume input, cancellation, and timeout behavior;
- deterministic code, model calls, caller handoffs, and external process calls;
- filesystem, network, device, credential, and other side effects;
- idempotency keys, durable receipts, and recovery assumptions;
- existing tests and externally observable behavior that must remain stable.

Record evidence from code and tests. Do not infer a graph only from filenames or README prose.

If the user asks only for assessment, stop after producing the routing decision, mapping table,
unsupported capabilities, and verification plan. Do not edit files.

## 3. Select the smallest truthful route

- Choose Domain `static-dag` for a fixed acyclic flow composed of deterministic Script Steps, fixed
  Agent Tasks, caller handoffs, and bounded local Gates.
- Choose Domain `module-kernel` for a fixed Module Manifest with Driver operations, Gate decisions,
  retry, revise, strategy reset, invalidation, or partial completion.
- Choose LangGraph codegen for a reviewable topology that requires real back-edges, conditional
  routing, or graph checkpoints.
- Keep an existing custom engine outside the maintained author paths when its semantics cannot be
  represented without a rewrite. Report the missing adapter or protocol instead.

Use [the Domain migration guide](references/domain-migration-guide.md) when either Domain route is
selected. For LangGraph, read the repository's current
`docs/development/workflow/langgraph-codegen-authoring.md` completely.

## 4. Produce an integration map

Before implementation, map each existing concept to its target:

| Existing concept                             | Target contract                 |
| -------------------------------------------- | ------------------------------- |
| public arguments or request object           | Workflow Input Schema           |
| successful externally consumed value         | Workflow Output Schema          |
| stable progress view                         | optional public Snapshot Schema |
| deterministic operation                      | Script Step                     |
| model-owned bounded task                     | Agent Task                      |
| caller-provided decision or work             | `caller-agent` node             |
| side-effecting operation with reconciliation | Module Kernel Driver            |
| deterministic acceptance or routing check    | Gate                            |
| private checkpoint or engine state           | Runtime-private state           |
| produced file or report                      | Artifact/Evidence               |

For every row, name the original source file and the target package file. Mark behavior that is
intentionally not migrated. Do not silently drop retries, cancellation, partial outcomes, or
idempotency behavior.

## 5. Implement a thin integration

Read the current repository contracts before writing:

1. `docs/development/workflow/domain-quickstart.md` when considering Domain
2. `docs/development/workflow/README.md`
3. `docs/development/workflow/current-author-runtime-chains.md`
4. `docs/development/workflow/domain-authoring.md` for Domain
5. `docs/development/workflow/langgraph-codegen-authoring.md` for LangGraph
6. `workflow/protocol/schemas/authoring/workflow-descriptor.v1.schema.json`
7. the closest maintained Workflow package

Implementation rules:

- Preserve domain logic in its existing owning module when a thin adapter can call it.
- Create package-owned adapters only for input projection, context injection, outcome mapping, and
  Artifact/Event publication.
- Never duplicate public Run, Result, Event, Snapshot, Catalog, Agent Host, or Artifact storage.
- Never import from `src/foundation/workflow/native/`.
- Keep executable paths, models, credentials, Hosts, sandbox settings, and Session IDs out of
  Workflow Input.
- Treat externally returned paths as untrusted and validate them against the workspace or injected
  Run Artifact root.
- Keep Runtime state private. Publish only a bounded author-declared Snapshot.
- Preserve idempotency and reconciliation for side effects. Use a Driver when an operation may have
  completed before a crash.
- For Manifest v3, map every Module to unique `owns` scopes, supported `acceptsCorrections`, and one
  `consumes` declaration per direct dependency. Use `digestStepId` when precise invalidation requires stable
  content/interface projections.
- A Domain Module may use an attached `child-workflow` binding with a build-time-fixed target allowlist. Keep `maxChildRuns = 0`
  without Child Modules; otherwise make it cover every declared Child Module.
- When `completion.assemblyVerdict` is present, map the selected Module output to a structured pass or findings
  verdict and preserve current Evidence identity.
- Do not start real Agents, devices, profilers, or network jobs while creating the integration
  package.

When a new package must be scaffolded, use the current templates owned by
`workflow/skills/pico-workflow-creator/references/` rather than copying their full contents into this
skill.

## 6. Register and verify

For an internal maintained package:

1. Add its build entries to `scripts/build-internal-workflows.ts`.
2. Add the package to `workflow/README.md` and `workflow/internal/README.md`.
3. Add focused tests under `tests/`.
4. Run the narrowest relevant tests first.
5. Run:

```bash
npm run workflow:packages:typecheck
npm run workflow:packages:build
npm run build:internal
node dist/index.js workflow describe <workflow-name> --format json
```

The verification must prove:

- the Descriptor and Definition use a maintained v1 route;
- the example satisfies the Input Schema;
- every Step, Agent Task, Gate, Driver, and asset resolves before start;
- the registered Contract and Runtime version are fixed;
- no real Workflow was started unless explicitly authorized.

Run broader repository gates when the change modifies shared Foundation behavior rather than only
one package.

## 7. Report the handoff

Report:

1. source implementation and selected target route;
2. preserved behavior and deliberate omissions;
3. created or changed files;
4. registration and verification evidence;
5. unsupported capabilities or runtime prerequisites;
6. whether any real Workflow, Agent, process, device, or network action was started.

Never claim that an external process, dynamic child Workflow, cancellation path, or cross-process
Agent Session is supported unless current production code and focused tests demonstrate it.

## Agent execution and observation

Declare Agent Tasks using role instructions, input/output schemas, sandbox requirements and
fresh/retained sessions. Do not select an executable, Host, model, or transport in the task
manifest or business Input. The shared Executor inherits the calling agent's execution selection
from the Run; the workflow maker chooses a development environment by starting their own main
agent session. Do not implement another model-selection path inside Workflow code.

Publish truthful node IDs when invoking Agent Tasks so the shared Web projection can attach
messages and token usage to nodes. Progress events are replaceable snapshots; completed messages
require native identity. Treat missing usage as unknown and context-window occupancy separately.
