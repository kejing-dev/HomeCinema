# Editor Material Selection

Use this reference for material-route planning or review within the owning Editor
Workflow. The decision report is planning evidence, not a new v6 submission kind.
Assembly follows [the default-PBR path](pbr-materials.md); confirmed Graph targets
enter [managed material production](material-production.md) after assembly and before particles.

Read [proactive material design](material-design.md) before SceneSpec, then produce
a material-route decision before authoring. Recheck the original scene goal alongside
the accepted SceneSpec so an agent-authored simplification cannot erase an important
surface's material design. Treat `shadergraphy`, ShaderGraph,
and Shader Graph as the graph-authoring route unless the user identifies a different
tool. Do not assume a tool exists from its name.

Keep the lighting model separate from the authoring route. A Shader Graph can implement
PBR. General PBR model features do not establish available Editor authoring controls;
apply the current RGBA-only boundary below.

Read [capability evidence and boundary cases](material-selection-capabilities.md).
Return a decision report using [the output schema](../assets/material-selection.schema.json).
This Skill selects a route; it does not create, bind, or approve a material.

## Current RGBA-Only PBR Boundary

Use the user-confirmed capability boundary for this selection test: the current
default-PBR authoring path supports only `Entity.set_color(r,g,b,a)`. Keep the default
lighting response and other material properties. Do not assume available metallic,
roughness, emission, blend/refraction, normal-map, texture-assignment, UV, or persistent
parameter-animation controls.

- Select PBR when RGBA plus the existing default appearance realizes the selected
  behavior, such as solid-color panels, painted blocks, or explicitly simple surfaces.
  First evaluate effect-bearing surfaces using material-design.md; lack of the word
  "shader" in the request and an RGBA-only execution path are insufficient reasons.
- A numerical alpha value can be set, but does not establish see-through blending.
  BaseColor RGB does not establish emission. Required transparency or emission
  therefore exceeds this authoring path.
- When a required feature exceeds RGBA/default appearance, record a `pbr_path_gap`
  and include the material in the Graph requirement table. Examples include controlled
  metallic/roughness, visible wood grain, normal detail, glass/refraction, glow,
  flowing water, holographic bands, and dissolve effects.
- Preserve a suitable existing/imported material that already meets the requirement;
  unavailable new controls are not a reason to replace it.
- Retain defaults for optional unsupported polish, with a limitation. Do not call a
  required effect satisfied by changing its color.

Confirm the route requirement from this capability boundary and the scene contract;
verify Graph execution separately in the dedicated material subflow. The table
may confirm that Graph is needed before native authoring capabilities are discovered.
Reconsider the PBR boundary only after an explicit, verified capability update.

Before submitting SceneSpec, encode a selected new Graph requirement with
`materials[].generation="generate"` and its exact semantic `subjectIds`.
Descriptions containing Shader Graph, Time or flowing water do not select this
route by themselves. Omitted generation and `auto` do not explicitly request Graph
generation; `preserve` keeps an existing material.
Keep material-local flow, ripples, glow pulses or dissolve behavior in the material
description and later `generationRequirement`, without a separate effect entry.
Specify Shader Graph Time-driven surface behavior for these dynamic requirements;
the material Agent must connect Time to the actual surface output.
For example, declare a generated flowing-water material on `["Moat"]` directly.
Editor does not support ordinary animation generation or registration; never declare
`effects[].kind="animation"` or relabel it as `other`.
If material/timeline ownership is unresolved, resolve the planning choice before
submission. Object/timeline animation requires a supported workflow.

## Extract the contract

For each distinct material requirement:

1. Identify the surface and its selected visible behavior. Separate user requirements,
   bounded agent design choices and optional polish in the reason/feature lists.
   Treat explicitly requested features as required unless the user has accepted a
   fallback; do not silently relabel them as optional. For creative scenes, actively
   evaluate water, glass, luminous and other effect-bearing surfaces before accepting
   a color-only design. Preserve explicit blockout or flat-color restrictions.
2. Inspect supplied material facts and current bindings. Prefer preserving a suitable
   bound material. An imported asset is not automatically a material rewrite target.
3. Record exact target entity paths when supplied. During planning, allow an empty list
   and state how targets will be resolved. At binding handoff, require exact,
   observed paths; do not invent paths or use wildcard targets.
