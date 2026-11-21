#!/bin/sh
# Run this ON THE PI, from inside the copied moonlight-web-test folder.
set -eu
DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$DIR"

echo "== unpacking Moonlight Web into $DIR/app"
mkdir -p app/server
tar -xzf files/moonlight-web-aarch64.tar.gz

if [ ! -f package/web-server ]; then
  echo "!! tarball did not contain package/web-server" >&2
  exit 1
fi

rm -rf app/web-server app/static
mv package/web-server app/web-server
mv package/static app/static
rmdir package 2>/dev/null || true

cp files/server-config.json app/server/config.json
cp files/key.pem app/server/key.pem
cp files/cert.pem app/server/cert.pem
chmod +x app/web-server

echo "== ready"
echo "   capability test: python3 serve-capability.py"
echo "   moonlight web:   ./run.sh"
