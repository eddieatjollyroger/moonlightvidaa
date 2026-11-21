"""List the Sidee client functions that can register tiles / HTTP apps.

Copy into the Sidee folder containing core.py and run:

    python3 inspect_sidee.py

Paste the output back so we can call the same function that created the
working tubetv / jellyfin tiles.
"""
import inspect

from core import client

names = [
    n for n in dir(client)
    if any(k in n.lower() for k in ("tile", "install", "app", "url", "register"))
]
for name in names:
    obj = getattr(client, name)
    if callable(obj):
        try:
            print(name + str(inspect.signature(obj)))
        except (TypeError, ValueError):
            print(name + "(?)")
    else:
        print(name + " = " + str(obj)[:120])
