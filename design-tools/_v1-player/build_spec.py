"""Write .scratch/design-spec.json from the approved Preview (Write Spec stage).
Usage: python3 build_spec.py <scratch-dir>"""
import json, os, re, sys, hashlib
from html.parser import HTMLParser

S = sys.argv[1]
html = open(os.path.join(S, "preview.html")).read()
notes = json.loads(re.search(r'<script type="application/json" id="scene-design-notes">(.*?)</script>', html, re.S).group(1))
i18n = json.loads(re.search(r'<script id="i18n-data" type="application/json">(.*?)</script>', html, re.S).group(1))

VOID = {"img", "input", "br", "meta", "link"}


class El:
    def __init__(self, tag, attrs, parent):
        self.tag, self.a, self.parent, self.kids, self.text = tag, dict(attrs), parent, [], ""


class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.root = El("root", [], None); self.cur = self.root
    def handle_starttag(self, tag, attrs):
        e = El(tag, attrs, self.cur); self.cur.kids.append(e)
        if tag not in VOID: self.cur = e
    def handle_endtag(self, tag):
        c = self.cur
        while c is not None and c.tag != tag: c = c.parent
        if c is not None and c.parent is not None: self.cur = c.parent
    def handle_data(self, d):
        self.cur.text += d


p = P(); p.feed(html)

SKIP = {"preview-bar", "scene-shared", "tabs-anchor", "scene-cinema-wrap", "library-volume", "cinema-floor",
        "scene-design-notes", "i18n-data", "title-data"}
SKIP_PREFIX = ("pv-",)
COLOR = {"var(--label-semidark-alpha)": "labelTertiary", "var(--label-darkest-alpha)": "labelPrimary",
         "var(--semantic-interaction)": "interaction", "var(--fill-neutral-alpha)": "fillTertiary",
         "var(--fill-light-alpha)": "fillLight", "var(--semantic-passable)": "passable"}
DROP_ATTR = {"id", "class", "style", "role", "tabindex", "draggable", "hidden", "for", "alt", "src"}

nodes, order = {}, []


def ided_children(e):
    out = []
    for k in e.kids:
        if k.a.get("id") and k.a["id"] not in SKIP and not k.a["id"].startswith(SKIP_PREFIX) and k.tag != "script":
            out.append(k)
        elif k.tag not in ("script",) and not (k.a.get("id") in SKIP and k.a.get("id") in ("library-volume",)):
            out.extend(ided_children(k))
    return out


def i18n_of(e):
    res = {}
    for k, v in e.a.items():
        if k.startswith("data-t-"):
            res[k[7:]] = {"en": i18n["en"][v], "zh": i18n["zh"][v], "key": v}
    return res


def style_px(e, prop):
    m = re.search(prop + r":\s*(\d+)px", e.a.get("style", ""))
    return int(m.group(1)) if m else None


