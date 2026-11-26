"""Rebuild the packed local bundle from SIDEE PACK1 log lines.

Usage:
    python3 rebuild_packed.py LOGS.txt OUTPUT.html

The TV page `packed-export.html` gzips and base64-encodes the full UTF-8 bytes
of `emanual/Local_ebook/ownmoon-local.html`, then posts 700-char chunks as
`SIDEE PACK1 i/n ...`. The matching `SIDEE PACKINFO` line records the gzip flag,
base64 length, chunk count, UTF-8 byte length and SHA-256 of the original file.
"""
from pathlib import Path
import base64
import binascii
import gzip
import hashlib
import re
import sys

CHUNK_RE = re.compile(r"SIDEE\s+PACK1\s+(\d+)/(\d+)\s+(.*?)\s*(?:\|\s*\?)?$")
INFO_RE = re.compile(r"SIDEE\s+PACKINFO\s+\d+/\d+\s+(.*?)\s*(?:\|\s*\?)?$")
FIELDS_RE = re.compile(
    r"GZIP\s+(\d+)\s+B64LEN\s+(\d+)\s+CHUNKS\s+(\d+)\s+BYTES\s+(\d+)\s+"
    r"SHA\s+([0-9a-fA-F]{64})"
)


def clean(data):
    return re.sub(r"[^A-Za-z0-9+/=]", "", data)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: rebuild_packed.py LOGS.txt OUTPUT.html")

    src = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    chunks = {}
    total = None
    for line in src.splitlines():
        m = CHUNK_RE.search(line)
        if not m:
            continue
        index = int(m.group(1))
        count = int(m.group(2))
        data = clean(m.group(3))
        if not data:
            continue
        if total is None:
            total = count
        elif total != count:
            raise SystemExit("inconsistent chunk total: %d vs %d" % (total, count))
        chunks[index] = data  # last complete export wins

    if not chunks or total is None:
        raise SystemExit("no SIDEE PACK1 lines found")
    missing = [i for i in range(total) if i not in chunks]
    if missing:
        raise SystemExit("missing chunks: " + ",".join(map(str, missing[:30])))

    b64 = "".join(chunks[i] for i in range(total))

    infos = INFO_RE.findall(src)
    if not infos:
        raise SystemExit("no SIDEE PACKINFO line found")
    fields = FIELDS_RE.search(infos[-1])
    if not fields:
        raise SystemExit("could not parse SIDEE PACKINFO: " + infos[-1][:200])
    gz_flag, b64_len, info_chunks, byte_len, sha = fields.groups()
    gz_flag = int(gz_flag)
    b64_len = int(b64_len)
    info_chunks = int(info_chunks)
    byte_len = int(byte_len)
    sha = sha.lower()

    if info_chunks != total:
        raise SystemExit("chunk count mismatch: logs=%d PACKINFO=%d" % (total, info_chunks))
    if b64_len != len(b64):
        raise SystemExit("base64 length mismatch: logs=%d PACKINFO=%d" % (len(b64), b64_len))

    try:
        payload = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise SystemExit("bad base64: %s" % exc)
    if gz_flag:
        try:
            raw = gzip.decompress(payload)
        except OSError as exc:
            raise SystemExit("bad gzip payload: %s" % exc)
    else:
        raw = payload
    if len(raw) != byte_len:
        raise SystemExit("byte length mismatch: decoded=%d PACKINFO=%d" % (len(raw), byte_len))

    digest = hashlib.sha256(raw).hexdigest()
    if digest != sha:
        raise SystemExit("sha mismatch: decoded=%s PACKINFO=%s" % (digest, sha))

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit("decoded data is not UTF-8: %s" % exc)

    out = Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    print("chunks", total)
    print("gzip", gz_flag)
    print("bytes", byte_len)
    print("sha256", digest)
    print("wrote", out)
    if text[:15] != "<!DOCTYPE html>":
        print("warning: head does not look like HTML: " + text[:80].replace("\n", " "))


if __name__ == "__main__":
    main()
