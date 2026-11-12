---
name: spatial-editor
description: Run managed Spatial Editor workflows for scene or asset authoring, materials, visual review and packaging. Use for Editor content requests; integrating an existing .bundle and .scenes.json pair uses spatial-app-dev-workflow.
license: 'Apache-2.0'
---

# Spatial Editor Workflow

## When to Use

- 3D scene/asset/material authoring in Spatial Editor
- Managed Editor workflow for scene packaging

## When NOT to Use

- Code-defined Entity scenes — use `spatial-sdk-scene-builder`
- UI panel layout — use `spatial-ui-ability`
- Existing bundle integration — use `spatial-app-dev-workflow`

## Load Only What The Current State Needs

This Skill owns workflow intent and task decomposition. Start one
`start_editor_workflow` Run and generate its SceneSpec first, including particle-only
requests. The public Run owns model inventory and bundle delivery.

- SceneSpec particle effects: read `particle-workflow.md` for managed preparation.
- Current v6: Read `contracts.md` from this Skill directory and follow
  `next.submission.inputSchema`.
- Primitive orientation or joints: read `references/primitive-geometry.md`.
- Native PBR, captures or containers: read `references/authoring-quality.md`.
- Before SceneSpec, read `references/material-design.md` and `references/material-selection.md`.
- Material production Agent: read `references/material-production.md` before authoring or binding.
  For transparent surfaces, also read `references/transparent-preview-surface.md` for the
  catalog-confirmed opacity input, minimal graph, exterior preview and scene-save procedure.
- Rejection, interruption or blocker: Read `recovery.md` from this Skill directory;
  follow its current recovery actions.

This Skill supports current v6 Runs only; see `contracts.md`'s Gate Action Map.

## Ownership And Safety

Editor owns content and packaging; `spatial-sdk-scene-builder` owns Kotlin
Entities and runtime behavior. Apps consume Editor packages.

Mutations and packaging stay in the managed public Workflow Run. Before it,
do not invoke a direct Editor readiness command or start a standalone session.
Read-only status is allowed; the Workflow Session must establish and own its Editor
process. Resolve other sessions' ownership before writing.

Never bypass the Workflow Service or its Drivers for writes or packaging.
`get_scene_info` and `get_entity_info` are read-only and do not require a Workflow Handoff.
At `author-scene`, use `get_editor_workspace` and `execute_editor_operation`;
the gateway checks session, editing window, scene fingerprint and operation receipts.

## Managed Workflow

Use the `start_editor_workflow` entry for the public
`spatial-3d-generation` root with `backendPreference="editor"`; never start the Editor Child directly.
For SGS supplied assets, read `references/sgs-supplied-assets.md`.
Revision uses root `base_run_id`; production uses `workspace_root` and optional
`target_scene_path` for new geometry. Verify the active scene.
For `project_name` and filename rules, see `contracts.md`.
Legacy `content_kind` values remain compatible hints; SceneSpec determines particle work.
Default headless; explicit GUI uses `preferred_mode="gui"` and `gui_reason="user_requested"`.
SceneSpec materials/particles select GUI; see `references/session-admission.md`.

The normal loop is:

1. Start one public production or revision Run for the goal.
2. Resume the initial `author-scene-spec` Handoff with every subject/count.
   Keep models and structural primitives in the complete asset inventory.
   Check live `subjects[].count` limits; split excess and preserve totals/references.
   Set `authoringStrategy` to `generated-model`, `imported-model`, `editor-primitives`, or `group`;
   Imported models declare `source.path` as a normalized workspace-relative USDZ file.
   Generation and import may coexist; import never requires a generation prompt.
   a geometry-free root is a group, not an extra model. Primitive-only uses
   `modelGeneration="forbidden"`; tags and `kind` do not select production.
   Declare `effects` with `kind="particle"`; follow `particle-workflow.md` for
   batch production after scene assembly, node bindings and missing-effect records.
3. Let model production advance. When `next.action="wait"`, call `next.tool` with
   its returned bounded arguments. Primitives do not enter model production.
4. At `review-editor-assets`, inspect all previews. Record `worldForwardAxis`,
   semantic features and opposite views when a front is visible. Use `not_applicable`
   for no intrinsic front. Use `ambiguous` only when a directional model's evidence
   is insufficient, and revise generated models only. Imported sources are retained;
   their asset review covers direction, with scene placement checked later.
   All prerequisite models must pass before assembly.
5. At `author-scene`, use `get_editor_workspace` and `execute_editor_operation`
   for one bounded arrangement recipe of models, primitives and enhancements.
   Split for script/output size or async dependencies; await imports.
   Use the reuse recipe in `references/authoring-quality.md`; query uncovered APIs
   with `detail="brief"` through the gateway and reuse its exact `auth_token` in scripts.
   Apply supported default PBR from `authoring.intent.sourceContract` during creation;
   see `references/pbr-materials.md`. Submit `inventory.shadergraphMaterials` before particles.
   Later changes use SceneSpec Revision with lineage.
   Finish writes before review; report progress every 60 seconds.
   Default extra local/detail screenshots: zero; use them only for a concrete open issue.
   Submit the candidate, complete asset inventory, successful operation
   receipts, and complete Interaction Contract from `contracts.md`.
