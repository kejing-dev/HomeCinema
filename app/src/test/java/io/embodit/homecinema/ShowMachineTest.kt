package io.embodit.homecinema

import io.embodit.homecinema.domain.Cause
import io.embodit.homecinema.domain.FrameLayout
import io.embodit.homecinema.domain.Phase
import io.embodit.homecinema.domain.ShowMachine
import io.embodit.homecinema.domain.SleepTimer
import io.embodit.homecinema.domain.Style
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Show lighting (PRD 4.3, A5, A6, A8) and frame geometry (A2 / A3: nothing in the opening). */
class ShowMachineTest {
    /** Feed one sound reading per second from t0 for [secs] seconds, ticking every 50 ms. */
    private fun ShowMachine.run(t0: Long, secs: Int, sound: Boolean): Long {
        var t = t0
        repeat(secs * 20) { i ->
            tick(t)
            if (i % 20 == 0) onSound(t, sound)
            t += 50
        }
        return t
    }

    @Test fun soundStartsAndEightSecondsOfSilenceEnds() {
        val m = ShowMachine(auto = true)
        var t = m.run(0, 3, false)
        assertEquals(Phase.UP, m.state.phase)
        t = m.run(t, 1, true)
        assertEquals(Phase.OPENING, m.state.phase)
        t = m.run(t, 5, true)
        assertEquals(Phase.SHOWING, m.state.phase)
        assertEquals(ShowMachine.SHOW_LEVEL, m.level(t), 1e-4f)
        t = m.run(t, 7, false)
        assertEquals("7 s of silence keeps the show", Phase.SHOWING, m.state.phase)
        t = m.run(t, 3, false)
        assertTrue(m.state.phase == Phase.CLOSING || m.state.phase == Phase.UP)
        t = m.run(t, 7, false)
        assertEquals(Phase.UP, m.state.phase)
        assertEquals(1f, m.level(t), 1e-4f)
    }

    @Test fun shortPauseDoesNotEndTheShow() {
        val m = ShowMachine(auto = true)
        var t = m.run(0, 6, true)
        t = m.run(t, 5, false)
        t = m.run(t, 5, true)
        t = m.run(t, 5, false)
        assertEquals(Phase.SHOWING, m.state.phase)
    }

    @Test fun manualStartIsNotUndoneByTheNextPoll() {
        // A5: auto on, no sound, the user starts the show: it stays on through any amount of silence
        val m = ShowMachine(auto = true)
        var t = m.run(0, 2, false)
        assertTrue(m.start(t, Cause.MANUAL))
        t = m.run(t, 30, false)
        assertEquals(Phase.SHOWING, m.state.phase)
        // a later edge hands control back to the sound: sound starts then stops for 8 s -> ends
        t = m.run(t, 2, true)
        t = m.run(t, 9, false)
        assertTrue(m.state.phase == Phase.CLOSING || m.state.phase == Phase.UP)
    }

    @Test fun manualEndIsNotUndoneWhileSoundContinues() {
        val m = ShowMachine(auto = true)
        var t = m.run(0, 6, true)
        assertEquals(Phase.SHOWING, m.state.phase)
        assertTrue(m.end(t, Cause.MANUAL))
        t = m.run(t, 20, true)
        assertEquals(Phase.UP, m.state.phase)
        // next pause + play starts it again
        t = m.run(t, 2, false)
        t = m.run(t, 1, true)
        assertEquals(Phase.OPENING, m.state.phase)
    }

    @Test fun autoOffButtonRunsTheFullCycle() {
        // A5: auto off, the button alone runs Opening -> Showing -> Closing -> Lights up
        val m = ShowMachine(auto = false)
        var t = m.run(0, 2, true)
        assertEquals(Phase.UP, m.state.phase)
        m.start(t, Cause.MANUAL)
        t = m.run(t, 5, false)
        assertEquals(Phase.SHOWING, m.state.phase)
        m.end(t, Cause.MANUAL)
        t = m.run(t, 3, true)
        assertEquals(Phase.CLOSING, m.state.phase)
        t = m.run(t, 4, true)
        assertEquals(Phase.UP, m.state.phase)
    }

