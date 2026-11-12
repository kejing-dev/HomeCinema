# Shader Graph Material Entity Report

Scene path: <actual path>

Scene fingerprint: <current fingerprint>

Editor version: <actual version, or unknown>

This report records material selections and binding targets. After assembly, submit
confirmed rows needing creation or binding as `candidate.inventory.shadergraphMaterials`,
using `name`, `generationRequirement`, `reason`, and `entityPaths`. A dedicated material
Agent creates and binds these materials before the main workflow produces particles.

Design materials before submitting SceneSpec. Review the original scene goal for
surfaces such as water, glass, and emission. Label user requirements or Agent design
choices and their priority in each generation requirement. Retain selected Shader
Graph effects whose execution is unavailable, marking them unimplemented; do not
report no targets solely because an effect cannot yet be produced.

New default PBR currently supports only RGBA settings. When a required effect exceeds
RGBA and the default appearance, explain the capability gap in the reason. Preserve
suitable existing materials first.

## Confirmed Shader Graph Requirements

| Material name | Generation requirement | Reason | Entity paths using this material |
| ------------- | ---------------------- | ------ | -------------------------------- |

<Use one row per reusable material with a stable name such as flowingWater.
Describe complete effect details in the generation requirement. Explain the specific
PBR gap or explicit user requirement and cite evidence in the reason. List all observed
absolute entity paths for the material in the final column, separated by semicolons.
Write "no confirmed targets" when none exist.>

## Candidates Requiring Verification

| Material name | Generation requirement | Reason | Entity paths using this material |
| ------------- | ---------------------- | ------ | -------------------------------- |

<Aggregate by material. Explain the unresolved question, current evidence, and next
verification step in the reason. Write "no candidates" when none exist. Unknown PBR
support is not a confirmed capability gap.>

## Coverage

- Reviewed material requirements: <reviewed count / total count>
- Unique mapped entities: <count; count repeated instances separately>
- Unmapped subjects: <IDs and reasons, or none>
- Requirements preserving existing materials or using PBR: <count and brief rationale>
- Graph execution: <per material: preserve binding, delegate to material production, or verify>
- Conclusion: <confirmed / candidate / incomplete mapping; state "no Shader Graph needed" only after complete coverage with no targets>

<Replace all prompts before reporting. Retain evidence sources and unresolved questions.>
