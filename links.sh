#!/bin/bash
# Prints the TV and remote addresses from .env, and can save the RapidAPI key to the board.
#   bash links.sh          show the addresses
#   bash links.sh --key    also send RAPIDAPI_KEY from .env to the board
set -e
cd "$(dirname "$0")"
[ -f .env ] || { echo "No .env file here. Copy .env.example to .env and fill it in."; exit 1; }
set -a; . ./.env; set +a
missing=""
for v in SITE_URL FIREBASE_DB_URL BOARD_ID; do [ -n "${!v}" ] || missing="$missing $v"; done
[ -z "$missing" ] || { echo "Fill these in .env first:$missing"; exit 1; }
DB="${FIREBASE_DB_URL%/}"
ENC=$(python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1],safe=""))' "$DB")
echo "TV address (Edge kiosk settings):"
echo "  ${SITE_URL}#db=${ENC}&board=${BOARD_ID}"
echo
echo "Remote (phone or computer):"
echo "  ${SITE_URL}control.html#db=${ENC}&board=${BOARD_ID}"
if [ "$1" = "--key" ]; then
  [ -n "$RAPIDAPI_KEY" ] || { echo; echo "RAPIDAPI_KEY is empty in .env."; exit 1; }
  BODY=$(python3 -c 'import json,sys;print(json.dumps({"apiKey":sys.argv[1]}))' "$RAPIDAPI_KEY")
  code=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH -d "$BODY" "${DB}/boards/${BOARD_ID}/settings.json")
  echo
  [ "$code" = "200" ] && echo "RapidAPI key sent to the board." || echo "Could not save the key (HTTP $code). Check FIREBASE_DB_URL and BOARD_ID."
fi
