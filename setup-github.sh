#!/bin/bash
# One-time setup: creates github.com/<you>/flapboard and turns on GitHub Pages.
set -e
cd "$(dirname "$0")"
REPO=flapboard

if ! command -v gh >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    echo "Installing GitHub CLI..."; brew install gh
  else
    echo "Please install the GitHub CLI first: https://cli.github.com  (or install Homebrew from https://brew.sh)"; exit 1
  fi
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Signing in to GitHub (a browser window will open)..."
  gh auth login --hostname github.com --web --git-protocol https
fi
gh auth setup-git >/dev/null 2>&1 || true

GHUSER=$(gh api user --jq .login)
echo "Signed in as $GHUSER"

[ -d .git ] || git init -q -b main
git config user.name  >/dev/null 2>&1 || git config user.name  "$GHUSER"
git config user.email >/dev/null 2>&1 || git config user.email "$GHUSER@users.noreply.github.com"
git add index.html setup-github.sh publish.sh README.md
git commit -q -m "Flapboard split-flap display" || true

if gh repo view "$GHUSER/$REPO" >/dev/null 2>&1; then
  echo "Repo $GHUSER/$REPO already exists, pushing to it..."
  git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$GHUSER/$REPO.git"
  git push -u origin main || { echo; echo "Push was refused because the GitHub repo already has other files. Delete that repo on github.com (Settings > Delete) and run this again."; exit 1; }
else
  gh repo create "$REPO" --public --source=. --remote=origin --push --description "Vintage split-flap board for the TV"
fi

echo "Turning on GitHub Pages..."
gh api -X POST "repos/$GHUSER/$REPO/pages" -f "source[branch]=main" -f "source[path]=/" >/dev/null 2>&1 || true

URL="https://$GHUSER.github.io/$REPO/"
echo
echo "Done. In a minute or two the board will be live at:"
echo "  $URL"
echo
echo "Open that address in Chrome on the PC stick."
