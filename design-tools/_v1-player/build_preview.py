"""Build .scratch/preview.html (Home Cinema design Preview) from data.

Usage: python3 build_preview.py <scratch-dir>
Static HTML carries every Spec node (English default); JS switches language / state.
"""
import json, sys, os

OUT = sys.argv[1]

TITLES = [
    # key, en, zh, year, runtime, kind(en,zh), rating, overview en, overview zh, progress(0..1 or None)
    ("harbor", "Harbor Lights", "港湾灯火", 2023, "1h 52m", ("Drama", "剧情"), "4K · HDR",
     "A night-shift crane operator keeps a lantern burning for a ship that never arrives, until one foggy winter it finally does.",
     "夜班吊车司机每晚为一艘迟迟未归的船点灯，直到某个起雾的冬夜，它真的回来了。", 0.38),
    ("moon", "Paper Moon Express", "纸月亮快车", 2022, "1h 38m", ("Fantasy", "奇幻"), "1080p",
     "A sleeper train that only runs under a full moon carries strangers toward the places they forgot.",
     "一列只在满月夜运行的卧铺列车，载着陌生人驶向他们遗忘的地方。", 0.72),
    ("orchard", "The Quiet Orchard", "静谧果园", 2021, "1h 46m", ("Family", "家庭"), "4K",
     "Three siblings return to their grandmother's orchard for one last harvest.",
     "三兄妹回到外婆的果园，完成最后一次丰收。", None),
    ("vega", "Signal from Vega", "织女星信号", 2024, "2h 05m", ("Sci-fi", "科幻"), "4K · HDR",
     "A small-town radio club picks up a repeating pattern from a nearby star.",
     "小镇无线电社团收到了来自邻近恒星的重复信号。", 0.12),
    ("relay", "Desert Relay", "沙漠接力", 2020, "1h 41m", ("Adventure", "冒险"), "1080p",
     "Four runners carry a message across a desert where every phone has gone silent.",
     "所有电话都失灵后，四名跑者接力把一封信送过沙漠。", None),
    ("rain", "Rain on Glass", "雨窗", 2019, "1h 33m", ("Romance", "爱情"), "1080p",
     "Two neighbours who have never met share a window, a rainy season and a playlist.",
     "从未谋面的两位邻居，隔着一扇窗共享了一个雨季和一张歌单。", None),
    ("kite", "Kite Season", "风筝季", 2024, "1h 29m", ("Comedy", "喜剧"), "4K",
     "A retired engineer enters the city kite festival with a kite that refuses to fly.",
     "退休工程师带着一只怎么也飞不起来的风筝报名了城市风筝节。", None),
    ("keepers", "Lighthouse Keepers", "守塔人", 2023, "Season 1 · 8 episodes", ("Series", "剧集"), "4K",
     "Two keepers, one island, eight storms.",
     "两位守塔人，一座岛，八场风暴。", 0.55),
]
T = {t[0]: t for t in TITLES}

