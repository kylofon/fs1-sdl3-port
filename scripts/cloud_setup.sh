#!/usr/bin/env bash
# Prepares a headless Linux session (cloud agent, CI): tools, Python deps, the original
# disk image from the repo's private "disk-image" release, a build, and the analysis files.
# Usage: bash scripts/cloud_setup.sh
set -euo pipefail
cd "$(dirname "$0")/.."

IMAGE="original/Microsoft Flight Simulator v1.05 (198x)(Microsoft Corporation).ima"

if command -v apt-get >/dev/null; then
    SUDO=$(command -v sudo || true)
    $SUDO apt-get update -qq
    $SUDO apt-get install -y -qq build-essential cmake ninja-build git python3 python3-pip curl >/dev/null
fi
pip3 install -q -r requirements.txt || pip3 install -q --break-system-packages -r requirements.txt

if [ ! -f "$IMAGE" ]; then
    mkdir -p original
    if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
        gh release download disk-image --pattern "*.ima" --output "$IMAGE"
    elif [ -n "${GITHUB_TOKEN:-}" ]; then
        repo=$(git remote get-url origin | sed -E 's#.*github.com[:/]##; s#\.git$##')
        id=$(curl -fsSL -H "Authorization: Bearer $GITHUB_TOKEN" \
             "https://api.github.com/repos/$repo/releases/tags/disk-image" |
             python3 -c "import json,sys; print(json.load(sys.stdin)['assets'][0]['id'])")
        curl -fsSL -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/octet-stream" \
             -o "$IMAGE" "https://api.github.com/repos/$repo/releases/assets/$id"
    else
        echo "No disk image and no GitHub access (gh or GITHUB_TOKEN) to fetch it." >&2
        exit 1
    fi
fi
size=$(stat -c %s "$IMAGE")
[ "$size" = 163840 ] || { echo "Unexpected image size $size" >&2; exit 1; }

cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build
python3 tools/pc_loadstream.py "$IMAGE" --dump extracted
[ -f extracted/trace.bin ] || python3 tools/trace_campaign.py --fresh
python3 tools/fs1dis.py
echo "Setup complete."
