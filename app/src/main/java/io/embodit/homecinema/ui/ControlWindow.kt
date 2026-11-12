package io.embodit.homecinema.ui

import android.util.Log
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.pico.spatial.ui.design.Icon
import com.pico.spatial.ui.design.PicoTheme
import com.pico.spatial.ui.design.Switch
import com.pico.spatial.ui.design.windows.TabBar
import com.pico.spatial.ui.platform.ViewPoint
import io.embodit.homecinema.R
import io.embodit.homecinema.domain.Cause
import io.embodit.homecinema.domain.Language
import io.embodit.homecinema.domain.Phase
import io.embodit.homecinema.domain.Settings
import io.embodit.homecinema.domain.SleepTimer
import io.embodit.homecinema.domain.Style
import io.embodit.homecinema.platform.Graph
import io.embodit.homecinema.platform.Page
import io.embodit.homecinema.platform.TAG

/**
 * The controls window (Planar 480 x 760 dp, Placement.right of the frame). Two pages switched by the native TabBar
 * (D8; the design's Show / Settings segment became the TabBar, deviation d1). Show page tappables: style ◀ ▶, Start /
 * End, Start with the sound, Align = 5 (+ 2 tabs = 7, B31; Mute is the always-visible exception).
 */
@Composable
fun ControlWindow() {
    val context = LocalContext.current
    val graph = remember(context) { Graph.from(context) }
    val settings by graph.settings.settings.collectAsStateWithLifecycle()
    val owner = LocalLifecycleOwner.current
    DisposableEffect(owner) {
        val obs = LifecycleEventObserver { _, e -> graph.window.onPanelLifecycle(e.name) }
        owner.lifecycle.addObserver(obs)
        onDispose { owner.lifecycle.removeObserver(obs) }
    }
    LaunchedEffect(graph.page) {
        Log.i(TAG, "PAGE ${graph.page}")
        if (graph.page != Page.SETTINGS) graph.exitConfirm = false
    }

    Box(Modifier.fillMaxSize().padding(horizontal = 24.dp, vertical = 22.dp)) {
        when {
            graph.page == Page.SETTINGS && graph.exitConfirm -> ExitConfirmPage(graph, settings)
            graph.page == Page.SETTINGS -> SettingsPage(graph, settings)
            else -> ShowPage(graph, settings)
        }
    }

    // The TabBar ornament is composed apart from this window's localized context: resolve the labels here (in the
    // window's language) and hand plain strings in, so English shows English tabs after a cold start too.
    val tabs = listOf(
        Triple(Page.SHOW, R.drawable.ic_slow_motion_video, stringResource(R.string.tab_show)),
        Triple(Page.SETTINGS, R.drawable.ic_settings, stringResource(R.string.tab_settings)),
    )
    TabBar(followViewpoints = setOf(ViewPoint.Front, ViewPoint.Left)) {
        tabs.forEach { (page, icon, label) ->
            item(
                selected = graph.page == page,
                onClick = { graph.page = page },
                mainContent = { Icon(painter = painterResource(icon), contentDescription = label) },
                supportContent = { Txt(label, "tabbar/${page.name}", style = PicoTheme.typography.labelMedium) },
            )
        }
    }
}

@Composable
private fun PageColumn(content: @Composable ColumnScope.() -> Unit) {
    Column(Modifier.fillMaxSize(), verticalArrangement = SpaceBetweenMin16, content = content)
}

/**
 * Space-between that never lets two neighbours come closer than 16 dp (B31: controls >= 16 dp apart; QA q1-1 found
 * 6 dp gaps where the native slider / segment control drawn a layer in front overlapped the row above when seen
 * at an angle).
 */
internal object SpaceBetweenMin16 : Arrangement.Vertical {
    override val spacing = 16.dp
    override fun androidx.compose.ui.unit.Density.arrange(totalSize: Int, sizes: IntArray, outPositions: IntArray) {
        if (sizes.isEmpty()) return
        val min = 16.dp.roundToPx()
        val gap = if (sizes.size > 1) maxOf(min, (totalSize - sizes.sum()) / (sizes.size - 1)) else 0
        var y = 0
        sizes.forEachIndexed { i, h -> outPositions[i] = y; y += h + gap }
    }
}