I18N = {
    "en": {
        "tab.items": "Home,Library,Sources,Settings",
        "home.title": "Home", "home.sub": "Demo library · 8 titles",
        "home.search": "Search library", "home.refresh": "Refresh library",
        "home.continue": "Continue watching", "home.recent": "Recently added",
        "left": "{m} min left",
        "lib.title": "Library", "lib.sub": "All titles from your connected sources",
        "lib.segments": "All,Movies,Shows",
        "src.title": "Sources", "src.sub": "Only media you own or are authorized to play",
        "src.add": "Add source",
        "src.demo.h": "Demo library", "src.demo.s": "Built in · 8 original short demo titles",
        "src.jf.h": "Living room Jellyfin", "src.jf.s": "http://192.168.1.20:8096 · Connected",
        "src.nas.h": "NAS · WebDAV", "src.nas.s": "https://nas.local/webdav/Movies · Connected",
        "src.local.h": "On this headset", "src.local.s": "Movies folder · 3 videos",
        "set.title": "Settings", "set.sub": "Home Cinema 0.1",
        "set.lang.h": "Language", "set.lang.v.sys": "Follow system", "set.lang.v.zh": "简体中文", "set.lang.v.en": "English",
        "set.depth.h": "3D poster depth", "set.depth.s": "Off · Subtle · Standard · Strong",
        "set.depth.levels": "Off,Subtle,Standard,Strong",
        "set.resume.h": "Resume where you left off", "set.resume.s": "Start from the saved position automatically",
        "set.sub.h": "Preferred subtitles", "set.sub.v": "Chinese",
        "set.audio.h": "Preferred audio", "set.audio.v": "Original",
        "set.clear.h": "Clear watch history", "set.clear.s": "Removes saved positions on this headset",
        "set.about.h": "About", "set.about.s": "Plays media you own. Home Cinema provides no films or streams.",
        "set.exit": "Exit Home Cinema",
        "det.title": "Details", "det.close": "Close details",
        "det.resume": "Resume {t}", "det.play": "Play", "det.restart": "Play from start",
        "det.audio": "Audio", "det.audio.v": "Original · Stereo",
        "det.subs": "Subtitles", "det.subs.v": "Chinese (SRT)",
        "det.eps": "Episodes",
        "sheet.title": "Add media source", "sheet.emby": "Emby", "sheet.jf": "Jellyfin", "sheet.dav": "NAS (WebDAV)", "sheet.local": "Headset storage",
        "sheet.server": "Server address", "sheet.user": "Username", "sheet.pass": "Password",
        "sheet.server.ph": "http://192.168.1.20:8096", "sheet.user.ph": "Your account name", "sheet.pass.ph": "Password",
        "sheet.note": "Only connect to servers and files you own or are authorized to use.",
        "sheet.connect": "Connect", "sheet.pick": "Choose folder",
        "sheet.local.note": "Home Cinema reads video files from the folder you choose on this headset.",
        "cin.exit": "Exit cinema", "cin.subs": "Subtitles", "cin.audio": "Audio track", "cin.size": "Screen size",
        "cin.env": "Dim the room", "cin.back": "Back 15 seconds", "cin.fwd": "Forward 15 seconds",
        "cin.play": "Play", "cin.pause": "Pause", "cin.vol": "Volume",
        "cin.subline": "The fog is lifting. Keep the lantern burning.",
        "cin.sub.off": "Off", "cin.sub.zh": "Chinese (SRT)", "cin.sub.en": "English (embedded)", "cin.sub.load": "Load subtitle file…",
        "cin.aud.1": "Original · Stereo", "cin.aud.2": "Commentary · Stereo",
        "cin.size.s": "Small · 3 m", "cin.size.m": "Medium · 6 m", "cin.size.l": "Large · 10 m",
        "clear.title": "Clear watch history?", "clear.body": "Saved positions for all titles on this headset will be removed.",
        "clear.ok": "Clear", "clear.cancel": "Cancel",
        "snack.cleared": "Watch history cleared", "ep.1": "48 min · Watched", "ep.2": "51 min · 21 min left", "ep.3": "49 min", "snack.connected": "Source connected",
    },
    "zh": {
        "tab.items": "首页,媒体库,媒体源,设置",
        "home.title": "首页", "home.sub": "演示片库 · 8 部",
        "home.search": "搜索片库", "home.refresh": "刷新片库",
        "home.continue": "继续观看", "home.recent": "最近添加",
        "left": "剩余 {m} 分钟",
        "lib.title": "媒体库", "lib.sub": "所有已连接媒体源中的影片",
        "lib.segments": "全部,电影,剧集",
        "src.title": "媒体源", "src.sub": "只连接你拥有或有权播放的媒体",
        "src.add": "添加媒体源",
        "src.demo.h": "演示片库", "src.demo.s": "内置 · 8 部原创演示短片",
        "src.jf.h": "客厅 Jellyfin", "src.jf.s": "http://192.168.1.20:8096 · 已连接",
        "src.nas.h": "NAS · WebDAV", "src.nas.s": "https://nas.local/webdav/Movies · 已连接",
        "src.local.h": "本机存储", "src.local.s": "Movies 文件夹 · 3 个视频",
        "set.title": "设置", "set.sub": "私人影院 0.1",
        "set.lang.h": "语言", "set.lang.v.sys": "跟随系统", "set.lang.v.zh": "简体中文", "set.lang.v.en": "English",
        "set.depth.h": "3D 海报景深", "set.depth.s": "关 · 轻微 · 标准 · 强烈",
        "set.depth.levels": "关,轻微,标准,强烈",
        "set.resume.h": "从上次位置继续", "set.resume.s": "自动从保存的进度开始播放",
        "set.sub.h": "首选字幕", "set.sub.v": "中文",
        "set.audio.h": "首选音轨", "set.audio.v": "原声",
        "set.clear.h": "清除观看记录", "set.clear.s": "删除本机保存的所有播放进度",
        "set.about.h": "关于", "set.about.s": "播放你自己的媒体。私人影院不提供任何影片或片源。",
        "set.exit": "退出私人影院",
        "det.title": "详情", "det.close": "关闭详情",
        "det.resume": "从 {t} 继续", "det.play": "播放", "det.restart": "从头播放",
        "det.audio": "音轨", "det.audio.v": "原声 · 立体声",
        "det.subs": "字幕", "det.subs.v": "中文（SRT）",
        "det.eps": "剧集",
        "sheet.title": "添加媒体源", "sheet.emby": "Emby", "sheet.jf": "Jellyfin", "sheet.dav": "NAS（WebDAV）", "sheet.local": "本机存储",
        "sheet.server": "服务器地址", "sheet.user": "用户名", "sheet.pass": "密码",
        "sheet.server.ph": "http://192.168.1.20:8096", "sheet.user.ph": "你的账号名", "sheet.pass.ph": "密码",
        "sheet.note": "只连接你拥有或有权使用的服务器和文件。",
        "sheet.connect": "连接", "sheet.pick": "选择文件夹",
        "sheet.local.note": "私人影院读取你在本机选择的文件夹里的视频文件。",
        "cin.exit": "退出影院", "cin.subs": "字幕", "cin.audio": "音轨", "cin.size": "屏幕大小",
        "cin.env": "调暗房间", "cin.back": "后退 15 秒", "cin.fwd": "前进 15 秒",
        "cin.play": "播放", "cin.pause": "暂停", "cin.vol": "音量",
        "cin.subline": "雾快散了，别让灯熄灭。",
        "cin.sub.off": "关闭", "cin.sub.zh": "中文（SRT）", "cin.sub.en": "英文（内嵌）", "cin.sub.load": "加载字幕文件…",
        "cin.aud.1": "原声 · 立体声", "cin.aud.2": "评论音轨 · 立体声",
        "cin.size.s": "小 · 3 米", "cin.size.m": "中 · 6 米", "cin.size.l": "大 · 10 米",
        "clear.title": "清除观看记录？", "clear.body": "将删除本机上所有影片的播放进度。",
        "clear.ok": "清除", "clear.cancel": "取消",
        "snack.cleared": "已清除观看记录", "ep.1": "48 分钟 · 已看完", "ep.2": "51 分钟 · 剩余 21 分钟", "ep.3": "49 分钟", "snack.connected": "媒体源已连接",
    },
}
E = I18N["en"]


