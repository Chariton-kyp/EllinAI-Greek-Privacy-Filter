#!/usr/bin/env bash
# Local docker smoke test for v3 train_teacher.py.
#
# Verifies the SFTConfig + pre-tokenize + SFTTrainer.train() path works
# against the unsloth/unsloth:latest image with a tiny model + 5 samples
# before paying for an EC2 GPU.
#
# Pre-req: `docker pull unsloth/unsloth:latest` already complete.
#
# Pass criterion: docker exits 0 AND the live log contains a non-zero
# loss value AND `[v3-teacher] DONE` line.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RUN_DIR="${REPO_ROOT}/artifacts/v3/teacher/smoke-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "${RUN_DIR}"

REPO_LIN="${REPO_ROOT}"
if command -v cygpath >/dev/null 2>&1; then
  REPO_LIN="$(cygpath -u "${REPO_ROOT}")"
fi

echo "[smoke] repo=${REPO_LIN}"
echo "[smoke] run dir=${RUN_DIR}"

# Git Bash on Windows rewrites argv tokens that look like POSIX paths
# (e.g. /bin/bash, /workspace/...) into Windows paths before spawning
# the child. That breaks docker --entrypoint /bin/bash plus every
# /workspace/... arg. Disable that conversion just for this command.
export MSYS_NO_PATHCONV=1

docker run --rm --gpus all --ipc=host --shm-size=4g \
  -u 0:0 \
  -v "${REPO_LIN}:/workspace/gpf" \
  -e HF_HUB_ENABLE_HF_TRANSFER=1 \
  --entrypoint /bin/bash \
  unsloth/unsloth:latest \
  /workspace/gpf/scripts/v3/_run_in_container.sh \
  /workspace/gpf/scripts/v3/train_teacher.py \
  --config /workspace/gpf/configs/v3_smoke.yaml \
  --output-dir "/workspace/gpf/artifacts/v3/teacher/smoke-$(basename "${RUN_DIR}")" \
  --train-jsonl /workspace/gpf/data/processed/v3_chat_smoke/train.jsonl \
  --eval-jsonl  /workspace/gpf/data/processed/v3_chat_smoke/validation.jsonl \
  --max-train-samples 5
