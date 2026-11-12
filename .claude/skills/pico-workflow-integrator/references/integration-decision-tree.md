# Workflow integration decision tree

Use verified source behavior, not the author's preferred framework name, to choose the integration
route. For the Domain ownership model, author files, and completion criteria, read
`docs/development/workflow/domain-quickstart.md`.

## 1. Reject unsupported targets first

Stop with an integration-gap report when any required behavior depends on:

- launching an arbitrary executable as a Workflow Runtime;
- dynamically registering new topology during a Run;
- author-controlled public Run, Result, Event, or Snapshot storage;
- unbounded child Workflow creation;
- restoring an Agent Session in a different process when no current contract supports it.

Do not work around these gaps with a new compatibility `node-module` package.

This classification ends the current implementation pass. Do not edit or register a package after
reporting the gap, and do not run implementation, build, test, scaffolding, formatting, or
speculative compatibility probes. Present the supported alternatives and wait for an explicit choice; a request to
integrate or launch an existing executable does not also authorize a migration or rewrite. If the
user later chooses migration, restart classification with that new target and verify preserved
behavior separately.

## 2. Choose Domain static-dag

Use Domain Static DAG when all of these are true:

- topology is fixed before the Run starts;
- dependencies form an acyclic graph;
- each unit can be represented as a Script Step, Agent Task, or caller handoff;
- retries are local and bounded;
- no package-owned scheduler or checkpoint engine must be preserved.

Parallel-looking branches may still execute conservatively. Do not promise concurrency unless
current Runtime tests prove it.

## 3. Choose Domain module-kernel

Use Domain Module + Kernel when the topology is fixed but execution needs one or more of:

- Driver `execute`, `reconcile`, and `cancel` operations;
- durable handling of side effects;
- Gate decisions such as retry, revise, strategy reset, request input, skip, block, or fail;
- invalidation and bounded graph replanning;
- partial completion;
- graph-level retry or elapsed-time budgets.

Every Module and Gate must resolve from a fixed Manifest during Catalog construction.

## 4. Choose LangGraph codegen

Use LangGraph codegen when:

- the reviewed topology contains real back-edges;
- route selection depends on graph state;
- graph checkpoint semantics are part of the existing behavior;
- rewriting the graph as a fixed DAG would change observable behavior.

The topology and state schema must remain reviewable build-time assets. Do not preserve arbitrary
runtime graph generation merely because the old engine allowed it.

## 5. Classify without forcing a route

Use this order:

1. Can a fixed acyclic graph preserve behavior? Use Domain static-dag.
2. Does a fixed graph need Drivers, rich Gates, recovery, or partial completion? Use Domain
   module-kernel.
3. Are real back-edges or graph checkpoints required? Use LangGraph codegen.
4. Does the implementation own an irreducible custom engine or executable process? Report it as
   unsupported by current maintained author paths.

When evidence is incomplete, keep the classification provisional and name the missing fact. Do not
invent a topology.

## 6. Compatibility is not a destination

Existing `node-module`, `agent-guided`, and `pico-managed` packages may be maintained while migration
is pending. They are not valid targets for new integrations.

For a legacy package, first determine whether its public behavior maps to Domain or LangGraph. Keep
the old package unchanged until focused tests prove the replacement preserves its Contract,
side-effect, waiting, and terminal behavior.
