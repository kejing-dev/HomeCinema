# Managed Shader Graph Material Production

Order: saved assembly → Graph binding → default-PBR sharing and orphan cleanup →
`produce-particles` → final freeze
and seven-view review. Assembly submits the confirmed table in
`candidate.inventory.shadergraphMaterials`:

```json
[
  {
    "name": "flowingWater",
    "generationRequirement": "Blue translucent water with visible flowing ripples",
    "reason": "The accepted water effect exceeds default PBR RGBA controls",
    "entityPaths": ["/Root/Water"]
  }
]
```

One row describes one shared material and all its exact observed binding targets.
Preserve suitable existing bindings; leave unmapped/provisional candidates in the
selection report. Use `[]` when no new Graph work is needed. Also submit
`candidate.inventory.materialCleanupEntityPaths` with every exact primitive created
in this assembly, or `[]` when none. Exclude groups and imported/inherited subtrees.
Runtime checks asset ownership and stores both lists as content references. A
nonempty cleanup list runs `produce-materials` even with an empty Graph table.
Primitive authoring selects a GUI session before assembly so cleanup can inspect appearance.
Runtime stores the table
as a content reference and launches one fresh ACP production Agent, with the same
verified GUI scene. The material Agent uses native Editor MCP, owns creation and
binding, and can iterate freely within its time budget.

The parent accepts optional `material.backend` / `material.timeoutMs`; a configured
particle backend is reused by default. Supply the current verified ACP host when
`configure-scene-materials` requests it. No second specification Agent is launched.

Read `executionLimits` before work. Runtime supplies absolute `reportBy` and
`finalizationStartsAt` using the remaining deadline after mount preparation.
Reserve up to three minutes (20% for smaller budgets) for settling, saving and
reporting. Cleanup has a cumulative maximum of ten minutes, capped by the execution
budget remaining after the finalization reserve
(`cleanupBudgetMs = min(600000, timeoutMs - finalizationBudgetMs)`).
This includes its pre-binding inventory, discovery, checkpoint
saves, USD tooling preparation/parsing, sharing, deletion and verification.
Count active cleanup work from its first inspection; pause that accounting during
Graph authoring/binding. Absolute finalization and report deadlines still apply.
Check the clock before
phases/batches; at either boundary stop new work,
retain safe bindings and report incomplete work as failed/partial/skipped.
These are Agent phase instructions; the ACP execution timeout remains the hard
outer limit. Runtime does not infer a successful report from elapsed time.

Discover the actual mounted namespace once; refresh it on a missing-tool error
instead of retrying guessed aliases. Cache brief capability documentation and
selected node definitions. Use scene summaries/scoped trees and locally aggregate
cleanup observations into counts, required identities, failures and small samples.
Keep each returned observation under 4 KiB; complete audits belong in scratch files.
Do not repeatedly print full native Entity.info/component trees or node catalogs.
Preserve the facts needed for safe cleanup; incomplete evidence means retain candidates.

Resolve binding → authoring profile → capabilities. If the target lacks an authorable
material, use `ensure_material_authoring_target` and resolve again. Choose
`apply_material_intent`, `apply_material_preset` or `set_material_properties` for
supported high-level work. For custom graphs export/get a template, discover nodes
and their catalog, modify USDA, validate and repair issues/rewrites, then preview.
Discover actual native signatures rather than inventing a batch binding API.

For transparent PreviewSurface work, read
[the transparent-surface recipe](transparent-preview-surface.md) before preview.
It provides a minimal candidate and the repair/save sequence for high-level helpers
that write an unsupported opacity attribute. Reuse its current catalog checks;
do not repeat a failing preset with progressively lower alpha values.

Treat templates and exported graphs as starting points, not current contract proof:

