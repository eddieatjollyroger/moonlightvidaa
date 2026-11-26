# Local Moonlight backup

This folder holds the local, restorable copy workflow for the VIDAA Moonlight
client. The app HTML itself is exported from the TV; it is not pasted into chat
or into this repository by hand.

## What is in the repo

- `ownmoon-local.html` - decoded Moonlight HTML rebuilt from TV logs
- `sidee-export.html` - TV page that decodes the installed bundle and exports it
- `sidee-localize.html` - TV page that writes the decoded app into `Local_ebook`
- `install-ownmoon-local.html` - tile installer with backup/restore
- `rebuild_backup.py` - rebuilds `ownmoon-local.html` from `SIDEE BKUP4` logs;
  older `BKUP3`/`BKUP2`/`BKUP` lines are fallbacks only. It verifies the
  `INFO4` base64 length before decoding.

## Export from TV

Open:

```text
https://moonlight.joaopacheco.me/own-webrtc/sidee-export.html?v=5
```

Press:

```text
1 EXPORT TO LOGS
```

Save the `SHA256` line.

Rebuild on Mac or Pi:

```sh
curl -s http://192.168.1.69:8484/logs > ~/moonlight-backup-logs.txt
python3 rebuild_backup.py ~/moonlight-backup-logs.txt ~/moonlight-local-repo/ownmoon-local.html
shasum -a 256 ~/moonlight-local-repo/ownmoon-local.html
```

The rebuilt hash must match the TV hash. Current verified copy:

```text
bytes   79752
sha256  70e4fec39cd0b8f6c3d9945f35c9b13072152f2e7c5c58ae3c6e9264995e3e86
```

The byte check is deliberate: the HTML contains accented characters, so its
JavaScript string length is 79689 even though its UTF-8 byte length is 79752.

## Install / restore to the TV

First copy the rebuilt file and updated installer from the Mac to the Pi home:

```sh
scp ~/moonlight-web-test/backup/ownmoon-local.html \
    ~/moonlight-web-test/files/own-local-installer/install-ownmoon-local.html \
    eddie@192.168.1.69:/home/eddie/moonlightvidaa/files/own-local-installer/
```

Then, on the Pi, copy them into the web root:

```sh
sudo cp /home/eddie/moonlightvidaa/files/own-local-installer/ownmoon-local.html /mnt/ssd1/moonlight-web/own-webrtc/ownmoon-local.html
sudo cp /home/eddie/moonlightvidaa/files/own-local-installer/install-ownmoon-local.html /mnt/ssd1/moonlight-web/own-webrtc/install-ownmoon-local.html
```

Open on the TV:

```text
https://moonlight.joaopacheco.me/own-webrtc/install-ownmoon-local.html
```

If AppInfo is intact, press in order:

```text
0 WRITE FILE FROM HTTPS
1 BACKUP
3 ADD / REPOINT TILE
4 READBACK
```

Then power-cycle the TV.

If AppInfo was cleared and all tiles are gone, press `6 RESTORE APPINFO` first,
then repeat the sequence above.

Notes:

- `0 WRITE FILE FROM HTTPS` verifies length and SHA-256 before and after write.
- The Sidee tile is not touched by `3 ADD / REPOINT TILE`.
- `5 REMOVE TILE` removes only the `ownmoon` tile.
- `6 RESTORE APPINFO` restores from `websdk/Appinfo.json.ownbak-local`.

## Runtime notes

- The decoded app connects only to `ws://<PC>:8000` on the LAN.
- No `fetch`, `XMLHttpRequest`, or `http://`/`https://` server endpoint was found.
- Settings and pairing data are stored in `window.localStorage`.
- The Sidee tile and original files are not modified by the export.
