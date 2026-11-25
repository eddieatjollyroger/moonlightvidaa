# Moonlight-on-TV test kit (preview only)

Nothing here has been installed on the Pi or the TV by the assistant. Everything
is reversible; no TV system files are touched.

## What is in here

- `docker-compose.yml` - host-network service block, HTTPS on **443**, WebRTC UDP 40000-40100
- `files/cert.pem`, `files/key.pem` - self-signed cert for `192.168.1.69` (step 3)
- `files/capability/index.html` - TV browser capability test (port **8444**)
- `files/serve-capability.py` - tiny HTTPS server for that page
- `files/static-patch/stream.js`, `478.js` - patched frontend bundles (step 3)
- `files/moonlight-web-aarch64.tar.gz` - offline ARM64 binary, fallback only
- `files/setup.sh`, `files/run.sh` - bare-metal fallback scripts

Port 443 must be free on the Pi. Port 8444 (capability test) does not conflict
with TubeTV (8484) or Home Assistant (8123). The container runs as root only so
it can bind port 443; everything else stays under `/mnt/ssd1/moonlight-web/`.

## Step 1 - copy to the Pi (Mac)

```
rsync -av /Users/joaopacheco/moonlight-web-test/ eddie@192.168.1.69:/home/eddie/moonlight-web-test/
```

## Step 2 - capability test (Pi, only when checking the TV browser)

```
cd /home/eddie/moonlight-web-test/files
chmod +x serve-capability.py
python3 serve-capability.py
```
TV -> `https://192.168.1.69:8444/`, accept the cert warning, report all lines.
Ctrl-C to stop.

## Step 3 - start Moonlight Web with the TV-safe frontend patch (Pi)

The VIDAA Chrome 111 browser throws on AV1 codec strings in
`VideoDecoder.isConfigSupported`, which makes the stock frontend fail at stream
start. The patched bundles turn those throws into `supported:false`, so H.264
still works. They are bind-mounted over the image's own files.

They also fix two TV-specific hangs:
- the worker (`478.js`) probe now has a 5s timeout, so a silent/failed worker
  can no longer leave the popup stuck on "Selecting pipeline automatically";
- both `stream.js` and `478.js` are cache-busted (`?tv=18`);
- `stream.html` gives the CSS vars that position/resize the video sane defaults
  and pins `.video-stream` to a full-screen box (`object-fit:contain`). On VIDAA
  the on-screen-keyboard event that normally seeds those vars never fires, so
  without this the video sits at native size in the top-left corner.

```
sudo mkdir -p /mnt/ssd1/moonlight-web/static
sudo cp /home/eddie/moonlight-web-test/files/static-patch/{stream.js,478.js,stream.html} /mnt/ssd1/moonlight-web/static/
sudo chmod 644 /mnt/ssd1/moonlight-web/static/*
sudo mkdir -p /mnt/ssd1/moonlight-web/certs /mnt/ssd1/moonlight-web/data
sudo cp /home/eddie/moonlight-web-test/files/cert.pem /home/eddie/moonlight-web-test/files/key.pem /mnt/ssd1/moonlight-web/certs/
sudo chmod 644 /mnt/ssd1/moonlight-web/certs/*.pem
sudo chown -R 999:999 /mnt/ssd1/moonlight-web/data
```

Paste the `moonlight-web` service from `docker-compose.yml` into your compose
file, then:

```
docker compose up -d --force-recreate moonlight-web
docker logs --tail 40 moonlight-web
```

TV -> `https://192.168.1.69/`. Log in (first username/password you type
creates the admin account), add the PC by its LAN IP, and pair with Sunshine.

`stream.html` loads `stream.js?tv=18`, which in turn loads `478.js?tv=18`, so the
TV cannot silently reuse cached bundles from an earlier attempt.

### If WebCodecs still fails: force the Media Source fallback

`files/static-patch-mse/` contains the same bundles plus a shim that removes
`window.VideoDecoder` before the app probes pipes. The app then uses its built-in
H.264 MediaSource decoder instead. Higher latency, but it avoids WebCodecs
entirely. To switch:
```
sudo cp /home/eddie/moonlight-web-test/files/static-patch-mse/{stream.js,478.js,stream.html} /mnt/ssd1/moonlight-web/static/
sudo chmod 644 /mnt/ssd1/moonlight-web/static/*
docker compose restart moonlight-web
```
Reload the TV page. If it works you will see a notice about increased latency -
that is expected and confirms the fallback path.

