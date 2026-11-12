"""Build apps/home-cinema/options.html (门 B 改: feasibility + options) as one double-clickable file."""
import base64, pathlib, sys
A = pathlib.Path(sys.argv[1])
def img(n):
    return "data:image/jpeg;base64," + base64.b64encode((A / "feasibility" / n).read_bytes()).decode()
SKETCH = """
<svg viewBox="0 0 960 560" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Option A sketch">
 <defs><linearGradient id="cur" x1="0" x2="1"><stop offset="0" stop-color="#5a0f14"/><stop offset=".5" stop-color="#8e1c24"/><stop offset="1" stop-color="#4a0c10"/></linearGradient></defs>
 <rect width="960" height="560" fill="#d9d4cc"/>
 <text x="20" y="30" font-size="14" fill="#555">真实房间（透视，亮度不变） / real room, passthrough unchanged</text>
 <rect x="250" y="120" width="460" height="260" fill="#222" stroke="#999" stroke-dasharray="6 4"/>
 <text x="480" y="255" text-anchor="middle" font-size="16" fill="#ccc">别的应用的播放窗口 / other app's player</text>
 <text x="480" y="278" text-anchor="middle" font-size="12" fill="#999">（用户手动放进框里 / user aligns it）</text>
 <rect x="170" y="70" width="620" height="360" fill="none" stroke="#b8862b" stroke-width="26"/>
 <rect x="157" y="57" width="646" height="10" fill="#ffd27a" opacity=".9"/>
 <path d="M183 83 h70 q-20 150 0 334 h-70z" fill="url(#cur)"/>
 <path d="M777 83 h-70 q20 150 0 334 h70z" fill="url(#cur)"/>
 <g fill="#3a2a22">
  <rect x="200" y="460" width="70" height="60" rx="10"/><rect x="290" y="460" width="70" height="60" rx="10"/><rect x="380" y="460" width="70" height="60" rx="10"/>
  <rect x="510" y="460" width="70" height="60" rx="10"/><rect x="600" y="460" width="70" height="60" rx="10"/><rect x="690" y="460" width="70" height="60" rx="10"/>
 </g>
 <g fill="#ffc35a"><circle cx="472" cy="540" r="5"/><circle cx="488" cy="520" r="5"/><circle cx="472" cy="500" r="5"/></g>
 <rect x="810" y="380" width="130" height="110" rx="14" fill="#2b2b30" opacity=".92"/>
 <text x="875" y="405" text-anchor="middle" font-size="12" fill="#fff">厅 Hall ▾</text>
 <text x="875" y="430" text-anchor="middle" font-size="12" fill="#fff">开场 / 散场</text>
 <text x="875" y="455" text-anchor="middle" font-size="12" fill="#fff">计时 90 min</text>
 <text x="875" y="478" text-anchor="middle" font-size="11" fill="#aaa">设置 · 退出</text>
 <text x="20" y="550" font-size="12" fill="#555">金框 = 我们的体积窗口（可等比缩放），中间留空，座椅 / 过道灯在前下方 / gold = our volume, hollow centre</text>
</svg>"""
html = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>Home Cinema · 门 B 改：只改氛围可行性</title>
<style>body{{font:15px/1.6 -apple-system,'PingFang SC',sans-serif;max-width:1040px;margin:24px auto;padding:0 20px;color:#1d1d1f}}
h1{{font-size:24px}}h2{{margin-top:32px;border-bottom:1px solid #ddd;padding-bottom:4px}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:6px 8px;vertical-align:top}}th{{background:#f4f4f6}}
.v{{color:#0a7a33;font-weight:600}}.i{{color:#9a6200;font-weight:600}}.no{{color:#b3261e;font-weight:600}}
.shots{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.shots figure{{margin:0}}.shots img{{width:100%;border-radius:8px}}figcaption{{font-size:13px;color:#555}}
.opt{{border:2px solid #ddd;border-radius:12px;padding:12px 16px;margin:12px 0}}.rec{{border-color:#b8862b}}
.en{{color:#666;font-size:13px}}</style></head><body>
<h1>Home Cinema 门 B 改 · 只改氛围，能做到哪</h1>
<p><b>结论：只能做一半。</b>我们可以在别的应用的播放窗口旁边或四周，放一个自己的「影院框」体积窗口，里面有幕布、座椅、灯，有声开始和结束时自动开场、散场。<br><b>做不到：</b>调暗或调色透视、换影院环境、自动把框套到别人的窗口上。原因是这些能力都要进 Full Space，而 Full Space 会把别的应用的窗口藏起来，还会让它停播（模拟器实测）。
<br><span class="en">Half feasible: a decorative volume can coexist with another app's player; dimming passthrough or swapping the environment requires Full Space, which hides the other app and stops its audio (verified on emulator).</span></p>

<h2>四个问题 / Four answers</h2>
<table><tr><th>#</th><th>问题</th><th>结论</th><th>依据</th></tr>
<tr><td>1</td><td>别人的窗口在播放时，能不能在它周围放 3D？遮挡、抢输入？</td><td><span class="v">能并存（实测）</span>，但内容只能放在我们自己的体积框里；遮挡、抢射线 <span class="i">推断，需真机</span></td><td>截图 02；structure-decisions.md 能力表：Shared Space 里 Free 3D ❌</td></tr>
<tr><td>2</td><td>能不能调暗或换环境，同时不藏别人的窗口？</td><td><span class="no">不能（实测）</span>：开 Stage 进入 Full Space，播放器窗口被隐藏，声音也停了</td><td>截图 03、04；container-selection.md：「Full Space … hides other applications' windows」</td></tr>
<tr><td>3</td><td>能不能知道别人的窗口在哪？</td><td><span class="no">不能（推断：SDK 里没有这类接口）</span>，只能手动拖动和缩放来对齐</td><td>6.1.9 类表；追踪类都带 @RequiredFullSpace</td></tr>
<tr><td>4</td><td>能不能感知正在播放或亮度变化？</td><td><span class="v">能知道「有声在播」（实测，isMusicActive）</span>；媒体会话被拒（实测）；画面亮度 <span class="i">读不到（推断）</span></td><td>probe-logcat.txt</td></tr></table>

<h2>模拟器实测截图 / Emulator evidence</h2>
<div class="shots">
<figure><img src="{img('01-player-alone.jpg')}"><figcaption>01 系统播放器在播测试片（控制条可见）</figcaption></figure>
<figure><img src="{img('02-player-plus-probe-volume.jpg')}"><figcaption>02 探针体积窗口（金框）和播放器同屏，SHARED_SPACE</figcaption></figure>
<figure><img src="{img('03-stage-mixed-dark.jpg')}"><figcaption>03 开 Stage（Mixed + Dark）后：FULL_SPACE，播放器被隐藏，声音停</figcaption></figure>
<figure><img src="{img('04-after-close-stage.jpg')}"><figcaption>04 关 Stage 后：播放器回来，继续出声</figcaption></figure>
</div>

<h2>请选一个方向 / Pick one</h2>
<div class="opt rec"><h3>A · 「影院框」装饰体积（推荐）</h3>
{SKETCH}
<ul><li>能和任何播放器、浏览器、PICO Video 同时开。我们只是一个约 2.4 × 1.6 × 0.9 m 的体积窗口，可等比缩放：四边台口和两侧帷幕，中间空着；前下方一排座椅剪影和过道灯；顶上一条灯带。</li>
<li>反复用的理由（只做两件）：① 三种厅（老戏院 / 黑盒 / 露天），一键切换；② 有声时自动开场（灯暗、幕开、可选放映机嗡声），无声或计时到点自动散场，另有睡眠计时。</li>
<li>局限：房间亮度改不了；要用户手动对齐一次；需要真机确认，透明的中间区域不会挡住你去点播放器。</li>
<li>小控制面板在框外右下角：切厅、开场 / 散场、计时、环境声、设置（中英、退出应用）。</li></ul></div>
<div class="opt"><h3>B · 沉浸影院 + 内置屏</h3>
<p>进 Stage，能真正把房间调暗或换成影院。但别的应用会被藏起来，所以屏上只能放我们自己能播的东西，例如本机或 NAS 文件、网页。这就又回到了「播放器」，和你这次的意见相反，列在这里只是说明全部选项。</p></div>
<div class="opt"><h3>C · 先不做</h3><p>如果「不能调暗房间」就失去了意义，这个应用可以先搁置。</p></div>

<h2>需要真机确认</h2>
<ol><li>体积窗口透明的中间区域会不会挡住射线（手势、手柄、眼手三种都要试）</li><li>播放器窗口能不能推进我们的框里，交叠时谁画在前面</li><li>PICO Video 或浏览器暂停时，isMusicActive 会不会变成 false</li><li>模拟器里视频是半透明的，真机上应该是不透明的</li></ol>
<p class="en">Full write-up: apps/home-cinema/feasibility.md · probe source: feasibility/Probe.kt.txt</p>
</body></html>"""
(A / "options.html").write_text(html, encoding="utf-8")
print((A / "options.html").stat().st_size)
