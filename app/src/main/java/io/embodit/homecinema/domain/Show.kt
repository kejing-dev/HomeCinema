package io.embodit.homecinema.domain

/** The five ambient wall treatments (design R4). Model file assets/models/frame_<id>.glb; ambience assets/sounds/amb_<id>.ogg if any. */
enum class Style(val id: String, val ambience: String?) {
    WALNUT("walnut", "amb_walnut"),
    BETON("beton", "amb_beton"),
    LINEN("linen", "amb_linen"),
    SLATS("slats", "amb_slats"),
    BRONZE("bronze", null);

    fun next(step: Int): Style = entries[((ordinal + step) % entries.size + entries.size) % entries.size]

    companion object {
        fun of(id: String?): Style = entries.firstOrNull { it.id == id } ?: WALNUT
    }
}

enum class Phase { UP, OPENING, SHOWING, CLOSING }

enum class Language { SYSTEM, ZH, EN }

/** Who started the current phase: the sound detector, the user's button, or the sleep timer. */
enum class Cause { SOUND, MANUAL, TIMER, DEBUG }

/** What the control window shows; the one source for the status line and the start / end button. */
data class ShowState(
    val phase: Phase = Phase.UP,
    val cause: Cause = Cause.SOUND,
    /** soft light level the current fade starts from (0..1), and when the fade started (ms) */
    val fromLevel: Float = 1f,
    val since: Long = 0L,
) {
    val running: Boolean get() = phase == Phase.OPENING || phase == Phase.SHOWING
}

/**
 * Show lighting (design action toggle-show / toggle-auto-show, PRD 4.3). Pure: the caller feeds time and the sound
 * reading, the machine says what the light does. One path for everything: the panel button, the debug broadcast,
 * the sound detector and the sleep timer all call [start] / [end] / [onSound] / [tick].
 *
 * - Opening: soft light from where it is to 12 % over 4 s, then Showing.
 * - Closing: back to 100 % over 6 s, then Lights up.
 * - Auto (default on): sound inactive → active starts the show; 8 s of continuous silence ends it.
 * - A manual press overrides auto until the next change of the sound reading (an edge), so the next 1 s poll
 *   doesn't undo it (A5).
 */
class ShowMachine(var auto: Boolean = true) {
    var state = ShowState()
        private set
    /** set by a manual / timer press; cleared on the next sound edge */
    var override = false
        private set
    private var lastSound: Boolean? = null
    private var silentSince: Long? = null

    fun level(now: Long): Float = levelOf(state, now)

    fun start(now: Long, cause: Cause): Boolean {
        if (state.running) return false
        state = ShowState(Phase.OPENING, cause, levelOf(state, now), now)
        override = cause != Cause.SOUND
        silentSince = null
        return true
    }

    fun end(now: Long, cause: Cause): Boolean {
        if (!state.running) return false
        state = ShowState(Phase.CLOSING, cause, levelOf(state, now), now)
        override = cause != Cause.SOUND
        return true
    }

    /** Advance timed phases. Returns true when the phase changed. */
    fun tick(now: Long): Boolean {
        val s = state
        return when {
            s.phase == Phase.OPENING && now - s.since >= OPEN_MS -> { state = s.copy(phase = Phase.SHOWING, fromLevel = SHOW_LEVEL, since = now); true }
            s.phase == Phase.CLOSING && now - s.since >= CLOSE_MS -> { state = s.copy(phase = Phase.UP, fromLevel = 1f, since = now); true }
            else -> false
        }
    }

    /** One reading of "something is playing" (every 1 s). Returns true when it started or ended the show. */
    fun onSound(now: Long, active: Boolean): Boolean {
        val prev = lastSound
        lastSound = active
        val edge = prev != null && prev != active
        if (edge) override = false
        if (active) silentSince = null else if (silentSince == null || edge) silentSince = now
        if (!auto || override) return false
        if (active && (edge || prev == null) && !state.running) return start(now, Cause.SOUND)
        val quiet = silentSince
        if (!active && quiet != null && now - quiet >= SILENCE_MS && state.running) return end(now, Cause.SOUND)
        return false
    }

    /** Debug / tests: the last sound reading. */
    val soundReading: Boolean? get() = lastSound

    companion object {
        const val OPEN_MS = 4_000L
        const val CLOSE_MS = 6_000L
        const val SILENCE_MS = 8_000L
        const val SHOW_LEVEL = 0.12f

        fun levelOf(s: ShowState, now: Long): Float {
            val t = (now - s.since).coerceAtLeast(0L)
            return when (s.phase) {
                Phase.UP -> 1f
                Phase.SHOWING -> SHOW_LEVEL
                Phase.OPENING -> lerp(s.fromLevel, SHOW_LEVEL, ease(t / OPEN_MS.toFloat()))
                Phase.CLOSING -> lerp(s.fromLevel, 1f, ease(t / CLOSE_MS.toFloat()))
            }
        }

        private fun lerp(a: Float, b: Float, t: Float) = a + (b - a) * t
        /** smoothstep: slow in, slow out, no flash (A6) */
        fun ease(t: Float): Float { val x = t.coerceIn(0f, 1f); return x * x * (3 - 2 * x) }
    }
}

/** Sleep timer (Off / 60 / 90 / 120 min). Debug can set it to 1 min for A8. */
class SleepTimer {
    var minutes: Int = 0
        private set
    var endsAt: Long? = null
        private set

    fun set(minutes: Int, now: Long) {
        this.minutes = minutes
        endsAt = if (minutes > 0) now + minutes * 60_000L else null
    }

    /** ms left, or null when off */
    fun left(now: Long): Long? = endsAt?.let { (it - now).coerceAtLeast(0L) }

    /** True once when it runs out; the timer then switches itself off. */
    fun expired(now: Long): Boolean {
        val e = endsAt ?: return false
        if (now < e) return false
        endsAt = null
        minutes = 0
        return true
    }

    companion object {
        val OPTIONS = listOf(0, 60, 90, 120)

        fun format(ms: Long): String {
            val m = (ms + 59_999) / 60_000
            return if (m >= 60) "%d:%02d".format(m / 60, m % 60) else "$m min"
        }
    }
}

/** Ambience volume stops (B20: three snapping stops + percent). */
val AMBIENCE_PERCENT = intArrayOf(30, 60, 100)

/** Persisted settings (one store, every UI and debug path writes through it). */
data class Settings(
    val style: Style = Style.WALNUT,
    val auto: Boolean = true,
    val ambience: Boolean = false,
    val volume: Int = 2,
    val muted: Boolean = false,
    val language: Language = Language.SYSTEM,
    val aligned: Boolean = false,
)
