#!/usr/bin/env bash
# ec2_v3_distill.sh — STUB: forked from ec2_spot_finetune.sh.
#
# WARNING: this script is a launcher TEMPLATE for v3 STUDENT distillation
# (mini/pro/max tiers, parametrised). Before first use, replace the
# user-data block to:
#   1. pip install -r requirements-unsloth.txt
#   2. aws s3 sync data/processed/v3_chat/ /opt/gpf/data/v3_chat/
#   3. aws s3 sync data/processed/v3_pseudo/ /opt/gpf/data/v3_pseudo/
#   4. python scripts/v3/train_student_distill.py
#         --config configs/v3_distillation.yaml --tier ${V3_TIER}
#         --output-dir /opt/gpf/artifacts/v3/students/${V3_TIER}-${TIMESTAMP}
#         --train-jsonl ... --eval-jsonl ...
#   5. aws s3 sync /opt/gpf/artifacts/v3/students/ s3://${BUCKET}/v3/students/
#
# Recommended instance: g6.xlarge spot eu-north-1b ($0.25/h * 1-2h per tier).
# Run all 4 student distills in parallel (4 separate launches).
# See docs/V3_DISTILLATION_PLAN.md.
#
# Required env vars:
#   V3_TIER  — one of: mini | pro | max  (lite uses run_opf_train.py instead)
#
# Original v1/v2 docstring follows for reference until adaptation.
# -----------------------------------------------------------------
# ec2_spot_finetune.sh — Launch an EC2 spot instance that fine-tunes
# openai/privacy-filter on the v1 Greek dataset.
#
# On the instance, the boot script (user-data):
#   1. Installs Python deps + AWS CLI + (re)clones opf at pinned commit
#   2. Downloads v1 splits from S3
#   3. Downloads base checkpoint from S3
#   4. Runs baseline eval on test + hard_test (untrained model)  → S3
#   5. Runs `python -m opf train` (3 epochs, bs=4, gas=4, lr=5e-5)  → S3
#   6. Runs finetuned eval on test + hard_test                    → S3
#   7. EXIT trap syncs final artefacts + logs, then terminates
#
# Required env vars:
#   BUCKET                 — S3 bucket holding training data + base checkpoint
#   IAM_INSTANCE_PROFILE   — EC2 profile with read+write to BUCKET
#   AWS_REGION             — default eu-north-1
#   V1_RUN_ID              — required, e.g. 20260426T092703Z (where v1 data lives)
#
# Optional:
#   DATASET_S3_PREFIX      — explicit S3 prefix (under BUCKET) holding the
#                            train/validation/test/hard_test JSONL splits.
#                            Overrides the default `generated/run-${V1_RUN_ID}/data`.
#                            Use this to fine-tune against a relabelled or
#                            blended dataset (e.g. `relabelled/v1_1` for
#                            the AFM-cleaned v1.1 splits, or
#                            `generated/run-<v2-run>/combined` for v2).
#   INSTANCE_TYPE          — default g6e.xlarge (L40S 48GB)
#   SPOT_MAX_PRICE         — default 1.00
#   EPOCHS                 — default 3
#   BATCH_SIZE             — default 4
#   GRAD_ACCUM_STEPS       — default 4
#   LEARNING_RATE          — default 5e-5
#   N_CTX                  — default 256
#   SEED                   — default 1337
#   OUTPUT_PARAM_DTYPE     — default bf16
#   OPF_REPO_URL           — default https://github.com/openai/privacy-filter.git
#   OPF_COMMIT             — default f7f00ca7fb869683eb732c010299d901457f19c3
#   BASE_CKPT_S3_PREFIX    — default checkpoints/base/privacy-filter (under BUCKET)
#   LABEL_SPACE_S3_KEY     — default finetune/label_space.json (under BUCKET)

set -euo pipefail

