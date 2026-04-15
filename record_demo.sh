#!/bin/bash
# Record a demo GIF using asciinema + agg
# Install: pip install asciinema && cargo install agg
#
# Usage: bash scripts/record_demo.sh

set -e

CAST_FILE="demo.cast"
GIF_FILE="demo.gif"
REPO="https://github.com/pallets/click"

echo "Recording demo — press Ctrl+D when done"
echo ""

asciinema rec "$CAST_FILE" \
  --title "repo-navigator demo" \
  --command "python main.py --repo $REPO --output /tmp/demo-out.md --compare" \
  --overwrite

echo "Converting to GIF..."
agg "$CAST_FILE" "$GIF_FILE" \
  --font-size 14 \
  --cols 100 \
  --rows 35 \
  --speed 1.5

echo "Done — $GIF_FILE ready"
echo "Add it to README.md: ![demo](demo.gif)"
