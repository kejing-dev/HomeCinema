package io.embodit.homecinema.scene

import android.os.SystemClock
import android.util.Log
import com.pico.spatial.core.ecs.DirectionalLightComponent
import com.pico.spatial.core.ecs.Entity
import com.pico.spatial.core.ecs.ModelComponent
import com.pico.spatial.core.ecs.OpacityControllerComponent
import com.pico.spatial.core.ecs.TransformComponent
import com.pico.spatial.core.ecs.resource.BlendingMode
import com.pico.spatial.core.ecs.resource.MaterialCullingMode
import com.pico.spatial.core.ecs.resource.MeshResource
import com.pico.spatial.core.ecs.resource.PhysicallyBasedMaterial
import com.pico.spatial.core.ecs.resource.UnlitMaterial
import com.pico.spatial.core.math.Color4
import com.pico.spatial.core.math.Quat
import com.pico.spatial.core.math.Vector3
import io.embodit.homecinema.domain.FrameLayout
import io.embodit.homecinema.domain.Lighting
import io.embodit.homecinema.domain.Style
import io.embodit.homecinema.platform.TAG
import kotlin.math.PI

internal fun Entity.transform(): TransformComponent = components[TransformComponent::class.java]!!

/** A loaded wall treatment: its root and the soft-light (emit_*) materials with their authored emissive colour. */
private class LoadedFrame(val style: Style, val root: Entity, val emit: List<Pair<PhysicallyBasedMaterial, Color4>>)

/**
 * Everything in the frame Volume (design node frame-model + align-outline).
 *
 * ```
 * root (volume centre) └ fit (uniform scale so the 3.4 x 2.0 m model fills the volume's real size)
 *   ├ frame_<style>.glb, shifted back so the wall sits at the back of the volume (player in front, A3)
 *   ├ outline: 4 dashed edges round the 1.6 x 0.9 m player rect (align mode only, unlit, no collider)
 *   └ key light
 * ```
 * The opening holds no geometry and no collider. Nothing in the Volume is interactable except the two attachment panels
 * (align card, [Open controls] chip), which sit below the opening. Per-frame work runs from [FrameSystem].
 */
internal class FrameScene {
    val root: Entity = Entity().apply { setName("root") }
    private val fit = Entity().apply { setName("fit") }
    private val outline = Entity().apply { setName("alignOutline"); enabled = false }
    private var current: LoadedFrame? = null
    private var leaving: LoadedFrame? = null
    private var fadeStart = 0L
    private var lastLevel = -1f
    private var scale = 1f
    @Volatile var wantOutline = false
    private var baseLight: DirectionalLightComponent? = null
    private var softLight: DirectionalLightComponent? = null
    private var baseNow = -1f
    private var softNow = -1f
    private var lastLightLog = 0L
    /** Process-start -> first frame model shown (startup budget <= 2 s, QA #1 K4). */
    var firstShownAt = 0L
        private set

    init {
        root.addChild(fit)
        fit.addChild(outline)
        buildLight()
    }

    /** Real half extents of the volume in metres (from the view); keeps the 16:9 opening's shape. */
    fun setRegion(halfX: Float, halfY: Float) {
        val s = FrameLayout.fitScale(halfX, halfY)
        if (kotlin.math.abs(s - scale) < 1e-4f) return
        scale = s
        fit.transform().setScaleVector(Vector3(s, s, s))
        Log.i(TAG, "SCENE region half=${"%.3f".format(halfX)}x${"%.3f".format(halfY)} m scale=${"%.3f".format(s)}")
    }

    /** Add a newly loaded GLB and cross-fade to it (design choose-style: 1.2 s). */
    fun show(style: Style, model: Entity) {
        model.setName("frame-${style.id}")
        model.transform().setPosition(Vector3(0f, 0f, FrameLayout.MODEL_Z))
        val emit = ArrayList<Pair<PhysicallyBasedMaterial, Color4>>()
        model.walk { e ->
            val mc = e.components[ModelComponent::class.java] ?: return@walk
            for (m in mc.materials) {
                val name = runCatching { (m as? PhysicallyBasedMaterial)?.getName() }.getOrNull() ?: continue
                if (name.startsWith("emit_")) emit += (m as PhysicallyBasedMaterial).let { pm -> pm to pm.getEmissiveColor() }
            }
        }
        Log.i(TAG, "FRAME ${style.id} soft-light materials=${emit.map { it.first.getName() }}")
        leaving?.let { drop(it) }
        leaving = current
        current = LoadedFrame(style, model, emit)
        fit.addChild(model)
        lastLevel = -1f
        if (firstShownAt == 0L) {
            firstShownAt = SystemClock.elapsedRealtime()
            val sinceStart = firstShownAt - android.os.Process.getStartElapsedRealtime()
            Log.i(TAG, "STARTUP frame ${style.id} visible ${sinceStart} ms after process start")
        }
        if (leaving != null) {
            model.components.set(OpacityControllerComponent(0f))
            leaving!!.root.components.set(OpacityControllerComponent(1f))
            fadeStart = SystemClock.uptimeMillis()
        }
    }

    val currentStyle: Style? get() = current?.style

