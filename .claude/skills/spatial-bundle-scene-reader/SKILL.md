---
name: spatial-bundle-scene-reader
description: >-
  Read an existing Spatial Editor .scenes.json and .bundle handoff on demand.
  Use when inspecting packed scenes, entry scenes, entity names, parent scopes,
  bounded subtrees, transforms, or manifest-to-runtime addressing.
  NOT for scene authoring or repackaging (spatial-editor), SDK component API
  guidance (spatial-sdk-guideline), Kotlin Entity edits (spatial-sdk-scene-builder),
  or complete app integration (spatial-app-dev-workflow).
license: 'Apache-2.0'
---

# Spatial Bundle Scene Reader

## When to Use

- A project already contains co-located `<name>.bundle` and `<name>.scenes.json`, and the question
  asks which scenes are packed, which scene is the entry, or whether an entity exists.
- Inspecting names, parent scopes, transforms, or bounded subtrees in an existing manifest.
- Mapping manifest addresses to runtime traversal as a subordinate inspection step in
  `spatial-app-dev-workflow`.

## When NOT to Use

- Authoring, modifying, or repackaging scene content — use `spatial-editor`.
- SDK component API facts or runtime component diagnosis — use `spatial-sdk-guideline`.
- Implementing or editing Kotlin Entity loading, hierarchy, or behavior — use
  `spatial-sdk-scene-builder`.
- Complete integration, build, or APK validation — keep `spatial-app-dev-workflow` as the enclosing
  workflow; this reader only supplies manifest facts.

## Manifest Facts

Verified against a managed Workflow pack (`detail: "full"`, 1 scene, 2135 entities, 4.1 MB):

| Level  | Fields                                                                                                                               |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| Top    | `schemaVersion` (`"0.1"`), `scope` (`bundle_scenes`), `activeScenePath`, `detail`, `sourceTool`, `source`, `scenes[]`, `warnings[]`  |
| Scene  | `id`, `name`, `guid`, `sourcePath`, `bundlePath`, `container`, `entityCount`, `rootCount`, `hierarchy[]`, `entities[]`, `warnings[]` |
| Entity | `path`, `parentPath`, `name`, `entityId`, `protocolEntityId`, `type`, `transform`, `components[]`, `resources`, `bounds`, `active`   |

`sourcePath` is the scene source (for example `Sources/Scenes/Room.usda`). `activeScenePath` is
the entry scene. `hierarchy` is a nested tree; `entities` is the same set flattened, so either can
answer structural questions.

## Hard Rules

1. **`<name>.scenes.json` is the only structural source.** Never infer structure from the
   `.bundle` binary, and never unpack it to look for entities.
2. **Never read the manifest whole.** A 2135-entity scene is ~4 MB (roughly one million tokens).
   Always run a bounded `jq` query and cap the output.
3. **Absent fields are unknown, not empty.** The current export reports `[]` for `components` and
   `null` for `bounds`, but the schema is additive. Check presence and content with a bounded query
   before concluding a field is unavailable. An absent or empty manifest component list does not
   prove that the loaded entity lacks components. Inspect runtime state before adding or replacing
   components, and use SDK references to interpret any exported component data.
4. **`entityId` and `protocolEntityId` are manifest-scoped, not runtime identities.** They change
   between runs. Never carry them into application code.
5. **`path` is manifest notation, not a runtime lookup key.** The SDK exposes no path-based
   lookup; resolving a path means walking one level at a time.
6. **Sibling names are unique; global names are not.** `DefaultMaterial` appeared 1035 times in a
   single scene. An unscoped name query is ambiguous by design.
7. **A manifest always pairs with a bundle of the same basename.** Verify `<name>.bundle` and
   `<name>.scenes.json` both exist. When `<name>.provenance.json` is present — the packer names it
   after the bundle, not as a bare `provenance.json` — compare its `bundle.digest.value` /
   `bundle.scenesDigest.value` (sha256) against the files. A sibling `checksums.json` carries the
   same values.
