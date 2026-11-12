# SGS Supplied Assets

When the user explicitly requests SGS asset supply, use `start_3d_generation_workflow` with root
input `spatialcraft.spatial-3d-generation-input/v2`, an explicit `assetSupply` policy (`provider`,
`maxSubmissions`, and `fallbackPolicy`), and the Editor backend. The current Root and Editor
packages are version 7.0.0, while Editor authoring still uses the v6 contract. `inputs` may identify
text-to-3D, image-to-3D, or explicit Editor gaps by `subjectId`. SceneSpec must preserve those IDs,
while orchestration owns model instance counts. The managed supply module creates and downloads SGS
tasks; do not create the same task separately through the CLI.

Do not retry an unknown submission or convert it to fallback generation. Import each source model
into Editor and complete six-axis screenshots, metadata, and review before scene orchestration.
This phase supports only self-contained GLB handoff. If a source-model review fails, report it and
require the caller to start a new supply Run explicitly. Do not use a revision prompt to resubmit
the cloud task automatically or replace it with Editor generation.

Continue through the root response's `next.tool` and `next.arguments`. Requests without SGS supply
still use the compatibility facade. Use the standalone `pico-sgs-cli` Skill for text-to-image and
image-to-image requests; this phase does not deliver an image directly as a model.
