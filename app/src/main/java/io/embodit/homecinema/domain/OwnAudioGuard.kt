package io.embodit.homecinema.domain

/**
 * q2-1 (QA round 2): tells "the other app's player is playing" apart from our own ambience loop.
 *
 * AudioManager.isMusicActive counts every music-stream player on the device, ours included, and it stays true for a
 * short while after our player is stopped and released (QA saw it ~50 ms after `AMBIENCE released` and up to ~1 s on
 * the emulator). So while our ambience player exists, and for [GRACE_MS] after it went away, the plain flag is not
 * trusted: we use the active playback list with our own USAGE_GAME player filtered out (`othersPlaying`), and when
 * that list is not available we read "nothing else playing" until the grace window has passed.
 *
 * Pure Kotlin so the unit tests can drive the exact timeline from the QA log.
 */
class OwnAudioGuard(private val graceMs: Long = GRACE_MS) {
    /** Last time our own ambience player existed (opened, playing, fading or not yet released). */
    var lastOwnAt: Long? = null
        private set

    /**
     * @param ownPlayer our ambience player exists right now (from open() until release())
     * @param musicActive AudioManager.isMusicActive
     * @param othersPlaying active playback list minus our own player, or null when it could not be read
     */
    fun reading(now: Long, ownPlayer: Boolean, musicActive: Boolean, othersPlaying: Boolean?): Boolean {
        if (ownPlayer) lastOwnAt = now
        val own = lastOwnAt
        val suppressed = ownPlayer || (own != null && now - own < graceMs)
        if (!suppressed) return musicActive
        return othersPlaying ?: false
    }

    /** True while the plain isMusicActive flag is being ignored. */
    fun suppressed(now: Long): Boolean = lastOwnAt?.let { now - it < graceMs } ?: false

    companion object {
        const val GRACE_MS = 2_000L
    }
}