def x(key, attr="text"):
    """data-i18n attributes + English static value for attr."""
    return f'data-t-{attr.lower()}="{key}" {attr}="{E[key]}"'


def poster(prefix, key, size=(176, 264)):
    k, en, zh = T[key][0], T[key][1], T[key][2]
    w, h = size
    return (
        f'<div id="{prefix}-poster-{k}" class="poster3d" role="button" tabindex="0" data-title="{k}" '
        f'aria-label="{en}" style="width:{w}px;height:{h}px">'
        f'<img id="{prefix}-poster-{k}-back" class="layer back" src="assets/backdrop-{k}.svg" alt="" draggable="false">'
        f'<img id="{prefix}-poster-{k}-plate" class="layer plate" src="assets/poster-{k}.svg" alt="" draggable="false">'
        f'<img id="{prefix}-poster-{k}-logo" class="layer logo" src="assets/logo-{k}.svg" alt="" draggable="false">'
        f'</div>'
    )


def cont_card(key):
    k, en = T[key][0], T[key][1]
    p = T[key][9]
    mins = {"harbor": 70, "moon": 27, "vega": 110, "keepers": 21}[k]
    return (
        f'<div id="cont-{k}" class="cont-card" role="button" tabindex="0" data-title="{k}" aria-label="{en}">'
        f'<img id="cont-img-{k}" class="cont-img" src="assets/backdrop-{k}.svg" alt="{en}">'
        f'<sui-linear-progress id="cont-prog-{k}" class="cont-prog" value="{p}" size="small" progress-color="var(--semantic-interaction)" track-color="var(--fill-neutral-alpha)"></sui-linear-progress>'
        f'<div id="cont-copy-{k}" class="cont-copy">'
        f'<sui-text id="cont-name-{k}" class="t-name" data-title-text="{k}" text="{en}" text-style="titleSmall"></sui-text>'
        f'<sui-text id="cont-left-{k}" class="t-left" data-left="{mins}" text="{mins} min left" text-style="bodySmall" color="var(--label-semidark-alpha)"></sui-text>'
        f'</div></div>'
    )


home_recent = ["vega", "kite", "harbor", "keepers", "moon", "orchard"]
lib_all = ["harbor", "moon", "orchard", "vega", "relay", "rain", "kite", "keepers"]