REGION="${AWS_REGION:-eu-north-1}"
INSTANCE_TYPE="${INSTANCE_TYPE:-g6e.xlarge}"
SPOT_MAX_PRICE="${SPOT_MAX_PRICE:-1.00}"
EPOCHS="${EPOCHS:-3}"
BATCH_SIZE="${BATCH_SIZE:-4}"
GRAD_ACCUM_STEPS="${GRAD_ACCUM_STEPS:-4}"
LEARNING_RATE="${LEARNING_RATE:-5e-5}"
N_CTX="${N_CTX:-256}"
SEED="${SEED:-1337}"
OUTPUT_PARAM_DTYPE="${OUTPUT_PARAM_DTYPE:-bf16}"
OPF_REPO_URL="${OPF_REPO_URL:-https://github.com/openai/privacy-filter.git}"
OPF_COMMIT="${OPF_COMMIT:-f7f00ca7fb869683eb732c010299d901457f19c3}"
BASE_CKPT_S3_PREFIX="${BASE_CKPT_S3_PREFIX:-checkpoints/base/privacy-filter}"
LABEL_SPACE_S3_KEY="${LABEL_SPACE_S3_KEY:-finetune/label_space.json}"
MARKET_TYPE="${MARKET_TYPE:-spot}"

: "${BUCKET:?BUCKET env var required}"
: "${IAM_INSTANCE_PROFILE:?IAM_INSTANCE_PROFILE env var required}"
: "${V1_RUN_ID:?V1_RUN_ID env var required (e.g. 20260426T092703Z)}"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
GIT_COMMIT="$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || echo 'unknown')"
REPO_KEY="code/gpf-ft-${TIMESTAMP}.tar.gz"
RUN_PREFIX="finetune/run-${TIMESTAMP}"
REPO_TAR="/tmp/gpf-ft-${TIMESTAMP}.tar.gz"
DATA_S3_PREFIX="${DATASET_S3_PREFIX:-generated/run-${V1_RUN_ID}/data}"

echo "[1/5] Packing repo scripts + configs to ${REPO_TAR}"
tar -czf "${REPO_TAR}" \
    -C "${REPO_ROOT}" \
    scripts/ src/ configs/ LICENSING.md ATTRIBUTION.txt docs/

echo "[2/5] Uploading repo tar to s3://${BUCKET}/${REPO_KEY}"
aws s3 cp "${REPO_TAR}" "s3://${BUCKET}/${REPO_KEY}" --region "${REGION}"

echo "[3/5] Resolving Deep Learning Base GPU AMI (Ubuntu 22.04)"
AMI_ID="$(aws ec2 describe-images --region "${REGION}" \
    --owners amazon \
    --filters \
        'Name=name,Values=Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 22.04)*' \
        'Name=state,Values=available' \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' --output text)"
echo "  AMI: ${AMI_ID}"

USERDATA_FILE="/tmp/gpf-ft-userdata-${TIMESTAMP}.sh"
cat > "${USERDATA_FILE}" <<EOF
#!/bin/bash
set -euxo pipefail
exec > /var/log/gpf-ft.log 2>&1

RUN_TIMESTAMP="${TIMESTAMP}"
RUN_BUCKET="${BUCKET}"
RUN_REGION="${REGION}"
RUN_PREFIX="${RUN_PREFIX}"

_ft_checkpoint() {
    local stage="\$1"
    set +e
    [ -d /opt/gpf/artifacts ] && aws s3 sync /opt/gpf/artifacts/ \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/artifacts/" \\
        --region "\${RUN_REGION}" --only-show-errors || true
    [ -d /opt/gpf/model ] && aws s3 sync /opt/gpf/model/ \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/model/" \\
        --region "\${RUN_REGION}" --only-show-errors || true
    echo "[checkpoint] stage=\${stage} synced to S3 at \$(date -u +%H:%M:%S)"
    set -e
}