    @Test fun fadesAreSlowAndMonotonic() {
        // A6: 100 % -> 12 % over 4 s and back over 6 s, no step bigger than 2 % per 50 ms frame
        val m = ShowMachine(auto = false)
        m.start(0, Cause.MANUAL)
        var prev = m.level(0)
        var t = 0L
        while (t <= ShowMachine.OPEN_MS) { m.tick(t); val l = m.level(t); assertTrue(l <= prev + 1e-6f); assertTrue(prev - l < 0.02f); prev = l; t += 50 }
        assertEquals(ShowMachine.SHOW_LEVEL, m.level(t), 1e-3f)
        m.end(t, Cause.MANUAL)
        val t1 = t
        prev = m.level(t1)
        while (t <= t1 + ShowMachine.CLOSE_MS) { m.tick(t); val l = m.level(t); assertTrue(l >= prev - 1e-6f); assertTrue(l - prev < 0.02f); prev = l; t += 50 }
        assertEquals(1f, m.level(t), 1e-3f)
    }

    @Test fun reversingMidFadeStartsFromTheCurrentLevel() {
        val m = ShowMachine(auto = false)
        m.start(0, Cause.MANUAL)
        m.tick(2000)
        val mid = m.level(2000)
        m.end(2000, Cause.MANUAL)
        assertEquals(mid, m.level(2000), 1e-4f)
    }

    @Test fun sleepTimerEndsTheShowOnceAndSwitchesOff() {
        // A8 with the 1-minute test setting
        val m = ShowMachine(auto = true)
        val timer = SleepTimer()
        var t = m.run(0, 6, true)
        timer.set(1, t)
        var fired = 0
        repeat(70 * 20) { i ->
            m.tick(t)
            if (i % 20 == 0) m.onSound(t, true)
            if (timer.expired(t)) { fired++; m.end(t, Cause.TIMER) }
            t += 50
        }
        assertEquals(1, fired)
        assertEquals(0, timer.minutes)
        assertEquals("sound still on: the timer's lights-up stays", Phase.UP, m.state.phase)
    }

    @Test fun stylesCycleBothWays() {
        assertEquals(Style.BETON, Style.WALNUT.next(1))
        assertEquals(Style.BRONZE, Style.WALNUT.next(-1))
        assertEquals(Style.WALNUT, Style.BRONZE.next(1))
        assertEquals(Style.WALNUT, Style.of("nope"))
    }

    @Test fun nothingSitsInTheOpening() {
        // A2: the attachments and the guide never cover the player rect; all inside the volume
        assertFalse(FrameLayout.overlapsOpening(FrameLayout.ALIGN_PANEL))
        assertFalse(FrameLayout.overlapsOpening(FrameLayout.OPEN_CHIP))
        assertTrue(FrameLayout.insideVolume(FrameLayout.ALIGN_PANEL))
        assertTrue(FrameLayout.insideVolume(FrameLayout.OPEN_CHIP))
        for (d in FrameLayout.dashes(FrameLayout.PLAYER_W, FrameLayout.PLAYER_H)) {
            // dashes run along the player edge, inside the 2 cm margin of the opening
            assertTrue(kotlin.math.abs(d.x) <= FrameLayout.OPENING_W / 2 && kotlin.math.abs(d.y) <= FrameLayout.OPENING_H / 2)
        }
    }

    @Test fun fitKeepsTheShapeAndFitsTheVolume() {
        assertEquals(1f, FrameLayout.fitScale(1.7f, 1.0f), 1e-5f)
        assertEquals(0.5f, FrameLayout.fitScale(0.85f, 0.5f), 1e-5f)
        // clamped volume: the smaller axis wins (opening stays 16:9, nothing spills out)
        assertEquals(0.8f, FrameLayout.fitScale(1.36f, 1.0f), 1e-5f)
    }
}
