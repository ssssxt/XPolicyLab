#!/usr/bin/env bash
set -euo pipefail
P="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAME="${1:-phoenix-mwa}"
MODE="${2:-eval}"
case "$MODE" in eval|train) ;; *) echo "Usage: install.sh [env-name] [eval|train]" >&2; exit 2 ;; esac
source "$(conda info --base)/etc/profile.d/conda.sh"
conda create -n "$NAME" python=3.10 -y
conda activate "$NAME"
python -m pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
python -m pip install -e "$P/runtime[modelscope]" -r "$P/requirements-robodojo.txt" -e "$P/../.."
if [[ "$MODE" == train ]]; then
    python -m pip install -e "$P/runtime[train,logging,modelscope]"
fi
# Each server explicitly activates the selected benchmark's bundled source.