_ft_finalize() {
    local exit_code=\$?
    set +e
    [ -d /opt/gpf/artifacts ] && aws s3 sync /opt/gpf/artifacts/ \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/artifacts/" \\
        --region "\${RUN_REGION}" --only-show-errors || true
    [ -d /opt/gpf/model ] && aws s3 sync /opt/gpf/model/ \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/model/" \\
        --region "\${RUN_REGION}" --only-show-errors || true
    [ -f /tmp/run_metadata.json ] && aws s3 cp /tmp/run_metadata.json \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/run_metadata.json" \\
        --region "\${RUN_REGION}" || true
    aws s3 cp /var/log/gpf-ft.log \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/gpf-ft.log" \\
        --region "\${RUN_REGION}" || true
    echo "[trap] exit_code=\${exit_code}; instance terminating now"
    shutdown -h now
}
trap _ft_finalize EXIT INT TERM

# Live log streaming every 30 s
( while true; do
    aws s3 cp /var/log/gpf-ft.log \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/gpf-ft.live.log" \\
        --region "\${RUN_REGION}" --quiet 2>/dev/null || true
    sleep 30
  done ) &

apt-get update -q
apt-get install -y python3-pip git jq

INSTANCE_ID="\$(curl -s http://169.254.169.254/latest/meta-data/instance-id || echo unknown)"

mkdir -p /opt/gpf
cd /opt/gpf

# Pull repo tar
aws s3 cp "s3://\${RUN_BUCKET}/${REPO_KEY}" /tmp/gpf-ft.tar.gz --region "\${RUN_REGION}"
tar -xzf /tmp/gpf-ft.tar.gz -C /opt/gpf

# Pull v1 splits
mkdir -p /opt/gpf/data/processed
aws s3 sync "s3://\${RUN_BUCKET}/${DATA_S3_PREFIX}/" /opt/gpf/data/processed/ \\
    --region "\${RUN_REGION}" --exclude '*' \\
    --include 'train.jsonl' --include 'validation.jsonl' \\
    --include 'test.jsonl' --include 'hard_test.jsonl'

# Pull base checkpoint
mkdir -p /opt/gpf/checkpoints/base/privacy-filter
aws s3 sync "s3://\${RUN_BUCKET}/${BASE_CKPT_S3_PREFIX}/" /opt/gpf/checkpoints/base/privacy-filter/ \\
    --region "\${RUN_REGION}"

# Pull label space
aws s3 cp "s3://\${RUN_BUCKET}/${LABEL_SPACE_S3_KEY}" /opt/gpf/configs/label_space.json \\
    --region "\${RUN_REGION}"

# Clone + install opf at pinned commit
git clone "${OPF_REPO_URL}" /opt/gpf/external/privacy-filter
git -C /opt/gpf/external/privacy-filter checkout "${OPF_COMMIT}"
pip install -e /opt/gpf/external/privacy-filter

# CUDA visibility check
nvidia-smi
python3 -c "import torch; print('cuda available:', torch.cuda.is_available()); print('cuda device:', torch.cuda.get_device_name(0))"

mkdir -p /opt/gpf/artifacts/metrics /opt/gpf/artifacts/logs /opt/gpf/model

# 1. Baseline eval (untrained) on test + hard_test
# Base checkpoint label scheme != Greek-extended scheme, so use --eval-mode untyped
# (span detection only, no class match). Post-finetune we switch to typed.
python3 -m opf eval /opt/gpf/data/processed/test.jsonl \\
    --checkpoint /opt/gpf/checkpoints/base/privacy-filter \\
    --device cuda --n-ctx ${N_CTX} --eval-mode untyped \\
    --metrics-out /opt/gpf/artifacts/metrics/baseline_test_metrics.json
python3 -m opf eval /opt/gpf/data/processed/hard_test.jsonl \\
    --checkpoint /opt/gpf/checkpoints/base/privacy-filter \\
    --device cuda --n-ctx ${N_CTX} --eval-mode untyped \\
    --metrics-out /opt/gpf/artifacts/metrics/baseline_hard_test_metrics.json
_ft_checkpoint "after_baseline_eval"

