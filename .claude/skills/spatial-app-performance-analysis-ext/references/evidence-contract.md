# RenderDoc × Perfetto Evidence Contract

RenderDoc XML describes one captured frame or capture session history. Perfetto/FastPerf describes a time window. They complement each other but normally do not share a frame identity.

## Provenance

Record RenderDoc path, size, parse time, API/driver, app/engine metadata, live artifact paths, package/device, capture start/duration, sample count, and whether a shared frame/timestamp key exists. Without a verified key, use `relative_scope_only`.

## Evidence levels

| Level | Meaning |
|---|---|
| `strong_cross_support` | Same metric family, verified scope, close magnitude or shared key. |
| `mechanism_support` | RenderDoc structure plausibly explains a live symptom, but no same-frame timing binding. |
| `independent_candidate` | A signal exists in one source and is not bound to the other. |
| `not_comparable` | Different identity/scope, missing provenance, or conflicting build/scene. |

## Safe calculations

- Raw triangles: `sum(indexCount) / 3`.
- Instanced triangle upper bound: `sum(indexCount * max(instanceCount, 1)) / 3`.
- Instance total: `sum(max(instanceCount, 1))`.
- Barrier density: `pipeline_barrier_count / indexed_draw_count`; this is API-event density, not GPU time.
- Declared image size: sum parsed `vkCreateImage` memory requirement `size`; do not call it resident VRAM.

## Guardrails

- High draw/triangle/texture counts need same-window GPU timing or a controlled A/B before `gpu_geometry_complexity` can be likely or confirmed.
- GPU usage is supporting evidence, not a root-cause category by itself.
- GC/low-memory markers need target-process ownership and overlap with the abnormal frame window.
- Binder client waits need callee-side lock, queue, runnable, or server-work evidence before calling service contention.
- API event counts are not duration; a high count can be initialization or capture overhead.

## Reference HTML

Reuse a reference report's structure, terminology, colors, charts, and action organization only after extracting its values. Never copy old measurements into a new report. State which reference measurements were excluded.