@Composable
private fun styleName(s: Style): String = stringResource(
    when (s) { Style.WALNUT -> R.string.st_walnut; Style.BETON -> R.string.st_beton; Style.LINEN -> R.string.st_linen; Style.SLATS -> R.string.st_slats; Style.BRONZE -> R.string.st_bronze },
)

@Composable
private fun styleDesc(s: Style): String = stringResource(
    when (s) { Style.WALNUT -> R.string.sd_walnut; Style.BETON -> R.string.sd_beton; Style.LINEN -> R.string.sd_linen; Style.SLATS -> R.string.sd_slats; Style.BRONZE -> R.string.sd_bronze },
)

private fun thumb(s: Style): Int = when (s) {
    Style.WALNUT -> R.drawable.thumb_walnut; Style.BETON -> R.drawable.thumb_beton; Style.LINEN -> R.drawable.thumb_linen
    Style.SLATS -> R.drawable.thumb_slats; Style.BRONZE -> R.drawable.thumb_bronze
}

/** Status line, read straight from the show state (D38: no hard-coded state text). */
@Composable
private fun statusText(graph: Graph, settings: Settings): String {
    if (graph.align) return stringResource(R.string.status_align)
    val s = graph.show
    return when (s.phase) {
        Phase.UP -> stringResource(if (settings.auto) R.string.status_up else R.string.status_up_manual)
        Phase.OPENING -> stringResource(R.string.status_opening)
        Phase.SHOWING -> stringResource(if (s.cause == Cause.SOUND) R.string.status_showing else R.string.status_showing_manual)
        Phase.CLOSING -> stringResource(R.string.status_closing)
    }
}

/** Icon, name, status line (+ timer line), and the always-visible [Mute] (D15, B31 exception). */
@Composable
private fun Header(graph: Graph, settings: Settings, title: String) {
    Row(Modifier.fillMaxWidth().height(64.dp), verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(48.dp).clip(RoundedCornerShape(12.dp)).background(androidx.compose.ui.graphics.Color(0xFF3B2A20)), contentAlignment = Alignment.Center) {
            Image(painterResource(R.drawable.ic_launcher_fg), contentDescription = null, modifier = Modifier.requiredSize(72.dp))
        }
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) {
            Txt(title, "header/title", style = PicoTheme.typography.titleLarge)
            Txt(statusText(graph, settings), "header/status", style = PicoTheme.typography.bodySmall, color = HcColors.InkSecondary, maxLines = 2)
            graph.timerLeft?.let { left ->
                Txt(stringResource(R.string.status_timer, SleepTimer.format(left)), "header/timer", style = PicoTheme.typography.bodySmall, color = HcColors.InkSecondary)
            }
        }
        Spacer(Modifier.width(8.dp))
        ToggleButton(
            stringResource(if (settings.muted) R.string.unmute else R.string.mute), "header/mute", on = settings.muted,
            onClick = { graph.settings.update { it.copy(muted = !it.muted) } },
            icon = if (settings.muted) R.drawable.ic_volume_off else R.drawable.ic_volume_up,
            modifier = Modifier.width(132.dp),
        )
    }
}

// ------------------------------------------------------------------ Show

