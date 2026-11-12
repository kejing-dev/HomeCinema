package io.embodit.homecinema.platform

import android.app.ActivityManager
import android.app.Application
import android.content.Context
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.pico.spatial.ui.foundation.dsl.launch
import com.pico.spatial.ui.platform.stub.SpatialLaunchActivity
import io.embodit.homecinema.domain.Cause
import io.embodit.homecinema.domain.Phase
import io.embodit.homecinema.domain.ShowMachine
import io.embodit.homecinema.domain.ShowState
import io.embodit.homecinema.domain.SleepTimer
import io.embodit.homecinema.mainApp
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlin.system.exitProcess

const val TAG = "HomeCinema"

class LaunchActivity : SpatialLaunchActivity()

class SpatialApplication : Application() {
    lateinit var graph: Graph
        private set

    override fun onCreate() {
        super.onCreate()
        graph = Graph(this)
        DebugReceiver.register(this, graph)
        launch(::mainApp)
    }
}

enum class Page { SHOW, SETTINGS }

/**
 * Process-wide state shared by the frame Volume and the controls window (native-window-move.md §3.4).
 * The show runs on a 50 ms ticker here, not in Compose and not in the render loop, so it keeps going while a window
 * is closed; the frame's ECS system only reads [lightLevel] each frame.
 */
class Graph(val context: Context) {
    val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    val settings = SettingsStore(context)
    val probe = SoundProbe(context)
    val ambience = AmbiencePlayer(context)
    val window = WindowCtl()
    private val machine = ShowMachine(settings.value.auto)
    private val timer = SleepTimer()

    // Compose-visible snapshot (written only on the main thread by the ticker / commands)
    var show by mutableStateOf(ShowState())
        private set
    var timerLeft by mutableStateOf<Long?>(null)
        private set
    var timerMinutes by mutableStateOf(0)
        private set
    var page by mutableStateOf(Page.SHOW)
    var exitConfirm by mutableStateOf(false)
    /** Align mode (first launch, or [Align frame to player]). */
    var align by mutableStateOf(!settings.value.aligned)
        private set
    var soundReading by mutableStateOf<Boolean?>(null)
        private set

    /** Read by the frame every render frame. */
    @Volatile var lightLevel = 1f
        private set

    private var ticker: Job? = null
    private var lastPoll = 0L

    init {
        if (align) Log.i(TAG, "ALIGN first launch")
        startTicker()
    }

    private fun now() = SystemClock.elapsedRealtime()

    private fun startTicker() {
        ticker = scope.launch {
            while (isActive) {
                step()
                delay(50)
            }
        }
    }

    private fun step() {
        val t = now()
        machine.auto = settings.value.auto
        var changed = machine.tick(t)
        if (t - lastPoll >= 1000) {
            lastPoll = t
            val active = probe.read(t, ambience.holding)
            if (soundReading != active) Log.i(TAG, "SOUND active=$active")
            soundReading = active
            if (machine.onSound(t, active)) changed = true
        }
        if (timer.expired(t)) {
            // the closing fade takes the ambience out with the light; the other app keeps playing
            Log.i(TAG, "TIMER expired: end the show, ambience fades out")
            machine.end(t, Cause.TIMER)
            changed = true
        }
        if (changed || machine.state != show) publish()
        timerLeft = timer.left(t)
        timerMinutes = timer.minutes
        // align mode keeps the light up so the opening is easy to see (design enter-align-mode)
        val level = if (align) 1f else machine.level(t)
        lightLevel = level
        val mix = ((1f - level) / (1f - ShowMachine.SHOW_LEVEL)).coerceIn(0f, 1f)
        ambience.drive(settings.value.style, settings.value, mix)
    }

    private fun publish() {
        val s = machine.state
        if (s.phase != show.phase) Log.i(TAG, "SHOW ${show.phase} -> ${s.phase} cause=${s.cause} override=${machine.override}")
        show = s
    }

    // ---- one path for the panel, the frame chip and the debug broadcast

    fun toggleShow(cause: Cause = Cause.MANUAL) {
        val t = now()
        if (machine.state.running) machine.end(t, cause) else machine.start(t, cause)
        publish()
    }

    fun startShow(cause: Cause) { machine.start(now(), cause); publish() }
    fun endShow(cause: Cause) { machine.end(now(), cause); publish() }

    fun setAuto(on: Boolean) { settings.update { it.copy(auto = on) }; machine.auto = on }

    fun setTimer(minutes: Int) {
        timer.set(minutes, now())
        timerMinutes = timer.minutes
        timerLeft = timer.left(now())
        Log.i(TAG, "TIMER set $minutes min")
    }

    fun enterAlign() { align = true; Log.i(TAG, "ALIGN on") }

    fun leaveAlign() {
        align = false
        settings.update { it.copy(aligned = true) }
        Log.i(TAG, "ALIGN off")
    }

    /** D26 / D44 exit: release audio, close both window containers, remove every task, end the process. */
    fun exit() {
        Log.i(TAG, "EXIT release + close windows + finishAndRemoveTask + exitProcess")
        ticker?.cancel()
        ambience.stop()
        window.closeAll()
        Handler(Looper.getMainLooper()).postDelayed({
            runCatching {
                val am = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
                am.appTasks.forEach { runCatching { it.finishAndRemoveTask() } }
            }
            Handler(Looper.getMainLooper()).postDelayed({ exitProcess(0) }, 500)
        }, 300)
    }

    fun dump(): String {
        val s = settings.value
        return "DUMP phase=${show.phase} cause=${show.cause} level=${"%.2f".format(lightLevel)} override=${machine.override} sound=$soundReading forced=${probe.forced} " +
            "align=$align page=$page exitConfirm=$exitConfirm timer=${timerMinutes}min left=${timerLeft} style=${s.style.id} auto=${s.auto} ambience=${s.ambience} " +
            "gain=${"%.2f".format(ambience.gain)} vol=${s.volume} muted=${s.muted} lang=${s.language} panel=${window.panelState}"
    }

    companion object {
        fun from(context: Context): Graph = (context.applicationContext as SpatialApplication).graph
    }
}

val Phase.isRunning: Boolean get() = this == Phase.OPENING || this == Phase.SHOWING
