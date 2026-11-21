#!/bin/sh
# Run this ON THE PI to start Moonlight Web over HTTPS on port 8443.
set -eu
DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$DIR/app"
echo "== Moonlight Web at https://192.168.1.69:8443/"
exec ./web-server
