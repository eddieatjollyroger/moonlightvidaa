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
- both `stream.js` and `478.js` are cache-busted (`?tv=5`);
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

`stream.html` loads `stream.js?tv=5`, which in turn loads `478.js?tv=5`, so the
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
it. It is mounted over the image's `index.html`.

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
