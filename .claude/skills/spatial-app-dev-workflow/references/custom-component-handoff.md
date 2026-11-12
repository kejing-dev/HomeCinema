# Custom Component Declaration Handoff

Use this section when the app introduces or changes a Kotlin ECS `Component` that must be authored in Spatial Editor.

## Separation of responsibilities

- `spatial-editor` owns syncing the Kotlin `Component` declaration into the editor project's `.Component/component.json` through `pico-cli editor sync component`.
- This app workflow owns app-side runtime work: imports, `registerComponent<T>()` or the current SDK registration mechanism, bundle loading, build, install, launch, and runtime verification.

Do not manually edit `.Component/component.json` from this workflow. If the Editor declaration is missing or stale, route to `spatial-editor` and resume here after it reports `added`, `updated`, or `skipped`.

## After declaration sync

- Editor visibility may require reopening the current Spatial Editor project or refreshing the component panel.
- Spatial app runtime behavior still requires app-side code to recognize the component.
- A successful declaration sync alone is not proof that the component works at runtime.
