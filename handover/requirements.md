# Home Cinema（私人影院）— 需求与约束

## 产品
眼手操作的私人影院播放器（PICO Spatial SDK + SpatialUI，Kotlin/Compose）。
- 媒体源（只接用户自己的正版来源，不内置、不推荐任何资源站）：
  1. Emby / Jellyfin 媒体库：用户在应用里填服务器地址 + 用户名 + 密码登录（走 Emby/Jellyfin 公开 REST API：/Users/AuthenticateByName、/Users/{id}/Items、/Items/{id}/Images/Primary、/Videos/{id}/stream）。
  2. NAS：WebDAV（必做）；SMB 可作为后续增量。
  3. 本机视频（设备存储里的视频文件）。
  4. 首次打开无源时：内置 1–2 段自制/CC0 演示短片或程序生成的演示条目，让用户不配置也能看到海报墙和播放流程（不要用任何受版权保护的电影海报 / 片段）。
- 海报墙：把每张 2D 海报做成有景深的 3D 立体海报（离线做法：海报分层视差 / 前景主体 + 背景的浅浮雕厚度 + 边框厚度 + 注视/指向时轻微倾斜和视差），不依赖任何付费 / 需要私钥的 AI API。
- 大屏观影：选片后进入大屏播放（影院模式：大屏幕 + 暗环境），播放控制条（播放/暂停、进度拖动、±10s、音量）、续播（记住每部片的播放进度，下次「继续观看」）、字幕（外挂 SRT/ASS + 内嵌字幕轨切换）、音轨切换。
- 名字与界面全部原创（应用名：私人影院 / Home Cinema），不使用任何参考产品的商标、图标、截图。

## 交互规矩（必须一开始就满足）
- 中英双语（跟随系统语言，设置里可切换）。
- 设置里有「退出应用」。
- 面板不要压住 3D 主体（海报墙 / 大屏）；控制条放在屏幕下方或侧边，不遮挡画面。
- 控制器射线、手势射线、眼手（注视 + 捏合）三种输入都能操作所有控件和 3D 海报。
- Shared Space 里窗口不承诺「回到面前」类功能。
- 核心功能不能依赖需要私钥 / 付费的 API；需要 AI 的地方给离线兜底或可选配置。

## 工程约束
- 项目目录：/Users/bytedance/Downloads/home-cinema（git 随意）。
- Java：export JAVA_HOME=~/.pico/primer-cli/jdk/jdk-21.0.13+9/Contents/Home
- 模拟器是多个任务共享资源：**不要创建新的 AVD，也不要启动新的模拟器**。需要模拟器时只用已在线的那台，并且先通过下面命令借用、用完归还：
  借：`python3 -I "/Users/bytedance/Desktop/Spatial Apps/spatial-app-factory/bin/emu_borrow.py" borrow home-cinema --wait-min 60`（打印分到的 serial，之后所有 adb / pico-cli 命令都显式带这个 serial）；还：`... emu_borrow.py return home-cinema`。只在安装 / 自测 / 截图时借，用完立即还。
- 头显（真机，序列号 PB324XJGL2090081G）连着：只允许 `adb -s PB324XJGL2090081G install -r <apk>`，不要在真机上启动 / 卸载 / 清数据。
- 需要 3D 模型或音效素材时，优先 PICO CLI 自带的生成能力（Spatial Editor / SGS），或本机 CC0 库 ~/Downloads/cc0-sounds/；不要下载来路不明的文件。
- 宣传材料不带公司名。

## 设计阶段要求
- 设计稿请输出到项目内 `design/`，并另外导出一份**单个可双击打开的 HTML** 设计稿 `design/sample.html`（含海报墙、登录 / 添加媒体源、影院播放、设置 四个主要界面；图片内嵌或同目录相对路径），以及一份 PRD `design/prd.html`。
