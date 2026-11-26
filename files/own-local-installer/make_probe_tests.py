"""Generate app.js probe variants from the full no-image bundle."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = (HERE / "ladder-js9.html").read_text(encoding="utf-8")

TAIL = "showHome();\ngamepadUiNavigation.start();\nrenderGateways();\nprobeSavedGateways();"
if TAIL not in BASE:
    raise SystemExit("startup tail not found")

variants = {
    "ladder-js9-noprobe.html": BASE.replace(
        TAIL,
        "showHome();\ngamepadUiNavigation.start();\nrenderGateways();",
    ),
    "ladder-js9-defer.html": BASE.replace(
        TAIL,
        "showHome();\ngamepadUiNavigation.start();\nrenderGateways();\nsetTimeout(probeSavedGateways, 3000);",
    ),
    "ladder-js9-nows.html": BASE.replace(
        "probe = new WebSocket(gatewayWebSocketUrl(gateway));",
        'complete("Offline"); return;',
    ),
}

for name, text in variants.items():
    (HERE / name).write_text(text, encoding="utf-8")
    print("wrote", name, len(text.encode("utf-8")), "bytes")
