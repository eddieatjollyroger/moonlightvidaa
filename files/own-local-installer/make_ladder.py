"""Build incremental content variants for the working OWN HELLO tile.

Each variant is written to the same flat file that the working hello tile
points at, so no AppInfo changes are needed while bisecting.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "own-webrtc"
OUT = HERE

SCRIPTS = [
    "gamepad-input.js",
    "gamepad-ui-navigation.js",
    "preferences.js",
    "gateway-store.js",
    "gateway-ipv4.js",
    "application-artwork.js",
    "ui.js",
    "tv-patch.js",
    "app.js",
]

html = (SRC / "index.html").read_text(encoding="utf-8")
css = (SRC / "ui.css").read_text(encoding="utf-8")
html = html.replace(
    '<link rel="stylesheet" href="ui.css?v=own1">',
    "<style>\n" + css + "\n</style>",
)
html = html.replace(
    'src="assets/moonlight-logo.svg?v=own1"',
    'src="data:image/gif;base64,R0lGODlhAQABAAAAACw="',
)


def inline(js_names):
    out = html
    for name in SCRIPTS:
        tag = '<script src="' + name + '?v=own1"></script>'
        if name in js_names:
            js = (SRC / name).read_text(encoding="utf-8")
            if "</script" in js.lower():
                raise SystemExit("script contains </script: " + name)
            out = out.replace(tag, "<script>\n" + js + "\n</script>")
        else:
            out = out.replace(tag, "")
    return out


files = {
    "ladder-hello.html": (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>OK LOCAL</title></head><body style='background:#111;color:#7f7;"
        "font:48px sans-serif;padding:40px'>OK LOCAL PATH</body></html>"
    ),
    "ladder-css.html": inline([]),
    "ladder-js1.html": inline([SCRIPTS[0]]),
    "ladder-jsall.html": (HERE / "ownmoon.html").read_text(encoding="utf-8"),
}

for i in range(1, len(SCRIPTS) + 1):
    files["ladder-js%d.html" % i] = inline(SCRIPTS[:i])
files["ladder-noimg.html"] = inline(SCRIPTS)

for name, text in files.items():
    (OUT / name).write_text(text, encoding="utf-8")
    print("wrote", name, len(text.encode("utf-8")), "bytes")
