# RenderDoc XML Extraction Notes

Accept any RenderDoc-exported `.xml` filename; the filename basename is not significant. A binary `.rdc` capture is not directly supported by this skill. Ask the user to open it in RenderDoc and manually export XML before analysis.

The common root is `<rdc><header>...<chunks>...`. Each Vulkan API event is a `<chunk name="...">` with nested typed fields.

Important fields:

- `vkCmdDrawIndexed`: `indexCount`, `instanceCount`, `firstIndex`, `vertexOffset`, `firstInstance`.
- `vkCmdDispatch`: `x`, `y`, `z`.
- `vkCmdPipelineBarrier`: command-buffer and barrier counts; nested records can exceed top-level API-call count.
- `vkCreateImage`: `width`, `height`, `depth`, `mipLevels`, `arrayLayers`, `samples`, `format`, and nested memory requirement `size`.
- `vkCreateBuffer`: nested memory requirement `size`.
- State calls: graphics/compute pipeline creation, pipeline binds, descriptor binds, vertex/index buffer binds.

Do not assume numeric `format` values are self-describing, `size` is resident VRAM, RenderDoc timestamps are wall-clock timestamps shared with Perfetto, or every nested barrier is a unique GPU stall. Missing fields must be null/zero with a limitation.