1. Compare edited nodes' actual `info:id`, port names and types with the current
   Editor catalog/definitions. After validation, inspect any normalized/rewritten
   candidate and repeat this check; canonicalization can change the node ID without
   correcting obsolete ports. The current `ND_UsdPreviewSurface_surfaceshader`
   exposes `opacity` as a float input, displayed as **Opacity** in the node UI,
   with default value `1`. Some Editor MCP PreviewSurface/glass templates incorrectly
   author `inputs:diffuseOpacity`; this is not a hidden input or an alias for
   `opacity` on this node. USD can retain an attribute the shader does not consume.
   After confirming the current catalog, set `float inputs:opacity` to the intended
   value and remove the unsupported `inputs:diffuseOpacity` from that shader.
   `1` is fully opaque; `0` is fully transparent. A graph with `inputs:opacity = 1`
   and `inputs:diffuseOpacity = 0.07` still has effective opacity `1`.
   Do not rename fields globally across other PBR or shader types.
2. Verify material surface connections resolve to active nodes and documented
   outputs with compatible types in the composed scene. A node present in USDA
   text is unusable when it or an ancestor has `active = false`.
   For the catalog-confirmed PreviewSurface graph, connect material
   `outputs:mtlx:surface` to the active shader's `outputs:out`, using the actual
   resolved material/shader paths, and declare `token outputs:out` on that shader.
   Preserve valid render-context outputs; remove or repair proven stale connections
   before validation, including `outputs:surface` referencing a missing or inactive
   `DefaultSurfaceShader`. Export normalization can select that stale legacy
   connection and replace a correct `mtlx:surface` connection with it.
   When returned, inspect `original_exported_usda_path` as well as the normalized
   export; after validation, inspect `normalized_usda_text` again for the intended
   active surface source. Export or validation success alone does not exclude
   unsupported inputs or invalid output targets.
3. For required transparency, verify the connected opacity input and supported
   blend/depth/culling settings. For ordinary alpha-blended glass, use supported
   `blendingMode = "TRANSPARENT"` and `depthWrite = false`; these settings do not
   substitute for a valid opacity input and surface source.
   Preview from outside with expected background or
   interior content visible through the surface. Hiding the glass or observing
   from inside does not prove transparency. If it remains opaque, inspect the
   current normalized/exported graph and repair concrete defects within the
   authoring budget before cleanup. Revalidate and preview the changed candidate,
   then commit/bind/save and reread the actual bound material in both the live
   composed scene and saved target scene. Check the effective opacity value or
   connected source and every authored surface output; the exported material file
   alone can omit stale opinions retained in the target scene.
   Repair proven defects through supported managed Editor authoring tools while
   authoring budget remains, then save and reread. Never patch the target USDA
   behind the Editor. Record unresolved defects and unmet transparency in `reason`
   if repair cannot finish; preserve the existing non-blocking visual-review policy.
4. A Host approval-policy denial is a permission error, not missing Editor capability.
   Record it exactly and use available documented definitions or supported read-only
   inspection. Do not guess ports, repeat unchanged denied calls or bypass permissions.

Material-local dynamic effects must use a Shader Graph Time node. Verify the persisted
graph connects Time through supported coordinate/parameter operations to the actual
surface output. For flow, scale Time by flow speed, then offset UV/coordinates that
feed the required ripple/surface response. Static approximations, disconnected Time
nodes, host-driven parameter updates, object/timeline animation or particles do not
fulfill the material requirement. High-level tools are suitable only when their
resulting graph provides this Time-driven path; otherwise use the budgeted custom
graph path below. This graph check does not add a blocking visual-effect gate.

Compare the high-level result with the row's complete `generationRequirement`.
A static approximation does not fulfill requested motion or procedural behavior;
a high-level helper limitation does not establish missing native Editor capability.
When the result omits or rejects that behavior and enough authoring budget remains
for discovery, validation, preview and commit/binding before `finalizationStartsAt`,
attempt a minimal custom graph. Go directly to custom authoring when the profile
already documents the high-level limitation.