8. **Validate the schema before structural queries.** Require `schemaVersion == "0.1"`,
   `scope == "bundle_scenes"`, and a non-empty `scenes` array. Stop on missing or incompatible
   metadata. Report unavailable entity or hierarchy data instead of treating it as an empty scene.
9. **Select one scene before resolving entities.** Identify it by `sourcePath` and require exactly
   one scene match. A manifest path alone is insufficient across multiple scenes.

## Addressing Model

An entity address is the ordered chain of **child names from the scene root**, such as
`Root/BuildingA/Door`. Because siblings never share a name, each segment resolves to exactly one
child at its level, so the chain is deterministic even though the same name may recur in other
branches.

Consequences:

- Resolve **per level**, not by passing the whole path to a lookup function.
- An address is only meaningful relative to a selected scene and declared root scope. Always state
  the scene `sourcePath` and root path used for the lookup.
- A name alone is insufficient input. Always pair it with a parent scope, or accept that the
  answer is a candidate set.
- Zero matches and multiple matches are both failures; report them instead of picking one.

## On-Demand Queries

Set the file once. Run these examples in the same Bash session. The wrapper limits each successful
output to 16,000 bytes; if exceeded, narrow the query or paginate before retrying. It reports the
limit instead of printing a truncated JSON document.

```bash
M=/path/to/app/src/main/assets/Room.scenes.json

jq -e '.schemaVersion == "0.1" and .scope == "bundle_scenes"
  and (.scenes | type == "array" and length > 0)' "$M" >/dev/null || {
  printf '%s\n' 'Missing or incompatible scene manifest metadata.' >&2
  exit 1
}

manifest_query() {
  local filter="$1"
  shift
  local LC_ALL=C
  local output
  output="$(jq -c --arg scene "${SCENE:-}" "$@" '
    def selectedScene:
      [.scenes[] | select(.sourcePath == $scene)]
      | if length == 1 then .[0] else error("Scene selection must match exactly once") end;
    def sceneEntities:
      selectedScene.entities
      | if type == "array" then . else error("Entity data unavailable") end;
    '"$filter" "$M")" || return 1
  if [ "${#output}" -gt 16000 ]; then
    printf '%s\n' 'Query output exceeds 16000 bytes; narrow or paginate it.' >&2
    return 1
  fi
  printf '%s\n' "$output"
}
```

Scene inventory and entry scene, with bounded pages and warnings:

```bash
manifest_query '{schemaVersion, scope, detail, activeScenePath,
  sceneCount: (.scenes|length),
  warningCount: ((.warnings // [])|length), warnings: (.warnings // [])[0:5]}' || exit 1
manifest_query '{sceneCount: (.scenes|length), offset: $offset,
  scenes: [.scenes[$offset:($offset + 10)][] |
    {name, sourcePath, entityCount, rootCount}]}' --argjson offset 0 || exit 1
```

Increase `offset` to read later pages. Select the user-specified scene by setting `SCENE` to its
inventory `sourcePath`. Otherwise use `activeScenePath` when present, then the first scene only
when the entry field is absent. An invalid entry path is a failure; do not silently fall back.

```bash
SCENE="$(jq -er '.activeScenePath // .scenes[0].sourcePath' "$M")" || exit 1
manifest_query 'selectedScene | {name, sourcePath, entityCount, rootCount}' || exit 1
```

Locate a direct child inside one parent scope. Exact `parentPath` matching prevents a nested
descendant with the same name from being mistaken for a sibling:

```bash
manifest_query '[sceneEntities[] | select(.name == $name and .parentPath == $parent)
  | {name, path, parentPath, transform}]
  | {scene: $scene, count: length, matches: .[0:10]}' \
  --arg name "Door" --arg parent "Root/BuildingA" || exit 1
```

Check a name across the selected scene to report candidates:

```bash
manifest_query '[sceneEntities[] | select(.name == $name) | {path, parentPath}]
  | {scene: $scene, count: length, sample: .[0:5]}' --arg name "Lamp" || exit 1
```

