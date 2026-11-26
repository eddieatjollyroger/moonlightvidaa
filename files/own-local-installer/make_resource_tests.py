"""Test the remaining resource tags that can keep document.readyState=interactive."""
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
BASE = (HERE / "ladder-js9-loadlog.html").read_text(encoding="utf-8")

BAD_GIF = "data:image/gif;base64,R0lGODlhAQABAAAAACw="
GOOD_GIF = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

variants = {
    "ladder-js9-goodgif.html": BASE.replace(BAD_GIF, GOOD_GIF),
    "ladder-js9-noimg.html": re.sub(r"<img\b[^>]*>", "", BASE),
    "ladder-js9-noautoplay.html": BASE.replace(
        '<video id="video" autoplay playsinline hidden></video>',
        '<video id="video" playsinline hidden></video>',
    ),
}

for name, text in variants.items():
    (HERE / name).write_text(text, encoding="utf-8")
    print("wrote", name, len(text.encode("utf-8")), "bytes")
