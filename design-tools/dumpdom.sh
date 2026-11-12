#!/bin/bash
C="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
D=$(mktemp -d /private/tmp/claude-501/-Users-bytedance-Desktop-Spatial-Apps/f3376a48-ca74-48de-a02c-e25b0f38c43c/scratchpad/hcd.XXXX)
"$C" --headless --disable-gpu --window-size=1800,1100 --virtual-time-budget=8000 --run-all-compositor-stages-before-draw --user-data-dir=$D --dump-dom "$1" > "$2" 2>/dev/null &
pid=$!
for i in $(seq 1 40); do grep -q 'audit-report' "$2" 2>/dev/null && break; sleep 0.5; done
sleep 0.5; kill $pid 2>/dev/null; wc -c "$2"