4. Separate material behavior from geometry, lighting, particles, and application
   interaction. Moving spark geometry, a particle emitter, and illuminating nearby
   objects are not established by assigning an emissive material.
5. Identify the intended surface model as `pbr`, `unlit`, `other`, or `unknown`.
   Do not infer it solely from a graph file, preset name, or API name.

## Establish capability evidence

Use supplied, resolvable evidence for the exact Editor build and route first. Reuse
verified evidence within an unchanged session rather than repeating probes.

- Apply the pinned RGBA-only boundary for route selection. Do not repeatedly query
  known unavailable PBR controls or assume an alternative texture/animation path.
  Keep an unknown Editor build unknown; the boundary alone does not prove readiness.
- Record evidence IDs, source locations or operation receipts, scope, build, date,
  and the specific supported or unsupported behavior.
- Distinguish `current_build`, `historical`, and `general_model` evidence. Historical
  tests and generic PBR documentation guide investigation; they cannot establish
  current Editor readiness.
- If required behavior is unknown, query only the relevant advertised native MCP
  documentation or capability tools. If these are absent, record the missing
  capability and a focused verification step; do not invent tools or node names.
- This decision task is read-only. Describe any needed isolated probe for the
  authorized authoring workflow to perform through its managed workspace gateway.
  Do not launch Editor, install tools, or mutate the user's scene to make a decision.
- Scope a failed API call to that API, build, and value. Check an advertised alternative
  before concluding that the entire PBR route is unavailable.
- For Graph readiness, establish the actual graph implementation, required node and
  render-state support, and an available authoring/reuse, validation, preview,
  binding, and save path. A graph-authoring tool alone is insufficient.

## Select the route

Evaluate these rules in order after designing the appearance. Compare selected
features against verified route capabilities; prefer the least complex route that
satisfies them. Optional agent choices may justify a Graph candidate without becoming
mandatory user requirements. If their execution is unavailable, retain the choice and
report the omitted effect through the live schema; never turn it into "no matches".

| Condition                                                                                                      | Route and trigger                                                                                               |
| -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| A currently bound material satisfies all required features, including an explicit Graph requirement if present | `preserve` / `reuse`                                                                                            |
| The user explicitly requires Shader Graph                                                                      | `shader_graph` / `user_required_graph`; reuse a suitable graph before proposing generation                      |
| RGBA plus existing default PBR appearance satisfies all required features                                      | `pbr_parameters` / `default_supported`                                                                          |
| A required custom computation cannot be expressed by available PBR controls                                    | `shader_graph` / `custom_logic`, with a specific `pbrGap`                                                       |
| PBR could represent the effect, but its available Editor authoring path has a verified required-feature gap    | `shader_graph` / `pbr_path_gap`, with the API-specific `pbrGap`                                                 |
| There is insufficient evidence to choose or execute a path                                                     | Keep a justified candidate `provisional`; use `unresolved` for a PBR candidate awaiting capability verification |
| No permitted, available path can satisfy the required contract                                                 | `blocked` / `unresolved`, with the missing feature or execution path                                            |

Treat an existing unbound graph selected for reuse as `shader_graph` / `reuse`;
record its exact material identity in the reason/evidence. `preserve` means keeping
an existing binding, not creating a new one.

Use `pbr_path_gap` for required non-RGBA features under the current boundary,
including effects that standard PBR could represent through unavailable controls.
Use `custom_logic` when the required behavior additionally needs custom computation.
Do not suggest baking or parameter animation as a current PBR fallback; those
authoring paths are outside the admitted RGBA-only capability.

Do not select a graph merely because PBR support is unknown. Use `provisional` when
capability verification remains possible. Use `blocked` when there is a confirmed
missing route, a denied prerequisite, or an unresolved prerequisite that cannot be
checked in the permitted environment. A user-required Graph may remain provisional
or blocked even when PBR would produce a similar appearance.

Retain defaults for unavailable optional controls and report the visual limitation.
If a required feature fails, do not declare readiness by silently retaining defaults.
An upstream workflow's documented default-only fallback may be recorded as a
limitation; it does not prove the user's original material requirement is satisfied.

## Return and review the decision

