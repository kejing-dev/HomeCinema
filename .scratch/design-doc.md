# Home Cinema · Cinema Frame · design record (pico-spatial-app-designer, revision 4)

> Gate B round 4 「改」 (2026-11-12): 「needs to be ambient - it shouldn't feel it is too eye-catchy, and it should have taste and not feel cartoonish」.
> Revision 4 replaces the six bright styles of revision 3 (Gallery, Neon Night, Washi & Wood, Holo Portal, Moss & Stone, Cosmos; archived in `.scratch/_v3-bright/` and `apps/home-cinema/design/_v3-bright/`) with five ambient wall treatments. Everything else (Shared Space only, hollow opening, manual alignment, show states from sound, sleep timer, controls window on the right) carries over unchanged.

## R4 · Styles

| Style | Look | Soft light (the one emit_* material) | Ambience | Triangles | Showing: frame L* / C* / p95 L* |
|---|---|---|---|---|---|
| Walnut Gallery 胡桃画廊 | Charcoal limewash panel; walnut shadow-box frame (4 members, grain along each), dark linen slip, 6 mm brass hairline; walnut ledge with Tripo vase + books | warm top wash (emissive map), 0.22 | quiet room tone | 6,332 | 30.1 / 7.6 / 43.2 |
| Béton 清水混凝土 | Board-formed concrete panel with tie holes; 14 cm chamfered concrete reveal; stub shelf with Tripo travertine pebble stack | warm-white top wash (uv1 emissive map), 0.20 | rain on a skylight | 3,656 | 33.6 / 3.6 / 43.8 |
| Linen Room 亚麻软包 | 24 fabric-wrapped acoustic tiles (dark greige linen, cut around the opening), walnut trim; walnut ledges with Tripo lamp + books | hidden LED line under the top trim, 0.55 | very low fireplace | 6,630 | 31.5 / 6.5 / 41.2 |
| Smoked Oak 烟熏橡木格栅 | Vertical smoked-oak slats (34 mm, 68 mm pitch) on black felt; matte black steel sight frame; shelf with Tripo vase | neutral bias light hugging the opening (emissive map on felt), 0.14 | muffled city night | 5,616 | 18.9 / 6.0 / 37.7 |
| Bronze Line 青铜细框 | Black linen museum mat + 3 cm darkened-bronze frame; no props | faint warm bias on the mat, 0.10 | none | 224 | 17.7 / 3.5 / 24.7 |

**Ambient rule** (written before rendering; `design-tools/ambient_check.py`; mask splits frame / player / room in the peripheral view: eye 1.45 m from a 1.6 m player, vertical FOV 79°, ~100° horizontal, Showing state): frame mean L* ≤ player mean L* − 15, frame mean C* ≤ 12, frame 95th-percentile L* ≤ player mean L*, and with Lights up frame mean C* ≤ 15. All five pass. Round-3 styles in the same shot: Neon Night C* 16.6 / p95 63.2, Holo Portal L* 50.2 / p95 80.0, Gallery L* 83.6 — all fail. Results: `review/renders/ambient-check.json`.

**How they were made**
- Panels, frames, ledges: `design-tools/frame-lab/lab4.js` (three.js r160, headless Chrome + SwiftShader, GLTFExporter). Real thickness, 1–20 mm bevels, frames built from four members so wood grain follows each member. Procedural 512 px colour + normal maps (walnut, smoked / light oak, limewash, board-formed concrete, linen, felt, patinated bronze), albedo kept between about 0.08 and 0.45 and chroma low. No bloom pass.
- Props: Tripo text-to-3D in the user's own Chrome session (H3.1, about 1.9 M faces each, GLB downloaded to `~/Downloads/home-cinema-tripo/`): stoneware vase, three art books, linen-shade table lamp, travertine pebble stack. Decimated with `bin/glb_decimate.py` (books 2,500, others 3,500 triangles, 512 px), then texture saturation × 0.35–0.7 and value × 0.8–0.85 (`design-tools/mute.py`) so the props do not pop.
- Why the frames are not Tripo: the 1.64 × 0.94 m opening must be an exact empty hole and the soft light must be a separate material that dims with the show; generated meshes give neither.
- Budget: ≤ 15k triangles (max 6.6k), ≤ 8 materials, colour + normal map per material at 512 px, GLB 0.4–3.3 MB (textures; KTX2 at build time is the way to get under 1 MB).