@Composable
private fun ShowPage(graph: Graph, settings: Settings) {
    val style = settings.style
    PageColumn {
        Header(graph, settings, stringResource(R.string.app_name))
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Txt(stringResource(R.string.style_label), "show/style-label", style = PicoTheme.typography.titleSmall, color = HcColors.InkSecondary)
            // one horizontal style picker: ◀ preview ▶ (B31: the five cards became one control)
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
                IconKey(R.drawable.ic_chevron_left, stringResource(R.string.style_prev), "show/prev") { graph.settings.update { it.copy(style = it.style.next(-1)) } }
                Image(
                    painterResource(thumb(style)), contentDescription = styleName(style), contentScale = ContentScale.Crop,
                    modifier = Modifier.width(296.dp).height(166.dp).clip(RoundedCornerShape(14.dp)).border(1.dp, HcColors.Hairline, RoundedCornerShape(14.dp)),
                )
                IconKey(R.drawable.ic_chevron_right, stringResource(R.string.style_next), "show/next") { graph.settings.update { it.copy(style = it.style.next(1)) } }
            }
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Txt(styleName(style), "show/style-name", style = PicoTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                Txt(stringResource(R.string.style_count, style.ordinal + 1, Style.entries.size), "show/style-count", style = PicoTheme.typography.labelLarge, color = HcColors.InkSecondary)
            }
            Txt(styleDesc(style), "show/style-desc", style = PicoTheme.typography.bodySmall, color = HcColors.InkSecondary, maxLines = 2, modifier = Modifier.height(40.dp))
        }
        val running = graph.show.phase == Phase.OPENING || graph.show.phase == Phase.SHOWING
        PrimaryButton(
            stringResource(if (running) R.string.show_end else R.string.show_start), "show/toggle",
            onClick = { graph.toggleShow(Cause.MANUAL) }, modifier = Modifier.fillMaxWidth(),
            icon = if (running) R.drawable.ic_lightbulb else R.drawable.ic_play_arrow,
        )
        SwitchRow2(stringResource(R.string.auto_h), stringResource(R.string.auto_s), "show/auto", settings.auto) { graph.setAuto(it) }
        SecondaryButton(stringResource(R.string.align_open), "show/align", onClick = { graph.enterAlign() }, modifier = Modifier.fillMaxWidth(), icon = R.drawable.ic_crop_free, enabled = !graph.align)
    }
}

@Composable
private fun IconKey(icon: Int, label: String, tag: String, onClick: () -> Unit) {
    com.pico.spatial.ui.design.Button(
        onClick = onClick, modifier = Modifier.width(56.dp),
        size = com.pico.spatial.ui.design.ButtonDefaults.Regular.copy(height = 96.dp, minWidth = 56.dp),
        shape = RoundedCornerShape(18.dp),
        colors = com.pico.spatial.ui.design.ButtonDefaults.buttonColors(containerColor = PicoTheme.colorScheme.fillSecondary, contentColor = PicoTheme.colorScheme.labelPrimary),
    ) {
        Icon(painter = painterResource(icon), contentDescription = label, modifier = Modifier.size(28.dp), tint = PicoTheme.colorScheme.labelPrimary)
    }
}

/** A whole >= 48 dp row that toggles: headline + supporting text + Switch (the bare Switch is ~32 x 20 dp, D44). */
@Composable
private fun SwitchRow2(head: String, sub: String, tag: String, checked: Boolean, onChange: (Boolean) -> Unit) {
    Row(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(PicoTheme.colorScheme.fillLight)
            .toggleable(value = checked, role = Role.Switch, onValueChange = onChange).padding(horizontal = 14.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            Txt(head, "$tag/head", style = PicoTheme.typography.labelLarge)
            Txt(sub, "$tag/sub", style = PicoTheme.typography.bodySmall, color = HcColors.InkSecondary, maxLines = 3)
        }
        Spacer(Modifier.width(12.dp))
        Switch(checked = checked, onCheckedChange = null)
    }
}

// ------------------------------------------------------------------ Settings

