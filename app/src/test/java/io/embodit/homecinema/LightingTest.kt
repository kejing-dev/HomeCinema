package io.embodit.homecinema

import io.embodit.homecinema.domain.Lighting
import io.embodit.homecinema.domain.ShowMachine
import io.embodit.homecinema.domain.Style
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** QA #1 K1: every style's soft light must visibly change between Lights up and Showing; the key light stays on. */
class LightingTest {
    @Test fun softLightScalesWithShowLevel() {
        for (s in Style.entries) {
            val l = Lighting.of(s)
            val up = Lighting.at(l, 1f)
            val show = Lighting.at(l, ShowMachine.SHOW_LEVEL)
            assertEquals("$s base light constant", up.first, show.first, 0f)
            assertTrue("$s soft wash dims to 12 %", show.second <= up.second * 0.121f)
            assertTrue("$s lux-scale values, not 0..1 (build.md 2026-11-12)", l.baseLux >= 100f && l.softLux >= 100f)
            // the soft wash at lights up is at least as strong as the constant key light, so lights up vs showing is visible
            assertTrue("$s soft >= base", l.softLux >= l.baseLux)
        }
    }

    @Test fun dimStylesGetMoreSoftLight() {
        val ref = Lighting.of(Style.WALNUT)
        for (s in listOf(Style.LINEN, Style.SLATS, Style.BRONZE)) {
            assertTrue("$s soft light boosted", Lighting.of(s).softLux > ref.softLux)
            assertTrue("$s emissive boosted", Lighting.of(s).emitGain > ref.emitGain)
        }
    }

    @Test fun debugOverrideIsOnlyAnOverride() {
        Lighting.override = null
        assertEquals(Lighting.of(Style.SLATS), Lighting.current(Style.SLATS))
    }

    @Test fun ambienceForEveryStyleButBronze() {
        for (s in Style.entries) if (s == Style.BRONZE) assertNull(s.ambience) else assertNotNull("$s ambience", s.ambience)
    }
}