### A/B test: WebSocket + MediaSource (VIDAA hardware decoder)

The 4K receiver in `jh1909/vidaaOS-moonlight` gets its low latency from VIDAA's
hardware ES-player: fMP4 into `<video>` via MediaSource, with the live edge
trimmed to ~0.5 s. That native path needs TV system writes and is not used here.
The same *browser* primitive is available in `moonlight-web-stream`: force the
WebSocket transport, remove WebCodecs, and the app feeds fMP4 to MediaSource.

`files/static-patch-mse/stream.js` is the current patch with a small shim that
deletes `window.VideoDecoder` before capability probing. Select it with:

```
sudo cp /home/eddie/moonlight-web-test/files/static-patch-mse/stream.js /mnt/ssd1/moonlight-web/static/stream.js
sudo cp /home/eddie/moonlight-web-test/files/static-patch/stream.html /mnt/ssd1/moonlight-web/static/stream.html
sudo chmod 644 /mnt/ssd1/moonlight-web/static/stream.js /mnt/ssd1/moonlight-web/static/stream.html
```

Then open `https://moonlight.joaopacheco.me/?mse=1` once on the TV. The page
shim persists `dataTransport=websocket`, `canvasRenderer=false` and redirects
to the normal home page. Start a stream as usual. Metrics will contain
`mse:1` plus `ahead` (seconds of buffered video ahead of `currentTime`),
`ready`, `ct` and `w`. Compare smoothness and `ahead` against the WebRTC path.

To go back: copy `files/static-patch/stream.js` over `stream.js` on the Pi and
open `https://moonlight.joaopacheco.me/?webrtc=1` once. Both switches only
change browser `localStorage`; no TV or Pi system files are modified.

The MSE variant also asks for an IDR after the **first** dropped frame instead
of 60, and after 5 s it stops waiting for an IDR and appends anyway. This is
for VIDAA ignoring the IDR request, which otherwise leaves audio only with the
video element stuck at `readyState=1` and no buffered ranges.