css = r"""
html,body{margin:0;font-family:system-ui,-apple-system,"PingFang SC","Noto Sans CJK SC",sans-serif}
*{box-sizing:border-box}
[hidden]{display:none!important}
#preview-bar{position:sticky;top:0;z-index:50;display:flex;gap:16px;align-items:center;padding:10px 40px;background:#2b2b2e;color:#eee;font-size:13px}
#preview-bar b{color:#fff}
#preview-bar button{background:#444;border:0;color:#fff;border-radius:8px;padding:6px 12px;cursor:pointer}
#preview-bar button[aria-pressed=true]{background:#3377ff}
#scene-shared{position:relative;padding-top:104px;width:1700px}
#main-tabs{position:absolute;top:-112px;left:50%;transform:translateX(-50%);z-index:5}
#vol-root{overflow:visible}
#library-volume{position:relative}
#vol-root{position:absolute;inset:0;display:flex;flex-direction:column;padding:32px;gap:20px}
.page{display:flex;flex-direction:column;gap:20px;min-height:0;flex:1}
.page[hidden]{display:none}
.page-head{display:flex;align-items:center;gap:16px;min-height:56px}
.head-copy{display:flex;flex-direction:column;gap:4px;flex:1}
.head-actions{display:flex;gap:8px;align-items:center}
.section{display:flex;flex-direction:column;gap:12px}
.cont-row{display:flex;gap:24px}
.cont-card{width:224px;display:flex;flex-direction:column;gap:8px;border-radius:16px;padding:8px;cursor:pointer;background:var(--fill-light-alpha)}
.cont-img{width:208px;height:117px;object-fit:cover;border-radius:12px;display:block}
.cont-prog{width:208px}
.cont-copy{display:flex;flex-direction:column;gap:2px;padding:0 4px 4px}
.wall{display:flex;gap:32px;perspective:1400px;padding:12px 0 8px}
.wall.grid{flex-wrap:wrap;gap:28px 32px;overflow:auto;flex:1;min-height:0;padding:12px 4px}
.poster3d{position:relative;transform-style:preserve-3d;transition:transform .25s cubic-bezier(.3,0,.2,1);cursor:pointer;border-radius:14px;flex:none}
.poster3d .layer{position:absolute;display:block;pointer-events:none;border-radius:12px}
.poster3d .back{inset:-3%;width:106%;height:106%;object-fit:cover;filter:blur(10px) brightness(.8);transform:translateZ(calc(var(--depth,1) * -22px));opacity:.55}
.poster3d .plate{inset:0;width:100%;height:100%;object-fit:cover;box-shadow:0 0 0 2px rgba(255,255,255,.25),0 calc(var(--depth,1)*10px) calc(var(--depth,1)*18px) rgba(0,0,0,.35);transform:translateZ(0)}
.poster3d .logo{left:4%;width:92%;bottom:6%;height:auto;transform:translateZ(calc(var(--depth,1) * 26px))}
.poster3d:focus-visible{outline:3px solid var(--semantic-interaction);outline-offset:4px}
.list-col{display:flex;flex-direction:column;gap:8px;overflow:auto;min-height:0;flex:1;max-width:760px}
.src-icon{width:40px;height:40px;border-radius:12px;display:flex;align-items:center;justify-content:center;background:var(--fill-light-alpha)}
.settings-cols{display:flex;gap:32px;min-height:0;flex:1}
.exit-row{display:flex;justify-content:flex-end;padding-top:8px}
/* Detail subwindow */
.det{width:360px;height:760px;display:flex;flex-direction:column}
.det-body{padding:0 32px 32px;display:flex;flex-direction:column;gap:14px;flex:1;min-height:0;overflow:auto}
.det-art{width:296px;height:167px;border-radius:16px;object-fit:cover;display:block}
.chips{display:flex;gap:8px;flex-wrap:wrap}
.det-actions{display:flex;flex-direction:column;gap:8px;margin-top:auto}
.ep-list{display:flex;flex-direction:column;gap:6px}
/* Sheet */
.sheet-body{display:flex;flex-direction:column;gap:16px;width:100%}
.opt-row{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.field{display:flex;flex-direction:column;gap:8px}
.sheet-actions{display:flex;justify-content:flex-end;gap:8px}
/* Cinema */
#scene-cinema{position:relative;width:1400px;height:900px;border-radius:24px;overflow:hidden;background:radial-gradient(ellipse at 50% 30%,#1a1c26 0%,#07080c 70%)}
#scene-cinema.dimmed{background:radial-gradient(ellipse at 50% 30%,#55585f 0%,#2a2b30 70%)}
#cinema-floor{position:absolute;left:0;right:0;bottom:0;height:340px;background:linear-gradient(#0b0c12,#030305);transform-origin:top;}
#scene-cinema.dimmed #cinema-floor{background:linear-gradient(#3a3b40,#26272b)}
#cinema-screen{position:absolute;left:50%;top:60px;width:1024px;height:576px;transform:translateX(-50%);border-radius:6px;overflow:hidden;box-shadow:0 0 120px 30px rgba(242,166,90,.18),0 0 0 1px rgba(255,255,255,.08);transition:width .4s,height .4s,top .4s}
#cinema-screen img{width:100%;height:100%;object-fit:cover;animation:kb 30s ease-in-out infinite alternate}
#cinema-screen.paused img{animation-play-state:paused}
@keyframes kb{from{transform:scale(1)}to{transform:scale(1.12) translate(-2%,-1%)}}
#cinema-subline{position:absolute;left:0;right:0;bottom:28px;text-align:center;color:#fff;font-size:26px;text-shadow:0 2px 6px #000}
#cinema-controls{position:absolute;left:50%;bottom:40px;width:900px;transform:translateX(-50%) perspective(900px) rotateX(14deg);transition:opacity .4s}
#cinema-controls.idle{opacity:0;pointer-events:none}
.cc-body{padding:20px 28px 22px;display:flex;flex-direction:column;gap:12px}
.cc-row{display:flex;align-items:center;gap:12px}
.cc-grow{flex:1}
.cc-sep{width:1px;height:32px;background:var(--sub-black-12)}
.cap{color:#5b5b5b;font-size:12px;margin:10px 0 0}
.scene-label{color:#555;font:600 13px system-ui;margin:0 0 8px}
"""

# ---------------- HTML ----------------
h = []
h.append('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">')
h.append('<title>Home Cinema · Design Preview</title><link rel="stylesheet" href="runtime/tokens.css"><script src="runtime/components.js" defer></script>')
h.append(f'<style>{css}</style></head><body>')
h.append('<div id="preview-bar" aria-hidden="false"><b>Home Cinema · Preview</b>'
         '<span>Language</span><button id="pv-en" aria-pressed="true">English</button><button id="pv-zh" aria-pressed="false">中文</button>'
         '<span style="margin-left:24px">Scene</span><button id="pv-shared" aria-pressed="true">Library (Shared Space)</button><button id="pv-cinema" aria-pressed="false">Cinema (Full Space)</button>'
         '<span style="margin-left:auto;opacity:.7">Preview controls only · not part of the app</span></div>')
h.append('<sui-preview-stage>')

# ---- Shared space: Volume + TabBar + Subwindow + Sheet
h.append('<div id="scene-shared"><p class="scene-label">Shared Space · Library Volume 1280 × 760 × 360 dp · TabBar attached above · Details Subwindow on the right</p>')
h.append(f'<div id="tabs-anchor"><sui-tab-bar id="main-tabs" items="{E["tab.items"]}" data-t-items="tab.items" '
         'icons="ic_home,ic_film,ICON7-S029,ICON7-A117" selected-index="0" show-labels></sui-tab-bar></div>')
h.append('<sui-volume id="library-volume" width="1280" height="760" depth="360"><div id="vol-root">')

# Home page
h.append('<section id="page-home" class="page">')
h.append(f'<div id="home-head" class="page-head"><div id="home-head-copy" class="head-copy">'
         f'<sui-text id="home-title" {x("home.title")} text-style="headlineLarge"></sui-text>'
         f'<sui-text id="home-sub" {x("home.sub")} text-style="bodyMedium" color="var(--label-semidark-alpha)"></sui-text></div>'
         f'<div id="home-actions" class="head-actions">'
         f'<sui-icon-button id="home-search" icon="ic_search" size="regular" {x("home.search","semantic-label")}></sui-icon-button>'
         f'<sui-icon-button id="home-refresh" icon="ic_refresh" size="regular" {x("home.refresh","semantic-label")}></sui-icon-button></div></div>')
