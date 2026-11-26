# Local Moonlight backup

This folder holds the local, restorable copy workflow for the VIDAA Moonlight
client. The app HTML itself is exported from the TV; it is not pasted into chat
or into this repository by hand.

## What is in the repo

- `ownmoon-local.html` - decoded Moonlight HTML rebuilt from TV logs
- `sidee-export.html` - TV page that decodes the installed bundle and exports it
- `sidee-localize.html` - TV page that writes the decoded app into `Local_ebook`
- `install-ownmoon-local.html` - tile installer with backup/restore
- `rebuild_backup.py` - rebuilds `ownmoon-local.html` from `SIDEE BKUP2` logs;
  older partial `SIDEE BKUP` lines are ignored when `BKUP2` exists

## Export from TV

Open:

```text
https://moonlight.joaopacheco.me/own-webrtc/sidee-export.html?v=3
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

The rebuilt hash must match the TV hash.

## Runtime notes

- The decoded app connects only to `ws://<PC>:8000` on the LAN.
- No `fetch`, `XMLHttpRequest`, or `http://`/`https://` server endpoint was found.
- Settings and pairing data are stored in `window.localStorage`.
- The Sidee tile and original files are not modified by the export.
