package io.embodit.homecinema.platform

import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.pico.spatial.ui.platform.containers.SpatialNavigator

/** Ids of the two window containers. The frame is the default container (manifest). */
object Containers {
    const val FRAME = "CinemaFrame"
    const val CONTROLS = "CinemaControls"
    const val CONTROLS_TAG = "controls"
}

/**
 * Opens / reopens the controls window. Shared Space only (profile D44 correction): no "bring in front of you"; the
 * window always opens with Placement.right(frame) (Main.kt), so it never lands on the opening. [reopen] = close, wait
 * for ON_DESTROY, open again. Exit closes both containers before the tasks are removed (D44).
 * No head pose is read anywhere in this app (Shared Space has none, and the frame is placed by the user).
 */
class WindowCtl {
    var panelState by mutableStateOf("never")
        private set
    val panelOpen: Boolean get() = panelState != "never" && panelState != "ON_DESTROY"
    var exiting = false
        private set

    private var navigator: SpatialNavigator? = null
    private var reopenPending = false

    fun attach(nav: SpatialNavigator) { navigator = nav }
    fun detach(nav: SpatialNavigator) { if (navigator === nav) navigator = null }

    fun open(why: String) {
        if (exiting) return
        Log.i(TAG, "WINDOW open why=$why state=$panelState")
        runCatching { navigator?.openWindowContainer(Containers.CONTROLS, Containers.CONTROLS_TAG) }.onFailure { Log.e(TAG, "WINDOW open failed", it) }
    }

    /** Settings [Reopen controls]. */
    fun reopen() {
        if (!panelOpen) open("reopen")
        else { reopenPending = true; Log.i(TAG, "WINDOW reopen close"); runCatching { navigator?.closeWindowContainer(Containers.CONTROLS, Containers.CONTROLS_TAG) } }
    }

    fun onPanelLifecycle(event: String) {
        panelState = event
        Log.i(TAG, "WINDOW lifecycle $event")
        if (reopenPending && event == "ON_DESTROY") { reopenPending = false; open("reopen") }
    }

    /** Debug: the system [×] on the controls window (the frame then offers [Open controls]). */
    fun closeControlsOnly() { runCatching { navigator?.closeWindowContainer(Containers.CONTROLS, Containers.CONTROLS_TAG) } }

    fun closeAll() {
        exiting = true
        val nav = navigator ?: return
        runCatching { nav.closeWindowContainer(Containers.CONTROLS, Containers.CONTROLS_TAG) }.onFailure { Log.w(TAG, "EXIT close controls: $it") }
        runCatching { nav.closeWindowContainer() }.onFailure { Log.w(TAG, "EXIT close frame: $it") }
        Log.i(TAG, "EXIT closed all window containers")
    }
}