def build(e):
    nid = e.a["id"]
    cls = e.a.get("class", "")
    kids = [build(k) for k in ided_children(e)]
    n = {"id": nid}
    loc = i18n_of(e)
    if e.tag == "sui-text" or (e.tag in ("span", "div") and ("data-t-textcontent" in e.a) and not kids):
        n["kind"] = "text"
        n["content"] = e.a.get("text", e.text.strip())
        if e.tag == "sui-text":
            n["textStyle"] = {"typography": e.a.get("text-style", "bodyMedium"),
                              "color": COLOR.get(e.a.get("color", ""), "labelPrimary")}
        elif nid == "det-heading":
            n["textStyle"] = {"overrides": {"weight": 700}}
        elif nid == "cinema-subline":
            n["textStyle"] = {"typography": "headlineMedium", "color": "labelPrimaryLight"}
            n["purpose"] = "Subtitle line rendered on the lower part of the cinema screen"
        if e.a.get("slot"): n["props"] = {"slot": e.a["slot"]}
        if not n["content"]:
            n["bindings"] = {"content": "selectedTitle.overview (localized)"}
    elif e.tag.startswith("sui-"):
        n["kind"] = "spatialui"; n["component"] = e.tag
        props = {}
        for k, v in e.a.items():
            if k in DROP_ATTR or k.startswith("data-") or k.startswith("aria-"): continue
            if k == "color" or k == "tint" or k.endswith("-color"):
                v = COLOR.get(v, v)
            if v == "" : v = True
            if isinstance(v, str) and re.fullmatch(r"-?\d+(\.\d+)?", v) and k not in ("text", "label", "title", "headline", "supporting"):
                v = float(v) if "." in v else int(v)
            props[k] = v
        if e.tag == "sui-segment-control" and style_px(e, "width"): props["custom-width"] = str(style_px(e, "width"))
        if e.tag == "sui-button" and "width:100%" in e.a.get("style", ""): n["layout"] = {"width": "fill"}
        n["props"] = props
    elif e.tag == "img":
        n["kind"] = "media"
        src = e.a.get("src", "")
        n["assetId"] = os.path.splitext(os.path.basename(src))[0]
    elif "poster3d" in cls:
        n["kind"] = "domain_visual"; n["rendererKey"] = "layered-poster-3d"
        n["purpose"] = "One 3D layered poster entity: backdrop plane, poster plate with edge thickness, title logo plane"
        n["layout"] = {"widthDp": style_px(e, "width"), "heightDp": style_px(e, "height")}
        n["bindings"] = {"title": "dataCases.titles[" + e.a["data-title"] + "]"}
    elif "cont-card" in cls or "src-icon" in cls:
        n["kind"] = "content"
        if "cont-card" in cls:
            n["layout"] = {"mode": "column", "widthDp": 224, "gapDp": 8, "paddingDp": 8}
            n["appearance"] = {"fill": "fillLight", "radiusDp": 16}
            n["bindings"] = {"title": "dataCases.titles[" + e.a["data-title"] + "]"}
        else:
            n["layout"] = {"widthDp": 40, "heightDp": 40, "align": "center", "justify": "center"}
            n["appearance"] = {"fill": "fillLight", "radiusDp": 12}
            if e.a.get("slot"): n["props"] = {"slot": e.a["slot"]}
    else:
        n["kind"] = "layout"
        lay = {"mode": "column"}
        if any(c in cls for c in ("page-head", "head-actions", "cont-row", "cc-row", "sheet-actions", "exit-row", "chips", "settings-cols")):
            lay["mode"] = "row"
        if "opt-row" in cls: lay = {"mode": "grid", "columns": 4, "gapDp": 8}
        if "wall" in cls: lay = {"mode": "row", "gapDp": 32}
        if "grid" in cls.split(): lay = {"mode": "wrap", "rowGapDp": 28, "columnGapDp": 32, "overflow": "auto", "grow": 1}
        gaps = {"page": 20, "page-head": 16, "head-copy": 4, "head-actions": 8, "section": 12, "cont-row": 24, "cont-copy": 2,
                "list-col": 8, "settings-cols": 32, "det-body": 14, "chips": 8, "det-actions": 8, "ep-list": 6,
                "sheet-body": 16, "field": 8, "sheet-actions": 8, "cc-body": 12, "cc-row": 12}
        for c in cls.split():
            if c in gaps and "gapDp" not in lay and lay.get("mode") != "wrap": lay["gapDp"] = gaps[c]
        if nid == "vol-root": lay.update({"paddingDp": 32, "gapDp": 20})
        if "det-body" in cls: lay.update({"paddingDp": {"top": 0, "right": 32, "bottom": 32, "left": 32}, "overflow": "auto", "grow": 1})
        if "cc-body" in cls: lay.update({"paddingDp": {"top": 20, "right": 28, "bottom": 22, "left": 28}})
        if "page" in cls.split() or "list-col" in cls: lay["grow"] = 1
        if "list-col" in cls: lay["overflow"] = "auto"
        if "cc-grow" in cls: lay = {"mode": "row", "grow": 1}
        if "det-actions" in cls: lay["marginTop"] = "auto"
        if "exit-row" in cls: lay["justify"] = "end"
        if "sheet-actions" in cls: lay["justify"] = "end"
        if lay: n["layout"] = lay
        if e.a.get("slot"): n["props"] = {"slot": e.a["slot"]}
    if loc:
        n["localizedText"] = loc
    if nid in notes:
        n["designNotes"] = notes[nid]
        if nid.endswith("poster-wall"):
            n["kind"] = "domain_visual"; n["rendererKey"] = "poster-wall-3d"
            n["purpose"] = "3D model group: " + notes[nid]["represents"]
            n.pop("layout", None); n["layout"] = {"mode": "row" if nid.startswith("home") else "wrap", "gapDp": 32}
        if nid == "cinema-screen":
            n["kind"] = "domain_visual"; n["rendererKey"] = "cinema-screen-videomaterial"; n["purpose"] = "3D model: " + notes[nid]["represents"]
        if nid == "scene-cinema":
            n["kind"] = "domain_visual"; n["rendererKey"] = "virtual-theater-stage"; n["purpose"] = "3D scene: " + notes[nid]["represents"]
            n.pop("layout", None)
    if e.tag == "img":
        if "layer" in cls:
            n["layout"] = {"sizing": "matchParent", "fit": "cover", "radiusDp": 12,
                           "depthLayer": {"back": "behind plate, about 2 cm, blurred", "plate": "plate, 6 mm edge thickness", "logo": "in front, about 2.5 cm"}[cls.split()[1]]}
            n["purpose"] = {"back": "Backdrop layer", "plate": "Poster plate", "logo": "Title logo layer"}[cls.split()[1]]
        elif "cont-img" in cls: n["layout"] = {"widthDp": 208, "heightDp": 117, "fit": "cover", "radiusDp": 12}
        elif "det-art" in cls: n["layout"] = {"widthDp": 296, "heightDp": 167, "fit": "cover", "radiusDp": 16}; n["bindings"] = {"assetId": "selectedTitle.backdrop"}
        elif nid == "cinema-frame": n["layout"] = {"sizing": "matchParent", "fit": "cover"}; n["purpose"] = "Stands in for the decoded video frame"; n["bindings"] = {"assetId": "playingTitle.backdrop"}
    if kids: n["children"] = [k["id"] for k in kids]
    nodes[nid] = n; order.append(nid)
    return n