Query only relevant current nodes/catalog entries and their actual IDs, ports,
types and support notes. For water flow, investigate Time, UV and coordinate
arithmetic plus Noise for moving ripples; query Fresnel when view-dependent surface
appearance is required. Do not hardcode IDs or guess signatures.
Catalog presence or `cataloged_unverified` status alone proves neither rendered
support nor lack of support. Connect time-driven coordinates and ripple variation
to the actual surface output before adding required secondary detail; isolated
nodes do not implement behavior. Revalidate each edit and use compilation evidence.
Repair or simplify concrete defects within the authoring budget without repeating
unchanged failures. Retain the last safe committed material if this path fails or
does not fit the budget. Record the attempted path, precise capability, validation,
compilation, rendering or budget limitation and unmet behavior in `reason`, then
clear unsuccessful previews and continue. This authoring fallback adds no blocking
effect gate and does not extend the finalization window.

Preview submission is asynchronous. Wait for supported compilation status, capture
and visually inspect settled native Editor screenshots, then commit promptly before preview expiry. Repair concrete
defects within the authoring budget; cleanup and persistence audits follow commit.
After a successful material commit, flush and checkpoint-save the exact target scene
before starting cleanup or unrelated material work. `binding_verified = true` with
`external_scene_save_status = "unverified"` proves no scene-save persistence.
Reuse that save when unchanged; save again after subsequent binding changes.
The authorized table selections permit autonomous commit; no per-material human
confirmation or fixed number of authoring rounds is imposed by this subflow.
Use `edit_scope=selection`; do not include unlisted shared references with
`all_references`. Bind every listed target to the same actual material identity and
resolve each binding to verify it. Matching colors or names do not prove sharing.
Imported targets must preserve unrelated mesh slots.

The material Agent performs visual review before particles and final scene review.
Use each row's complete `generationRequirement` as the checklist and inspect
representative bound targets in the requested surface region; shared materials
do not need a screenshot of every instance. Read actual image content from native
responses or the Host's supported image-viewing path. A successful capture call,
filename, file existence, image hash or changing bytes does not establish acceptance.
Use supported isolated material/target captures and verify restoration of temporary
visibility state before continuing or handing the scene to another writer.

For dynamic materials, after commit/binding and while authoring budget remains,
keep camera/framing fixed and capture native frames as needed to assess the required
surface motion, direction, ripple/glow/dissolve changes and appearance. There is no
fixed screenshot count or capture interval. Tool latency and imprecise timing may
sample similar phases; a short sequence missing a change is not by itself proof of
failure. Confirm the supported Shader Graph Time/render-preview progression mechanism,
allow further progression and capture more images for concrete evidence gaps.
Replay/restart only when supported by native tools; do not assume exact timestamps,
precise seek or deterministic replay. Particle playback and object/timeline animation
cannot substitute for Shader Graph Time.

Reuse current valid observations across authoring and reopening; recapture after
material changes or for a concrete evidence gap before `finalizationStartsAt`.
Record distinct screenshots actually viewed in `imagePaths`, retaining the most
relevant references within the 32-image report limit. Summarize observed requirements
and remaining gaps in `reason`. If images cannot be read, record
`IMAGE_OBSERVATION_UNAVAILABLE` in that row's reason, retain the committed material
and finalize without claiming a visual pass or blocking the Workflow solely for
this evidence gap.

Before any rebinding, inspect cleanup primitives and record their original actual
material identities, types, sources and default creation configuration. Only proven
defaults belonging to this assembly enter the cleanup candidate set. Unknown
provenance remains protected. Scope alone does not establish default provenance.

After Graph binding, share remaining equivalent default PBR within the cleanup
list. Complete default creation configuration plus RGBA is sufficient only when
RGBA was the sole modification. Other materials need full equivalence of properties,
textures, UV, shader and render settings. Keep one existing canonical identity,
rebind exact eligible targets and verify every actual binding. Preserve committed
Graph bindings. Do not upgrade PBR through `ensure_material_authoring_target` merely
to enable deduplication; unsupported PBR inspection/binding produces a skip reason.

