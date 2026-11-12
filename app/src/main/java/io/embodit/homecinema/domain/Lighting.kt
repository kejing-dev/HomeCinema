package io.embodit.homecinema.domain

/**
 * Per-style lighting of the frame (QA #1 K1 "dark block" + soft light invisible on Linen / Smoked Oak / Bronze).
 *
 * - [baseLux]: a constant key light (Spatial SDK light intensities are lux-scale: the v0.1.0 value 0.8 was effectively off). It lifts the walls out of near-black while Showing, still kept >= 15 L* under the picture
 *   (B30 peripheral check, design-tools/ambient_check.py).
 * - [softLux]: a front wash light that IS the soft light: scaled by the show level (100 % lights up -> 12 % showing).
 * - [emitGain]: multiplier on the authored emissive of the style's emit_* material, also scaled by the show level.
 * Values were set from emulator screenshots (apps/home-cinema/build/ambient-check-emulator.json, ui-audit §7).
 */
data class StyleLight(val baseLux: Float, val softLux: Float, val emitGain: Float)

object Lighting {
    // Emulator calibration 2026-11-12 (PICO 6.1 emulator, sample room, ambient_check rule; ui-audit §7). On this scene
    // ~900 lux of key light already takes the charcoal walls from L* 12 to ~23; 6000 washed them out to L* 57.
    fun of(style: Style): StyleLight = when (style) {
        Style.WALNUT -> StyleLight(baseLux = 800f, softLux = 800f, emitGain = 1.0f)
        Style.BETON -> StyleLight(baseLux = 800f, softLux = 800f, emitGain = 1.0f)
        Style.LINEN -> StyleLight(baseLux = 900f, softLux = 1600f, emitGain = 2.5f)
        Style.SLATS -> StyleLight(baseLux = 1300f, softLux = 1900f, emitGain = 3.0f)
        Style.BRONZE -> StyleLight(baseLux = 1400f, softLux = 2400f, emitGain = 4.0f)
    }

    /** Debug overrides (emulator calibration only; `--es state light --es v base=..,soft=..,emit=..`). */
    @Volatile var override: StyleLight? = null

    fun current(style: Style): StyleLight = override ?: of(style)

    /** Intensities for one frame: (base, soft wash, emissive scale) at show level 0..1. */
    fun at(l: StyleLight, level: Float): Triple<Float, Float, Float> = Triple(l.baseLux, l.softLux * level, l.emitGain * level)
}
