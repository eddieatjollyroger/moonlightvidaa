"""Point the installer's button 0 at the final English packed bundle.

Usage:
    python3 patch_installer.py OUT.html

Reads the generated English packed file, computes its UTF-8 byte length and
SHA-256, then updates BACKUP_URL / EXPECT_LEN / EXPECT_SHA in
`install-ownmoon-local.html`.
"""
from pathlib import Path
import hashlib
import re
import sys

HERE = Path(__file__).resolve().parent
INSTALLER = HERE / "install-ownmoon-local.html"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_installer.py OUT.html")
    src = Path(sys.argv[1]).read_bytes()
    size = len(src)
    sha = hashlib.sha256(src).hexdigest()

    text = INSTALLER.read_text(encoding="utf-8")
    old_url = re.search(r"var BACKUP_URL='([^']*)';", text)
    old_len = re.search(r"var EXPECT_LEN=(\d+);", text)
    old_sha = re.search(r"var EXPECT_SHA='([0-9a-fA-F]{64})';", text)
    if not (old_url and old_len and old_sha):
        raise SystemExit("installer constants not found")

    text = text.replace(
        "var BACKUP_URL='%s';" % old_url.group(1),
        "var BACKUP_URL='https://moonlight.joaopacheco.me/own-webrtc/ownmoon-en-packed.html';",
    )
    text = text.replace("var EXPECT_LEN=%d;" % int(old_len.group(1)), "var EXPECT_LEN=%d;" % size)
    text = text.replace(
        "var EXPECT_SHA='%s';" % old_sha.group(1), "var EXPECT_SHA='%s';" % sha
    )
    INSTALLER.write_text(text, encoding="utf-8")
    print("backup_url", "https://moonlight.joaopacheco.me/own-webrtc/ownmoon-en-packed.html")
    print("expect_len", size)
    print("expect_sha", sha)
    print("patched", INSTALLER)


if __name__ == "__main__":
    main()