    /** Put an attachment panel below the opening (scales with the frame). */
    fun attach(e: Entity, at: FrameLayout.Rect3) {
        runCatching { e.removeFromParentSafe() }
        fit.addChild(e)
        e.transform().setPosition(Vector3(at.x, at.y, at.z))
        // undo the frame's fit scale so the card reads at the system's native panel size (emulator: fit 0.635)
        e.transform().setScaleVector(Vector3(FrameLayout.ATTACH_SCALE, FrameLayout.ATTACH_SCALE, FrameLayout.ATTACH_SCALE))
        Log.i(TAG, "ATTACH ${e.getName()} at ${at.x},${at.y},${at.z}")
    }

    /** Per frame: soft light level (0..1) and the cross-fade. */
    fun onFrame(level: Float) {
        val now = SystemClock.uptimeMillis()
        val old = leaving
        val cur = current
        if (old != null && cur != null) {
            val t = ((now - fadeStart) / FrameLayout.CROSSFADE_MS.toFloat()).coerceIn(0f, 1f)
            cur.root.components[OpacityControllerComponent::class.java]?.opacity = t
            old.root.components[OpacityControllerComponent::class.java]?.opacity = 1f - t
            if (t >= 1f) {
                // build.md 2026-10-29: an opacity component at 1.0 still renders blended — remove it, don't just set 1
                cur.root.components.remove(OpacityControllerComponent::class.java)
                drop(old)
                leaving = null
                Log.i(TAG, "FRAME cross-fade done -> ${cur.style.id}")
            }
        }
        if (cur != null) {
            val (baseLux, softLux, emit) = Lighting.at(Lighting.current(cur.style), level)
            // lights ease toward the style's values (~0.4 s), so a style change or a debug tweak never pops
            baseNow = if (baseNow < 0f) baseLux else baseNow + (baseLux - baseNow) * 0.12f
            softNow = if (softNow < 0f) softLux else softNow + (softLux - softNow) * 0.12f
            runCatching { baseLight?.intensity = baseNow; softLight?.intensity = softNow }
            if (kotlin.math.abs(emit - lastLevel) > 0.002f) {
                lastLevel = emit
                for ((m, base) in cur.emit) runCatching { m.setEmissiveColor(Color4(base.red * emit, base.green * emit, base.blue * emit, 1f)) }
                old?.emit?.forEach { (m, base) -> runCatching { m.setEmissiveColor(Color4(base.red * emit, base.green * emit, base.blue * emit, 1f)) } }
            }
            if (now - lastLightLog > 5000) {
                lastLightLog = now
                Log.i(TAG, "LIGHT ${cur.style.id} level=${"%.2f".format(level)} base=${baseNow.toInt()} soft=${softNow.toInt()} emit=${"%.2f".format(emit)}")
            }
        }
        if (outline.enabled != wantOutline) outline.enabled = wantOutline
    }

    private fun drop(f: LoadedFrame) {
        runCatching { fit.removeChild(f.root) }
        runCatching { f.root.destroy(true) }
    }

    /** Dashed guide round the player rect (design align-outline): abstract indicator, unlit, no collider. */
    fun buildOutline() {
        runCatching {
            val mat = UnlitMaterial.create(BlendingMode.OPAQUE).apply {
                setBaseColor(Color4(0.44f, 0.66f, 0.86f, 1f)); setCullingMode(MaterialCullingMode.NONE); setApplyToneMapping(false)
            }
            val w = FrameLayout.PLAYER_W
            val h = FrameLayout.PLAYER_H
            val z = FrameLayout.OUTLINE_Z
            val t = 0.008f
            for (seg in FrameLayout.dashes(w, h)) {
                // gate:allow geometry align-mode dashed outline of the opening (abstract guide, unlit, no collider, hidden after Done)
                val mesh = MeshResource.createBox(Vector3(if (seg.horizontal) seg.length else t, if (seg.horizontal) t else seg.length, 0.004f), 0f)
                val e = Entity().apply { setName("dash") }
                e.components.set(ModelComponent(mesh, mat))
                e.transform().setPosition(Vector3(seg.x, seg.y, z))
                outline.addChild(e)
            }
            Log.i(TAG, "OUTLINE built")
        }.onFailure { Log.w(TAG, "OUTLINE failed: $it") }
    }

    private fun buildLight() {
        runCatching {
            // B24: a moderate, slightly warm key light from above front-left (constant; lux-scale, see Lighting) ...
            val key = Entity().apply { setName("keyLight") }
            val kc = DirectionalLightComponent(Color4(1f, 0.95f, 0.88f, 1f), 0f, false)
            key.components.set(kc)
            key.transform().setQuaternion(Quat(Vector3(0f, 1f, 0f), (-20 * PI / 180).toFloat()).times(Quat(Vector3(1f, 0f, 0f), (-40 * PI / 180).toFloat())))
            root.addChild(key)
            baseLight = kc
            // ... and the soft light: a warm front wash from just above eye height, dimmed with the show
            val wash = Entity().apply { setName("softWash") }
            val wc = DirectionalLightComponent(Color4(1f, 0.88f, 0.74f, 1f), 0f, false)
            wash.components.set(wc)
            wash.transform().setQuaternion(Quat(Vector3(1f, 0f, 0f), (-18 * PI / 180).toFloat()))
            root.addChild(wash)
            softLight = wc
        }.onFailure { Log.w(TAG, "LIGHT unavailable: $it") }
    }

    fun dispose() {
        current?.let { drop(it) }
        leaving?.let { drop(it) }
        current = null
        leaving = null
    }
}

internal fun Entity.removeFromParentSafe() { getParent()?.removeChild(this) }

internal fun Entity.walk(f: (Entity) -> Unit) {
    f(this)
    for (c in getChildren()) c.walk(f)
}