h.append(f'<div id="home-continue" class="section"><sui-text id="home-continue-title" {x("home.continue")} text-style="titleLarge"></sui-text>'
         f'<div id="cont-row" class="cont-row">' + "".join(cont_card(k) for k in ["harbor", "keepers", "moon", "vega"]) + '</div></div>')
h.append(f'<div id="home-recent" class="section"><sui-text id="home-recent-title" {x("home.recent")} text-style="titleLarge"></sui-text>'
         f'<div id="home-poster-wall" class="wall">' + "".join(poster("home", k) for k in home_recent) + '</div></div>')
h.append('</section>')

# Library page
h.append('<section id="page-library" class="page" hidden>')
h.append(f'<div id="lib-head" class="page-head"><div id="lib-head-copy" class="head-copy">'
         f'<sui-text id="lib-title" {x("lib.title")} text-style="headlineLarge"></sui-text>'
         f'<sui-text id="lib-sub" {x("lib.sub")} text-style="bodyMedium" color="var(--label-semidark-alpha)"></sui-text></div>'
         f'<sui-segment-control id="lib-filter" style="width:300px" options="{E["lib.segments"]}" data-t-options="lib.segments" selected-index="0"></sui-segment-control></div>')
h.append('<div id="library-poster-wall" class="wall grid">' + "".join(poster("lib", k) for k in lib_all) + '</div>')
h.append('</section>')

# Sources page
src_rows = [
    ("demo", "ic_film", "src.demo.h", "src.demo.s"),
    ("jf", "ic_cloud", "src.jf.h", "src.jf.s"),
    ("nas", "ic_computer", "src.nas.h", "src.nas.s"),
    ("local", "ic_memory_card", "src.local.h", "src.local.s"),
]
h.append('<section id="page-sources" class="page" hidden>')
h.append(f'<div id="src-head" class="page-head"><div id="src-head-copy" class="head-copy">'
         f'<sui-text id="src-title" {x("src.title")} text-style="headlineLarge"></sui-text>'
         f'<sui-text id="src-sub" {x("src.sub")} text-style="bodyMedium" color="var(--label-semidark-alpha)"></sui-text></div>'
         f'<sui-button id="src-add" {x("src.add")} leading-icon="ic_plus" size="regular"></sui-button></div>')
h.append('<div id="src-list" class="list-col">')
for sid, ic, hk, sk in src_rows:
    hidden = ' hidden' if sid in ("jf", "nas", "local") else ''
    h.append(f'<sui-list-item id="src-{sid}" custom-width="760" content-padding="16" {x(hk,"headline")} {x(sk,"supporting")}{hidden}>'
             f'<div id="src-{sid}-icon" class="src-icon" slot="leading"><sui-icon id="src-{sid}-glyph" name="{ic}" size="24"></sui-icon></div>'
             f'<sui-icon id="src-{sid}-check" slot="trailing" name="ic_check_circle_fill" size="24" tint="var(--semantic-passable)"></sui-icon></sui-list-item>')
h.append('</div></section>')

# Settings page
h.append('<section id="page-settings" class="page" hidden>')
h.append(f'<div id="set-head" class="page-head"><div id="set-head-copy" class="head-copy">'
         f'<sui-text id="set-title" {x("set.title")} text-style="headlineLarge"></sui-text>'
         f'<sui-text id="set-sub" {x("set.sub")} text-style="bodyMedium" color="var(--label-semidark-alpha)"></sui-text></div></div>')
h.append('<div id="set-cols" class="settings-cols"><div id="set-col-a" class="list-col" style="max-width:560px">')
h.append(f'<sui-list-item id="set-lang" custom-width="560" content-padding="16" leading-icon="ic_globe" {x("set.lang.h","headline")}>'
         f'<sui-button id="set-lang-btn" slot="trailing" size="small" {x("set.lang.v.sys")} trailing-icon="ic_arrow_down"></sui-button></sui-list-item>')
h.append(f'<sui-list-item id="set-depth" custom-width="560" content-padding="16" leading-icon="ic_layers" {x("set.depth.h","headline")} {x("set.depth.s","supporting")}>'
         f'<sui-segment-slider id="set-depth-slider" slot="trailing" segment-count="3" step="2" width="180" semantic-label="3D poster depth"></sui-segment-slider></sui-list-item>')
h.append(f'<sui-list-item id="set-resume" custom-width="560" content-padding="16" leading-icon="ic_history" {x("set.resume.h","headline")} {x("set.resume.s","supporting")}>'
         f'<sui-switch id="set-resume-switch" slot="trailing" checked></sui-switch></sui-list-item>')
h.append(f'<sui-list-item id="set-subs" custom-width="560" content-padding="16" leading-icon="ic_message_square_text" {x("set.sub.h","headline")}>'
         f'<sui-text id="set-subs-v" slot="trailing" {x("set.sub.v")} color="var(--label-semidark-alpha)"></sui-text></sui-list-item>')
h.append(f'<sui-list-item id="set-audio" custom-width="560" content-padding="16" leading-icon="ic_headphones" {x("set.audio.h","headline")}>'
         f'<sui-text id="set-audio-v" slot="trailing" {x("set.audio.v")} color="var(--label-semidark-alpha)"></sui-text></sui-list-item>')
