"""Print the raw Sidee records for the working and broken web tiles.

Copy this file into the Sidee folder that contains core.py / sidee.py and run:

    python3 compare_tiles.py

Paste the output back. We only need the Type, StoreType, URL and StartCommand
fields for tubetv / jellyfin / moonlight.
"""
import json

from core import client

session = client.Session.load()
apps = client.list_tiles(session)
for app in apps:
    app_id = str(app.get("appId", "")).lower()
    if app_id in ("tubetv", "joaotube", "jellyfin", "moonlight"):
        print("=== " + app_id + " ===")
        for key in ("appId", "Type", "StoreType", "URL", "StartCommand", "from"):
            print(key + " = " + str(app.get(key)))
