"""Rebuild the decoded local Moonlight HTML from SIDEE BKUP3 log lines.

Usage:
    python3 rebuild_backup.py LOGS.txt OUTPUT.html

LOGS.txt can be a raw dump of http://192.168.1.69:8484/logs.
BKUP3 is preferred. Older BKUP2/BKUP lines are fallbacks only.
"""
from pathlib import Path
import base64
import hashlib
import re
import sys

TAGS = [
    ("BKUP3", re.compile(r"SIDEE\s+BKUP3\s+(\d+)/(\d+)\s+(.*)$")),
    ("BKUP2", re.compile(r"SIDEE\s+BKUP2\s+(\d+)/(\d+)\s+(.*)$")),
    ("BKUP", re.compile(r"SIDEE\s+BKUP\s+(\d+)/(\d+)\s+(.*)$")),
]
CHARS = re.compile(r"[^A-Za-z0-9+/=]")


def collect(src, tag):
    chunks = {}
    total = None
    for line in src.splitlines():
        m = tag.search(line)
        if not m:
            continue
        index = int(m.group(1))
        count = int(m.group(2))
        data = CHARS.sub("", m.group(3))
        if not data:
            continue
        if total is None:
            total = count
        elif total != count:
            raise SystemExit("inconsistent total: %d vs %d" % (total, count))
        chunks[index] = data
    return chunks, total


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: rebuild_backup.py LOGS.txt OUTPUT.html")

    src = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    chunks = {}
    total = None
    tag_name = None
    for name, tag in TAGS:
        chunks, total = collect(src, tag)
        if chunks:
            tag_name = name
            break

    if not chunks:
        raise SystemExit("no SIDEE BKUP3 / BKUP2 / BKUP lines found")
    missing = [i for i in range(total) if i not in chunks]
    if missing:
        raise SystemExit("missing chunks: " + ",".join(map(str, missing[:20])))

    b64 = "".join(chunks[i] for i in range(total))
    html = base64.b64decode(b64).decode("utf-8")
    out = Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    digest = hashlib.sha256(html.encode("utf-8")).hexdigest()
    print("source", tag_name, "chunks", total)
    print("wrote", out, len(html.encode("utf-8")), "bytes")
    print("sha256", digest)


if __name__ == "__main__":
    main()