Extract a subtree, including the root, with depth measured relative to that root. Require the root
to exist exactly once before returning the bounded result:

```bash
manifest_query 'sceneEntities as $entities
  | [$entities[] | select(.path == $root)] as $roots
  | if ($roots|length) != 1 then error("Subtree root must match exactly once")
    else [$entities[] | select(.path == $root or (.path|startswith($root + "/")))
      | select(((.path|split("/")|length) - ($root|split("/")|length)) <= $maxDepth)
      | {path, name, type, transform}]
      | {scene: $scene, count: length, items: .[0:40]}
    end' --arg root "Root/Vegetation" --argjson maxDepth 3 || exit 1
```

Read a selected top-level hierarchy root with a bounded child list:

```bash
manifest_query 'selectedScene.hierarchy
  | if type != "array" then error("Hierarchy data unavailable") else . end
  | [.[] | select(.path == $root)]
  | if length != 1 then error("Hierarchy root must match exactly once") else .[0] end
  | {scene: $scene, name, path, childCount: ((.children // [])|length),
    children: [(.children // [])[0:20][] | {name, path}]}' \
  --arg root "Root" || exit 1
```

If `jq` is unavailable, use a `node -e` reader that prints only the selected fields. Do not fall
back to opening the file with a general file reader. Apply the same schema checks, unique scene
selection, result limits, and byte budget.

## Mapping a Manifest Path to the Runtime

A manifest path starts above the entity the app actually loads. In the verified sample the chain is
`Root/FloatingVoxelIsland/Vegetation/...`: `Root` is the manifest container segment and the next
segment is the scene's own root entity. `bundle.loadModel(...)` returns an entity somewhere in that
chain, so pass that entity's manifest path as an explicit scope and require the target path to sit
under it. Never locate the loaded root by matching its name: another branch can reuse the same name,
and the first match would silently resolve to the wrong entity.

Before calling the resolver, establish which manifest node corresponds to the `loadModel` result
using the selected scene, the SDK loading contract, and runtime inspection. Verify the scoped child
chain and require exactly one match per level. Do not assume that the returned wrapper corresponds
to the scene root, and do not select its first child by index. If the correspondence cannot be
established, stop and report the unresolved loaded-root scope.

```kotlin
val bundle = AssetBundle.load("asset://.../FloatingVoxelIsland.bundle")
val loadedRoot = bundle.loadModel("FloatingVoxelIsland")

// rootPath must be verified as the selected scene's manifest path of loadedRoot.
// It may refer to a wrapper; do not infer it from the model name or child order.
fun resolveFrom(loadedRoot: Entity, rootPath: String, targetPath: String): Entity? {
    val root = rootPath.trim('/')
    val target = targetPath.trim('/')
    if (root.isEmpty() || target.isEmpty()) return null
    if (target != root && !target.startsWith("$root/")) return null  // outside the loaded subtree
    var current = loadedRoot
    for (segment in target.removePrefix(root).trim('/').split('/').filter { it.isNotEmpty() }) {
        val matches = current.getChildren().filter { it.name == segment }
        if (matches.size != 1) return null                            // zero or ambiguous both fail
        current = matches.single()
    }
    return current
}
```

Do not substitute `entityId` for traversal, and do not assume a path-string lookup exists because the
manifest uses paths. Verify the child accessor against the project's SDK version through
`spatial-sdk-guideline` before writing code.

## Pairing Manifest Facts with the SDK

The manifest describes **structure only**. Use this table to connect each fact to the SDK surface
that consumes it, then read the owning reference rather than re-deriving the API here.