# 2. Train
python3 -m opf train /opt/gpf/data/processed/train.jsonl \\
    --validation-dataset /opt/gpf/data/processed/validation.jsonl \\
    --checkpoint /opt/gpf/checkpoints/base/privacy-filter \\
    --output-dir /opt/gpf/model \\
    --label-space-json /opt/gpf/configs/label_space.json \\
    --device cuda --n-ctx ${N_CTX} \\
    --epochs ${EPOCHS} --batch-size ${BATCH_SIZE} \\
    --grad-accum-steps ${GRAD_ACCUM_STEPS} \\
    --learning-rate ${LEARNING_RATE} \\
    --weight-decay 0.01 --max-grad-norm 1.0 \\
    --shuffle-seed ${SEED} \\
    --output-param-dtype ${OUTPUT_PARAM_DTYPE} \\
    --overwrite-output 2>&1 | tee /opt/gpf/artifacts/logs/train.log
cp /opt/gpf/configs/label_space.json /opt/gpf/model/label_space.json
_ft_checkpoint "after_train"

# 3. Finetuned eval on test + hard_test
python3 -m opf eval /opt/gpf/data/processed/test.jsonl \\
    --checkpoint /opt/gpf/model \\
    --device cuda --n-ctx ${N_CTX} --eval-mode typed \\
    --metrics-out /opt/gpf/artifacts/metrics/finetuned_test_metrics.json
python3 -m opf eval /opt/gpf/data/processed/hard_test.jsonl \\
    --checkpoint /opt/gpf/model \\
    --device cuda --n-ctx ${N_CTX} --eval-mode typed \\
    --metrics-out /opt/gpf/artifacts/metrics/finetuned_hard_test_metrics.json
_ft_checkpoint "after_finetuned_eval"

