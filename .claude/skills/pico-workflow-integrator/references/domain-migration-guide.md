# Domain Workflow migration guide

Use this guide after the integration decision selects Domain.

## Preserve the public boundary

Identify the existing caller-visible request and successful result before extracting nodes. Create
separate Workflow Input and Output Schemas that preserve those semantics without exposing process
paths, credentials, model selection, Host configuration, or private checkpoint fields.

Add a public Snapshot only when callers need a stable current view. A Snapshot is not a dump of
private Runtime state.

## Map behavior to Domain concepts

| Existing behavior                               | Domain target                  |
| ----------------------------------------------- | ------------------------------ |
| pure deterministic function                     | Script Step                    |
| bounded model task                              | Agent Task                     |
| work returned to the initiating Agent           | `caller-agent`                 |
| validation or routing predicate                 | Gate                           |
| side effect with an external operation identity | Module Kernel Driver           |
| fixed dependency                                | `dependsOn`                    |
| input or dependency projection                  | JSON Pointer binding           |
| generated file, trace, or report                | Artifact and optional Evidence |
| recoverable in-progress view                    | Snapshot                       |

Keep adapters thin. If reusable domain code already has a stable owner, call it from the Step or
Driver instead of copying it into the Workflow package.

## Choose the Domain control model

### Static DAG

Use a static DAG for fixed acyclic coordination. A node should own one coherent operation and return
JSON that matches its declared contract. Use a local Gate only for bounded deterministic retry.

Do not invent back-edge, arbitrary `goto`, nested Workflow, or custom scheduler fields.

### Module + Kernel

Use Module + Kernel for side-effecting or policy-driven orchestration:

- bind every Module and Gate through the package Manifest;
- use Manifest v3 `owns` to assign unique responsibility and `acceptsCorrections` to declare supported repairs;
- declare exactly one `consumes` entry for every direct dependency;
- declare finite graph budgets;
- make Driver operation identities durable and idempotent;
- implement `reconcile` before retrying an operation after uncertain completion;
- use `cancel` to stop the external operation owned by the Driver;
- map unknown recovered side effects to an unknown/blocked public outcome instead of replaying them;
- preserve partial outputs only through the Runtime's supported partial-completion path.

Use `content_sensitive` when a Module consumes its dependency's complete result. Use `projected.paths` only when
the listed JSON Pointers fully describe the consumed interface. Add `digestStepId` when stable content/interface
projections are needed for precise invalidation.

An attached `child-workflow` binding may select from a build-time-fixed target allowlist. Keep
`maxChildRuns = 0` without Child Modules; otherwise make it cover every declared Child Module. Current Domain
support does not include detached Child Workflows or multiple Child Runs from one parent-node attempt.

When final assembly can reject otherwise accepted Modules, bind `completion.assemblyVerdict` to a required Module
output. Return `{ "kind": "pass", "reason": "..." }` or a findings verdict whose blocking findings identify a
current Evidence set, an owned scope, and a supported correction category.

## Separate state and evidence

- WorkflowRun and Result are owned by pico-cli.
- Private execution state belongs to the Domain Runtime.
- Public Snapshot contains only bounded author-selected fields.
- Product output stays at the caller-selected workspace location.
- Run evidence belongs under the injected Artifact root.
- Never register an arbitrary absolute path returned by an Agent or external tool.

## Validate the migration

Add tests that compare the old and new externally observable behavior:

- valid and invalid Input;
- successful Output;
- deterministic failure and structured Error;
- waiting and Resume when applicable;
- retry and reconciliation for side effects;
- Event and Snapshot projection;
- Artifact paths and Evidence;
- restart behavior;
- no real Agent, process, device, or network side effect during package registration tests.

Do not delete the previous implementation until the replacement passes its focused tests and is
discoverable through the maintained Catalog.
