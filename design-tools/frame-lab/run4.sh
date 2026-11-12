#!/bin/bash
# run4.sh <style> <mode>  -- open lab4 in headless Chrome (SwiftShader WebGL) until out4/<style>-<mode>.done appears
C="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUTD=$(dirname "$0")/out4; M="$OUTD/$1-$2.done"; rm -f "$M"
D=$(mktemp -d /private/tmp/claude-501/-Users-bytedance-Desktop-Spatial-Apps/f3376a48-ca74-48de-a02c-e25b0f38c43c/scratchpad/lab.XXXX)
"$C" --headless=new --use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist --window-size=1600,1000 --user-data-dir=$D "http://127.0.0.1:8793/index4.html?style=$1&mode=$2" >/dev/null 2>&1 &
pid=$!
for i in $(seq 1 240); do [ -e "$M" ] && break; sleep 1; done
echo "$1 $2: $(cat "$M" 2>/dev/null || echo TIMEOUT)"
kill $pid 2>/dev/null; sleep 1; rm -rf $D 2>/dev/null; true
