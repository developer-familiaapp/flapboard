#!/bin/bash
# Push changes in this folder to GitHub. The board updates online about a minute later.
set -e
cd "$(dirname "$0")"
git add -A
git commit -q -m "${1:-Update board}" || { echo "Nothing new to publish."; exit 0; }
git push -q
echo "Published. The TV picks it up on its next reload (or press F5 on the stick)."
