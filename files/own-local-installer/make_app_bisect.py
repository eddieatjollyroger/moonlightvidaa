"""Bisect app.js by generating syntactically valid prefixes appended to JS8."""
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
BASE = (HERE / "ladder-js8.html").read_text(encoding="utf-8")
APP = (HERE.parent / "own-webrtc" / "app.js").read_text(encoding="utf-8")
LINES = APP.splitlines(keepends=True)


def valid(n):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write("".join(LINES[:n]))
        path = f.name
    try:
        r = subprocess.run(["node", "--check", path], capture_output=True)
        return r.returncode == 0
    finally:
        Path(path).unlink(missing_ok=True)


cuts = []
for pct in range(10, 101, 10):
    target = max(1, round(len(LINES) * pct / 100))
    n = target
    while n > 0 and not valid(n):
        n -= 1
    if n == 0:
        raise SystemExit("no valid cut for " + str(pct))
    cuts.append((pct, n))

for pct, n in cuts:
    prefix = "".join(LINES[:n])
    html = BASE.replace("</body>", "<script>\n" + prefix + "\n</script>\n</body>")
    name = "ladder-app%d.html" % pct
    (HERE / name).write_text(html, encoding="utf-8")
    print("wrote", name, "lines", n, "bytes", len(html.encode("utf-8")))
