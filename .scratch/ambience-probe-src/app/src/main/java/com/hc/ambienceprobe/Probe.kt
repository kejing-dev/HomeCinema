package com.hc.ambienceprobe

import android.app.Activity
import android.app.Application
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.media.AudioManager
import android.media.session.MediaSessionManager
import android.util.Log
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pico.spatial.core.container.getSelfSpaceState
import com.pico.spatial.ui.design.Button
import com.pico.spatial.ui.design.PicoTheme
import com.pico.spatial.ui.design.Text
import com.pico.spatial.ui.foundation.dsl.Brightness
import com.pico.spatial.ui.foundation.dsl.DefaultWindowContainer
import com.pico.spatial.ui.foundation.dsl.SpatialAppScope
import com.pico.spatial.ui.foundation.dsl.Stage
import com.pico.spatial.ui.foundation.dsl.launch
import com.pico.spatial.ui.platform.containers.StageStyle
import com.pico.spatial.ui.platform.containers.closeStage
import com.pico.spatial.ui.platform.containers.openStage
import com.pico.spatial.ui.platform.stub.SpatialLaunchActivity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/** Feasibility probe for home-cinema 门 B 改: coexistence, space state, stage dimming, playback signals. Not shipped. */
const val TAG = "AmbProbe"

class LaunchActivity : SpatialLaunchActivity()

object Probe {
    val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    var ctx: Context? = null
    var status by mutableStateOf("…")

    fun snapshot(c: Context): String {
        val am = c.getSystemService(AudioManager::class.java)
        val space = runCatching { c.getSelfSpaceState().name }.getOrElse { "ERR " + it.javaClass.simpleName }
        val music = am.isMusicActive
        val cfgs = runCatching { am.activePlaybackConfigurations.map { it.audioAttributes.usage } }.getOrElse { listOf(-1) }
        val sessions = runCatching {
            c.getSystemService(MediaSessionManager::class.java).getActiveSessions(null).map { it.packageName }.toString()
        }.getOrElse { it.javaClass.simpleName + ": " + (it.message ?: "").take(80) }
        return "space=$space musicActive=$music playbackCfgUsages=$cfgs sessions=$sessions"
    }

    fun cmd(c: String) {
        val context = ctx ?: return run { Log.w(TAG, "no ctx") }
        scope.launch {
            val r = runCatching {
                when (c) {
                    "mixed" -> context.openStage("DimStage", StageStyle.Mixed).toString()
                    "prog" -> context.openStage("DimStage", StageStyle.Progressive).toString()
                    "full" -> context.openStage("DimStage", StageStyle.Full).toString()
                    "close" -> { closeStage(); "closed" }
                    else -> "noop"
                }
            }
            Log.i(TAG, "cmd=$c result=${r.getOrElse { "EXC $it" }}")
            delay(1500)
            Log.i(TAG, "after $c: " + snapshot(context))
        }
    }
}

class ProbeApp : Application() {
    override fun onCreate() {
        super.onCreate()
        registerReceiver(object : BroadcastReceiver() {
            override fun onReceive(context: Context, intent: Intent) {
                Probe.cmd(intent.getStringExtra("cmd") ?: "")
            }
        }, IntentFilter("com.hc.ambienceprobe.CMD"), Context.RECEIVER_EXPORTED)
        Probe.scope.launch {
            while (true) {
                val c = Probe.ctx ?: this@ProbeApp
                Probe.status = Probe.snapshot(c)
                Log.i(TAG, "tick " + Probe.status)
                delay(3000)
            }
        }
        launch(::probeApp)
    }
}

fun probeApp(scope: SpatialAppScope) = with(scope) {
    DefaultWindowContainer { PicoTheme { ProbeVolume() } }
    Stage("DimStage", brightness = Brightness.Dark) { PicoTheme { StagePanel() } }
}

@Composable
fun ProbeVolume() {
    val c = LocalContext.current
    LaunchedEffect(Unit) { Probe.ctx = c; Log.i(TAG, "volume composed, activity=${c is Activity}") }
    Box(Modifier.fillMaxSize().border(24.dp, Color(0xFFB8862B)), contentAlignment = Alignment.BottomCenter) {
        Column(
            Modifier.padding(32.dp).background(Color(0xCC111111)).padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("Ambience probe — gold border = our volume", color = Color.White, fontSize = 18.sp)
            Text(Probe.status, color = Color.White, fontSize = 14.sp)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = { Probe.cmd("mixed") }) { Text("Stage Mixed+Dark") }
                Button(onClick = { Probe.cmd("prog") }) { Text("Stage Progressive") }
                Button(onClick = { Probe.cmd("close") }) { Text("Close Stage") }
            }
        }
    }
}

@Composable
fun StagePanel() {
    Box(Modifier.size(400.dp, 200.dp).background(Color(0xCC331100)), contentAlignment = Alignment.Center) {
        Text("DimStage open", color = Color.White, fontSize = 24.sp)
    }
}