h.append('</div><div id="set-col-b" class="list-col" style="max-width:560px">')
h.append(f'<sui-list-item id="set-clear" custom-width="560" content-padding="16" leading-icon="ICON7-S280" {x("set.clear.h","headline")} {x("set.clear.s","supporting")}></sui-list-item>')
h.append(f'<sui-list-item id="set-about" custom-width="560" content-padding="16" leading-icon="ICON7-A007" {x("set.about.h","headline")} {x("set.about.s","supporting")}></sui-list-item>')
h.append(f'<div id="set-exit-row" class="exit-row"><sui-button id="set-exit" {x("set.exit")} leading-icon="ic_arrow_exit_door" size="regular"></sui-button></div>')
h.append('</div></div></section>')
h.append('</div></sui-volume>')

# Detail subwindow
h.append('<sui-subwindow id="detail-window" for="library-volume" placement="end" dismiss-on-click-outside="false" dismiss-on-escape="false" hidden>'
         '<div id="det-content" class="det">'
         f'<sui-title-bar id="det-titlebar"><sui-icon-button id="det-close" slot="leading" size="small" icon="ic_cross" {x("det.close","semantic-label")}></sui-icon-button>'
         f'<span id="det-heading" style="font-weight:700" data-t-textcontent="det.title">{E["det.title"]}</span></sui-title-bar>'
         '<div id="det-body" class="det-body">'
         '<img id="det-art" class="det-art" src="assets/backdrop-harbor.svg" alt="">'
         '<sui-text id="det-name" text="Harbor Lights" text-style="headlineMedium"></sui-text>'
         '<div id="det-chips" class="chips"><sui-chip id="det-year" clickable="false" size="small" label="2023"></sui-chip>'
         '<sui-chip id="det-run" clickable="false" size="small" label="1h 52m"></sui-chip>'
         '<sui-chip id="det-genre" clickable="false" size="small" label="Drama"></sui-chip>'
         '<sui-chip id="det-quality" clickable="false" size="small" label="4K · HDR"></sui-chip></div>'
         '<sui-text id="det-overview" text-style="bodyMediumMultiline" color="var(--label-semidark-alpha)" text=""></sui-text>'
         f'<sui-list-item id="det-audio" custom-width="296" content-padding="12" leading-icon="ic_headphones" {x("det.audio","headline")} {x("det.audio.v","supporting")}></sui-list-item>'
         f'<sui-list-item id="det-subs" custom-width="296" content-padding="12" leading-icon="ic_message_square_text" {x("det.subs","headline")} {x("det.subs.v","supporting")}></sui-list-item>'
         f'<div id="det-eps" class="ep-list" hidden><sui-text id="det-eps-title" {x("det.eps")} text-style="titleSmall"></sui-text>'
         '<sui-list-item id="det-ep1" custom-width="296" content-padding="12" headline="1 · The First Storm" data-t-supporting="ep.1" supporting="48 min · Watched"></sui-list-item>'
         '<sui-list-item id="det-ep2" custom-width="296" content-padding="12" headline="2 · Low Tide" data-t-supporting="ep.2" supporting="51 min · 21 min left"></sui-list-item>'
         '<sui-list-item id="det-ep3" custom-width="296" content-padding="12" headline="3 · Signal Fires" data-t-supporting="ep.3" supporting="49 min"></sui-list-item></div>'
         '<div id="det-actions" class="det-actions">'
         '<sui-button id="det-resume" size="regular" leading-icon="ic_player_play" text="Resume 42:10" style="width:100%"></sui-button>'
         f'<sui-button id="det-restart" size="regular" {x("det.restart")} style="width:100%" container-color="var(--fill-light-alpha)" content-color="var(--label-darkest-alpha)"></sui-button>'
         '</div></div></div></sui-subwindow>')

# Add-source sheet
h.append(f'<sui-sheet id="add-sheet" title="{E["sheet.title"]}" data-t-title="sheet.title" width="600" hidden>'
         '<div id="sheet-body" class="sheet-body">'
         '<div id="sheet-types" class="opt-row" role="radiogroup">'
         f'<sui-option id="opt-emby" icon="ic_cloud" {x("sheet.emby","label")}></sui-option>'
         f'<sui-option id="opt-jf" icon="ic_cloud" {x("sheet.jf","label")} checked></sui-option>'
         f'<sui-option id="opt-dav" icon="ic_computer" {x("sheet.dav","label")}></sui-option>'
         f'<sui-option id="opt-local" icon="ic_memory_card" {x("sheet.local","label")}></sui-option></div>'
         '<div id="sheet-remote" class="sheet-body">'
         f'<div id="f-server" class="field"><sui-text id="f-server-label" {x("sheet.server")} text-style="labelLarge"></sui-text>'
         f'<sui-text-field id="f-server-input" width="536" {x("sheet.server.ph","placeholder")}></sui-text-field></div>'
         f'<div id="f-user" class="field"><sui-text id="f-user-label" {x("sheet.user")} text-style="labelLarge"></sui-text>'
         f'<sui-text-field id="f-user-input" width="536" {x("sheet.user.ph","placeholder")}></sui-text-field></div>'
         f'<div id="f-pass" class="field"><sui-text id="f-pass-label" {x("sheet.pass")} text-style="labelLarge"></sui-text>'
         f'<sui-text-field id="f-pass-input" width="536" {x("sheet.pass.ph","placeholder")}></sui-text-field></div></div>'
         f'<div id="sheet-local" class="sheet-body" hidden><sui-text id="sheet-local-note" {x("sheet.local.note")} text-style="bodyMedium"></sui-text></div>'
         f'<sui-text id="sheet-note" {x("sheet.note")} text-style="bodySmall" color="var(--label-semidark-alpha)"></sui-text>'
         f'<div id="sheet-actions" class="sheet-actions"><sui-button id="sheet-connect" {x("sheet.connect")} size="regular"></sui-button></div>'
         '</div></sui-sheet>')

