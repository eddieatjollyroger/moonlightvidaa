# Local Moonlight backup

This folder holds the local, restorable copy workflow for the VIDAA Moonlight
client. The app HTML itself is exported from the TV; it is not pasted into chat
or into this repository by hand.

## What is in the repo

- `ownmoon-local.html` - decoded Moonlight HTML rebuilt from TV logs
- `sidee-clone.html` - TV page that copies the packed `index.html` verbatim to
  `ownmoon-local.html`; this preserves the launcher-ready wrapper
- `sidee-export.html` - TV page that decodes the installed bundle and exports it
- `sidee-localize.html` - TV page that writes the decoded app into `Local_ebook`
- `install-ownmoon-local.html` - tile installer with backup/restore; after
  translation its button `0` writes the English **packed** bundle
- `rebuild_backup.py` - rebuilds `ownmoon-local.html` from `SIDEE BKUP4` logs;
  older `BKUP3`/`BKUP2`/`BKUP` lines are fallbacks only. It verifies the
  `INFO4` base64 length before decoding.
- `packed-export.html` - TV page that gzips and base64-exports the full packed
  wrapper as `SIDEE PACK1` log chunks
- `rebuild_packed.py` - gunzips, validates, and rebuilds the packed wrapper from
  those logs
- `translate_app.py` - Italian-to-English UI string map for the decoded app
- `make_english_packed.py` - replaces only the `moonlight` gzip blob in the
  packed wrapper, keeping the wrapper code and `emu` blob unchanged
- `packed-backup.html` - flat-file backup/restore for the working packed clone
- `patch_installer.py` - updates installer button `0` with the final packed
  file URL, byte length, and SHA-256

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

## Preferred local tile setup

Use `sidee-clone.html` before the decoded-file installer. The decoded inner app
alone showed `error code 6`; the packed wrapper is what the launcher expects.

Open on the TV:

```text
https://moonlight.joaopacheco.me/own-webrtc/sidee-clone.html
```

Press:

```text
1 CLONE TO LOCAL FILE
```

Then power-cycle the TV. The tile can stay pointed at:

```text
file:///APPS/emanual/Local_ebook/ownmoon-local.html?app=moonlight
```

Do not press `0 WRITE FILE FROM HTTPS` afterward; that would overwrite the
packed copy with the decoded app again.

The tile entry mirrors Sidee's shape: no `AppId`, plus `configUrl`,
`configUrlDownload`, and `mediaId`. Its Id is `moonlight-ownlocal0001`.

## English translation

The decoded app is translated locally first:

```sh
python3 translate_app.py
shasum -a 256 ~/moonlight-web-test/backup/ownmoon-en.html
```

Then the English HTML is re-packed into the original wrapper. Do **not** install
the decoded HTML directly; that causes VIDAA `error code 6`.

### 1. Back up the working packed clone on the TV

Copy `packed-backup.html` to the Pi web root and open:

```text
https://moonlight.joaopacheco.me/own-webrtc/packed-backup.html
```

Press:

```text
1 BACKUP PACKED
2 VERIFY BACKUP
```

The backup is `emanual/Local_ebook/ownmoon-local.html.ownbak-en`.

### 2. Export the packed wrapper from the TV

Copy `packed-export.html` to the Pi web root and open:

```text
https://moonlight.joaopacheco.me/own-webrtc/packed-export.html
```

Press:

```text
1 EXPORT TO LOGS
```

Save the `SHA` line. Then on the Mac:

```sh
curl -s http://192.168.1.69:8484/logs > ~/packed-export-logs.txt
python3 rebuild_packed.py ~/packed-export-logs.txt ~/moonlight-web-test/backup/ownmoon-packed.html
shasum -a 256 ~/moonlight-web-test/backup/ownmoon-packed.html
```

The rebuilt hash must match the TV `SHA` line.

### 3. Re-pack the English app

```sh
python3 make_english_packed.py \
  ~/moonlight-web-test/backup/ownmoon-packed.html \
  ~/moonlight-web-test/backup/ownmoon-en.html \
  ~/moonlight-web-test/backup/ownmoon-local.html \
  ~/moonlight-web-test/backup/ownmoon-en-packed.html

python3 patch_installer.py ~/moonlight-web-test/backup/ownmoon-en-packed.html
```

### 4. Install on the TV

Copy `ownmoon-en-packed.html` and the patched `install-ownmoon-local.html` to
the Pi web root, then open the installer on the TV and press:

```text
0 WRITE FILE FROM HTTPS
1 BACKUP
3 ADD / REPOINT TILE
4 READBACK
```

Power-cycle the TV and open **OWN MOON LOCAL**.

If anything fails, open `packed-backup.html` again and press:

```text
3 RESTORE PACKED
```

Then power-cycle the TV to return to the working Italian packed clone.

## Legacy: decoded-file install / restore (do not use for normal install)

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

- In the legacy section below, `0 WRITE FILE FROM HTTPS` originally verified the
  decoded backup. After translation it is patched to verify the English packed
  file instead. Do not point it back at `ownmoon-local.html`.
- The Sidee tile is not touched by `3 ADD / REPOINT TILE`.
- `5 REMOVE TILE` removes only the `ownmoon` tile.
- `6 RESTORE APPINFO` restores from `websdk/Appinfo.json.ownbak-local`.

## Runtime notes

- The decoded app connects only to `ws://<PC>:8000` on the LAN.
- No `fetch`, `XMLHttpRequest`, or `http://`/`https://` server endpoint was found.
- Settings and pairing data are stored in `window.localStorage`.
- The Sidee tile and original files are not modified by the export.
