package io.embodit.homecinema.platform

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Handler
import android.os.Looper
import android.util.Log
import io.embodit.homecinema.domain.Cause
import io.embodit.homecinema.domain.Language
import io.embodit.homecinema.domain.Style

/**
 * QA screenshots: `adb shell am broadcast -a io.embodit.homecinema.DEBUG -p io.embodit.homecinema --es state <cmd> [--es v <value>]`.
 * Every command calls the same Graph function as the panel button (build.md 2026-10-29: no debug shortcuts that set
 * state directly). The design states[] are: lights-up, first-launch-align, showing, settings.
 */
object DebugReceiver {
    const val ACTION = "io.embodit.homecinema.DEBUG"

    fun register(context: Context, graph: Graph) {
        context.registerReceiver(object : BroadcastReceiver() {
            override fun onReceive(c: Context, intent: Intent) {
                val cmd = intent.getStringExtra("state") ?: intent.getStringExtra("cmd") ?: return
                val v = intent.getStringExtra("v")
                Handler(Looper.getMainLooper()).post { run(graph, cmd, v) }
            }
        }, IntentFilter(ACTION), Context.RECEIVER_EXPORTED)
    }

    fun run(g: Graph, cmd: String, v: String?) {
        Log.i(TAG, "DEBUG $cmd ${v ?: ""}")
        when (cmd) {
            // design states[]
            "lights-up" -> { if (g.align) g.leaveAlign(); g.endShow(Cause.DEBUG); g.page = Page.SHOW; g.exitConfirm = false }
            "first-launch-align" -> { g.enterAlign(); g.page = Page.SHOW }
            "showing" -> { if (g.align) g.leaveAlign(); g.startShow(Cause.DEBUG); g.page = Page.SHOW }
            "settings" -> { g.page = Page.SETTINGS; g.exitConfirm = false }
            // actions
            "show" -> g.page = Page.SHOW
            "toggle-show" -> g.toggleShow(Cause.MANUAL)
            "style" -> g.settings.update { it.copy(style = Style.of(v)) }
            "style-next" -> g.settings.update { it.copy(style = it.style.next(1)) }
            "style-prev" -> g.settings.update { it.copy(style = it.style.next(-1)) }
            "auto" -> g.setAuto(v != "off")
            "timer" -> g.setTimer(v?.toIntOrNull() ?: 0)
            "ambience" -> g.settings.update { it.copy(ambience = v != "off") }
            "volume" -> g.settings.update { it.copy(volume = (v?.toIntOrNull() ?: 2).coerceIn(0, 2)) }
            "mute" -> g.settings.update { it.copy(muted = v != "off") }
            "lang" -> g.settings.update { it.copy(language = when (v) { "en" -> Language.EN; "zh" -> Language.ZH; else -> Language.SYSTEM }) }
            "align" -> g.enterAlign()
            "align-done" -> g.leaveAlign()
            // sound sensor override (emulator has no other app playing on demand): same ShowMachine.onSound path
            "sound" -> g.probe.forced = when (v) { "on" -> true; "off" -> false; else -> null }
            "exit-confirm" -> { g.page = Page.SETTINGS; g.exitConfirm = true }
            "exit-cancel" -> g.exitConfirm = false
            "exit" -> g.exit()
            "reopen" -> g.window.reopen()
            "close-controls" -> g.window.closeControlsOnly()
            "open-controls" -> g.window.open("debug")
            "fresh" -> { g.settings.reset(); g.enterAlign() }
            // emulator light calibration only: v = "base=6000,soft=9000,emit=1.5" (empty / "off" = the style's own values)
            "light" -> io.embodit.homecinema.domain.Lighting.override = parseLight(v, g.settings.value.style)
            "dump" -> Unit
            else -> Log.w(TAG, "DEBUG unknown $cmd")
        }
        Log.i(TAG, g.dump())
    }

    private fun parseLight(v: String?, style: Style): io.embodit.homecinema.domain.StyleLight? {
        if (v.isNullOrBlank() || v == "off") return null
        var l = io.embodit.homecinema.domain.Lighting.of(style)
        v.split(',').forEach { kv ->
            val (k, x) = kv.split('=').let { it[0].trim() to (it.getOrNull(1)?.trim()?.toFloatOrNull() ?: return@forEach) }
            l = when (k) { "base" -> l.copy(baseLux = x); "soft" -> l.copy(softLux = x); "emit" -> l.copy(emitGain = x); else -> l }
        }
        return l
    }
}