# Language menu & clear dialog
h.append('<sui-menu id="lang-menu" for="set-lang-btn" hidden>'
         f'<sui-menu-item id="lang-sys" {x("set.lang.v.sys","title")} data-lang="sys"></sui-menu-item>'
         f'<sui-menu-item id="lang-zh" {x("set.lang.v.zh","title")} data-lang="zh"></sui-menu-item>'
         f'<sui-menu-item id="lang-en" {x("set.lang.v.en","title")} data-lang="en"></sui-menu-item></sui-menu>')
h.append(f'<sui-alert-dialog id="clear-dialog" {x("clear.title","title")} {x("clear.body","text")} '
         f'confirm-text="{E["clear.ok"]}" dismiss-text="{E["clear.cancel"]}" hidden></sui-alert-dialog>')
h.append('<p class="cap">Posters are 3D layered entities (backdrop plane behind, poster plate with thickness, title logo in front). Hover / gaze tilts the poster toward the pointer. Web uses CSS 3D only as an approximation.</p>')
h.append('</div>')  # scene-shared

# ---- Cinema scene (Full Space Stage)
h.append('<div id="scene-cinema-wrap" hidden><p class="scene-label">Full Space · Stage · virtual theater (StageStyle.Full) · screen 6 m wide at 7 m · control panel 0.9 m in front, below eye level</p>')
h.append('<div id="scene-cinema"><div id="cinema-floor"></div>')
h.append('<div id="cinema-screen" role="img" aria-label="Cinema screen playing Harbor Lights"><img id="cinema-frame" src="assets/backdrop-harbor.svg" alt="">'
         f'<div id="cinema-subline" data-t-textcontent="cin.subline">{E["cin.subline"]}</div></div>')
h.append('<sui-attachment-panel id="cinema-controls" background="material"><div id="cc-body" class="cc-body">'
         '<div id="cc-row1" class="cc-row"><div id="cc-copy" class="head-copy">'
         '<sui-text id="cc-title" text="Harbor Lights" text-style="titleLarge"></sui-text>'
         '<sui-text id="cc-time" text="42:10 / 1:52:30" text-style="bodySmall" color="var(--label-semidark-alpha)"></sui-text></div>'
         f'<sui-button id="cc-exit" size="small" leading-icon="ic_arrow_exit_door" {x("cin.exit")}></sui-button></div>'
         '<div id="cc-row2" class="cc-row"><sui-slider id="cc-seek" value="0.374" width="844" semantic-label="Playback position"></sui-slider></div>'
         '<div id="cc-row3" class="cc-row">'
         f'<sui-icon-button id="cc-back" icon="ic_skip_back_15" {x("cin.back","semantic-label")}></sui-icon-button>'
         f'<sui-icon-button id="cc-play" icon="ic_player_pause" {x("cin.pause","semantic-label")}></sui-icon-button>'
         f'<sui-icon-button id="cc-fwd" icon="ic_skip_forward_15" {x("cin.fwd","semantic-label")}></sui-icon-button>'
         '<div id="cc-sep1" class="cc-sep"></div>'
         f'<sui-symbol-slider id="cc-vol" icon="ic_volume_high" value="0.7" width="200" {x("cin.vol","semantic-label")}></sui-symbol-slider>'
         '<div id="cc-spacer" class="cc-grow"></div>'
         f'<sui-icon-button id="cc-subs" icon="ic_message_square_text" {x("cin.subs","semantic-label")}></sui-icon-button>'
         f'<sui-icon-button id="cc-audio" icon="ic_headphones" {x("cin.audio","semantic-label")}></sui-icon-button>'
         f'<sui-icon-button id="cc-size" icon="ic_expand_window" {x("cin.size","semantic-label")}></sui-icon-button>'
         f'<sui-toggle-icon-button id="cc-env" icon="ic_moon_stars" {x("cin.env","semantic-label")} checked></sui-toggle-icon-button>'
         '</div></div></sui-attachment-panel></div>')
h.append('<sui-menu id="subs-menu" for="cc-subs" hidden>'
         f'<sui-menu-item id="subs-off" {x("cin.sub.off","title")}></sui-menu-item>'
         f'<sui-menu-item id="subs-zh" {x("cin.sub.zh","title")} trailing-icon="ic_check"></sui-menu-item>'
         f'<sui-menu-item id="subs-en" {x("cin.sub.en","title")}></sui-menu-item>'
         f'<sui-menu-item id="subs-load" {x("cin.sub.load","title")} leading-icon="ICON7-S029"></sui-menu-item></sui-menu>')
h.append('<sui-menu id="audio-menu" for="cc-audio" hidden>'
         f'<sui-menu-item id="aud-1" {x("cin.aud.1","title")} trailing-icon="ic_check"></sui-menu-item>'
         f'<sui-menu-item id="aud-2" {x("cin.aud.2","title")}></sui-menu-item></sui-menu>')
h.append('<sui-menu id="size-menu" for="cc-size" hidden>'
         f'<sui-menu-item id="size-s" {x("cin.size.s","title")}></sui-menu-item>'
         f'<sui-menu-item id="size-m" {x("cin.size.m","title")} trailing-icon="ic_check"></sui-menu-item>'
         f'<sui-menu-item id="size-l" {x("cin.size.l","title")}></sui-menu-item></sui-menu>')
h.append('<p class="cap">Controls fade after 5 s without input; any ray, gaze or pinch toward the screen or panel brings them back. Subtitles render on the screen surface.</p></div>')
h.append('</sui-preview-stage>')

