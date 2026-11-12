package io.embodit.homecinema.scene

import android.util.Log
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.pico.spatial.core.ecs.Entity
import com.pico.spatial.core.ecs.SceneUpdateContext
import com.pico.spatial.core.ecs.System
import com.pico.spatial.core.ecs.ViewCoordinateSpace
import com.pico.spatial.core.math.Vector3
import com.pico.spatial.ui.design.Icon
import com.pico.spatial.ui.design.PicoTheme
import com.pico.spatial.ui.foundation.content.SpatialView
import com.pico.spatial.ui.foundation.dsl.registerSystem
import com.pico.spatial.ui.foundation.dsl.unregisterSystem
import com.pico.spatial.ui.platform.containers.LocalSpatialNavigator
import io.embodit.homecinema.R
import io.embodit.homecinema.domain.FrameLayout
import io.embodit.homecinema.domain.Style
import io.embodit.homecinema.platform.Graph
import io.embodit.homecinema.platform.TAG
import io.embodit.homecinema.ui.HcColors
import io.embodit.homecinema.ui.HcTheme
import io.embodit.homecinema.ui.PrimaryButton
import io.embodit.homecinema.ui.Txt
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.withContext
import kotlin.math.abs

/** Per-frame: soft light + cross-fade in the ECS (never in Compose). */
class FrameSystem : System() {
    private var frames = 0L
    private var lastLog = 0L
    override fun update(context: SceneUpdateContext) {
        val g = Holder.graph ?: return
        frames++
        val now = android.os.SystemClock.uptimeMillis()
        if (now - lastLog > 10_000) { lastLog = now; Log.i(TAG, "SYSTEM frames=$frames scene=${Holder.scene != null}") }
        try {
            Holder.scene?.let { s ->
                s.wantOutline = g.align
                s.onFrame(g.lightLevel)
            }
        } catch (t: Throwable) {
            Log.e(TAG, "SYSTEM frame failed", t)
        }
    }
}

internal object Holder {
    @Volatile var scene: FrameScene? = null
    @Volatile var graph: Graph? = null
}

private const val ALIGN = "alignPanel"
private const val CHIP = "openChip"

/**
 * The frame Volume (default container): loads the chosen style's GLB, swaps it on style change (one model loaded at a
 * time, 1.2 s cross-fade), opens the controls window beside it, and shows two attachments below the opening: the align
 * card (align mode) and [Open controls] (only while the controls window is closed).
 */
