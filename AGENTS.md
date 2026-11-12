# Home Cinema (io.embodit.homecinema) — agent notes

Ambient cinema frame (profile B29): a transparent Shared Space Volume with one of five real-material wall treatments
around a hollow 16:9 opening, plus a Planar controls window to its right. It never plays video; another app's player is
dragged into the opening by hand. Design: factory `apps/home-cinema/design/` (design-spec.json R4, design-doc.md),
PRD `apps/home-cinema/prd.html` v4, feasibility `apps/home-cinema/feasibility.md`.

## Build
- `export JAVA_HOME=~/.pico/primer-cli/jdk/jdk-21.0.13+9/Contents/Home && ./gradlew --offline assembleDebug testDebugUnitTest`
- SDK BOM 6.1.9 (Volcengine maven), same gradle setup as qubic-tower. APK `app/build/outputs/apk/debug/app-debug.apk`, versionName 0.1.2.
- Models: `design-tools/home-cinema_pack_glb.py <design glb> app/src/main/assets/models/frame_<style>.glb` (bakes
  emissive strength, PNG→JPEG, OPAQUE, cuts the linen backing open). Ambience: `design-tools/home-cinema_rain_loop2.py` (beton rain), `design-tools/home-cinema_amb_loop.py` (walnut room tone, linen fireplace, slats city night; sources in factory `apps/home-cinema/build/sound-sources.md`).

## Structure
- `Main.kt`: DefaultWindowContainer = frame Volume (manifest 2.16 x 1.27 x 0.6 m, transparent, uniform resize) +
  WindowContainer `CinemaControls` Planar 480 x 760 dp (opened once the frame model is in, or after 1.5 s), `Placement.right(frame)`.
- `domain/Show.kt`: ShowMachine (Lights up → Opening 4 s → Showing → Closing 6 s; auto from sound; manual override until
  the next sound edge), SleepTimer, Style, Settings. `domain/FrameLayout.kt`: geometry (opening, attachments, fit scale).
- `platform/App.kt`: Graph (50 ms ticker, 1 s sound poll, exit), `Stores.kt` (settings, SoundProbe, AmbiencePlayer),
  `WindowCtl.kt` (open / reopen / close all), `DebugReceiver.kt`.
- `scene/FrameScene.kt` + `FrameScreen.kt`: GLB load (starts at first composition, not after `initial`) + 1.2 s cross-fade;
  lighting per style in `domain/Lighting.kt`: constant key light + soft front wash light + `emit_*` emissive, the last two
  scaled by the show level (lux-scale intensities). Logs `STARTUP frame <style> visible N ms after process start`, `LIGHT ...`, dashed align guide, attachments (align card, [Open controls] chip).
- `ui/ControlWindow.kt`: native TabBar Show / Settings, exit confirm page.

## Debug broadcast
`adb shell am broadcast -a io.embodit.homecinema.DEBUG -p io.embodit.homecinema --es state <cmd> [--es v <value>]`

| cmd | effect (same Graph function as the UI) |
|---|---|
| lights-up / first-launch-align / showing / settings | design states[] |
| show · toggle-show · style <walnut/beton/linen/slats/bronze> · style-next · style-prev | Show page |
| auto on/off · timer <min> (1 = test) · ambience on/off · volume 0..2 · mute on/off · lang en/zh/system | settings |
| align · align-done · exit-confirm · exit-cancel · exit · reopen · close-controls · open-controls | windows / exit |
| light base=..,soft=..,emit=.. / off | emulator light calibration only (overrides `Lighting.of(style)`) |
| sound on/off/auto | force the "other app is playing" reading (goes through ShowMachine.onSound) |
| fresh · dump | reset to first launch · log a DUMP line |

## Screenshot list (QA)
first launch (align, zh/en) · each style lights-up + showing (camera moved back 1.6 m) · Show page zh/en, Showing with
sleep timer line · Settings zh/en · exit confirm zh/en · controls closed → [Open controls] chip · with the system video
player playing (`am start -a android.intent.action.VIEW -d file:///sdcard/Movies/hc-test.mp4 -t video/mp4 -p com.picoxr.videoplayer`).

## Real input on the emulator
`pico-cli interact` sees only the focused window; query first, reopen the controls window if it returns nothing.
Real-device items: rays through the opening to the player, draw order, bright room, pause → closing, three inputs.