notes = {
    "home-poster-wall": {
        "represents": "Row of 3D layered posters for recently added titles",
        "previewRepresentation": "CSS 3D approximation: blurred backdrop layer behind, poster plate, title logo layer in front",
        "assetStatus": "available",
        "assetId": "demo-titles",
        "appearance": ["Each poster is three stacked planes: Backdrop image ~2 cm behind, Primary poster plate 2:3 with ~6 mm edge thickness, Logo image ~2.5 cm in front",
                       "Real libraries use the server's Primary, Backdrop and Logo images; without a Logo image the title is rendered as text on the front plane"],
        "behaviors": ["Hover by controller ray, hand ray or gaze tilts the poster up to 8 degrees toward the pointer and increases layer separation",
                      "Select (trigger, pinch, gaze + pinch) opens the Details subwindow",
                      "Layer separation scales with Settings > 3D poster depth (Off, Subtle, Standard, Strong)"],
        "previewLimitations": ["No real parallax from head motion", "Thickness and lighting are approximated with shadows"],
    },
    "library-poster-wall": {
        "represents": "Scrollable grid of 3D layered posters for the whole library",
        "previewRepresentation": "Same layered poster as home-poster-wall, wrapped into a scrolling grid",
        "assetStatus": "available",
        "assetId": "demo-titles",
        "behaviors": ["Segment control filters All, Movies, Shows", "Vertical scroll by thumbstick, pinch-drag or ray drag"],
        "previewLimitations": ["Grid virtualization and server paging are not simulated"],
    },
    "cinema-screen": {
        "represents": "Large cinema screen entity in a Full Space Stage, video rendered with VideoMaterial",
        "previewRepresentation": "Backdrop image with a slow pan stands in for video playback",
        "assetStatus": "to-create",
        "appearance": ["16:9 plane, 6 m wide at 7 m distance by default, centre 1.6 m above floor, slight curvature optional",
                       "Soft light spill from the screen onto the virtual floor"],
        "behaviors": ["Screen size Small 3 m / Medium 6 m / Large 10 m, keeping the same visual centre",
                      "Subtitles (SRT/ASS external or embedded tracks) render on the lower part of the screen"],
        "previewLimitations": ["No real video decoding", "Curvature and light spill are approximated"],
    },
    "scene-cinema": {
        "represents": "Virtual dark theater environment for Full Space playback",
        "previewRepresentation": "Radial gradient room with a floor plane",
        "assetStatus": "to-create",
        "appearance": ["Dark matte room with floor and faint side walls; no branded elements"],
        "behaviors": ["Dim the room toggle switches between StageStyle.Full dark theater and a dimmed passthrough (Mixed) room"],
        "previewLimitations": ["Passthrough is shown as a lighter grey room"],
    },
    "cinema-controls": {
        "relationship": "Scene attachment owned by the cinema root, 0.9 m in front of the initial head position and 0.35 m below eye level, tilted 20 degrees toward the user; does not overlap the screen",
        "followBehavior": "Fixed in the scene after entering the cinema; does not follow head movement; fades after 5 s without input and reappears on ray, gaze or pinch",
    },
}
h.append('<script type="application/json" id="scene-design-notes">' + json.dumps(notes, ensure_ascii=False) + '</script>')
h.append('<script id="i18n-data" type="application/json">' + json.dumps(I18N, ensure_ascii=False) + '</script>')
h.append('<script id="title-data" type="application/json">' + json.dumps(
    {t[0]: {"en": t[1], "zh": t[2], "year": t[3], "run": t[4], "genre": {"en": t[5][0], "zh": t[5][1]}, "q": t[6],
            "ov": {"en": t[7], "zh": t[8]}, "p": t[9]} for t in TITLES},
    ensure_ascii=False) + '</script>')
h.append('<script src="preview.js" defer></script>')
h.append('</body></html>')

# ---- Post-process: put overlays under their Spec owners in the DOM
doc = "".join(h)
import re as _re
def cut(pattern):
    global doc
    m = _re.search(pattern, doc, _re.S); frag = m.group(0); doc = doc[:m.start()] + doc[m.end():]; return frag
tabs = cut(r'<div id="tabs-anchor">.*?</sui-tab-bar></div>')
tabs = tabs[len('<div id="tabs-anchor">'):-len('</div>')]
doc = doc.replace('<div id="vol-root">', '<div id="vol-root">' + tabs, 1)
sheet = cut(r'<sui-sheet id="add-sheet".*?</sui-sheet>')
langm = cut(r'<sui-menu id="lang-menu".*?</sui-menu>')
dlg = cut(r'<sui-alert-dialog id="clear-dialog".*?</sui-alert-dialog>')
i = doc.index('<section id="page-sources"'); j = doc.index('</section>', i)
doc = doc[:j] + sheet + doc[j:]
i = doc.index('<section id="page-settings"'); j = doc.index('</section>', i)
doc = doc[:j] + langm + dlg + doc[j:]
menus = cut(r'<sui-menu id="subs-menu".*?</sui-menu>') + cut(r'<sui-menu id="audio-menu".*?</sui-menu>') + cut(r'<sui-menu id="size-menu".*?</sui-menu>')
doc = doc.replace('</sui-attachment-panel>', '</sui-attachment-panel>' + menus, 1)
doc = doc.replace('<div id="cc-sep1" class="cc-sep"></div>', '<sui-vertical-divider id="cc-sep1"></sui-vertical-divider>')
open(os.path.join(OUT, "preview.html"), "w").write(doc)
print("written", os.path.join(OUT, "preview.html"))
