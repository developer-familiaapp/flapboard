# Flapboard

A vintage split-flap board (messages, clock, live weather, airport departures) that runs fullscreen in Chrome on a PC stick behind the TV.

- First time: `bash setup-github.sh`
- After any change to `index.html`: `bash publish.sh` (it first pulls anything published from elsewhere)
- Claude can also commit and push here directly; run `git pull` to bring this folder up to date.

On the TV: press **S** for settings, **F** for fullscreen, **Space** for the next screen, **M** for sound.

## Private settings (.env)
`.env` holds your keys and board links. It stays on this Mac; `.gitignore` keeps it off GitHub,
and `publish.sh` refuses to publish if a key shows up in any file.

- Fill in `.env`, then `bash links.sh` prints the TV and remote addresses.
- `bash links.sh --key` sends the RapidAPI key from `.env` to the board.
