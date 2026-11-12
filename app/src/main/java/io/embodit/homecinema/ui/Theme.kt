package io.embodit.homecinema.ui

import android.content.Context
import android.content.ContextWrapper
import android.content.res.Configuration
import android.content.res.Resources
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.pico.spatial.ui.design.PicoTheme
import com.pico.spatial.ui.design.systemColorScheme
import io.embodit.homecinema.domain.Language
import io.embodit.homecinema.platform.Graph
import java.util.Locale

/**
 * Walnut / charcoal palette (design app icon). Text is solid ink on the window glass (D13: no mid-grey on grey);
 * the interaction colour is a deep walnut so white labels on it stay far above 4.5:1.
 */
object HcColors {
    val Walnut = Color(0xFF5A3A24)
    val OnWalnut = Color(0xFFFFFFFF)
    val WalnutContainer = Color(0xFFEADBCB)
    val Ink = Color(0xFF17161A)
    /** Secondary / small text on the window glass (>= 4.5:1 on the darkest measured glass #B4B3B1). */
    val InkSecondary = Color(0xFF33363C)
    val Error = Color(0xFF8E2A22)
    val OnError = Color(0xFFFFFFFF)
    val Card = Color(0xFFF4F1EC)
    val Hairline = Color(0xFF8A8F98)
    /** Alignment guide in the frame: a calm blue (design: 蓝色虚线), only while aligning. */
    val Guide = Color(0xFF6FA8DC)
    /** Align panel and [Open controls] chip in the frame: a dark card with light ink (sits on dark walls). */
    val PanelFace = Color(0xF0201D1B)
    val PanelInk = Color(0xFFF2EEE8)
    val PanelInkSecondary = Color(0xFFCFC8BE)
}

/**
 * PicoTheme with all roles assigned. The language setting localises resources below this point through a
 * ContextWrapper that only overrides getResources (a bare configuration context breaks SpatialView).
 */
@Composable
fun HcTheme(content: @Composable () -> Unit) {
    val base = LocalContext.current
    val graph = remember(base) { Graph.from(base) }
    val settings by graph.settings.settings.collectAsStateWithLifecycle()
    val localized = remember(base, settings.language) { base.localized(settings.language) }
    val system = systemColorScheme(localized)
    val scheme = system.copy(
        labelPrimaryLight = HcColors.OnWalnut,
        labelPrimary = HcColors.Ink,
        labelSecondary = HcColors.InkSecondary,
        error = HcColors.Error,
        interaction = HcColors.Walnut,
    )
    CompositionLocalProvider(LocalContext provides localized) {
        PicoTheme(colorScheme = scheme, typography = PicoTheme.typography.withNotoSans(), content = content)
    }
}

fun Context.localized(language: Language): Context {
    val locale = when (language) {
        Language.SYSTEM -> return this
        Language.ZH -> Locale.SIMPLIFIED_CHINESE
        Language.EN -> Locale.ENGLISH
    }
    val config = Configuration(resources.configuration)
    config.setLocale(locale)
    val res = createConfigurationContext(config).resources
    return object : ContextWrapper(this) {
        override fun getResources(): Resources = res
    }
}
