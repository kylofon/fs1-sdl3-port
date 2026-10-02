# Working in a cloud session

Phase 3 subphases are checked by headless, scripted runs (`tools/verify_campaign.py`, screenshots), so
an agent can do them on a Linux machine without a display. Playtesting stays on the user's own machine.

## 1. The disk image

The image is stored as an asset of the private release `disk-image` in this repo. It is not in git
history. `scripts/cloud_setup.sh` downloads it with `gh` or `GITHUB_TOKEN`.

The original image is copyrighted and is **not** in this repo. A session needs it at:

    original/Microsoft Flight Simulator v1.05 (198x)(Microsoft Corporation).ima   (163,840 bytes)

Without it, the game can't boot, so nothing can be verified. How it gets there is the owner's decision.
Options:
- provide it to the session yourself
- have the environment's setup step download it from private storage
- keep it on a private branch

Check it with:

    python3 -c "import os; print(os.path.getsize('original/Microsoft Flight Simulator v1.05 (198x)(Microsoft Corporation).ima'))"

## 2. Setup (Debian/Ubuntu)

All of this is automated by `bash scripts/cloud_setup.sh`, including fetching the image from the
private `disk-image` release asset. The manual steps follow.

    sudo apt-get update
    sudo apt-get install -y build-essential cmake ninja-build git python3 python3-pip
    pip3 install -r requirements.txt

SDL3 3.4 or newer is used if it is installed. Otherwise CMake downloads and builds it
(`FetchContent`, tag `release-3.4.0`); this needs network access on the first configure.

    cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
    cmake --build build
    cmake -S . -B build-emu -G Ninja -DCMAKE_BUILD_TYPE=Release -DFS1_EMULATOR=ON
    cmake --build build-emu

`build/` is the game (no 8086 interpreter, 3.22). The verification tools run original code, so they
use the emulator build in `build-emu/` (or the executable named by `FS1_EXE`).

## 3. Running headless

The Python tools set `SDL_VIDEODRIVER=offscreen` and `SDL_AUDIODRIVER=dummy` themselves. For manual
runs:

    SDL_VIDEODRIVER=offscreen SDL_AUDIODRIVER=dummy build/fs1 --frames 900 --keys "120:A,180:B" --screenshot out.bmp

Offscreen output is byte-identical to windowed output; this was checked on Windows, including the
text-mode font.

## 4. Regenerating the analysis files

These are gitignored and derived from the image:

    python3 tools/pc_loadstream.py "original/Microsoft Flight Simulator v1.05 (198x)(Microsoft Corporation).ima" --dump extracted
    python3 tools/trace_campaign.py --fresh      # about 15 minutes
    python3 tools/fs1dis.py                      # extracted/fs1.asm, callgraph.txt, vars.txt

## 5. Before committing a subphase

    python3 tools/verify_campaign.py             # must print OK

Then follow the rules in [PHASE3_PLAN.md](PHASE3_PLAN.md) and push. The user pulls, playtests, and
clears the next subphase.
