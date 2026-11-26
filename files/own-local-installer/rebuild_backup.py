"""Rebuild the decoded local Moonlight HTML from SIDEE BKUP log lines.

Usage:
    python3 rebuild_backup.py LOGS.txt OUTPUT.html

LOGS.txt can be a raw dump of http://192.168.1.69:8484/logs.
Only lines containing "SIDEE BKUP <i>/<n> <base64>" are used.
"""
from pathlib import Path
import base64
import hashlib
import re
import sys

TAG = re.compile(r"SIDEE\s+BKUP\s+(\d+)/(\d+)\s+(.*)$")
CHARS = re.compile(r"[^A-Za-z0-9+/=]")


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: rebuild_backup.py LOGS.txt OUTPUT.html")

    src = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    chunks = {}
    total = None

    for line in src.splitlines():
        m = TAG.search(line)
        if not m:
            continue
        index = int(m.group(1))
        count = int(m.group(2))
        data = CHARS.sub("", m.group(3))
        if total is None:
            total = count
        elif total != count:
            raise SystemExit("inconsistent total: %d vs %d" % (total, count))
        chunks[index] = data

    if not chunks:
        raise SystemExit("no SIDEE BKUP lines found")
    missing = [i for i in range(total) if i not in chunks]
    if missing:
        raise SystemExit("missing chunks: " + ",".join(map(str, missing[:20])))

    b64 = "".join(chunks[i] for i in range(total))
    html = base64.b64decode(b64).decode("utf-8")
    out = Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    digest = hashlib.sha256(html.encode("utf-8")).hexdigest()
    print("wrote", out, len(html.encode("utf-8")), "bytes")
    print("sha256", digest)


if __name__ == "__main__":
    main()
