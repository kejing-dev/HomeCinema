# Home Cinema — design record (pico-spatial-app-designer, direct execution)

Request: eye-and-hand home cinema player for the user's own Emby / Jellyfin / NAS (WebDAV) / headset videos; 3D poster wall; big-screen cinema with resume, subtitles, audio tracks. Bilingual (zh-CN / en). Original name and UI. No bundled or recommended third-party content.

## 1 Frame
```
Frame Design Record
├─ User task: pick something from my own library and watch it on a big screen, continuing where I stopped
├─ Spatial value: posters become small 3D objects (layered depth) that make browsing tactile; playback gets a cinema-scale screen
├─ Content form: Library = primarily 3D posters with supporting 2D (headers, lists, settings); Cinema = 3D screen + 2D control attachment
├─ Container: Library = Volume (Shared Space, 1280 × 760 × 360 dp); Details = Subwindow of the Volume; Cinema = Stage (Full Space)
└─ Rationale: posters need real depth beyond Planar's default; the library must coexist with other apps (Shared Space);
              a 6 m screen and a dark room are environment-level, so playback enters Full Space Stage and leaves it on exit
```

## 2 Explore
- TabBar (window-attached, 4 stable destinations): Home · Library · Sources · Settings. Each keeps its own layout and scroll state.
- Home: header (title, source summary, Search, Refresh) · Continue watching (4 cards: backdrop 208×117, progress, time left) · Recently added (6 × 3D posters 176×264 dp).
- Library: header + SegmentControl All/Movies/Shows · scrolling grid of 3D posters.
- Sources: list of connected sources (demo library built in; Emby/Jellyfin, WebDAV, headset folder) + Add source → Sheet (type Option ×4; server / username / password; local → Choose folder). Copy states “only media you own”.
- Settings: Language (menu: Follow system / 简体中文 / English) · 3D poster depth (SegmentSlider Off/Subtle/Standard/Strong) · Resume where you left off (Switch) · Preferred subtitles · Preferred audio · Clear watch history (AlertDialog) · About · **Exit Home Cinema** button.
- Details Subwindow (360 × 760, right of Volume, opened by poster/card select, closed by its leading close): backdrop 296×167, title, chips (year, runtime, genre, quality), overview, audio + subtitle defaults, episodes for series, Resume hh:mm / Play from start.
- Cinema Stage: dark virtual theater (StageStyle.Full; toggle to dimmed passthrough Mixed), 16:9 screen entity with VideoMaterial, 6 m wide at 7 m (Small 3 m / Medium 6 m / Large 10 m), subtitles on the screen; control AttachmentPanel (Regular glass, ~900 × 180 dp) 0.9 m in front, 0.35 m below eye level, tilted 20°, fixed in scene, fades after 5 s idle. Controls: title + time, Exit cinema, seek slider, −15 s / play-pause / +15 s, volume, subtitles menu (Off / tracks / Load subtitle file…), audio track menu, screen size menu, Dim the room toggle.
- 3D poster (offline, no AI): three planes from data the media server already provides — Backdrop image (back, blurred, ≈2 cm behind), Primary poster plate (2:3, ≈6 mm edge thickness), Logo image (transparent title art, ≈2.5 cm in front; falls back to rendered title text). Hover by controller ray / hand ray / gaze tilts ≤ 8° toward the pointer; depth scales with the Settings level.
- Factory interaction rules covered: bilingual; Exit app in Settings; panels never overlap the 3D subject (Subwindow beside the Volume, cinema panel below the screen); all controls are standard SpatialUI / entities with hover + select so controller ray, hand ray and gaze+pinch all work; no “bring window back in front” promise in Shared Space; no paid / private-key API anywhere.

## 3 Plan
Preview `preview.html` (+ `preview.js`, runtime snapshot `runtime/`, assets `assets/`). Icons from ICON 7.0 catalog (ic_home, ic_film, ICON7-S029, ICON7-A117, ic_search, ic_refresh, ic_player_play/pause, ic_skip_back_15/forward_15, ic_volume_high, ic_message_square_text, ic_headphones, ic_expand_window, ic_moon_stars, ic_arrow_exit_door, ic_globe, ic_layers, ic_history, ICON7-S280, ICON7-A007, ic_cloud, ic_computer, ic_memory_card, ic_cross, ic_plus, ic_check). No generic gear / subtitles / language glyph exists in the catalog: used ICON7-A117 (pico settings), ic_message_square_text, ic_globe.
Artwork: 8 original demo titles generated procedurally (`design-tools/gen_demo_art.py`): poster, backdrop and logo layer each, plus app icon. No third-party imagery.

## 4 Critique (screenshots in review/)
Checked home, library (zh), sources + sheet, settings (zh), details (en / zh, series), cinema (en / zh).
Fixed during critique: second translated attribute on the same element was lost (Audio supporting stayed English) → per-attribute i18n keys; Sheet local-storage note visible with Jellyfin selected (`display:flex` beat `[hidden]`) → global hidden rule; blurred back layer too heavy → reduced; continue-watching progress invisible on light glass → interaction / fillTertiary colors.
Unverified (Web cannot show): real head-motion parallax, native Volume clipping of the tilted posters, VideoMaterial playback, passthrough dimming, TabBar native attachment, hover on 3D entities with all three input types.

## 5 Write Spec
`design-spec.json` generated from the Preview by `design-tools/build_spec.py` (235 nodes, 34 actions, 26 assets, dataCases.titles, localizedText per node).
`python3 scripts/check_design_spec.py .scratch/design-spec.json --target <project> --json` → PASS, 0 errors, 9 warnings.
Warning disposition: `large-text` ×9 (page headlines 24–32 sp, section titles, cinema title, on-screen subtitle line) — intentional: page headlines and a subtitle line read at cinema distance.

## 6 Consistency Review
`scripts/audit-preview.js` in the running Preview (headless Chrome, `?audit=`):
- initial: match 1057 / mismatch 1 / unverified 492 — the mismatch is the Preview URL carrying the audit query string.
- details-harbor (after selecting Harbor Lights): match 1080 / mismatch 2 / unverified 542 — URL query, and `detail-window surface.owner` expected `vol-root` vs actual `library-volume`: the audit maps a Subwindow owner to the owner surface's root node, but a Volume's shell id is the surface id (runtime README requires `for` = window id). Recorded as a CLI feedback item; Spec left as documented.
Reports: review/audit-initial.json, review/audit-details.json.

## Delivery
`.scratch/design-doc.md`, `.scratch/design-spec.json`, `.scratch/preview.html`, `.scratch/assets/`, `.scratch/runtime/` (reference snapshot), single-file copy for review: factory `apps/home-cinema/sample.html`.
Status: waiting for the user's design confirmation (factory gate B) before implementation.