def find(e, i):
    if e.a.get("id") == i: return e
    for k in e.kids:
        r = find(k, i)
        if r: return r


vol = find(p.root, "library-volume")
build(find(vol, "vol-root"))

build(find(p.root, "detail-window"))

build(find(p.root, "scene-cinema"))


HIDDEN = {"page-home": "destination != Home", "page-library": "destination != Library", "page-sources": "destination != Sources",
          "page-settings": "destination != Settings", "src-jf": "no Emby/Jellyfin source connected", "src-nas": "no WebDAV source connected",
          "src-local": "no headset folder chosen", "add-sheet": "closed until open-add-source", "lang-menu": "closed until open-language-menu",
          "clear-dialog": "closed until ask-clear-history", "subs-menu": "closed until open-subtitle-menu", "audio-menu": "closed until open-audio-menu",
          "size-menu": "closed until open-size-menu", "det-eps": "selected title is not a series", "sheet-local": "source type != Headset storage",
          "sheet-remote": "source type == Headset storage", "det-restart": "selected title has no saved position", "cinema-subline": "subtitles Off"}
for nid, cond in HIDDEN.items():
    nodes[nid].setdefault("bindings", {})["hidden"] = cond
# Subwindow specifics
dw = nodes["detail-window"]
dw["regions"] = {"titleBarNodeId": "det-titlebar", "bodyNodeId": "det-body"}
nodes["det-titlebar"]["props"]["title-node-id"] = "det-heading"
nodes["det-close"]["props"].update({"navigation-action": "close"})

# Events -> actions
EV = {
    "main-tabs": ("select", "switch-destination"),
    "det-close": ("click-action", "close-detail"),
    "det-resume": ("click-action", "enter-cinema"), "det-restart": ("click-action", "enter-cinema-from-start"),
    "cc-exit": ("click-action", "exit-cinema"), "cc-play": ("click-action", "toggle-playback"),
    "cc-back": ("click-action", "seek-back"), "cc-fwd": ("click-action", "seek-forward"),
    "cc-seek": ("value-change-finished", "seek-to"), "cc-vol": ("value-change", "set-volume"),
    "cc-subs": ("click-action", "open-subtitle-menu"), "cc-audio": ("click-action", "open-audio-menu"),
    "cc-size": ("click-action", "open-size-menu"), "cc-env": ("checked-change", "toggle-room-dimming"),
    "subs-off": ("select", "choose-subtitle"), "subs-zh": ("select", "choose-subtitle"), "subs-en": ("select", "choose-subtitle"),
    "subs-load": ("select", "load-subtitle-file"), "aud-1": ("select", "choose-audio-track"), "aud-2": ("select", "choose-audio-track"),
    "size-s": ("select", "choose-screen-size"), "size-m": ("select", "choose-screen-size"), "size-l": ("select", "choose-screen-size"),
    "set-lang-btn": ("click-action", "open-language-menu"), "lang-sys": ("select", "choose-language"),
    "lang-zh": ("select", "choose-language"), "lang-en": ("select", "choose-language"),
    "set-depth-slider": ("step-change", "set-poster-depth"), "set-resume-switch": ("checked-change", "toggle-auto-resume"),
    "set-clear": ("click-action", "ask-clear-history"), "clear-dialog": ("confirm", "clear-history"),
    "set-exit": ("click-action", "exit-app"), "src-add": ("click-action", "open-add-source"),
    "add-sheet": ("dismiss-request", "close-add-source"), "sheet-connect": ("click-action", "connect-source"),
    "opt-emby": ("checked-change", "choose-source-type"), "opt-jf": ("checked-change", "choose-source-type"),
    "opt-dav": ("checked-change", "choose-source-type"), "opt-local": ("checked-change", "choose-source-type"),
    "lib-filter": ("select", "filter-library"), "home-search": ("click-action", "search-library"),
    "home-refresh": ("click-action", "refresh-library"),
}
for nid, n in nodes.items():
    if nid in EV:
        n.setdefault("events", {})[EV[nid][0]] = EV[nid][1]
    if n.get("kind") == "domain_visual" and n.get("rendererKey") == "layered-poster-3d" or nid.startswith("cont-") and n.get("kind") == "content":
        n.setdefault("events", {})["select"] = "open-detail"