For a nonempty cleanup list, attempting cleanup is an expected part of the Agent's
work. Optional refers to the non-blocking outcome. Reserve time for the attempt
when planning material work before finalization; verified Graph bindings and saving
alone do not justify omitting it.
Use live MCP data plus saved USDA within that cleanup budget:

1. Use `get_scene_info` under its actual schema to collect material paths, actual
   types and hierarchy. Aggregate locally and keep observations bounded.
2. With previews settled, save the exact target scene and read only its confirmed
   saved USDA read-only. Parse complete material definitions and
   `rel material:binding` with available supported USD tooling, matching paths,
   types and bindings against the live scene. Partial text/regex scans do not
   establish complete configuration or reference coverage.
3. Compare PBR definitions by consistently normalizing each material's own
   namespace and internal connection paths. Preserve node names/topology, values,
   types, textures, external asset paths/references and render settings.
   Keep one existing identity per equivalent group and discover the actual
   `se.scene.bind_material()` signature for native batch rebinding when supported.
   After each batch check shared identity, affected geometry existence and RGBA
   readback. Live/file evidence does not expand the cleanup list or prove default
   provenance on its own.
4. Save again after sharing and reconcile updated references with the live scene
   before deletion. Saved bindings alone do not cover inherited bindings,
   slots/subsets, composed layers/references/payloads, hidden users or preview
   dependencies. Retain candidates when coverage is incomplete, saved data is
   stale or live/file observations disagree. Use `Entity.delete()` only with the
   material type, material-only semantics and zero-reference evidence established;
   check geometry existence and RGBA after each batch.
5. Save the final result within remaining budget and reconcile live material
   counts and saved bindings. Compare compact pre-cleanup non-material transform
   summaries and retained Graph/particle subtree content; keep detailed records in
   scratch. Reuse unchanged evidence instead of repeating full audits per batch.
   Example scene counts are observations, never cleanup targets.

Before giving up on a recoverable problem, try the applicable distinct alternative
within the same budget: refresh the documented namespace/signature for missing
tools, scope and aggregate oversized observations, save/reread the exact target for
stale evidence, or use complete composed USD data when a convenience helper omits
configuration/references. A missing helper, first tool error or incomplete query
does not establish unsupported native cleanup. Try each relevant alternative at
most once per unchanged failure; further retries need corrected input or new evidence.

Discover an existing OpenUSD interpreter, including the Editor's supported Python
environment. If none is usable and host permissions and budget allow, prepare
OpenUSD in an isolated task-scratch Python environment outside project source.
Do not change base Python or project dependencies. Preparation consumes the same
cleanup budget; report concrete preparation errors and use complete documented
native evidence when available. Resolve explicitly referenced layers/assets,
including USDZ composition; `Sdf.CopySpec` into scratch can normalize each
material's own namespace while preserving complete definitions.

Track independent groups separately. An unresolved candidate remains protected
while other proven groups continue. An actual preservation failure stops affected
writes immediately; other groups may proceed only with trustworthy baselines and
settled scene state. If the Editor adds `xformOp:orient.customData.euler`, ignore
that annotation only when verified display-only with unchanged actual quaternion,
position, scale and other content.

Complete each group's safe sharing, binding verification, proven orphan deletion
and post-checks before moving to the next group. Save the target and record
completed identities/counts in scratch at each completed group boundary.
Completed groups are retained without rollback if later groups fail or time runs
out. Do not reload the pre-cleanup scene, undo the whole cleanup, restore earlier
completed bindings or recreate their deleted orphan materials. Safe repairs stay
within the active incomplete group; otherwise retain partial progress and report
the limitation. Reuse completed records without reopening that group's work.

Final `partial`/`skipped` reasons include compact attempted paths, observed errors,
completed counts and remaining limitations. Stop only for no eligible candidates,
documented unavailable capability after relevant discovery/recovery, unresolved
safety evidence after applicable bounded alternatives, or budget/finalization
exhaustion. A verified lack of eligible candidates is a completed no-op.
Retain candidates rather than deleting without complete evidence.
This evidence path adds no completion gate. Read only the confirmed scene; do not scan project directories
or edit/delete source files. Geometry, inherited/imported materials and successful
Graph bindings remain protected.