**Preview changes**: style cards 5 (3 + 2 grid), default style `walnut`, cut-outs are WebP, room stand-in lighter (normal living-room passthrough), app icon redrawn in walnut / charcoal. Strings: 「框灯」→「框上的微光」 in status, auto-show and timer texts. controlCount on the Show page: tabs (1) + style picker (1, five cards) + Start the show + Start with the sound + Align = 5 groups (10 tappables if every card counts — accepted; the cards are one picker).

**Peripheral-view check by eye**: the frame sits in the outer third of the view; no edge glows, no saturated colour; the brightest things are the brass hairline (Walnut) and the pale travertine (Béton), both well under the picture.

**Spec / audit**: `build_spec.py` → 59 nodes, 12 actions, 21 assets; `check_design_spec.py` PASS, 0 errors, 2 large-text warnings (unchanged, intended).

(Revision 3 record below; superseded where R4 says so.)

# Home Cinema · Cinema Frame · design record (pico-spatial-app-designer, revision 3)

> Gate B rework, round 2 (2026-11-10). User feedback on revision 2: 「别太老气，看下能不能用3D 的框，可以用 tripo 或者自己设计一下」「把一些好看的，不同风格的都做」.
> Revision 3 replaces the three flat CSS halls (old theatre / black box / open-air) and the seat row with six contemporary real-3D frame styles. The rest of revision 2 carries over: Shared Space only, hollow opening, manual alignment, show states from sound, sleep timer, controls on the right.

## R3 · What changed and why

| Style | Look | Theme light | Ambience | Triangles | Textures |
|---|---|---|---|---|---|
| Gallery 白廊 | Deep matte-plaster box frame, warm LED reveal, floating oak shelf with a terracotta vase and a brass knot | warm white #ffd2a0 | Gallery room tone | 9,032 | none |
| Neon Night 霓虹夜 | Gunmetal frame, magenta outer and cyan inner neon tubes, amber corner slashes, cyan floor line | magenta #ff2bd6 | City rain, distant traffic | 7,492 | none |
| Washi & Wood 和纸木格 | Hinoki posts and beams, glowing shoji panels on both sides, round paper lantern | paper amber #ffc77a | Soft rain on a roof, wind chime | 1,200 | none |
| Holo Portal 全息光环 | Three floating emissive rounded rings, glass halo, light nodes, hovering base puck | cyan #6ff6ff | Low synth pad | 12,544 | none |
| Moss & Stone 苔石 | Stacked natural stone slabs, moss cushions, fern fronds | soft green #d8f0b0 | Forest stream, birds | 8,720 | none |
| Cosmos 星海 | Deep-navy frame, star field, ringed planet, orbit line, small moon | star blue #8fb4ff | Deep space drone | 10,676 | 1 × 512×256 |

**How the frames were made**: built by hand in code, without Tripo. The generator is `design-tools/frame-lab/lab.js`, which uses three.js r160 in headless Chrome with SwiftShader WebGL.
- Every frame is a real 3D model in metres, exported as GLB to `.scratch/assets/frames/<style>.glb`, with PBR materials and emissive `emit_*` theme lights.
- Each style has three real renders (front, angled, close-up, with bloom) in `review/renders/`, plus transparent lights-up and showing cut-outs used by the Preview.

**Why not Tripo**:
- The opening must be an exact, empty 1.6 × 0.9 m 16:9 hole with nothing in it that can catch input. Generated meshes come back as closed, roughly 1.9-million-face blobs, so the hole is neither exact nor guaranteed.
- Theme lights have to be separate emissive materials so the show state can dim them. A Tripo model bakes everything into one texture.

The organic parts (stones, moss, the planet) were exported at high resolution and decimated with `bin/glb_decimate.py`:
- stones: 12,672 → 5,000 triangles;
- moss: 4,320 → 3,000;
- planet: 24,320 → 2,500, texture limited to 512.

