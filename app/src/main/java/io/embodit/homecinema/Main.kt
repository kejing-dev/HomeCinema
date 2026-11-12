package io.embodit.homecinema

import androidx.compose.foundation.layout.Box
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.pico.spatial.ui.foundation.dsl.DefaultWindowContainer
import com.pico.spatial.ui.foundation.dsl.Form
import com.pico.spatial.ui.foundation.dsl.Placement
import com.pico.spatial.ui.foundation.dsl.SpatialAppScope
import com.pico.spatial.ui.foundation.dsl.WindowContainer
import com.pico.spatial.ui.foundation.dsl.WindowContainerSize
import io.embodit.homecinema.platform.Containers
import io.embodit.homecinema.scene.FrameScreen
import io.embodit.homecinema.ui.ControlWindow
import io.embodit.homecinema.ui.HcTheme

/**
 * Shared Space only (design surfaces): the frame Volume (default container, 3.4 x 2.0 x 0.6 m from the manifest,
 * transparent, uniform resize) and the controls window (Planar 480 x 760 dp; 720 -> 760 for the 64 dp buttons / 16 dp gaps, QA #1 q1-1) to its right. First open and every reopen
 * use Placement.right(frame), so the window never covers the opening (profile D44: no "in front of you").
 * No Stage: Stage forces Full Space, which hides the other app's player and stops its sound (feasibility.md).
 */
fun mainApp(scope: SpatialAppScope) =
    with(scope) {
        DefaultWindowContainer {
            HcTheme { FrameScreen() }
        }
        WindowContainer(
            Containers.CONTROLS,
            form = Form.Planar,
            defaultSize = WindowContainerSize(width = 480.dp, height = 760.dp),
            placement = { containers.firstOrNull { it.id == Containers.FRAME }?.let { Placement.right(it) } ?: Placement.none() },
        ) {
            HcTheme {
                Box(Modifier.windowConstraints(minWidth = 460.dp, minHeight = 720.dp, maxWidth = 640.dp, maxHeight = 820.dp)) { ControlWindow() }
            }
        }
    }
