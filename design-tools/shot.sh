#!/bin/bash
# shot.sh <out.png> <query> [w h]  -- headless Chrome screenshot of the local preview, killed after 9s
C="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
rm -f "$1"; W=${3:-1800}; H=${4:-1000}
D=$(mktemp -d /private/tmp/claude-501/-Users-bytedance-Desktop-Spatial-Apps/f3376a48-ca74-48de-a02c-e25b0f38c43c/scratchpad/hcc.XXXX)
"$C" --headless --disable-gpu --hide-scrollbars --force-device-scale-factor=${DPR:-1} --window-size=$W,$H --timeout=4000 --user-data-dir=$D --screenshot="$1" "${PREVIEW_URL:-http://127.0.0.1:8791/preview.html}?$2" >/dev/null 2>&1 &
pid=$!
for i in $(seq 1 18); do [ -s "$1" ] && break; sleep 0.5; done
sleep 1; kill $pid 2>/dev/null; rm -rf "$D"; ls -la "$1"