The hard-surface parts are authored within budget, so they need no decimation. `glb_decimate.py` merges everything into one mesh with a single base-colour material, which would destroy the separate emissive theme lights.

**Budget per frame**: ≤ 15k triangles, ≤ 1 texture at ≤ 512 px, ≤ 8 materials, GLB ≤ 1 MB. All six meet it; the largest is Holo Portal at 12.5k. Only one frame is loaded at a time, which is well inside the Shared Space guideline of about 175k triangles.

**Container**:
- **Volume**: 2550 × 1500 × 450 dp. A model extent of 3.4 × 2.0 × 0.6 m maps to 750 dp per metre at the default size.
- **Controls window**: 480 × 720 dp. A 3 × 2 style grid with thumbnails replaces the hall row, and a style line under it states each style's light and ambience.
- **Removed**: the seat row and the curtains. The décor of each style now does that job.

(Revision 2 record below; superseded where R3 says so.)

## 1 · Frame

**Task**: while the user watches a video in another app (system player, PICO Video or the browser), turn the area around that window into a cinema. The app only decorates. It never plays video.

**Content form**: primarily 3D (frame, curtains, seats, lights). A small 2D control surface supports it.

**Container**: Shared Space only.
- **Volume** `frame-volume`: 2400 × 1600 × 900 dp. Transparent (no material background, base panel hidden). Uniform resize only.
- **Planar window** `controls-window`: 480 × 640 dp, placed to the right of the Volume.

**Rationale**: the frame has to coexist with another app's window. Stage would mean Full Space, and Full Space hides other apps' windows. That is documented in container-selection.md ("Full Space … hides other applications' windows") and was verified on the emulator: the player was hidden and its audio stopped. So there is no Stage, no passthrough dimming and no environment.

**Spatial value**:
- The frame has real depth: seats in front, the proscenium and curtains at the back.
- The hollow opening keeps the player visible.
- The lights change with the show.

**Repeat-use hooks** (only two):
1. Three hall styles: Old theatre, Black box, Open-air.
2. Automatic show lighting from sound, plus a sleep timer.

## 2 · Explore

| Item | Content | Size / place |
|---|---|---|
| Frame Volume (main) | Proscenium with a 16:9 hollow opening; light strip (Open-air: string lights); left and right curtains that never cross into the opening; row of six seats with a centre aisle; four aisle lights; alignment outline and align panel (Align mode only) | Volume 2400 × 1600 × 900 dp; opening 1400 × 800 dp, which fits a 1280 × 720 dp player window with margin; seats at the front-bottom, frame at the back |
| Controls window | Header (icon, name, status line). Show / Settings segment. **Show**: hall picker (3 cards), Start / End the show, "Start with the sound" switch, Align frame to player. **Settings**: sleep timer (Off / 60 / 90 / 120), hall ambience sound and volume, language menu, limits note, Exit | Planar 480 × 640 dp, right of the Volume with a 60 dp gap, bottom-aligned; never over the opening |

**Relationships**
- First launch opens Align mode.
- Show states run Lights up → Opening (4 s) → Showing → Closing (6 s) → Lights up.
- Show states are driven by `AudioManager.isMusicActive`: sound starts the show; 8 s of silence ends it. The manual button overrides.
- When the timer expires, the app runs End the show and stops the ambience. The other app keeps playing.
- The chosen hall and Volume size persist.

No TabBar, because there are only two pages in a small window. No Toolbar.

## 3 · Plan

Preview: `.scratch/preview.html` and `preview.js`, using the skill runtime snapshot `.scratch/runtime/`.

**Components**: `sui-volume`, `sui-planar-window`, `sui-attachment-panel` (material), `sui-segment-control`, `sui-button` (primary; Align uses `container-color` fillTertiary), `sui-list-item`, `sui-switch`, `sui-slider`, `sui-menu`, `sui-text`.

**Icons** (ICON 7.0): ic_play, ic_sun, ic_volume_high, ic_expand, ic_check, ic_playback_timer_fill, ic_film, ic_globe, ic_arrow_down, ic_arrow_exit_door.

**Assets**: `assets/app-icon.svg` and the hall thumbnails `assets/hall-{theatre,blackbox,openair}.svg`. All are original.

