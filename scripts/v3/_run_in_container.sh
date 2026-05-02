#!/usr/bin/env bash
# _run_in_container.sh — wrapper that runs inside unsloth/unsloth:latest.
#
# The published `unsloth/unsloth:latest` (2026-04-23) ships
# `transformers==4.57.1`, which doesn't recognise `model_type=gemma4` yet.
# Loading `unsloth/gemma-4-31B-it-unsloth-bnb-4bit` therefore fails with
#   ValueError: ... model type `gemma4` ... Transformers does not recognise
# This is the documented Unsloth pattern for a brand-new architecture
# (see https://unsloth.ai/docs/models/tutorials/glm-5 — same `pip install
# --upgrade git+https://github.com/huggingface/transformers.git` step).
#
# Usage: this script is invoked by the v3 EC2 launchers as the docker
# `--entrypoint /bin/bash` argv[1]. argv[2..] is the python script + its
# flags, exec'd by /opt/venv/bin/python (the image's pre-installed venv).
set -euo pipefail

if [ "${SKIP_TRANSFORMERS_UPGRADE:-0}" != "1" ]; then
  /opt/venv/bin/pip install -q --upgrade --force-reinstall --no-deps \
    git+https://github.com/huggingface/transformers.git
  /opt/venv/bin/python -c "import transformers; print('transformers:', transformers.__version__)"
fi

exec /opt/venv/bin/python "$@"
