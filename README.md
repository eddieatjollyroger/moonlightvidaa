# Moonlight-on-TV test kit (preview only)

Nothing here has been installed on the Pi or the TV. This is a local, reversible
test kit. Removing the container and stopping the test server undoes everything;
no TV system files are touched.

## Docker or bare metal?

The official image `mrcreativ3001/moonlight-web-stream:latest` publishes a real
**arm64** variant (verified: its `web-server` is an AArch64 static binary), so it
runs on the Pi 5 directly. **Docker is the primary path** here to match how
TubeTV already runs (`network_mode: host`, absolute `/mnt/ssd1` paths).
A bare-metal fallback is kept in `files/` in case Docker Hub is unreachable.

## What is in here

- `docker-compose.yml` - paste-ready service block, host networking, HTTPS on
  **8443**, WebRTC UDP 40000-40100
- `files/cert.pem`, `files/key.pem` - self-signed cert for `192.168.1.69`
- `files/capability/index.html` - browser capability test page
- `files/serve-capability.py` - tiny HTTPS server for that page (port **8444**)
- `files/moonlight-web-aarch64.tar.gz` - offline ARM64 binary (fallback only)
- `files/setup.sh`, `files/run.sh` - bare-metal fallback start scripts
- `README.md` - this file

Ports 8443/8444 do not conflict with TubeTV (8484) or Home Assistant (8123).

## Step 1 - copy to the Pi (run on the Mac)

```
rsync -av /Users/joaopacheco/moonlight-web-test/ eddie@192.168.1.69:/home/eddie/moonlight-web-test/
```

## Step 2 - browser capability test (run on the Pi)

```
cd /home/eddie/moonlight-web-test/files
chmod +x serve-capability.py
python3 serve-capability.py
```

Then on the TV, open:

```
https://192.168.1.69:8444/
```

Accept the self-signed certificate warning, wait a few seconds, and report the
lines on screen - especially **Secure (HTTPS)**, **WebRTC**, **WebCodecs**,
**H264 decode / HEVC decode**, **Gamepad API**, and **RTC codecs**.

Stop the test server with Ctrl-C when done.

## Step 3 - only if step 2 looks good (run on the Pi)

The compose service uses `network_mode: host`, so there is **no `ports:` mapping**
and no DNAT - 8443/UDP 40000-40100 bind directly to the Pi. It also stores state
under `/mnt/ssd1`, like the other services. Prepare those paths first:

```
sudo mkdir -p /mnt/ssd1/moonlight-web/certs /mnt/ssd1/moonlight-web/data
sudo cp /home/eddie/moonlight-web-test/files/cert.pem /home/eddie/moonlight-web-test/files/key.pem /mnt/ssd1/moonlight-web/certs/
sudo chmod 644 /mnt/ssd1/moonlight-web/certs/cert.pem /mnt/ssd1/moonlight-web/certs/key.pem
sudo chown -R 999:999 /mnt/ssd1/moonlight-web/data
```

Paste the `moonlight-web` service block from `docker-compose.yml` into your
existing compose file (under `services:`), then:

```
docker compose up -d moonlight-web
docker logs --tail 40 moonlight-web
```

Then on the TV:

```
https://192.168.1.69:8443/
```

You should see the Moonlight Web login page. Create a user, add a PC at
`localhost`, and pair it with Sunshine on the gaming PC.

Useful commands:

```
docker compose stop moonlight-web        # pause it (keeps the container)
docker compose rm -f moonlight-web       # remove it cleanly
docker stats moonlight-web               # check CPU while streaming
docker exec moonlight-web ./web-server config print   # show effective config
```

If the page does not load, check `docker logs moonlight-web` and send me the
output. The container runs as UID 999; if startup complains about permissions,
re-run the `chown`/`chmod` commands above.

## Notes

- `BIND_ADDRESS`, `SSL_CERTIFICATE`, `SSL_PRIVATE_KEY`, `WEBRTC_PORT_RANGE`, and
  `WEBRTC_NAT_1TO1_HOST` were all verified as real env overrides in the binary.
- WebCodecs + Gamepad + Keyboard Lock need HTTPS, hence the self-signed cert.
  Without HTTPS it falls back to slower video playback.
- If the TV refuses the self-signed page entirely, that is a useful result: it
  means the browser route needs a trusted certificate (a separate step).
- This is a browser client, not a native VIDAA app. It can later be added as a
  Home tile exactly like TubeTV, with no TV system writes.
- No dock, guard, DNS, Pi service, or TV settings were changed by preparing this.
