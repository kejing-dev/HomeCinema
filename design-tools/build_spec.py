"""Write .scratch/design-spec.json for the Cinema Frame design (门 B 改, option A) from the approved Preview.
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
        self.tag, self.a, self.parent, self.kids = tag, dict(attrs), parent, []


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


p = P(); p.feed(html)
COLOR = {"var(--label-semidark-alpha)": "labelTertiary", "var(--label-darkest-alpha)": "labelPrimary",
         "var(--fill-neutral-alpha)": "fillTertiary", "var(--semantic-interaction)": "interaction"}
DROP = {"id", "class", "style", "role", "tabindex", "hidden", "for", "alt", "src", "width", "height"}
nodes, order = {}, []


def find(e, i):
    if e.a.get("id") == i: return e
    for k in e.kids:
        r = find(k, i)
        if r: return r


def idkids(e):
    out = []
    for k in e.kids:
        i = k.a.get("id")
        if k.tag == "script": continue
        if i and not i.startswith("pv-"): out.append(k)
        elif not i: out.extend(idkids(k))
    return out


def loc(e):
    r = {}
    for k, v in e.a.items():
        if k.startswith("data-t-"):
            r[k[7:]] = {"en": i18n["en"][v], "zh": i18n["zh"][v], "key": v}
    return r


LAYOUT = {
    "ctl-root": {"mode": "column", "paddingDp": 24, "gapDp": 16, "height": "fill"},
    "ctl-head": {"mode": "row", "gapDp": 12, "align": "center"},
    "ctl-head-copy": {"mode": "column", "gapDp": 2, "grow": 1},
    "page-show": {"mode": "column", "gapDp": 14, "grow": 1},
    "page-settings": {"mode": "column", "gapDp": 14, "grow": 1},
    "style-grid": {"mode": "grid", "columns": 3, "gapDp": 12},
    "show-row": {"mode": "column", "gapDp": 8},
    "set-list": {"mode": "column", "gapDp": 8, "grow": 1, "overflow": "auto"},
    "exit-row": {"mode": "row", "justify": "end"},
    "align-body": {"mode": "column", "widthDp": 640, "gapDp": 12, "paddingDp": 24},
    "align-steps": {"mode": "column", "gapDp": 6},
    "align-actions": {"mode": "row", "justify": "end", "gapDp": 8},
    "vol-root": {"mode": "stack", "sizing": "matchParent", "note": "Volume content root; 3D scene children are positioned in the Volume, the align panel is a scene attachment"},
}
RENDER = {"frame-model": "frame-style-model", "align-outline": "align-outline"}
GEOM = {"frame-model": {"sizing": "matchParent", "modelExtentM": [3.4, 2.0, 0.6], "openingM": [1.6, 0.9], "dpPerModelMetre": 750},
        "align-outline": {"xDp": 675, "yDp": 412, "widthDp": 1200, "heightDp": 676}}


def build(e):
    nid = e.a["id"]
    if e.tag == "img" and "frame-art" in e.a.get("class", ""): return None
    kids = [k for k in (build(k) for k in idkids(e)) if k]
    n = {"id": nid}
    if nid in RENDER:
        n["kind"] = "domain_visual"; n["rendererKey"] = RENDER[nid]
        n["purpose"] = "3D model: " + notes[nid]["represents"]
        n["layout"] = GEOM[nid]
        if nid == "frame-model":
            n["assetId"] = "frame-walnut"
            n["bindings"] = {"assetId": "frame-<style> (walnut | beton | linen | slats | bronze)", "showState": "showState", "alignMode": "alignMode"}
    elif e.tag == "sui-text":
        n["kind"] = "text"; n["content"] = e.a.get("text", "")
        n["textStyle"] = {"typography": e.a.get("text-style", "bodyMedium"), "color": COLOR.get(e.a.get("color", ""), "labelPrimary")}
    elif e.tag.startswith("sui-"):
        n["kind"] = "spatialui"; n["component"] = e.tag
        props = {}
        for k, v in e.a.items():
            if k in DROP or k.startswith("data-") or k.startswith("aria-"): continue
            if k.endswith("-color"): v = COLOR.get(v, v)
            if v == "": v = True
            if isinstance(v, str) and re.fullmatch(r"-?\d+(\.\d+)?", v) and k not in ("text", "headline", "supporting", "title", "options"):
                v = float(v) if "." in v else int(v)
            props[k] = v
        m = re.search(r"width:(\d+)px", e.a.get("style", ""))
        if m: props["custom-width"] = int(m.group(1))
        if "width:100%" in e.a.get("style", ""): n["layout"] = {"width": "fill"}
        n["props"] = props
    elif e.tag == "img":
        n["kind"] = "media"; n["assetId"] = os.path.splitext(os.path.basename(e.a["src"]))[0]
        n["layout"] = {"widthDp": 48, "heightDp": 48, "radiusDp": 12} if nid == "ctl-icon" else {"widthDp": 120, "heightDp": 75, "radiusDp": 10, "fit": "cover"}
    elif e.tag == "img" and "frame-art" in e.a.get("class", ""):
        return None
    elif "style-card" in e.a.get("class", ""):
        n["kind"] = "content"
        n["layout"] = {"mode": "column", "widthDp": 136, "gapDp": 6, "paddingDp": 8}
        n["appearance"] = {"fill": "fillLight", "radiusDp": 16}
        n["purpose"] = "Frame style card (thumbnail is a crop of the style's front render); the selected card shows a 3 dp inner stroke in the interaction colour"
        n["bindings"] = {"selected": "style == " + e.a["data-style"]}
        n["events"] = {"select": "choose-style"}
    else:
        n["kind"] = "layout"; n["layout"] = LAYOUT[nid]
    if e.a.get("slot"): n.setdefault("props", {})["slot"] = e.a["slot"]
    l = loc(e)
    if l: n["localizedText"] = l
    if nid in notes: n["designNotes"] = notes[nid]
    if kids: n["children"] = [k["id"] for k in kids]
    nodes[nid] = n; order.append(nid)
    return n


build(find(p.root, "vol-root"))
build(find(p.root, "ctl-root"))
build(find(p.root, "lang-menu"))
nodes["lang-menu"]["props"]["anchor-node-id"] = "lang-btn"
nodes["set-list"]["children"].insert(nodes["set-list"]["children"].index("lang-item") + 1, "lang-menu")
order.remove("lang-menu"); order.insert(order.index("lang-item") + 2, "lang-menu")

HIDDEN = {"page-settings": "panelPage != Settings", "page-show": "panelPage != Show", "align-panel": "alignMode == off",
          "align-outline": "alignMode == off", "lang-menu": "closed until open-language-menu"}
for k, v in HIDDEN.items(): nodes[k].setdefault("bindings", {})["hidden"] = v
nodes["ctl-status"]["bindings"] = {"content": "status text for the current show state (status.up / opening / showing / closing / align)"}
nodes["show-toggle"]["bindings"] = {"text": "show.start while Lights up or Closing; show.end while Opening or Showing", "leading-icon": "ic_play / ic_sun"}
nodes["style-desc"]["bindings"] = {"content": "sd.<style>: the selected style's light and ambience line"}

EV = {"ctl-tabs": ("select", "switch-panel-page"), "show-toggle": ("click-action", "toggle-show"),
      "auto-switch": ("checked-change", "toggle-auto-show"), "align-btn": ("click-action", "enter-align-mode"),
      "align-done": ("click-action", "leave-align-mode"), "timer-seg": ("select", "set-sleep-timer"),
      "sound-switch": ("checked-change", "toggle-ambience"), "sound-vol": ("value-change", "set-ambience-volume"),
      "lang-btn": ("click-action", "open-language-menu"), "lang-sys": ("select", "choose-language"),
      "lang-zh": ("select", "choose-language"), "lang-en": ("select", "choose-language"), "exit-btn": ("click-action", "exit-app")}
for k, (ev, act) in EV.items(): nodes[k].setdefault("events", {})[ev] = act

A = {
    "choose-style": "Loads the selected style's GLB (Walnut Gallery, Béton, Linen Room, Smoked Oak, Bronze Line) into the Volume with a 1.2 s cross-fade, switches its soft light (the one emit_* material: a baked wash or a hidden LED line) and ambience loop, updates the style line; remembered across launches.",
    "toggle-show": "Manual fallback. Start the show: Opening (the frame's soft light fades to 12 % over 4 s, ambience fades in) then Showing. End the show: Closing (soft light back to 100 % over 6 s, ambience fades out) then Lights up. Only our own frame lights change; the room is not dimmed.",
    "toggle-auto-show": "When on (default), polls AudioManager.isMusicActive every 1 s: inactive to active starts the show; 8 s of continuous inactivity ends it. A manual press overrides auto until the next state change from sound.",
    "enter-align-mode": "Shows the alignment outline and the align panel; the system window handles of the Volume are highlighted; the soft light stays up so the opening is easy to see.",
    "leave-align-mode": "Hides the alignment aids. The Volume keeps the size and position the user set (the system restores it on next launch where supported).",
    "set-sleep-timer": "Off / 60 / 90 / 120 min. On expiry runs End the show and stops ambience; it never pauses or closes the other app. A small remaining-time line appears under the status text while active.",
    "toggle-ambience": "Plays the selected style's looped ambience during Opening and Showing only; off by default.",
    "set-ambience-volume": "Sets ambience volume 0-1 (default 0.3).",
    "switch-panel-page": "Shows the Show or Settings page in the controls window.",
    "open-language-menu": "Opens the language menu anchored to the language button.",
    "choose-language": "Applies Follow system / Simplified Chinese / English to all strings immediately and persists it.",
    "exit-app": "Finishes the activity and closes the frame Volume and the controls window.",
}
actions = [{"id": k, "purpose": v} for k, v in A.items()]

assets = []
PURPOSE = {"app-icon": "Application icon (original)"}
for root, _, files in os.walk(os.path.join(S, "assets")):
    for f in sorted(files):
        path = os.path.join(root, f); rel = os.path.relpath(path, S); aid = os.path.splitext(f)[0]
        if f.endswith(".glb"):
            aid = "frame-" + aid; kind = "model"; purpose = "Frame style 3D model (GLB, metres, PBR wood / concrete / linen / bronze with 512 px colour + normal maps, one emit_* soft-light material; Tripo props decimated with bin/glb_decimate.py)"
        elif aid.startswith("frame-"):
            kind = "image"; purpose = "Preview-only transparent render of the frame GLB (" + aid.split("-")[-1] + " state)"
        elif aid.startswith("style-"):
            kind = "image"; purpose = "Frame style thumbnail (crop of the style's front render)"
        else:
            kind = "image"; purpose = PURPOSE.get(aid, "")
        if f.endswith(".png") and aid.startswith("frame-"): aid = aid + "-render"
        assets.append({"id": aid, "kind": kind, "src": rel, "purpose": purpose, "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()})

spec = {
    "schemaVersion": "write-spec-draft-1",
    "metadata": {"projectName": "Home Cinema", "revision": 4, "preview": "preview.html", "languages": ["en", "zh-CN"],
                 "references": [{"path": "runtime/" + f, "version": "pico-spatial-agentic-tools 0.7.0-beta.2 design-reference snapshot",
                                 "sha256": hashlib.sha256(open(os.path.join(S, "runtime", f), "rb").read()).hexdigest()} for f in ("components.js", "tokens.css", "tokens.json", "color-roles.json")]},
    "experience": {"subject": "A cinema frame that decorates around whatever video the user is already watching in another app (system player, PICO Video, browser): five ambient wall-treatment styles in real materials (Walnut Gallery, Béton, Linen Room, Smoked Oak, Bronze Line): low saturation, low brightness, no neon or glow, each with a soft light that fades during the show and an optional quiet ambience, with show lighting that follows the sound and a sleep timer. It does not play video, dim the room or control other apps.",
                   "form": "Shared Space only. A hollow 3D Volume (one of five ambient 3D wall-treatment styles) plus a small Planar controls window to its right. No Stage, because Stage forces Full Space, which hides other apps and stops their playback (verified on emulator, see feasibility.md)."},
    "theme": {"brandColors": {}},
    "surfaces": [
        {"id": "frame-volume", "type": "volume", "defaultSize": {"width": 2550, "height": 1500, "depth": 450, "unit": "dp"}, "rootNodeId": "vol-root",
         "purpose": "Main window. Transparent (no material background, base panel hidden), uniform resize only so the 16:9 opening keeps its shape. The user aligns it around the other app's player window by hand; Home Cinema cannot read other windows' poses. No recenter or bring-to-front promise."},
        {"id": "controls-window", "type": "planar", "defaultSize": {"width": 480, "height": 720, "unit": "dp"}, "rootNodeId": "ctl-root",
         "windowBackground": "material", "ownerSurfaceId": "frame-volume", "initiallyVisible": True,
         "placement": {"side": "end", "align": "bottom", "gapDp": 60, "depthDp": 0},
         "purpose": "Controls beside the frame (Placement.right of the Volume); never over the opening."},
    ],
    "initialStateId": "lights-up",
    "states": [
        {"id": "lights-up", "surfaceRoots": {"frame-volume": "vol-root", "controls-window": "ctl-root"},
         "values": {"style": "walnut", "showState": "up", "alignMode": "off", "panelPage": "Show", "autoShow": True, "sleepTimer": "Off", "ambience": False, "language": "Follow system"}},
        {"id": "first-launch-align", "surfaceRoots": {"frame-volume": "vol-root", "controls-window": "ctl-root"}, "values": {"alignMode": "on"},
         "note": "Shown automatically on first launch, then only from Align frame to player"},
        {"id": "showing", "surfaceRoots": {"frame-volume": "vol-root", "controls-window": "ctl-root"}, "values": {"showState": "showing"}},
        {"id": "settings", "surfaceRoots": {"frame-volume": "vol-root", "controls-window": "ctl-root"}, "values": {"panelPage": "Settings"}},
    ],
    "actions": actions,
    "nodes": [nodes[i] for i in order],
    "assets": assets,
}
json.dump(spec, open(os.path.join(S, "design-spec.json"), "w"), indent=1, ensure_ascii=False)
print("nodes", len(nodes), "actions", len(actions), "assets", len(assets))