for nid in ["home-poster-wall", "library-poster-wall"]:
    nodes[nid].setdefault("events", {})["hover"] = "tilt-poster"

A = {
    "switch-destination": "TabBar selection shows Home, Library, Sources or Settings inside the Library Volume; each destination keeps its scroll position and filter when revisited.",
    "open-detail": "Selecting a poster or continue-watching card opens the Details Subwindow beside the Volume and fills it with the selected title (backdrop, name, chips, overview, audio, subtitles, episodes for series). Selecting another title replaces the content without closing.",
    "close-detail": "Closes the Details Subwindow; the Volume keeps its current destination.",
    "tilt-poster": "Ray, hand-ray or gaze hover tilts the hovered poster up to 8 degrees toward the pointer and widens its layer separation; leaving restores it.",
    "enter-cinema": "Opens the Full Space cinema Stage and plays the selected title from its saved position (or from 0:00 when none); the Library Volume is hidden while the Stage is open.",
    "enter-cinema-from-start": "Same as enter-cinema but starts at 0:00 and overwrites the saved position as playback advances.",
    "exit-cinema": "Saves the playback position, closes the Stage and returns to the Library Volume with the Details Subwindow still showing the title.",
    "toggle-playback": "Toggles play/pause; the button icon and accessible name switch between Pause and Play.",
    "seek-back": "Seeks 15 s back.", "seek-forward": "Seeks 15 s forward.", "seek-to": "Seeks to the slider position and updates the time label.",
    "set-volume": "Sets the playback volume.",
    "open-subtitle-menu": "Opens the subtitle menu anchored to the subtitle button.",
    "choose-subtitle": "Selects Off, an external SRT/ASS track or an embedded subtitle track; the check mark moves and the screen subtitle line updates or hides.",
    "load-subtitle-file": "Opens the system file picker for a .srt/.ass file next to the video; the loaded track is added to the menu and selected.",
    "open-audio-menu": "Opens the audio track menu.", "choose-audio-track": "Switches the active audio track; the check mark moves.",
    "open-size-menu": "Opens the screen size menu.", "choose-screen-size": "Resizes the screen to Small 3 m, Medium 6 m or Large 10 m keeping the same visual centre.",
    "toggle-room-dimming": "On: dark virtual theater (StageStyle.Full). Off: dimmed passthrough room (Mixed).",
    "open-language-menu": "Opens the language menu (Follow system, Simplified Chinese, English).",
    "choose-language": "Applies the chosen language to every string immediately and persists it.",
    "set-poster-depth": "Sets 3D poster layer separation: Off, Subtle, Standard (default), Strong; posters update immediately.",
    "toggle-auto-resume": "When on, playback starts from the saved position; when off, from 0:00.",
    "ask-clear-history": "Opens the Clear watch history confirmation dialog.",
    "clear-history": "Removes all saved positions; Continue watching becomes empty; a snackbar confirms.",
    "exit-app": "Finishes the activity and closes all Home Cinema windows.",
    "open-add-source": "Opens the Add media source sheet with Jellyfin preselected.",
    "close-add-source": "Closes the sheet without saving.",
    "choose-source-type": "Single choice. Emby/Jellyfin/WebDAV show server, username and password fields; Headset storage hides them and the main button becomes Choose folder.",
    "connect-source": "Authenticates (Emby/Jellyfin AuthenticateByName, WebDAV PROPFIND) or opens the folder picker; on success the source appears in the Sources list and its titles join the library; on failure the field shows an error.",
    "filter-library": "Filters the library grid to All, Movies or Shows.",
    "search-library": "Opens a search field in the Home header filtering titles by name.",
    "refresh-library": "Re-reads all connected sources.",
}
actions = [{"id": k, "purpose": v} for k, v in A.items()]

