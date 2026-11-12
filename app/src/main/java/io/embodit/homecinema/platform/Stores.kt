package io.embodit.homecinema.platform

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioManager
import android.media.MediaPlayer
import android.util.Log
import io.embodit.homecinema.domain.AMBIENCE_PERCENT
import io.embodit.homecinema.domain.Language
import io.embodit.homecinema.domain.OwnAudioGuard
import io.embodit.homecinema.domain.Settings
import io.embodit.homecinema.domain.Style
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/** SharedPreferences-backed settings; the chosen style, switches, language and "aligned once" survive relaunch. */
class SettingsStore(context: Context) {
    private val prefs = context.getSharedPreferences("settings", Context.MODE_PRIVATE)
    private val flow = MutableStateFlow(read())
    val settings: StateFlow<Settings> = flow.asStateFlow()
    val value: Settings get() = flow.value

    private fun read() = Settings(
        style = Style.of(prefs.getString("style", null)),
        auto = prefs.getBoolean("auto", true),
        ambience = prefs.getBoolean("ambience", false),
        volume = prefs.getInt("volume", 2).coerceIn(0, 2),
        muted = prefs.getBoolean("muted", false),
        language = runCatching { Language.valueOf(prefs.getString("language", "SYSTEM")!!) }.getOrDefault(Language.SYSTEM),
        aligned = prefs.getBoolean("aligned", false),
    )

    fun update(change: (Settings) -> Settings) {
        val next = change(flow.value)
        if (next == flow.value) return
        flow.value = next
        prefs.edit()
            .putString("style", next.style.id).putBoolean("auto", next.auto).putBoolean("ambience", next.ambience)
            .putInt("volume", next.volume).putBoolean("muted", next.muted).putString("language", next.language.name)
            .putBoolean("aligned", next.aligned)
            .apply()
        Log.i(TAG, "SETTINGS $next")
    }

    /** Debug "fresh": back to the first-launch state. */
    fun reset() { prefs.edit().clear().apply(); flow.value = Settings() }
}

/**
 * "Is the other app playing?" (feasibility Q4: AudioManager.isMusicActive is the only reliable signal; no media sessions).
 * Our own ambience also plays on the music stream, and isMusicActive stays true for a moment after our player is
 * released (QA q2-1: a manual end was undone ~50 ms after `AMBIENCE released`). [OwnAudioGuard] ignores the plain
 * flag while our player exists and for 2 s after it went away; in that window we read the active playback list with
 * our own USAGE_GAME player filtered out (other players report USAGE_MEDIA / UNKNOWN). Debug can force the reading for
 * emulator tests; the forced value goes through the same [ShowMachine.onSound] path as the real one.
 */
class SoundProbe(context: Context) {
    private val am = context.getSystemService(AudioManager::class.java)
    private val guard = OwnAudioGuard()
    @Volatile var forced: Boolean? = null

    fun read(now: Long, ownPlayer: Boolean): Boolean {
        val music = am.isMusicActive
        val others = if (ownPlayer || guard.suppressed(now)) othersPlaying() else null
        val r = guard.reading(now, ownPlayer, music, others)
        if (music && !r && !ownPlayer && forced == null) Log.i(TAG, "SOUND ignore own ambience (musicActive=true, own=$ownPlayer, others=$others)")
        return forced ?: r
    }

    private fun othersPlaying(): Boolean? = runCatching {
        am.activePlaybackConfigurations.any { it.audioAttributes.usage == AudioAttributes.USAGE_MEDIA || it.audioAttributes.usage == AudioAttributes.USAGE_UNKNOWN }
    }.getOrNull()
}

/**
 * One looping ambience per style (CC0 recording, design toggle-ambience): fades with the show, never stacks (a style
 * change releases the old player before the new one starts), released on exit. USAGE_GAME so [SoundProbe] can tell it
 * apart from the other app's video sound.
 */
class AmbiencePlayer(private val context: Context) {
    private var player: MediaPlayer? = null
    private var loaded: String? = null
    var gain = 0f
        private set
    val audible: Boolean get() = player?.isPlaying == true && gain > 0.001f
    /** Our player exists (opened, maybe fading at gain 0, not yet released): the sound probe must not count it. */
    val holding: Boolean get() = player != null

    /** Called ~20 times a second by the show ticker: target 0..1 (show level), style, settings. */
    fun drive(style: Style, settings: Settings, showMix: Float) {
        val name = style.ambience
        val want = if (settings.ambience && !settings.muted && name != null) showMix else 0f
        if (want <= 0.001f && gain <= 0.001f) { stop(); return }
        if (name != loaded) { stop(); if (name == null) return; open(name) }
        val p = player ?: return
        // fade toward the target, at most ~2 s from silence to full (no clicks)
        val step = 0.025f
        gain = if (want > gain) minOf(want, gain + step) else maxOf(want, gain - step)
        val v = gain * AMBIENCE_PERCENT[settings.volume.coerceIn(0, 2)] / 100f
        runCatching { p.setVolume(v, v); if (!p.isPlaying && gain > 0.001f) p.start() }
    }

    private fun open(name: String) {
        runCatching {
            val fd = context.assets.openFd("sounds/$name.ogg")
            val p = MediaPlayer()
            p.setAudioAttributes(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_GAME).setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build())
            p.setDataSource(fd.fileDescriptor, fd.startOffset, fd.length)
            fd.close()
            p.isLooping = true
            p.prepare()
            p.setVolume(0f, 0f)
            player = p
            loaded = name
            gain = 0f
            Log.i(TAG, "AMBIENCE open $name")
        }.onFailure { Log.w(TAG, "AMBIENCE open $name failed: $it") }
    }

    fun stop() {
        player?.let { p -> runCatching { p.stop() }; runCatching { p.release() }; Log.i(TAG, "AMBIENCE released $loaded") }
        player = null
        loaded = null
        gain = 0f
    }
}
