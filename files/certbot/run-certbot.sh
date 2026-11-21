#!/bin/sh
# Runs inside certbot/dns-cloudflare: issue once, then renew forever.
set -u
DOMAIN="${CERTBOT_DOMAIN:-}"
EMAIL="${CERTBOT_EMAIL:-}"
CREDS=/etc/cloudflare.ini
HOOK="python3 /hooks/deploy-cert.py"

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
  echo "certbot: CERTBOT_DOMAIN and CERTBOT_EMAIL must be set" >&2
  exit 1
fi

if [ ! -f "$CREDS" ]; then
  echo "certbot: $CREDS is missing" >&2
  exit 1
fi

if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
  echo "certbot: existing cert found, checking renewal"
else
  echo "certbot: issuing first certificate for $DOMAIN"
  certbot certonly --dns-cloudflare \
    --dns-cloudflare-credentials "$CREDS" \
    --non-interactive --agree-tos -m "$EMAIL" \
    -d "$DOMAIN" --deploy-hook "$HOOK" || echo "certbot: initial issuance failed, will retry"
fi

while true; do
  sleep 12h
  echo "certbot: renewal check $(date -u +%FT%TZ)"
  certbot renew --dns-cloudflare \
    --dns-cloudflare-credentials "$CREDS" \
    --non-interactive --deploy-hook "$HOOK" || echo "certbot: renewal attempt failed, will retry"
done