Return one report with `stage`, `editorBuild`, reusable `evidence`, and `decisions`.
Use `stage=plan` until exact targets are established; use `binding` only for a
handoff with observed target paths.

- `provisional` means a candidate route needs capability evidence. It does not
  authorize generation or binding.
- `ready` means the selected path is supported for all required features on the
  current build. It does not mean a newly generated material passed visual review.
- `blocked` means authoring cannot proceed under the current contract and available
  capabilities. Give a concrete unblock step or explicitly state that no supported
  path is known.

Record `requiredFeatures`, `optionalFeatures`, `pbrGap`, `reason`,
`capabilityEvidenceRefs`, `verificationPlan`, and `limitations` for each decision.
Keep `pbrGap=null` when no gap is established. For graph authoring or reuse, plan to
verify the graph/material kind and identity, required visible behavior in a rendering
session, target binding, and save/reload persistence before acceptance.
Use the owning workflow's supported render handoff; headless creation alone does
not verify appearance.

Check these semantic invariants in addition to schema validation:

- Every evidence reference resolves; current-build records match `editorBuild`.
- Every `ready` decision cites current-build evidence covering every required
  feature and the selected execution path, not merely an API signature.
- `pbr_parameters` uses the PBR surface model; Graph does not imply `unlit`.
- Graph selection has an explicit user requirement, reusable graph, custom-logic
  gap, or verified PBR-path gap. Do not invent a gap to justify Graph.
- Binding handoff has exact targets; preserving a binding has observed identity.
- Required-feature failures remain visible, and blocked decisions cause no writes.

If the user changes required behavior, the Editor build changes, or binding facts
change, reassess only the affected decisions. Explain route changes with the new
requirement or evidence.

## Scene Material Binding Handoff

When the `author-scene` context contains `materialSelectionTest`, read this reference
before authoring and follow that test contract. Revisit the earlier material design
against the original goal; keep selected Graph effects whose execution is unavailable.
After assembly, map all accepted
material requirements to observed entity paths. Use one row per distinct reusable
material and collect every observed entity path using it in the same cell. Give
each material a stable name such as `flowingWater`; split incompatible material
requirements even when their names or colors are similar.
Use the complete candidate inventory and current read-only observations; do not
scan historical runs or create probe entities solely for this report.

Copy [the entity report template](../assets/shadergraph-material-entities.template.md)
to `get_editor_workspace.agentWorkspace.scratchDirectory` as
`shadergraph-material-entities.md`. Fill it and show both material tables to the user
before submitting the candidate.

- Use exactly four columns: `Material name`, `Generation requirement`, `Reason`,
  `Entity paths using this material`. Write a complete generation requirement with concrete
  requested appearance and behavior, such as flow direction, ripple variation,
  surface response, and transparency when required. Label bounded agent design choices
  and their priority; do not add unrelated effects or unsupported node names.
  List actual absolute entity paths separated by semicolons.
- In the confirmed table, include explicit user Graph requirements and evidenced
  custom-logic or RGBA-only PBR-path gaps for selected behavior. Include a selected
  optional design effect with a confirmed gap, label it optional, and retain its
  unavailable execution status. Explain the requirement and cite evidence in
  `Reason`; keep execution availability in the report notes.
- Put plausible Graph cases with unresolved PBR/Graph capabilities in the candidate
  table; state uncertainty, evidence and the focused next verification step in
  `Reason`. Unknown PBR support is not a confirmed Graph requirement.
- Include an already bound Graph only when the required behavior actually calls
  for Graph; note that it can be preserved. An existing Graph kind alone is not a
  requirement to use Graph.
- Record omitted selected effects and unmapped subjects separately rather than inventing paths. State the
  material-requirement coverage and unique mapped entity count. Say "no matches"
  only when coverage is complete and no confirmed or candidate targets exist.

A confirmed **route requirement** does not imply native execution readiness.
Submit confirmed rows needing creation or binding as `candidate.inventory.shadergraphMaterials`,
using `{name, generationRequirement, reason, entityPaths}`; use `[]` when none need work.
Preserve suitable already bound materials and keep provisional/unmapped rows in the report.
Runtime archives the table as a content reference for one autonomous material Agent.
Assembly only plans this work; [material production](material-production.md) owns Graph
creation and binding before particles. Final scene acceptance criteria remain in force.
