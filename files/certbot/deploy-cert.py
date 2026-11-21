#!/usr/bin/env python3
"""Deploy the issued cert for Moonlight Web, then restart its container.

Runs as certbot's --deploy-hook inside the certbot container.
Uses only the Python stdlib and the mounted Docker socket.
"""
import http.client
import os
import shutil
import socket

DOMAIN = os.environ.get("CERTBOT_DOMAIN", "")
LE = "/etc/letsencrypt/live/" + DOMAIN
CERTS = "/certs"


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, path, timeout=10):
        super().__init__("localhost", timeout=timeout)
        self.sock_path = path

    def connect(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        s.connect(self.sock_path)
        self.sock = s


def install(src, dst, mode, uid, gid):
    shutil.copyfile(src, dst)
    os.chmod(dst, mode)
    os.chown(dst, uid, gid)
    print("certbot: installed", dst)


def restart_moonlight():
    conn = UnixHTTPConnection("/var/run/docker.sock")
    conn.request("POST", "/containers/moonlight-web/restart")
    r = conn.getresponse()
    body = r.read()
    print("certbot: restart moonlight-web ->", r.status, body[:200].decode("utf-8", "replace"))
    if r.status != 204:
        raise SystemExit(1)


def main():
    if not DOMAIN:
        raise SystemExit("CERTBOT_DOMAIN is not set")
    fullchain = os.path.join(LE, "fullchain.pem")
    privkey = os.path.join(LE, "privkey.pem")
    if not (os.path.isfile(fullchain) and os.path.isfile(privkey)):
        raise SystemExit("certificate files not found for " + DOMAIN)

    os.makedirs(CERTS, exist_ok=True)
    install(fullchain, os.path.join(CERTS, "cert.pem"), 0o644, 0, 0)
    # moonlight-web runs as UID/GID 999 inside its container
    install(privkey, os.path.join(CERTS, "key.pem"), 0o600, 999, 999)
    restart_moonlight()


if __name__ == "__main__":
    main()