@Composable
private fun SettingsPage(graph: Graph, settings: Settings) {
    PageColumn {
        Header(graph, settings, stringResource(R.string.settings_title))
        Column {
            Txt(stringResource(R.string.timer_h), "settings/timer-h", style = PicoTheme.typography.labelLarge)
            Spacer(Modifier.height(2.dp))
            Txt(stringResource(R.string.timer_s), "settings/timer-s", style = PicoTheme.typography.bodySmall, color = HcColors.InkSecondary, maxLines = 2)
            // q1-1: 16 dp between the text and the segment control (it draws a layer in front of the panel)
            Spacer(Modifier.height(16.dp))
            val off = stringResource(R.string.timer_off)
            val opts = SleepTimer.OPTIONS.map { m -> m to if (m == 0) off else stringResource(R.string.timer_min, m) }
            val selected = if (graph.timerMinutes in SleepTimer.OPTIONS) graph.timerMinutes else -1
            Row(Modifier.fillMaxWidth()) {
                // same-page option (sleep timer stops), not a page switch
                Segments(opts, selected, "settings/timer", { m -> graph.setTimer(m) }, Modifier.weight(1f), small = true)
            }
        }
        Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
            SwitchRow2(stringResource(R.string.sound_h), stringResource(R.string.sound_s), "settings/ambience", settings.ambience) { v -> graph.settings.update { it.copy(ambience = v) } }
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Txt(stringResource(R.string.volume), "settings/volume", style = PicoTheme.typography.labelLarge, modifier = Modifier.width(88.dp))
                VolumeSlider(settings.volume, onChange = { v -> graph.settings.update { it.copy(volume = v) } }, modifier = Modifier.weight(1f))
            }
        }
        OptionRow(stringResource(R.string.lang_h), "settings/lang", labelWidth = 88.dp) {
            Segments(
                listOf(Language.SYSTEM to stringResource(R.string.lang_sys), Language.ZH to stringResource(R.string.lang_zh), Language.EN to stringResource(R.string.lang_en)),
                settings.language, "settings/lang", { l -> graph.settings.update { it.copy(language = l) } }, Modifier.weight(1f), small = true,
            )
        }
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            SecondaryButton(stringResource(R.string.reopen), "settings/reopen", onClick = { graph.window.reopen() }, icon = R.drawable.ic_open_in_new, modifier = Modifier.width(210.dp))
            Spacer(Modifier.width(16.dp))
            Txt(stringResource(R.string.reopen_hint), "settings/reopen-hint", style = PicoTheme.typography.bodySmall, color = HcColors.InkSecondary, maxLines = 3, modifier = Modifier.weight(1f))
        }
        Txt(stringResource(R.string.limits), "settings/limits", style = PicoTheme.typography.bodySmall, color = HcColors.InkSecondary, maxLines = 3)
        // D26: exit is the last row; the confirmation is a whole page.
        SecondaryButton(stringResource(R.string.exit), "settings/exit", onClick = { graph.exitConfirm = true; Log.i(TAG, "CONFIRM EXIT") }, icon = R.drawable.ic_exit, modifier = Modifier.fillMaxWidth(), danger = true)
    }
}

@Composable
private fun ExitConfirmPage(graph: Graph, settings: Settings) {
    // q1-2: the card wraps its content (min 340 dp since v0.1.2: outer blank was 24.6 / 25.0 %, right on the line) (no weight-filled card with big empty bands inside); card + buttons sit as one
    // group centred in the space under the header, so no band inside or around the card exceeds 20 % of the window.
    Column(Modifier.fillMaxSize()) {
        Header(graph, settings, stringResource(R.string.settings_title))
        Spacer(Modifier.weight(1f).heightIn(min = 16.dp))
        Column(
            Modifier.fillMaxWidth().heightIn(min = 340.dp).clip(RoundedCornerShape(20.dp)).background(HcColors.Card).padding(horizontal = 24.dp, vertical = 28.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp, Alignment.CenterVertically),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Icon(painter = painterResource(R.drawable.ic_exit), contentDescription = null, modifier = Modifier.size(48.dp), tint = HcColors.Ink)
            Txt(stringResource(R.string.exit_title), "exit/title", style = PicoTheme.typography.titleLarge, color = HcColors.Ink, maxLines = 2, align = TextAlign.Center)
            // K3: centred like the title, in both languages
            Txt(stringResource(R.string.exit_body), "exit/body", style = PicoTheme.typography.bodyMedium, color = HcColors.InkSecondary, maxLines = 3, align = TextAlign.Center, modifier = Modifier.fillMaxWidth())
        }
        Spacer(Modifier.height(24.dp))
        // q1-1: 64 dp buttons, 16 dp apart
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            SecondaryButton(stringResource(R.string.exit_no), "exit/no", onClick = { graph.exitConfirm = false }, modifier = Modifier.weight(1f))
            SecondaryButton(stringResource(R.string.exit_yes), "exit/yes", onClick = { graph.exit() }, icon = R.drawable.ic_exit, modifier = Modifier.weight(1f), danger = true)
        }
        Spacer(Modifier.weight(1f).heightIn(min = 16.dp))
    }
}