@Composable
fun FrameScreen() {
    val context = LocalContext.current
    val graph = remember(context) { Graph.from(context) }
    val settings by graph.settings.settings.collectAsStateWithLifecycle()
    val navigator = LocalSpatialNavigator.current
    val scene = remember { FrameScene() }
    var viewSize by remember { mutableStateOf(IntSize.Zero) }
    var ready by remember { mutableStateOf(false) }

    DisposableEffect(navigator) {
        graph.window.attach(navigator)
        onDispose { graph.window.detach(navigator) }
    }
    // Startup (QA #1 K4, <= 2 s to the frame): the frame comes first. The controls window opens once the frame model
    // is in (or after 1.5 s at the latest), so the second window doesn't compete with the volume's first frames
    // (emulator: 1.6-1.8 s from launch to the frame, vs 2.0-2.1 s when both open together).
    var frameShown by remember { mutableStateOf(false) }
    LaunchedEffect(frameShown) {
        if (graph.window.panelOpen) return@LaunchedEffect
        if (!frameShown) kotlinx.coroutines.delay(1500)
        if (!graph.window.panelOpen) graph.window.open(if (frameShown) "start" else "start-timeout")
    }

    DisposableEffect(scene) {
        Holder.scene = scene
        Holder.graph = graph
        registerSystem<FrameSystem>()
        onDispose {
            unregisterSystem<FrameSystem>()
            if (Holder.scene === scene) Holder.scene = null
            scene.dispose()
        }
    }

    // Style change: load the new GLB, then cross-fade (switching content = close then open, D41). The load starts at
    // once, without waiting for the volume's `initial` (it used to start ~1.4 s later, QA #1 K4); the model is added
    // to the scene when the volume is ready.
    var loaded by remember { mutableStateOf<Pair<Style, Entity>?>(null) }
    LaunchedEffect(settings.style) {
        val style = settings.style
        if (scene.currentStyle == style) return@LaunchedEffect
        val t0 = android.os.SystemClock.elapsedRealtime()
        val model = runCatching { withContext(NonCancellable + Dispatchers.Main) { Entity.loadSuspend("asset://models/frame_${style.id}.glb") } }
            .onFailure { Log.e(TAG, "FRAME load ${style.id} failed", it) }.getOrNull() ?: return@LaunchedEffect
        if (graph.settings.value.style != style) { runCatching { model.destroy(true) }; return@LaunchedEffect }
        loaded?.let { (_, stale) -> runCatching { stale.destroy(true) } }
        loaded = style to model
        Log.i(TAG, "FRAME ${style.id} loaded in ${android.os.SystemClock.elapsedRealtime() - t0} ms")
    }
    LaunchedEffect(ready, loaded) {
        val (style, model) = loaded ?: return@LaunchedEffect
        if (!ready) return@LaunchedEffect
        loaded = null
        if (graph.settings.value.style != style) { runCatching { model.destroy(true) }; return@LaunchedEffect }
        scene.show(style, model)
        frameShown = true
    }
    DisposableEffect(Unit) { onDispose { loaded?.let { (_, m) -> runCatching { m.destroy(true) } } } }

    SpatialView(
        modifier = Modifier.fillMaxSize().onSizeChanged { viewSize = it },
        attachments = {
            AttachmentPanel(ALIGN) { HcTheme { AlignCard(graph) } }
            AttachmentPanel(CHIP) { HcTheme { OpenChip(graph) } }
        },
        initial = { content, attachments ->
            content.addEntity(scene.root)
            scene.buildOutline()
            attachments.entity(ALIGN)?.let { scene.attach(it, FrameLayout.ALIGN_PANEL) }
            attachments.entity(CHIP)?.let { scene.attach(it, FrameLayout.OPEN_CHIP) }
            ready = true
            Log.i(TAG, "VOLUME initial done")
        },
        update = { content, attachments ->
            if (viewSize != IntSize.Zero) {
                val corner = content.convertPosition(Vector3.ZERO, ViewCoordinateSpace.Local, content.localSpatialCoordinateSpace)
                scene.setRegion(abs(corner.x), abs(corner.y))
            }
            attachments.entity(ALIGN)?.enabled = graph.align
            attachments.entity(CHIP)?.enabled = !graph.align && !graph.window.panelOpen && graph.window.panelState != "never"
        },
    )
}

@Composable
private fun AlignCard(graph: Graph) {
    Column(
        Modifier.width(560.dp).clip(RoundedCornerShape(24.dp)).background(HcColors.PanelFace).padding(horizontal = 24.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Txt(stringResource(R.string.align_title), "align/title", style = PicoTheme.typography.titleLarge, color = HcColors.PanelInk)
        Txt(stringResource(R.string.align_s1), "align/s1", style = PicoTheme.typography.bodyMedium, color = HcColors.PanelInk, maxLines = 2)
        Txt(stringResource(R.string.align_s2), "align/s2", style = PicoTheme.typography.bodyMedium, color = HcColors.PanelInk, maxLines = 2)
        Spacer(Modifier.height(8.dp)) // 16 dp above the [Done] row (B31)
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Txt(stringResource(R.string.align_note), "align/note", style = PicoTheme.typography.bodySmall, color = HcColors.PanelInkSecondary, maxLines = 2, modifier = Modifier.weight(1f))
            Spacer(Modifier.width(16.dp))
            PrimaryButton(stringResource(R.string.align_done), "align/done", onClick = { graph.leaveAlign() }, icon = R.drawable.ic_check, modifier = Modifier.width(160.dp))
        }
    }
}

@Composable
private fun OpenChip(graph: Graph) {
    Box(Modifier.clip(RoundedCornerShape(28.dp)).background(HcColors.PanelFace)) {
        PrimaryButton(stringResource(R.string.open_controls), "chip/open", onClick = { graph.window.open("chip") }, icon = R.drawable.ic_open_in_new, modifier = Modifier.width(260.dp))
    }
}
