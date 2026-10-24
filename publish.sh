#!/bin/bash
# Push changes in this folder to GitHub. The TV updates itself within about 10 minutes.
set -e
cd "$(dirname "$0")"
# Bring in changes published from elsewhere (e.g. by Claude) before adding yours.
git pull -q --rebase --autostash || { echo "Could not get the latest version from GitHub. Check the internet connection and try again."; exit 1; }
git add -A
# Safety check: never upload private files or keys.
bad=$(git diff --cached --name-only | grep -E '(^|/)\.env' | grep -v '\.env\.example$' || true)
if [ -n "$bad" ]; then
  git reset -q $bad
  echo "Stopped: $bad is private and must not be uploaded. Nothing was published."; exit 1
fi
if [ -f .env ]; then
  set -a; . ./.env; set +a
  for v in RAPIDAPI_KEY BOARD_ID; do
    val="${!v}"
    if [ -n "$val" ] && git diff --cached -U0 | grep -qF -- "$val"; then
      git reset -q
      echo "Stopped: your $v appears in a file you're about to publish. Nothing was published."; exit 1
    fi
  done
fi
git commit -q -m "${1:-Update board}" || { echo "Nothing new to publish."; exit 0; }
git push -q
echo "Published. The TV picks it up within about 10 minutes."
