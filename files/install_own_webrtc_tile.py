"""Register OUR Moonlight WebRTC client as a reversible Sidee HTTP_APP tile.

Copy this file into the Sidee folder containing core.py / sidee.py and run:

    python3 install_own_webrtc_tile.py

On the TV: Edit Home and tick the new "Own Moonlight" tile. To undo it, untick
the tile in Edit Home; nothing native is installed.

The tile points at a separate tiny static container on the Pi, so TubeTV is
untouched and the URL stays LAN-only:
    http://192.168.1.69:8485/?host=192.168.1.107&port=8000&v=1
"""
from core import client

APP_ID = "ownwebrtc"
NAME = "Own Moonlight"
URL = "http://192.168.1.69:8485/?host=192.168.1.107&port=8000&v=1"
ICON = "http://192.168.1.69:8485/assets/moonlight-icon.png"

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