Enumerate all material references once and recheck affected references after sharing,
reusing unchanged facts. Include hidden/disabled entities, inherited
bindings, mesh slots/subsets, unlisted users and previews. Delete only recorded
assembly defaults proven orphaned through a verified material-only native operation.
Generic `Entity.delete` requires actual material type and documented material-only
semantics. Never delete geometry, ancestors, active canonical identities,
imported/inherited materials, unlisted materials or project files. Unknown reference
coverage, deletion semantics or persistence means retain candidates and report
`partial`/`skipped`. Confirm deletion and affected bindings after each batch.
Do not restart completed groups or retry candidates already finally skipped after
bounded recovery.

Clear unsuccessful/uncommitted previews and verify settled state. Inspect actual
one contextual viewport screenshot after cleanup and save committed
bindings under the parent scene-delivery authorization, which permits checkpoint
and final saves; reuse a confirmed unchanged final save. Retain successes, report
failed rows with concrete reasons, and continue other rows. The final report records
each row's name, status, actual material identity, bound count, limitations and images.
When a cleanup list is supplied, also return `cleanup` with `status`
(`completed`/`partial`/`skipped`), `mergedGroups`, `reboundCount`, `deletedCount`,
`skippedCount`, `bindingsVerified` and a required reason for partial/skipped results.
Counts reflect observed groups, rebindings, deleted and retained candidate materials.
Cleanup completion is non-blocking; a nonempty list still requires a budgeted
attempt and applicable recovery. A failed, partial, skipped, missing or unverified
cleanup result does not fail successfully produced materials or stop the particle
phase. Record its reason and observed counts when available; use
`bindingsVerified=false` when cleanup verification was not completed. Protect
uncertain groups, complete independent safe work and finalize the material results
when cleanup completes or reaches an explained stop condition.
Empty `materials` is valid for cleanup-only work. Verified material-table bindings,
settled previews and saving remain required.
Runtime checks report coverage and completion, preserves geometry, and refreshes the
scene baseline before particles; it does not score node graphs or independently
certify the Agent's visual review or binding claims.

A successful save and verified current bindings suffice for ordinary completion.
Appearance, motion and reopen persistence checks are advisory. Keep a committed row
with verified full bindings succeeded and record unproven behavior in `reason`;
authoring/binding failures remain failed rows and do not block the whole Workflow.
Only an explicit row requirement and remaining budget permit one reopen of the exact saved target scene.
Check that row's binding and apply the visual review above to its dynamic requirements;
reuse valid observations and keep new captures within the authoring budget.
Time-node presence or whole-frame pixel changes alone
do not prove visible flow. A no-op reopen or unproven persistence is a precise
limitation; do not force unloading through `Hi.usda` or another scene, change Editor
instances, or repeat whole-scene material audits. Keep the target active.
Unconfirmed temporary scene-state restoration must be settled before further writes;
it is a scene-state issue rather than an advisory visual limitation.
Once required checks settle and cleanup completes or reaches an explained stop
condition, immediately return the final JSON and end the turn.
No additional audits, screenshots or tool calls follow a settled report.

The lightweight subflow gate accepts recorded per-row failures and explained
partial/skipped cleanup. Old candidates without a cleanup list retain their prior behavior.
Material-local motion is declared directly in generated material requirements,
without animation enhancement entries. Editor does not support animation generation
or registration; follow [material selection](material-selection.md).
Required lighting and other registered enhancements retain their gates.
The final review receives the current material report and its reasons. Record
material visual/dynamic limitations in check summaries rather than blocking findings,
without claiming unverified effects were fulfilled. Unconfirmed Agent process cleanup,
interrupted native previews or unknown save state stop subsequent writers until
the retained session is inspected; they are not silently converted into success.
