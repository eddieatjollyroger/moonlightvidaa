"""Build a single-file local app bundle from files/own-webrtc.

Output: ownmoon.html. It has no external JS/CSS and can be written to
/APPS/websdk/ownmoon.html with the documented mode-6 bridge, avoiding mkdir.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "own-webrtc"
OUT = HERE / "ownmoon.html"

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

for name in SCRIPTS:
    old = '<script src="' + name + '?v=own1"></script>'
    if old not in html:
        raise SystemExit("missing script tag: " + name)
    js = (SRC / name).read_text(encoding="utf-8")
    if "</script" in js.lower():
        raise SystemExit("script contains </script: " + name)
    html = html.replace(old, "<script>\n" + js + "\n</script>")

html = html.replace(
    'src="assets/moonlight-logo.svg?v=own1"',
    'src="https://moonlight.joaopacheco.me/own-webrtc/assets/moonlight-logo.svg"',
)

OUT.write_text(html, encoding="utf-8")
print("wrote", OUT, len(html.encode("utf-8")), "bytes")