| Manifest fact                             | Runtime counterpart                                                                                                              | Read more                                         |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| `<name>.bundle`                           | `AssetBundle.load("asset://.../<name>.bundle")`; hold it and close it explicitly                                                 | `spatial-sdk-guideline` › resources-loading       |
| `scenes[].sourcePath`                     | `bundle.loadModel(...)` argument: take the suffix after `/Scenes/` and drop `.usda`                                              | `spatial-sdk-guideline` › resources-loading       |
| `activeScenePath`                         | Which scene to load first; otherwise use `scenes[0]`                                                                             | this skill                                        |
| `container` (`Stage` / `WindowContainer`) | Container choice and `spaceRequirement`; `Stage` is Full Space only                                                              | `spatial-sdk-guideline` › containers              |
| `rootCount` and the scene root entity     | Verify the loaded wrapper/root correspondence; resolve children within that scope with exactly one match per level               | `spatial-sdk-guideline` › resources-loading       |
| `path`                                    | Level-by-level `getChildren()` matched on `name`; never a runtime lookup key                                                     | this skill                                        |
| `name`                                    | `Entity.name`; siblings are unique, so one match per level                                                                       | `spatial-sdk-guideline` › ecs-and-entities        |
| `transform`                               | Local `TransformComponent` on that entity; parent-relative, rotation as a quaternion                                             | `spatial-sdk-guideline` › ecs-and-entities        |
| `active`                                  | Runtime enabled/visibility state for that entity                                                                                 | `spatial-sdk-guideline` › ecs-and-entities        |
| `components`                              | Absent or empty means runtime state is unknown; inspect it first, preserve existing components, and add only what the task needs | `spatial-sdk-guideline` › interaction-hit-testing |
| `resources`                               | When absent or empty, load materials and assets through the bundle; when present, resolve the listed assets first                | `spatial-sdk-guideline` › resources-loading       |
| `entityCount`                             | Post-load sanity check on the resolved subtree                                                                                   | this skill                                        |

Typical sequence:

1. Load the chosen scene and verify the loaded root's manifest correspondence.
2. Resolve the target within that verified scope; stop on zero or multiple matches.
3. Inspect the target's runtime components through the owning SDK APIs. A manifest's empty
   `components` list is not evidence for removing, replacing, or recreating a collider.
4. Preserve existing component configuration. Add only missing components required by the requested
   behavior, following `spatial-sdk-guideline` › interaction-hit-testing or physics-collision.

Keep the boundary: this skill reads the handoff, `spatial-sdk-guideline` owns API facts,
`spatial-sdk-scene-builder` owns Kotlin scene edits, and `spatial-app-dev-workflow` owns app
integration. When a needed fact is absent from the manifest, say it is absent and route to runtime
ECS inspection or editor-side authoring — never invent the field.

## What the Current Export Cannot Answer

These limits belong to the current schema, not to the manifest format. Re-check field presence
before treating a row as unavailable; a later export may add it.

| Question                                | When the field is absent                     |
| --------------------------------------- | -------------------------------------------- |
| Which components an entity has          | Editor live query, or runtime ECS inspection |
| Physics / collision / interaction setup | Editor live query, or runtime ECS inspection |
| Material and Shader Graph parameters    | Editor live query, or runtime material APIs  |
| Mesh and texture resources              | Resolve via asset loading at runtime         |
| Entity bounds                           | Compute from runtime components              |

Names that look semantic (`*Light`, `*Collider`) are not evidence: in the current export every entity
reports `type: "Entity"`.

## Verification

Before reporting a resolved entity, confirm all of the following:

1. `<name>.bundle` and `<name>.scenes.json` both exist and share a basename.
2. `sha256` of both matches `<name>.provenance.json` (`bundle.digest`, `bundle.scenesDigest`) or a
   sibling `checksums.json` when either is present.
3. Schema metadata is compatible, the selected `sourcePath` matches exactly one scene, and entry
   selection agrees with what the app actually loads.
4. The loaded root's correspondence is verified and the resolved chain ends at exactly one entity;
   report zero or many as a failure with candidates.
5. Missing or empty exported component data is reported as unknown runtime state. Attribute any
   available data to its actual source and verify runtime components before proposing mutations.

## Related Skills

- `spatial-app-dev-workflow` — owns app integration and the build/APK check.
- `spatial-sdk-guideline` — owns SDK API facts and component contracts.
- `spatial-sdk-scene-builder` — owns Kotlin Entity implementation.
- `spatial-editor` — owns authored scene changes and repackaging.
