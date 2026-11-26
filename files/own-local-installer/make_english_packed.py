"""Rebuild the packed wrapper with the English decoded app.

Usage:
    python3 make_english_packed.py PACKED.html DECODED_EN.html DECODED_ORIG.html OUT.html

The wrapper's `moonlight` blob is gzip+base64. This script replaces only that
blob; the wrapper code and the `emu` blob stay byte-for-byte identical.
"""
from pathlib import Path
import base64
import gzip
import hashlib
import re
import sys

BLOB_RE = re.compile(r'("moonlight"\s*:\s*")([A-Za-z0-9+/=]+)(")')
EMU_RE = re.compile(r'("emu"\s*:\s*")([A-Za-z0-9+/=]+)(")')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 5:
        raise SystemExit(
            "usage: make_english_packed.py PACKED.html DECODED_EN.html "
            "DECODED_ORIG.html OUT.html"
        )

    packed_path = Path(sys.argv[1])
    en_path = Path(sys.argv[2])
    orig_path = Path(sys.argv[3])
    out_path = Path(sys.argv[4])

    packed = packed_path.read_text(encoding="utf-8")
    en_bytes = en_path.read_bytes()
    orig_bytes = orig_path.read_bytes()

    matches = list(BLOB_RE.finditer(packed))
    if len(matches) != 1:
        raise SystemExit("expected exactly one moonlight blob, found %d" % len(matches))
    match = matches[0]
    old_b64 = match.group(2)

    try:
        old_html = gzip.decompress(base64.b64decode(old_b64, validate=True))
    except Exception as exc:
        raise SystemExit("could not decode old moonlight blob: %s" % exc)
    if digest(old_html) != digest(orig_bytes):
        raise SystemExit(
            "packed blob does not match decoded original: %s != %s"
            % (digest(old_html), digest(orig_bytes))
        )
    print("verified old blob sha", digest(old_html))

    emu_matches = list(EMU_RE.finditer(packed))
    if len(emu_matches) != 1:
        raise SystemExit("expected exactly one emu blob, found %d" % len(emu_matches))
    old_emu = emu_matches[0].group(2)

    new_b64 = base64.b64encode(gzip.compress(en_bytes, compresslevel=9, mtime=0)).decode("ascii")
    new_packed = packed[: match.start(2)] + new_b64 + packed[match.end(2) :]

    # Verify replacement and that nothing else changed.
    check = list(BLOB_RE.finditer(new_packed))
    if len(check) != 1:
        raise SystemExit("replacement produced bad moonlight blob count")
    try:
        check_html = gzip.decompress(base64.b64decode(check[0].group(2), validate=True))
    except Exception as exc:
        raise SystemExit("new moonlight blob is not valid gzip: %s" % exc)
    if check_html != en_bytes:
        raise SystemExit("new blob did not round-trip to the English HTML")

    check_emu = list(EMU_RE.finditer(new_packed))
    if len(check_emu) != 1 or check_emu[0].group(2) != old_emu:
        raise SystemExit("emu blob changed unexpectedly")

    stripped_old = packed[: match.start(2)] + packed[match.end(2) :]
    stripped_new = new_packed[: check[0].start(2)] + new_packed[check[0].end(2) :]
    if stripped_old != stripped_new:
        raise SystemExit("wrapper changed outside the moonlight blob")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(new_packed, encoding="utf-8")
    out_bytes = new_packed.encode("utf-8")
    print("english decoded sha", digest(en_bytes))
    print("new packed bytes", len(out_bytes))
    print("new packed sha256", digest(out_bytes))
    print("wrote", out_path)


if __name__ == "__main__":
    main()
