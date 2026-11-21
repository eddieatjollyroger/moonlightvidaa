"""Register Moonlight as a real Sidee HTTP_APP tile (like tubetv / jellyfin).

Copy this file into the Sidee folder containing core.py / sidee.py and run:

    python3 install_moonlight_tile.py

Then on the TV: Edit Home and tick the new "Moonlight" tile. Leave the old
"moonlighter" shortcut alone for now; it can be removed later once this works.
"""
from core import client

APP_ID = "moonlightapp"
NAME = "Moonlight"
URL = "https://moonlight.joaopacheco.me/"
ICON = "https://moonlight.joaopacheco.me/moonlight.svg"

session = client.Session.load()
apps = client.add_tile(session, APP_ID, NAME, URL, ICON)
ok = any(client.tile_matches_request(a, APP_ID, URL) for a in apps)
print(("REGISTERED" if ok else "NOT confirmed by TV") + ": " + NAME + " -> " + URL)
for app in apps:
    if str(app.get("appId", "")).lower() == APP_ID:
        for key in ("appId", "Type", "StoreType", "from"):
            print(key + " = " + str(app.get(key)))
        for key in ("url", "URL", "defaultUrl", "startCommand", "StartCommand"):
            if app.get(key):
                print(key + " = " + str(app.get(key)))