6. At `capture-review-evidence`, follow returned waits while Driver captures the frozen
   candidate using six world-axis views and front three-quarter view. Driver fits cameras
   to bounds and retains valid receipts when retrying failed views.
7. At `review-editor-experience-v6`, the same caller agent inspects the evidence and
   submits checks and findings. Do not spawn a reviewer subagent. The scene is read-only.
   Failed checks return to the responsible production window; recapture after changes.
8. Worker packages, verifies and records provenance. Follow returned waits;
   submit packaging only when a live Handoff requests input.

Treat every Workflow MCP response as one observation of the public Run. Read
`runId`, `current`, `next`, `error`, terminal `result`/`artifacts`/`evidence`; replace cached
arguments and stage/child observations.

Judge `current.status`, `next.action` and `error` together. Follow non-terminal waits;
elapsed time is not a blocker. Cancel only on explicit user request. Refresh progress
and follow `recovery.md` for long waits and finalization.

After project readiness, use `agentWorkspace.directory` under
`.CacheData/AgentWorkspace/<rootRunId>`; temporary work belongs in `scratchDirectory`.
Read current resource paths and exact IDs/digests. Refresh missing files on the same
Run/workspace; never browse internal Run folders, edit published evidence, or clean
Editor caches/locks. See `contracts.md`.

For submissions, call `next.tool` with `next.arguments` and `input` that
validates against `next.submission.inputSchema`; use `next.submission.kind`.
Use `submit_editor_workflow` with returned `task_type` or one `next.submission.taskTypes`
value matching the payload. `task_id`/`expected_revision` bind the Handoff.
`get_editor_workflow_status` is observation-only. `current.module`, `current.phase`,
and `current.models` provide compact progress.

A Handoff mismatch is a non-terminal rejection: the Workflow Service preserves the
current public waiting state. Refresh before retrying; see `recovery.md`.

## Task Decomposition

Before model production, separate:

1. Distinct generated/imported model archetypes.
2. Repeated occurrences that can reuse one accepted archetype.
3. Structural or dimension-driven primitives.
4. Requested material work and semantic targets.
5. Whole-scene relationships and acceptance.
6. Lighting and supported static/particle effects.
7. Downstream runtime-node and delivery contracts.

### Asset Archetypes And Reuse

Generate one archetype for shared form, appearance and role; separate assets with
different identity, function, geometry or acceptance.
Reuse is a design heuristic, not an acceptance gate.
Reuse the accepted imported entity as the first formal instance; import only
missing occurrences up to `count`. For stale/foreign paths, inspect live instances
first. Do not retain hidden prototypes or create PrototypeCache by default.
Keep USDZ files and acceptance records for recovery.

### Structural Primitives

Use primitives for dimension-driven floors, walls, columns, platforms, partitions,
and simple volumes. Use generated/imported assets when silhouette, topology,
curvature, ornament, or semantic identity requires authored geometry.

Classify orientation before authoring a primitive transform:

- A `Cone` has a signed semantic direction from its base toward its tip.
- A `Cylinder` or `Capsule` has a longitudinal axis, but its positive and negative
  ends are equivalent unless accepted input adds an observable end distinction.
- A `Plane` has a signed normal only when face visibility, culling, or another
  accepted relationship makes the normal observable.
- A `Sphere` has no intrinsic direction. A `Cube` has no semantic front unless
  accepted input or a visible face distinction establishes one.

For every direction-sensitive primitive, derive the required world direction from
accepted scene intent or an explicit relationship, use the canonical Editor
primitive-axis mapping in `references/primitive-geometry.md`, and repeat that direction as an observable
primitive acceptance criterion. Never choose a direction from category convention,
hide an unresolved direction in `rationale`, or treat an axial primitive as having
a head and tail when its geometry does not distinguish them.

Choose joints from actual contact surfaces: use butt joints for sufficient flat-face
contact, and bounded insertion where curvature would leave only point/line contact.
Hide the entire inserted end, including corners, and check all exterior surfaces
for competing overlap. Internal contact/overlap is valid. These rules apply to all
geometry. Read joint selection and examples in `references/primitive-geometry.md`.

Defer final primitive transforms until accepted model bounds are known:

- Model-only: placements and optional instances.
- Mixed: placements, instances, and final primitives.
- Primitive-only: create declared primitives directly in the editing window.

The complete asset inventory retains primitive identity, count, and acceptance.
Create concrete primitive geometry and transforms in the authoring window after model
acceptance. Candidate submission checks that every declared primitive has live entity
bindings; final scene review checks its appearance and spatial relationships.

### Scene Intent And Hierarchy

Before candidate submission, delete temporary prototypes, canaries, duplicate imports
and empty staging containers; preserve required content and formal instances.
Verify absence/counts, save and reread the fingerprint. Hiding is not deletion.
Verify compound subjects' materials in the final seven views.