# Assets
assets = []
for f in sorted(os.listdir(os.path.join(S, "assets"))):
    path = os.path.join(S, "assets", f)
    aid = os.path.splitext(f)[0]
    kind = "data" if f.endswith(".json") else "image"
    purpose = {"poster": "Demo poster plate (2:3), original artwork", "backdrop": "Demo backdrop (16:9) used for the back poster layer, cards, details and the cinema stand-in",
               "logo": "Demo title logo (transparent) used as the front poster layer", "app": "Application icon (original)",
               "demo": "Manifest of demo titles and their three poster layers"}[aid.split("-")[0]]
    assets.append({"id": aid, "kind": kind, "src": "assets/" + f, "purpose": purpose,
                   "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()})

titles = json.loads(re.search(r'<script id="title-data" type="application/json">(.*?)</script>', html, re.S).group(1))
spec = {
    "schemaVersion": "write-spec-draft-1",
    "metadata": {"projectName": "Home Cinema", "revision": 1, "preview": "preview.html",
                 "references": [{"path": "runtime/" + f, "version": "pico-spatial-agentic-tools 0.7.0-beta.2 design-reference snapshot (AutoEva_SpatialDesignSystem 4b664e8)",
                                 "sha256": hashlib.sha256(open(os.path.join(S, "runtime", f), "rb").read()).hexdigest()} for f in ("components.js", "tokens.css", "tokens.json", "color-roles.json")],
                 "languages": ["en", "zh-CN"]},
    "experience": {"subject": "Browse your own Emby / Jellyfin / WebDAV / headset video library as a wall of 3D layered posters, then watch on a large screen in a virtual theater with resume, subtitles and audio track selection.",
                   "form": "Primarily 3D posters with supporting 2D in a Shared Space Volume (Library); Full Space Stage for playback (Cinema)."},
    "theme": {"brandColors": {}},
    "surfaces": [
        {"id": "library-volume", "type": "volume", "defaultSize": {"width": 1280, "height": 760, "depth": 360, "unit": "dp"}, "rootNodeId": "vol-root",
         "purpose": "Main window in Shared Space; TabBar attached above; no recenter or bring-to-front promise"},
        {"id": "detail-window", "type": "subwindow", "ownerSurfaceId": "library-volume", "defaultSize": {"width": 360, "height": 760, "unit": "dp"},
         "rootNodeId": "detail-window", "initiallyVisible": False,
         "placement": {"side": "end", "align": "top", "gapDp": 24, "depthDp": 0}},
        {"id": "cinema-stage", "type": "stage", "defaultSize": {"width": 10, "height": 5, "depth": 12, "unit": "m"}, "rootNodeId": "scene-cinema", "initiallyVisible": False,
         "purpose": "Full Space Stage; dark virtual theater (StageStyle.Full) or dimmed passthrough (Mixed); extent describes the authored theater around the user"},
    ],
    "initialStateId": "initial",
    "states": [
        {"id": "initial", "surfaceRoots": {"library-volume": "vol-root"},
         "values": {"destination": "Home", "language": "Follow system", "posterDepth": "Standard", "autoResume": True, "sources": ["Demo library"]}},
        {"id": "details-open", "surfaceRoots": {"library-volume": "vol-root", "detail-window": "detail-window"}, "values": {"selectedTitle": "harbor"}},
        {"id": "cinema", "surfaceRoots": {"cinema-stage": "scene-cinema"}, "values": {"playing": True, "subtitle": "Chinese (SRT)", "audio": "Original · Stereo", "screen": "Medium 6 m", "dimRoom": True}},
    ],
    "actions": actions,
    "nodes": [nodes[i] for i in order],
    "assets": assets,
    "dataCases": {"titles": titles},
}
json.dump(spec, open(os.path.join(S, "design-spec.json"), "w"), indent=1, ensure_ascii=False)
print("nodes", len(nodes), "actions", len(actions), "assets", len(assets))
