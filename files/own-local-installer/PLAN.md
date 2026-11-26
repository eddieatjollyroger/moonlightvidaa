# Own local file:// bundle installer - documented VIDAA lane

Research only. No TV/Pi commands are run by the assistant. No root, no boot,
no DNS changes, no Sidee+ entitlement reuse.

## Verdict

Feasible in principle **only if this TV firmware leaves the vendor JS bridge
open**. The hard part is not registering a tile; it is staging the bundle files.
The documented/vendor-exposed lane is:

- install/re-point a Browser entry in `/APPS/websdk/Appinfo.json`
- using `HiUtils_createRequest("fileRead"/"fileWrite", {path, mode})`
- with API-relative path `websdk/Appinfo.json` and `mode: 6` (`/APPS/`)

`Hisense_installApp(...)` is another documented vendor API, but local evidence
only shows HTTP(S) URLs with it. `file:///APPS/...` entries are better handled
through the `Appinfo.json` registry lane.

## Firmware gate

This lane is firmware-branch dependent:

- `55E7QTUK / V0000.09.09D.P1001`: verified open
- `43A5LE / V0000.09.60A.Q0707`: gated with HTTP 503
- `75U8QTUK / V0000.09.60I.Q0813`: self-install lane closed; root lane used
- our TV: `U9 / V0000.09.09F.P0930` - close to the open 09.09 family, but
  **not verified**; must probe read-only first

Use `probe.html` from this folder on the TV. It detects the bridge and reads
`websdk/Appinfo.json` without writing.

## Observed on our TV (2026-11-26)

- `HiUtils_createRequest` is a function; `Hisense_installApp` and
  `Hisense_uninstallApp` are undefined. The `Appinfo.json` lane is the one to use.
- Read probe returned the installed app list: `fileRead` mode 6 is open.
- Backup to `websdk/Appinfo.json.ownbak-20261126` returned `ret:true`.
- Writing `websdk/ownmoon/probe.txt` failed with `errno -2 ENOENT syscall open`.
  The bridge has no documented `mkdir`, so new nested directories cannot be created.
- Writing flat `websdk/ownmoon-probe.txt` succeeded: `ret:true`; readback returned
  `ret:true msg OWN STAGING TEST OK 20261126`.
- AppInfo install succeeded and tile appeared, but opening it threw `error code 6`.
  The user had not mains power-cycled the TV.
- `inspect.html` showed the working Sidee entry uses
  `file:///APPS/emanual/Local_ebook/index.html?app=moonlight`, `StoreType=hisense`,
  no `Type`; our entry used `file:///APPS/websdk/ownmoon.html?...`,
  `StoreType=custom`, `Type=Browser`.
- Query string was removed from our tile URL as the first fix; needs verification
  after a real power cycle.
- User gave explicit sign-off to try the E-Manual lane if the no-query `websdk`
  path still fails. `install-ownmoon-emanual.html` writes one new flat file to
  `emanual/Local_ebook/ownmoon.html` (never touches Sidee's `index.html`) and
  registers a Sidee-like entry: `StoreType:hisense`, no `Type`, no query.
- Therefore the bundle must be a **single flat file**:
  `websdk/ownmoon.html`, not `websdk/ownmoon/index.html`.
  `make_bundle.py` in this folder inlines all JS/CSS into that one file.

## Product-lane entry shape

From `/Users/joaopacheco/vidaa-edge/src/app/services/app-management.service.ts`:

```js
const cur = HiUtils_createRequest('fileRead', {
  path: 'websdk/Appinfo.json',
  mode: 6
});
const apps = cur.ret ? JSON.parse(cur.msg) : {AppInfo: []};
apps.AppInfo.push({
  Id: 'ownmoon',
  AppName: 'Own Moon',
  Title: 'Own Moon',
  URL: 'file:///APPS/websdk/ownmoon.html?host=192.168.1.107&port=8000&v=1',
  StartCommand: 'file:///APPS/websdk/ownmoon.html?host=192.168.1.107&port=8000&v=1',
  IconURL: 'https://moonlight.joaopacheco.me/own-webrtc/assets/moonlight-icon.png',
  Icon_96: 'https://moonlight.joaopacheco.me/own-webrtc/assets/moonlight-icon.png',
  Image: 'https://moonlight.joaopacheco.me/own-webrtc/assets/moonlight-icon.png',
  Thumb: 'https://moonlight.joaopacheco.me/own-webrtc/assets/moonlight-icon.png',
  Type: 'Browser',
  InstallTime: '2026-11-25',
  RunTimes: 0,
  StoreType: 'custom',
  PreInstall: false
});
HiUtils_createRequest('fileWrite', {
  path: 'websdk/Appinfo.json',
  mode: 6,
  writedata: JSON.stringify(apps)
});
```

Then restart the TV; the app list is cached.

## Important constraints

- The bridge writes UTF-8 text only. Our HTML/JS/CSS can be staged as text.
  PNG assets cannot go through it reliably; keep icons on the Pi over HTTP.
- Direct `file:///APPS/...` URLs are rejected when loaded from a Cobalt page,
  but launcher records from Sidee do use `file:///APPS/...`. Whether our
  registry entry opens a staged file URL must be verified on the TV.
- Sidee Moonlight uses the E-Manual path:
  `file:///APPS/emanual/Local_ebook/index.html?app=moonlight`.
  That suggests an allowed local-web container, but writing into another app's
  folder needs backup and explicit sign-off.
- `/APPS/websdk/Appinfo.json` is reported as mode `0660`, owner uid 311/gid 713
  on some builds, writable by bridge uid 314. Back it up before any write.
- No documented web-app "game mode" manifest flag was found. The speed win is
  likely the local file app context, not a special toggle.

## Hard boundaries

Allowed to investigate:

- read probe
- `fileRead` / `fileWrite` into `/APPS` via `mode: 6`
- merge one AppInfo entry
- remove only our own entry
- HTTP(S) icons

Not allowed:

- `../` traversal (exploit, not product API)
- `/OAD` / `mode: 7` (OTA staging)
- rootfs, `/etc`, boot scripts, dm-verity, recovery
- `postinst`, superwatch, Dropbear, persistent daemons
- native launcher surgery
- reusing Sidee+ bundles or entitlement

## Difficulty

- Read probe: easy
- Registry entry via documented bridge: medium, if gate is open
- Staging text bundle files under `/APPS`: medium
- Making `file://` launcher entry actually render: medium-hard / unverified
- Firmware portability: hard; gates differ by branch

## Reversal

- Keep a byte copy of `websdk/Appinfo.json` before writing.
- Uninstall = remove only `Id: ownmoon`, write the file back, restart TV.
- Stop the Pi static server if using HTTP icons.
- OTA may clear `/APPS/websdk/Appinfo.json`; re-register or untick as needed.

## Files in this folder

- `probe.html` - read-only bridge/Appinfo probe.
- `stage-probe.html` - backup + flat text write/read test.
- `make_bundle.py` - inlines `../own-webrtc` into `ownmoon.html`.
- `ownmoon.html` - generated single-file local app bundle (178,299 bytes).
- `install-ownmoon.html` - app-level installer using only documented mode-6
  `fileRead`/`fileWrite`. Buttons: backup, write bundle, add tile, readback,
  remove tile, restore.
- `inspect.html` - read-only dump of Moon-related AppInfo entries.
- `install-ownmoon-emanual.html` - same installer, but stages the flat bundle
  into the existing E-Manual folder and uses a Sidee-like local URL.