**3D**: every model is `assetStatus: to-create` and is recorded in `scene-design-notes`. Ambience loops are also to-create; the CC0 library has no hum or crickets, so they will be synthesized locally at build.

**What the Preview only approximates**:
- the passthrough room (beige scenery);
- the other app's player (a dark placeholder labelled "Other app");
- depth (flat front view);
- glow (CSS shadows);
- the language menu, which is drawn at 100 % while the room is zoomed to 50 %.

## 4 · Critique (preview-review)

Screenshots are in `.scratch/review/` and `review/gallery/`.

| # | Finding | Fix | Recheck |
|---|---|---|---|
| C1 | Closed curtains over the opening would cover the player and could block rays to its play button. Auto start needs sound, and sound needs a press on play, so the user could get stuck | Curtains never cross the opening; the show animates curtain width outward only | s5–s8 ✓ |
| C2 | Seat tops could cover the player's control bar | Seats sit below the opening's bottom edge (y ≥ 1330 dp, opening bottom 1100 dp) | s1 ✓ |
| C3 | "Align frame" had the same weight as "Start the show" | Align is now a secondary (fillTertiary) button | p1 ✓ |
| C4 | Screenshots caught transitions halfway | Added a `still=1` preview-only switch | s2, s3 ✓ |
| C5 | The language menu was clipped by the planar window and then mispositioned by the zoom | Menu moved to a sibling of the room, as the Menu README advises | p4 ✓ (scale is a preview artefact) |
| C6 | The room cannot be darkened, so Showing is low-contrast | Accepted platform limit; stated in the Settings limits note and the PRD | — |

**Not verified in Preview**: depth layering, real glow on a bright passthrough, ray pass-through in the hollow opening, and Volume resize handles. These are real-device acceptance items in the PRD.

## 5 · Write Spec

**R3**: `build_spec.py` produces 62 nodes, 12 actions and 25 assets (6 GLB models, 12 preview cut-outs, 6 thumbnails, 1 icon). The checker returns PASS with 2 warnings, the same large-text ones as below.

**R3 audits**: initial run 412 match / 3 mismatch; post-action run (align, Settings, zh, Cosmos) 357 match / 3 mismatch. They are the same 3 known mismatches as below. One gap mismatch (14 vs 16 dp) was found and fixed in Spec.

`design-tools/build_spec.py` produces `.scratch/design-spec.json`: 59 nodes, 12 actions, 4 assets, 2 surfaces and 4 states.

`python3 scripts/check_design_spec.py …/design-spec.json --target ~/Downloads/home-cinema --json` returns **PASS**, with 0 errors and 2 warnings.
- The first run had 6 errors: list-valued dp, the unknown appearance field `selected`, and per-hall widths as an object. All are fixed in the builder.
- The 2 warnings are large-text on `ctl-title` and `align-title` (titleLarge). The emphasis is intended.

## 6 · Consistency Review

`review/audit-preview.js` was run in headless Chrome, served from http://127.0.0.1:8792.

**Initial run**: 388 match, 3 mismatch, 143 unverified (`review/audit-initial.json`).

**Post-action run** (align on, Settings, zh): 388 match, 3 mismatch, 124 unverified. Every expected visibility for enter-align-mode, switch-panel-page and exit-app matches (`review/audit-align-settings.json`).

The 3 mismatches are known and accepted:
1. `$preview.url`: the query string used to preset the state.
2. `lang-menu.parent`: the Menu is a DOM sibling per the Menu README, while Spec records it under `set-list` with `anchor-node-id`.
3. `ctl-root.surface.owner`: the audit expects a companion planar surface to sit in the Volume's DOM. This is the same owner-mapping issue reported in v1.

The unverified items are native behaviour, hidden-state geometry and layout relationships. They need author or real-device review.

## Open items

These are real-device checks, listed in the PRD acceptance tests:
- hollow opening ray pass-through;
- player window inside or behind the Volume, and which draws in front;
- `isMusicActive` on pause;
- emissive glow readability in a bright room.

The ambience loops and all 3D models are to-create in Compose App, through Spatial Editor or procedural meshes.