# 4. Run metadata
cat > /tmp/run_metadata.json <<META
{
  "run_id": "\${RUN_TIMESTAMP}",
  "instance_id": "\${INSTANCE_ID}",
  "instance_type": "${INSTANCE_TYPE}",
  "region": "\${RUN_REGION}",
  "git_commit": "${GIT_COMMIT}",
  "v1_run_id": "${V1_RUN_ID}",
  "opf_commit": "${OPF_COMMIT}",
  "base_checkpoint_s3": "s3://\${RUN_BUCKET}/${BASE_CKPT_S3_PREFIX}",
  "hyperparameters": {
    "epochs": ${EPOCHS},
    "batch_size": ${BATCH_SIZE},
    "grad_accum_steps": ${GRAD_ACCUM_STEPS},
    "learning_rate": ${LEARNING_RATE},
    "n_ctx": ${N_CTX},
    "seed": ${SEED},
    "output_param_dtype": "${OUTPUT_PARAM_DTYPE}"
  },
  "trained_at_utc": "\$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
META

_ft_checkpoint "before_shutdown"
exit 0
EOF

USERDATA_B64="$(base64 -w0 < "${USERDATA_FILE}")"

echo "[4/5] Requesting EC2 spot instance"

SPEC_FILE="/tmp/gpf-ft-spec-${TIMESTAMP}.json"
cat > "${SPEC_FILE}" <<EOF
{
  "ImageId": "${AMI_ID}",
  "InstanceType": "${INSTANCE_TYPE}",
  "UserData": "${USERDATA_B64}",
  "IamInstanceProfile": {"Name": "${IAM_INSTANCE_PROFILE}"},
  "InstanceMarketOptions": {
    "MarketType": "spot",
    "SpotOptions": {
      "MaxPrice": "${SPOT_MAX_PRICE}",
      "SpotInstanceType": "one-time",
      "InstanceInterruptionBehavior": "terminate"
    }
  },
  "InstanceInitiatedShutdownBehavior": "terminate",
  "BlockDeviceMappings": [
    {
      "DeviceName": "/dev/sda1",
      "Ebs": {"VolumeSize": 100, "VolumeType": "gp3", "Iops": 16000, "Throughput": 1000, "DeleteOnTermination": true}
    }
  ],
  "TagSpecifications": [
    {
      "ResourceType": "instance",
      "Tags": [
        {"Key": "Name", "Value": "gpf-ft-${TIMESTAMP}"},
        {"Key": "Project", "Value": "greek-privacy-filter"},
        {"Key": "Purpose", "Value": "fine-tuning"},
        {"Key": "GitCommit", "Value": "${GIT_COMMIT}"},
        {"Key": "V1RunId", "Value": "${V1_RUN_ID}"}
      ]
    }
  ]
}
EOF

_PY_LOCAL=""
if command -v py >/dev/null 2>&1; then
  _PY_LOCAL="py -3"
elif command -v python >/dev/null 2>&1 && python --version 2>&1 | grep -qi 'python 3'; then
  _PY_LOCAL="python"
elif command -v python3 >/dev/null 2>&1; then
  _PY_LOCAL="python3"
fi

_SPEC_FILE_NATIVE="${SPEC_FILE}"
if command -v cygpath >/dev/null 2>&1; then
  _SPEC_FILE_NATIVE="$(cygpath -w "${SPEC_FILE}")"
fi
export GPF_SPEC_FILE="${_SPEC_FILE_NATIVE}"

if [ -n "${SSH_KEY_NAME:-}" ]; then
  if [ -z "${_PY_LOCAL}" ]; then
    echo "FAIL: SSH_KEY_NAME set but no local Python 3 found." >&2
    exit 1
  fi
  GPF_SSH_KEY="${SSH_KEY_NAME}" ${_PY_LOCAL} -c "import json, os; p=os.environ['GPF_SPEC_FILE']; d=json.load(open(p)); d['KeyName']=os.environ['GPF_SSH_KEY']; json.dump(d, open(p,'w'))"
fi

if [ "${MARKET_TYPE}" = "ondemand" ] || [ "${MARKET_TYPE}" = "on-demand" ]; then
  if [ -z "${_PY_LOCAL}" ]; then
    echo "FAIL: MARKET_TYPE=ondemand set but no local Python 3 found." >&2
    exit 1
  fi
  ${_PY_LOCAL} -c "import json, os; p=os.environ['GPF_SPEC_FILE']; d=json.load(open(p)); d.pop('InstanceMarketOptions', None); json.dump(d, open(p,'w'))"
  echo "  market: on-demand (spot block removed from spec)"
else
  echo "  market: spot (max-price=${SPOT_MAX_PRICE})"
fi
unset GPF_SPEC_FILE

SPEC_JSON="$(cat "${SPEC_FILE}")"
INSTANCE_ID="$(aws ec2 run-instances --region "${REGION}" \
    --cli-input-json "${SPEC_JSON}" \
    --query 'Instances[0].InstanceId' --output text)"

echo "[5/5] Spot instance requested: ${INSTANCE_ID}"
echo
echo "Run ID: ${TIMESTAMP}"
echo "Git commit: ${GIT_COMMIT}"
echo "v1 dataset: s3://${BUCKET}/${DATA_S3_PREFIX}/"
echo "Outputs will land at: s3://${BUCKET}/${RUN_PREFIX}/"
echo "Expected layout:"
echo "  artifacts/metrics/baseline_test_metrics.json"
echo "  artifacts/metrics/baseline_hard_test_metrics.json"
echo "  artifacts/metrics/finetuned_test_metrics.json"
echo "  artifacts/metrics/finetuned_hard_test_metrics.json"
echo "  artifacts/logs/train.log"
echo "  model/                    final fine-tuned checkpoint"
echo "  run_metadata.json         seeds, instance, hyperparameters"
echo "  logs/gpf-ft.log           full bash trace"
echo
echo "Tail live log:"
echo "  aws s3 cp s3://${BUCKET}/${RUN_PREFIX}/logs/gpf-ft.live.log - --region ${REGION}"
echo
echo "Watch instance:"
echo "  aws ec2 describe-instances --region ${REGION} --instance-ids ${INSTANCE_ID}"