Use `references/material-design.md` for appearance. Explicit
color, emission, opacity, roughness, metallic behavior, and render mode use supported
properties. `Entity.set_color(r,g,b,a)` updates default PBR BaseColor.
Color alone does not prove emission or transparent blending.

Group coherent assemblies with identity-transform `Xform` nodes.
Declare `scene.runtimeNodes` only for downstream-addressable entities using `./...`
from the discovered managed root. Editor operations use verified absolute paths;
never derive a root path from `scene.name`.

## Visual And Spatial Review

Actually inspect every image referenced by current evidence. File existence, a
successful call, bounds, or a package is not visual proof.

For `reuse_required`, scope that model's evidence-image review to direction-related evidence only. Do not evaluate or fail geometry, appearance, topology, or detail,
and use `orientation.verdict="ambiguous"` when an imported model has no reliable
semantic front. This is not a request to generate a replacement; final scene review still
evaluates placement and physical/spatial defects.

Floating, unintended penetration, instability, unusable scale, obstruction and
requirement violations block acceptance. Depth findings need multiple views.
Natural occlusion in a valid axis view is not itself a finding or a reason to
retake it. Inspect all seven current views and cite the useful views per criterion.
Missing proof of a required criterion blocks, except managed missing-particle gaps;
report those through delivery as described in `particle-workflow.md`.

For a direction-sensitive primitive, compare its named semantic feature against
its exact acceptance criterion in at least two useful current views. Opposite
world-axis views are preferred for a signed direction such as a cone tip. A reversed
tip, normal, or required longitudinal axis is an explicit requirement violation and
must return to authoring; recapturing the unchanged scene is not a correction.

Review contact and all exposed joint sides in useful current views. Reject unintended
gaps, point/line-only connections, exposed coincident or near-coincident surfaces,
breakthrough, flicker or viewpoint-dependent seams. Internal contact/overlap is valid.
A hidden end or one clean image does not prove that exterior surfaces are safe.

Before final planning:

1. Read required runtime-node paths and parents.
2. Read world bounds and imported transforms for every accepted model.
3. Treat placement as the entity pivot; derive pivot-to-bottom and pivot-to-center.
4. Ground objects on real supports and derive spacing from measured extents.
5. Determine scale from measured bounds and scene relationships; never supply category-based default dimensions.
6. Preserve imported rotation unless evidenced semantic direction requires a world
   `+Y` heading delta.
7. Check containment, circulation, access, occlusion, and interpenetration.

Nonuniform scale uses local axes. An imported -90 degree X rotation maps local Y
to world Z and local Z to world Y. Map measured world-size ratios back through the
actual imported/parent rotation, then remeasure; do not blindly swap axes for other poses.

Axis-aligned bounds overlap alone does not prove penetration.

### Lighting And Effects

Set `lighting.kind` to `"environment"`/`"light-entity"` and `effects[].kind` to
`"static"`/`"particle"`/`"other"`. Editor animation generation and registration are
unsupported; do not submit `kind="animation"` or disguise it as `other`.
Keep material-local motion in generated material requirements without an effect entry;
see `references/material-selection.md`. Particles use their dedicated workflow.
Lighting uses `execute_script`;
query `topic="lighting"` for `Entity.configure_light`, `aim_at` and `get_light`.
See `references/authoring-quality.md`; emission is not a light.

When static fallback is authorized, set the affected SceneSpec effect `required=false`
and report its enhancement ID and reason in `inventory.unsupportedWork`.
Only implemented work belongs in `enhancementIds`. Missing required non-particle work blocks;
Resolve ordinary object/timeline animation through a supported workflow before
Editor submission.

## Existing Scenes

Material/transform edits require revision with root `base_run_id`.
A runId is an execution record; it does not own permission to edit a scene.
Do not choose only the latest successful Run: its manifest may be empty.
Choose verified parent inventory covering each material target's exact subject ID
and accepted entity bindings; confirm scene/provenance still matches the project.
A material-only Floor change needs inherited `asset:Floor`, not a new primitive.
Coverage is checked before Session startup; see `recovery.md` for missing targets.
Pure transforms without material bindings may retain an empty manifest.

Preserve unrelated content; submit the complete retained and authored inventory
or `assetBindings: []` for an empty manifest. Correct rejections in the same active Run.

## Completion And Handoff

Report optional work in `unsupportedWork`.
Sync custom components with `pico-cli editor sync component --component <KotlinComponentName>`;
use `--editor-project` or `--file` when multiple projects/files match.

After packaging and Session release, return:

- Project and accepted scene paths.
- Co-located `<bundleName>.bundle`, `<bundleName>.scenes.json`, and provenance.
- Managed Run/revision/fingerprint/gate proof and SHA-256 digests.
- Runtime-node, orientation, material, warning, and unsupported-work results.

Distinguish saved verification from managed delivery; the facade requires a scene package.
For non-retryable Gate failure, report saved work and stop. Retry requires a changed
cause or explicit reproduction request.

App workflows own loading, Kotlin integration and runtime validation.
Completed handoffs are immutable; further edits require a new Run.
Direct CLI packaging is unmanaged.