`ahead` staying under ~0.6 s with smooth motion would confirm the hardware
MediaSource path is the browser-only winner. If `ahead` grows, the next step is
an IDR-aligned live-edge seek (the repo's finding 32), not more network tuning.

### Why 1080p60 needs this path

The canvas/WebCodecs renderer is software decoding on the TV's ARM CPU. 720p20
is 18.4 M pixels/s; 1080p60 is 124.4 M pixels/s, 6.8x more. It cannot reach
1080p60. The only browser-only route is MediaSource, which lets VIDAA's
hardware video decoder do the work. Our first two MSE runs got audio only,
with the video stuck at `readyState=1` and no buffered ranges - the init
segment arrived but media fragments never did. That looks like an
`appendBuffer` rejection being swallowed by a `try/catch` in the app.

`files/static-patch-mse-diag/stream.js` is a diagnostic build. It wraps
`SourceBuffer.appendBuffer`, `console.error` and `console.warn`, and polls the
decoder's internal gate, then posts `MLMSE ...` lines to TubeTV's `/api/log`.
It also makes the 5 s IDR failsafe call `tryAppendDecodeUnit()` after opening
the gate, which the original patch did not do.

```
sudo cp /home/eddie/moonlight-web-test/files/static-patch-mse-diag/stream.js /mnt/ssd1/moonlight-web/static/stream.js
sudo cp /home/eddie/moonlight-web-test/files/static-patch-mse-diag/stream.html /mnt/ssd1/moonlight-web/static/stream.html
sudo chmod 644 /mnt/ssd1/moonlight-web/static/stream.js /mnt/ssd1/moonlight-web/static/stream.html
```

Open `https://moonlight.joaopacheco.me/?mse=1` once, start a stream, then read
`http://192.168.1.69:8484/logs` and look for `MLMSE APPEND` / `MLMSE ERR`.
That tells us whether VIDAA rejects the fMP4 fragments and why. This build is
diagnostic only; revert with the normal WebRTC copy when done.

**Result of the first diagnostic:** the app throws
`tried to submit non idr as a keyframe` before appending anything. Its fMP4
muxer asserts that NAL byte 4 is an IDR (type 5) whenever Moonlight marks a
sample as a keyframe. Sunshine keyframes here start with AUD/SEI NALs, so byte 4
is not the IDR and every keyframe sample is discarded. That is why
`buffered=none` while `seq` keeps climbing.

`files/static-patch-mse-diag2/stream.js` removes that strict assertion and adds
`MLMSE BUF` lines showing the first 12 successful appends and their resulting
buffered ranges. If buffered ranges now grow, the hardware decoder path is
alive and 1080p60 is worth testing. Use it the same way (cache-bust `?tv=22`):

```
sudo cp /home/eddie/moonlight-web-test/files/static-patch-mse-diag2/stream.js /mnt/ssd1/moonlight-web/static/stream.js
sudo cp /home/eddie/moonlight-web-test/files/static-patch-mse-diag2/stream.html /mnt/ssd1/moonlight-web/static/stream.html
sudo chmod 644 /mnt/ssd1/moonlight-web/static/stream.js /mnt/ssd1/moonlight-web/static/stream.html
```

**Result:** MSE now works. `ready=4`, `buffered` grows steadily, and `ahead`
settles around 0.75-1.1 s instead of growing without bound. That is the
hardware decoder path. The remaining delay is live-edge buffer, not network or
decode throughput.

`files/static-patch-mse-final/stream.js` added a live-edge trim. **Do not use
it:** it made `ahead` read 0.2 s but stalled presentation after a second or two
while audio kept going. Seeking a VIDAA MSE video that often resets its decoder.
The stable build is `files/static-patch-mse-stable/stream.js`: the IDR fix,
error logging only, no trim. `stream.html` cache-bust is `?tv=24`.

One-shot presets in `files/tv-ui/index.html` avoid fighting the settings UI on
the TV:

- `/?mse=1` - WebSocket + MSE, keeps current resolution/fps/bitrate
- `/?mse720=1` - 720p / 20 fps / 4000 Kbps
- `/?mse720p60=1` - 720p / 60 fps / 10000 Kbps
- `/?mse1080p30=1` - 1080p / 30 fps / 8000 Kbps
- `/?mse1080=1` - 1080p / 60 fps / 10000 Kbps (diagnostic; see below)
- `/?webrtc=1` - back to the canvas/WebCodecs path at 720p / 20 fps / 4000

**Results so far:** 1080p60 connects but media time advances at only 0.37-0.54x
wall clock - the hardware decoder cannot sustain it. The one-off
`addSourceBuffer ... readyState is not 'open'` line is a startup race and did
not stop the stream. The no-trim MSE build at 720p20 was the only one the
viewer reported as actually playing, with a roughly 0.75 s delay. The trim
build made `ahead` look perfect but froze the picture.

Copy the stable build and preset shim, then open a preset once on the TV:

```
sudo cp /home/eddie/moonlight-web-test/files/static-patch-mse-stable/stream.js /mnt/ssd1/moonlight-web/static/stream.js
sudo cp /home/eddie/moonlight-web-test/files/static-patch-mse-stable/stream.html /mnt/ssd1/moonlight-web/static/stream.html
sudo cp /home/eddie/moonlight-web-test/files/tv-ui/index.html /mnt/ssd1/moonlight-web/static/index.html
sudo chmod 644 /mnt/ssd1/moonlight-web/static/stream.js /mnt/ssd1/moonlight-web/static/stream.html /mnt/ssd1/moonlight-web/static/index.html
```

Next test is `/?mse720p60=1` on the stable (no-trim) build. Judge it by the
picture and by `ct` advancing about 1 s per wall-clock second, not by `ahead`
alone. If it stutters, 60 fps browser-only is closed on this TV.

**720p60 result:** it holds ~1:1 and is much better, but still ~2 s behind.
`ahead` cycles from ~0.1 to ~1.0 because the app only seeks to the live edge
when a keyframe arrives, and Sunshine's keyframes are far apart. The app can
ask the host for an IDR over the control channel, and it already does so after
dropped frames. `files/static-patch-mse-idr/stream.js` asks for an IDR every
3 s. Each IDR makes the decoder seek to the live edge, but *at a keyframe*, so
it should lower latency without the freeze caused by arbitrary seeks.
`stream.html` cache-bust is `?tv=25`. Copy just these two files:

```
sudo cp /home/eddie/moonlight-web-test/files/static-patch-mse-idr/stream.js /mnt/ssd1/moonlight-web/static/stream.js
sudo cp /home/eddie/moonlight-web-test/files/static-patch-mse-idr/stream.html /mnt/ssd1/moonlight-web/static/stream.html
sudo chmod 644 /mnt/ssd1/moonlight-web/static/stream.js /mnt/ssd1/moonlight-web/static/stream.html
```

Reopen `?mse720p60=1` once. Watch that the picture stays smooth and that
`ahead` now peaks nearer 0.4 s instead of 1.0 s. If the picture freezes again,
revert to the stable build - the host may not be honouring frequent IDR
requests.

**IDR result, and correction:** the frequent-IDR build made both 720p60 and
1080p60 decode at ~1:1. My earlier "1080p60 is closed" conclusion was wrong:
it was based on the *trim* build, which was the broken one. 1080p60 works.
The IDR requests still cause forward jumps (`ct` cycling 0.83x/1.18x), so
`files/static-patch-mse-stable1080/stream.js` is the same decoder with the
periodic IDR removed and a fresh cache-bust (`?tv=26`). Use `/?mse1080=1`.
That should give smooth 1080p60 with the usual ~2 s MSE latency and no jumps.

## Step 4 - trusted cert via Docker certbot (recommended for the Home tile)

A Sidee tile cannot accept the self-signed warning. This uses only containers:
`certbot/dns-cloudflare` issues and renews a Let's Encrypt cert, then a hook
copies it into the existing cert volume and restarts `moonlight-web`.

1. Cloudflare DNS -> add `A` record `moonlight` -> `192.168.1.69`, **proxy OFF**
   (grey cloud, DNS only). Cloudflare proxy cannot reach a LAN IP.
2. Cloudflare -> My Profile -> API Tokens -> Create Token -> "Edit zone DNS",
   scoped to your zone. Copy the token.
3. Copy `certbot.env.example` from this kit to
   `/mnt/ssd1/moonlight-web/certbot.env`, then edit it:
```
CERTBOT_DOMAIN=moonlight.YOURDOMAIN.com
CERTBOT_EMAIL=you@example.com
```
4. On the Pi, create the Cloudflare credentials and hook folder:
```
sudo mkdir -p /mnt/ssd1/moonlight-web/letsencrypt /mnt/ssd1/moonlight-web/certbot-hooks /mnt/ssd1/moonlight-web/certs /mnt/ssd1/moonlight-web/data
sudo cp /home/eddie/moonlight-web-test/files/certbot/deploy-cert.py /mnt/ssd1/moonlight-web/certbot-hooks/
sudo cp /home/eddie/moonlight-web-test/files/certbot/run-certbot.sh /mnt/ssd1/moonlight-web/certbot-hooks/
sudo chmod 755 /mnt/ssd1/moonlight-web/certbot-hooks/*.sh /mnt/ssd1/moonlight-web/certbot-hooks/*.py
sudo cp /home/eddie/moonlight-web-test/files/certbot/cloudflare.ini.example /mnt/ssd1/moonlight-web/cloudflare.ini
sudo nano /mnt/ssd1/moonlight-web/cloudflare.ini          # paste your token
sudo chmod 600 /mnt/ssd1/moonlight-web/cloudflare.ini
```
5. Paste the `certbot` service from `docker-compose.yml` into your compose file.
   `moonlight-web` keeps pointing at `/moonlight-web/certs/cert.pem` and
   `key.pem` - the hook replaces those files. Then:
```
docker compose up -d --force-recreate moonlight-web certbot
docker logs --tail 40 certbot
docker logs --tail 20 moonlight-web
```
6. Sidee tile URL: `https://moonlight.YOURDOMAIN.com/` (no port, trailing slash)

### TV-sized UI and remote navigation

The stock `index.html` uses `rem` sizes and has no keyboard navigation, so on
VIDAA everything looks oversized and the remote cannot select tiles.
`files/tv-ui/index.html` injects a scale fix (`html` font-size 12px, `body`
zoom 0.75) plus a navigation shim: arrow keys move a yellow focus ring between
tiles/buttons and OK (Enter) activates the focused item. It also forces the
context menu ("Resume Session" / "Stop Current Session") into the middle of the
screen with big targets — on VIDAA the remote has no mouse coordinates so the
app otherwise opens it at 0,0 in the unreachable top-left corner. When that menu
opens, focus jumps to its first item automatically. Text/number fields are
select-all on focus so typing replaces the value instead of prepending digits to
it; range sliders and checkboxes keep normal arrow navigation. It also forces
`matchMedia("(display-mode: standalone)")` to report true so the stream opens in
the same full-screen window instead of a small `window.open` popup. It is
mounted over the image's `index.html`.

```
sudo cp /home/eddie/moonlight-web-test/files/tv-ui/index.html /mnt/ssd1/moonlight-web/static/index.html
sudo chmod 644 /mnt/ssd1/moonlight-web/static/index.html
docker compose up -d --force-recreate moonlight-web
```
Add this volume line to `moonlight-web`:
```
      - /mnt/ssd1/moonlight-web/static/index.html:/moonlight-web/static/index.html:ro
```
Reload the tile page. If the UI is now too small or too large, edit the two
numbers in the injected `<style>` on the Pi and reload — no TV changes needed.

Bitrate has no usable text-entry path on VIDAA (the range slider takes focus).
The shim hides that slider and **OK cycles** the highlighted Bitrate row through
`2000 / 4000 / 6000 / 8000 / 10000` Kbps, firing the app's change event each
press. FPS still uses normal digit entry. `?mse=1` / `?webrtc=1` on the home URL
are reversible A/B switches for the video path (see below).

The 4K TV / 1080p PC mismatch is **not** why the video is small: `object-fit:contain`
scales the 1080p source to whatever viewport size the browser reports. If the
video still looks small, `stream.js` now also applies the same sizing as inline
`!important` styles through a `MutationObserver` (flag `window.__tvStreamFix`),
so no stylesheet or app JS can override it.

To confirm the TV is really getting these files (rather than a cached copy):
```
curl -sk https://127.0.0.1/index.html | grep -o 'tv-nav'
curl -sk https://127.0.0.1/stream.html | grep -o 'stream.js?tv=[0-9]*'
curl -sk https://127.0.0.1/stream.js | head -c 100
```
The last command should start with the `tv-stream-fix` style injection and
contain `MutationObserver`. If any of these fail, the matching `:ro` volume line
is missing from `moonlight-web` in the Pi's compose file.

### If the existing Sidee tile still shows error 102

Sidee sometimes reports a URL change as successful without the TV actually
committing it. Since the TV browser can open the page, the tile is probably
still pointing at the old `:8443` address. The optional `moonlight-tile-proxy`
service fixes that **without touching the TV**: it is a pure TCP passthrough
from Pi port 8443 to 127.0.0.1:443:

```
docker compose up -d moonlight-tile-proxy
docker logs --tail 10 moonlight-tile-proxy
curl -skI https://127.0.0.1:8443/ | head -5
```

Whether the tile uses `:8443` or no port, it now reaches the same server. The
proxy can be removed later with `docker compose rm -sf moonlight-tile-proxy`
once the tile has genuinely been re-pointed.

All persistent files live under `/mnt/ssd1/moonlight-web/`:
`letsencrypt/`, `certs/`, `data/`, `certbot-hooks/`, `cloudflare.ini`,
`certbot.env`. The `/etc/...` paths appear only **inside containers** as mount
targets; nothing is created under `/etc` on the Pi host.

Renewal runs every 12h inside certbot; it only copies and restarts when a cert
is actually renewed. The key is installed as UID 999 mode 600 so
`moonlight-web` can read it. Nothing is installed on the Pi outside Docker.

## Useful commands

```
docker stats moonlight-web                    # CPU while streaming
docker compose stop moonlight-web             # pause
docker compose rm -f moonlight-web            # remove
docker logs --tail 40 moonlight-web           # diagnose
docker exec moonlight-web ./web-server config print
```

## Notes

- `BIND_ADDRESS`, `SSL_CERTIFICATE`, `SSL_PRIVATE_KEY`, `WEBRTC_PORT_RANGE`,
  `WEBRTC_NAT_1TO1_HOST` were verified as real env overrides in the binary.
- Container runs as UID 999: data dir writable, certs/JS readable.
- No dock, guard, DNS, Pi service, or TV setting was changed by preparing this.

Both the menu page and the stream page treat the remote Back key
(`Backspace`, `Escape`, `GoBack`, `BrowserBack`, key codes 8/27/461) as
`history.back()`, so there is no need to hunt for the on-screen Back button.
The Sidee tile must be registered with `add_tile` (a real HTTP_APP entry
showing `HTTP_APP_DEFAULT_URL<id>`), not as a raw-URL shortcut — otherwise the
TV opens it in a fixed 1280x720 browser window.

## Clean stream + smoothness metrics (tv=18)

The green diagnostic and the `OK = FILL SCREEN` button are gone. The stream now
collects WebRTC receive stats silently and posts them to TubeTV's `/api/log`
through a new LAN-only HTTPS-to-HTTP Node forwarder (`ml-metrics-proxy`, port 8444), so there is
no mixed-content blocking and no on-screen text.

After syncing/applying, recreate both services from your compose directory:

```
docker compose up -d --force-recreate moonlight-web ml-metrics-proxy
```

Run a stream for ~20 seconds, then open `http://192.168.1.69:8484/logs` and look
for `MLSTATS` lines. Fields:

- `dec` decoded frames, `realFps` measured decoded fps (the real smoothness number)
- `drop` frames dropped by WebRTC, `vdrop` frames dropped by the video element
- `lost` packets lost, `jit` jitter in ms, `rtt` round-trip time in ms
- `wh` received resolution, `fps` source fps, `codec` video codec

If `realFps` is well below ~50 while `lost`/`rtt` are low, the TV browser is
struggling to decode; lowering Sunshine's FPS/bitrate or forcing H.264 usually
helps. If `lost` or `rtt` are high, it is network/Wi-Fi.

If the old socat version of `ml-metrics-proxy` is still running, the compose
recreate above replaces it. Verify with:

```
curl -sk -X POST --data 'MLSTATS test' https://192.168.1.69:8444/api/log
curl -s http://192.168.1.69:8484/logs | tail -3
```

The first command should return `{"ok":true}` and the second should show the
`MLSTATS test` line. The stream page also now calls the native `fetch` captured
before the app can wrap it, so failed requests no longer raise UI toasts.

### tv=18 metrics

Adds `vFps` (video-element presented fps from `totalVideoFrames`),
`pres`/`presFps` (frames counted via `requestVideoFrameCallback`), `recv` and
`bytes`, and only samples peer connections in state `connected`. `vFps`/`presFps`
are the reliable smoothness numbers on VIDAA Chrome 111, where `framesDecoded`
can freeze.

### tv=18

Adds `vis` / `hid` / `focus` (Page Visibility and focus state), `paused`,
`ready` and `ct` (video `readyState` / `currentTime`), plus a silent
`window.focus()` + `requestFullscreen()` attempt with no on-screen UI. This
distinguishes browser background throttling from a decode/paint problem when
`recv` is high but `vFps` is low.

### tv=18

Adds `raf` / `rafFps` (requestAnimationFrame rate) and `tags` (whether the
rendered `.video-stream` is a VIDEO or CANVAS). If `rafFps` is ~60 while `vFps`
is ~3, the browser is fine and the video decode/paint path is the bottleneck;
if both are ~3, the browser is throttling animation globally.

### tv=18

The TV shim now sets `canvasRenderer: true` once in `mlSettings` (only when the
key is absent). VIDAA's `<video>` element painted ~3 fps despite 60 fps rAF and
33 fps arriving; the canvas/WebCodecs renderer avoids that path. If it causes
problems, turn off "Use Canvas Renderer" in Moonlight settings — the shim will
not force it back on.

## Recovery: "Cannot read properties of null (reading 'toString')" (tv=18 shim fix)

The old TV shim cleared number inputs on focus so VIDAA's remote could replace
values. The app then saved `parseInt('')` as `NaN`, which becomes `null` in
localStorage; on the next load `index.js` calls `.toString()` on the null
`videoSizeCustom.width` and the whole page dies.

The fixed `files/tv-ui/index.html` now:

- repairs null/NaN values in `mlSettings` **before** `index.js` runs;
- never blanks a number field — it replaces the old value on the first digit
  typed instead.

The site sends `cache-control: no-store`, so just re-opening the tile fetches
the fixed page and the repair runs automatically. As a fallback, a reset page
is provided at `files/static-patch/reset.html`: copy it to the static dir and
open `https://moonlight.joaopacheco.me/reset.html` on the TV. It removes
`mlSettings` and redirects to a cache-busted home URL. You will need to
re-enable "Use Canvas Renderer" and 720p afterwards.

### Number-field editing fix (shim)

- Range sliders (`input[type=range]`) are skipped by remote navigation, so OK
  lands on the bitrate number field instead of its slider (digits previously
  went nowhere).
- First-digit replacement moved from a per-field listener to the global
  keydown handler, with `tvTyped` cleared on blur. Neither field is ever
  blanked, so the app cannot save NaN/null again.
