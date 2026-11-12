package io.embodit.homecinema

import io.embodit.homecinema.domain.Cause
import io.embodit.homecinema.domain.OwnAudioGuard
import io.embodit.homecinema.domain.Phase
import io.embodit.homecinema.domain.ShowMachine
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * q2-1: a manual end with the style ambience on must not be undone by our own ambience stopping (PRD M5).
 * Replays the Graph loop: 50 ms ticks, one sound poll per second, our player released when the closing fade ends,
 * isMusicActive still true for a while after the release (QA log: 50 ms; we test up to 1.5 s).
 */
class OwnAmbienceTest {
    private class Sim(val staleMs: Long, val pollPhaseMs: Long) {
        val m = ShowMachine(auto = true)
        val g = OwnAudioGuard()
        var t = 0L
        var ownPlayer = false
        var releasedAt: Long? = null
        /** another app's player (USAGE_MEDIA), seen by both isMusicActive and the playback list */
        var other = false
        var lastPoll = -1_000_000L + pollPhaseMs
        val log = mutableListOf<String>()

        fun musicActive(): Boolean = other || ownPlayer || (releasedAt?.let { t - it < staleMs } ?: false)

        fun step() {
            val before = m.state.phase
            m.tick(t)
            if (t - lastPoll >= 1000) {
                lastPoll = t
                val r = g.reading(t, ownPlayer, musicActive(), other)
                m.onSound(t, r)
            }
            // AmbiencePlayer.drive: player exists while the show is running or the light is still coming back up
            val wantOwn = m.state.phase != Phase.UP
            if (wantOwn && !ownPlayer) { ownPlayer = true; releasedAt = null }
            if (!wantOwn && ownPlayer) { ownPlayer = false; releasedAt = t }
            if (m.state.phase != before) log += "$t ${before}->${m.state.phase} ${m.state.cause}"
            t += 50
        }

        fun run(ms: Long) { repeat((ms / 50).toInt()) { step() } }
    }

    @Test fun manualEndIsNotUndoneByOwnAmbienceStopping() {
        var cycles = 0
        for (stale in longArrayOf(0, 50, 300, 1_000, 1_500)) for (phase in 0L until 1000L step 50) {
            val s = Sim(stale, phase)
            s.run(2_000)
            s.m.start(s.t, Cause.MANUAL)             // [开场]
            s.run(6_000)
            assertEquals(Phase.SHOWING, s.m.state.phase)
            s.m.end(s.t, Cause.MANUAL)               // [散场]
            s.run(20_000)                            // closing 6 s, release, then long quiet
            assertEquals("stale=$stale phase=$phase ${s.log}", Phase.UP, s.m.state.phase)
            assertFalse("reopened: ${s.log}", s.log.any { it.contains("->OPENING") && it.endsWith("SOUND") })
            cycles++
        }
        assertEquals(100, cycles)
    }

    @Test fun realPlayerAfterManualEndStillStartsTheShow() {
        val s = Sim(1_000, 0)
        s.run(2_000)
        s.m.start(s.t, Cause.MANUAL); s.run(6_000)
        s.m.end(s.t, Cause.MANUAL); s.run(10_000)
        assertEquals(Phase.UP, s.m.state.phase)
        s.other = true                               // the player really starts
        s.run(2_100)
        assertTrue(s.log.toString(), s.m.state.running)
        assertEquals(Cause.SOUND, s.m.state.cause)
    }

    @Test fun otherPlayerSeenWhileOwnAmbiencePlays() {
        val g = OwnAudioGuard()
        assertFalse(g.reading(0, ownPlayer = true, musicActive = true, othersPlaying = false))
        assertTrue(g.reading(1_000, ownPlayer = true, musicActive = true, othersPlaying = true))
        // released: inside the grace window the stale flag is ignored, the list still counts
        assertFalse(g.reading(1_050, ownPlayer = false, musicActive = true, othersPlaying = false))
        assertTrue(g.reading(1_500, ownPlayer = false, musicActive = true, othersPlaying = true))
        assertFalse("no list: wait out the window", g.reading(2_000, ownPlayer = false, musicActive = true, othersPlaying = null))
        // after the window the plain flag is trusted again
        assertTrue(g.reading(3_100, ownPlayer = false, musicActive = true, othersPlaying = null))
        assertFalse(g.reading(4_100, ownPlayer = false, musicActive = false, othersPlaying = null))
    }

    @Test fun withoutTheGuardTheOldProbeReopens() {
        // documents the bug: plain isMusicActive right after release reads our own stream as the player
        val m = ShowMachine(auto = true)
        m.onSound(0, false)
        m.start(1_000, Cause.MANUAL); m.tick(5_000)
        m.end(6_000, Cause.MANUAL); m.tick(12_000)
        assertEquals(Phase.UP, m.state.phase)
        assertTrue(m.onSound(12_050, true))   // the stale flag would have restarted it
        assertEquals(Phase.OPENING, m.state.phase)
    }
}
