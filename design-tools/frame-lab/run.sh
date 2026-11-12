#!/bin/bash
# run.sh <query>  -- open frame-lab in headless Chrome (WebGL via SwiftShader) until LAB-DONE / LAB-ERROR
C="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
D=$(mktemp -d /private/tmp/claude-501/-Users-bytedance-Desktop-Spatial-Apps/f3376a48-ca74-48de-a02c-e25b0f38c43c/scratchpad/lab.XXXX)
OUT=$D/dom.html
"$C" --headless=new --use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist --window-size=1600,1000 --virtual-time-budget=600000 --user-data-dir=$D --dump-dom "http://127.0.0.1:8793/index.html?$1" > $OUT 2>$D/err.log &
pid=$!
for i in $(seq 1 360); do grep -q 'LAB-' $OUT 2>/dev/null && break; kill -0 $pid 2>/dev/null || break; sleep 1; done
grep -o 'LAB-[A-Z]*[^<]*' $OUT | head -c 800 || { echo "NO RESULT"; tail -5 $D/err.log; }
kill $pid 2>/dev/null; rm -rf $D
