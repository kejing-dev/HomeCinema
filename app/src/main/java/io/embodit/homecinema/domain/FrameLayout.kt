package io.embodit.homecinema.domain

/**
 * Geometry of the frame Volume, in model metres (design frame-model: extent 3.4 x 2.0 x 0.6 m, opening 1.64 x 0.94 m
 * centred, player 1.6 x 0.9 m). Model origin = opening centre; +z towards the user.
 */
object FrameLayout {
    const val VOLUME_W = 3.4f
    const val VOLUME_H = 2.0f
    const val VOLUME_D = 0.6f
    const val OPENING_W = 1.64f
    const val OPENING_H = 0.94f
    const val PLAYER_W = 1.6f
    const val PLAYER_H = 0.9f
    /** GLB walls span z -0.12..+0.19; pushed back so the wall sits near the back face and the front half stays free. */
    const val MODEL_Z = -0.15f
    /** Align guide just in front of the frame members. */
    const val OUTLINE_Z = 0.08f
    const val CROSSFADE_MS = 1200L
    /** Attachments live under the fit node; this brings them back to about native panel size at the default fit. */
    const val ATTACH_SCALE = 1.6f

    /** Attachments (world-space centre in model metres) and their size in metres; both below the opening. */
    val ALIGN_PANEL = Rect3(0f, -0.70f, 0.24f, 0.86f, 0.26f)
    val OPEN_CHIP = Rect3(0f, -0.70f, 0.24f, 0.36f, 0.09f)

    data class Rect3(val x: Float, val y: Float, val z: Float, val w: Float, val h: Float) {
        val top get() = y + h / 2
        val bottom get() = y - h / 2
        val left get() = x - w / 2
        val right get() = x + w / 2
    }

    /** Uniform scale that fits the 3.4 x 2.0 m model into the volume's real half extents (the opening keeps 16:9). */
    fun fitScale(halfX: Float, halfY: Float): Float {
        if (halfX <= 0f || halfY <= 0f) return 1f
        return minOf(halfX * 2 / VOLUME_W, halfY * 2 / VOLUME_H)
    }

    data class Dash(val x: Float, val y: Float, val length: Float, val horizontal: Boolean)

    /** Dashes (6 cm on, 4 cm off) round a w x h rectangle centred on the origin; corners always drawn. */
    fun dashes(w: Float, h: Float, on: Float = 0.06f, off: Float = 0.04f): List<Dash> {
        val out = ArrayList<Dash>()
        fun edge(len: Float, horizontal: Boolean, fixed: Float) {
            val n = ((len + off) / (on + off)).toInt().coerceAtLeast(1)
            val step = if (n > 1) (len - on) / (n - 1) else 0f
            for (i in 0 until n) {
                val c = -len / 2 + on / 2 + i * step
                out += if (horizontal) Dash(c, fixed, on, true) else Dash(fixed, c, on, false)
            }
        }
        edge(w, true, h / 2); edge(w, true, -h / 2); edge(h, false, -w / 2); edge(h, false, w / 2)
        return out
    }

    /** True when a rect (model metres, x/y centre + size) overlaps the opening. */
    fun overlapsOpening(r: Rect3): Boolean =
        r.right > -OPENING_W / 2 && r.left < OPENING_W / 2 && r.top > -OPENING_H / 2 && r.bottom < OPENING_H / 2

    /** True when a rect stays inside the volume's front face. */
    fun insideVolume(r: Rect3): Boolean =
        r.left >= -VOLUME_W / 2 && r.right <= VOLUME_W / 2 && r.bottom >= -VOLUME_H / 2 && r.top <= VOLUME_H / 2 && kotlin.math.abs(r.z) <= VOLUME_D / 2
}
