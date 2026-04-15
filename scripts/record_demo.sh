#!/bin/bash
set -e

CAST_FILE="demo.cast"
GIF_FILE="demo.gif"
REPO="https://github.com/pallets/click"

asciinema rec "$CAST_FILE" \
  --title "repo-navigator demo" \
  --command "python main.py --repo $REPO --output /tmp/demo-out.md --compare" \
  --overwrite

echo "Converting to GIF..."
agg "$CAST_FILE" "$GIF_FILE" --font-size 14 --cols 100 --rows 35 --speed 2.0 --last-frame-duration 10

echo "Done — $GIF_FILE ready"
