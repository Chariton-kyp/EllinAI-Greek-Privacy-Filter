#!/usr/bin/env bash
# ec2_v3_teacher.sh — Launch AWS EC2 instance to train v3 teacher inside the
# official Unsloth Docker image (unsloth/unsloth:latest).
#
# Pipeline (user-data on the instance):
#   1. Sync v3_chat data from S3 (read by container via bind mount)
#   2. Pull unsloth/unsloth:latest (Python 3.12 + PyTorch 2.10 + CUDA 12.8 +
#      bitsandbytes + trl + peft + transformers + datasets + accelerate)
#   3. Run scripts/v3/train_teacher.py inside the container
#        - LoRA Q4 SFT on gemma-4-31B-it (or override via TEACHER_HF_ID)
#        - configs/v3_distillation.yaml hyperparameters
#   4. Sync trained LoRA adapters + metrics → S3 via EXIT trap on host
#   5. EXIT trap: final sync + shutdown -h now (terminates spot instance)
#
# Why Docker (not pip on the DLAMI):
#   - Mirrors the project's existing pattern (ec2_spot_generate.sh pulls
#     ghcr.io/ggml-org/llama.cpp:server-cuda; this script pulls upstream
#     unsloth/unsloth — same convention).
#   - Eliminates the brittle conda/venv discovery problem hit by pilots
#     v3 + v4 (DLAMI variants ship torch in non-standard locations).
#   - "Use Unsloth Core fully" — the upstream image is the curated, tested
#     combination of unsloth + its dep stack. Hand-rolled pip install can
#     drift.
#
# Required env vars:
#   BUCKET                — S3 bucket holding v3_chat data + receiving outputs
#   IAM_INSTANCE_PROFILE  — EC2 profile with R/W access to BUCKET
#
# Optional:
#   AWS_REGION            — default eu-north-1
#   AVAIL_ZONE            — default eu-north-1b
#   INSTANCE_TYPE         — default g6e.xlarge (L40S 48GB)
#   MARKET_TYPE           — spot (default) or ondemand
#   SPOT_MAX_PRICE        — default 1.00
#   TEACHER_HF_ID         — override teacher.hf_id from yaml
#   V3_DATA_S3_PREFIX     — default assembled/v3_chat
#   V3_OUTPUT_S3_PREFIX   — default v3/teacher
#   MAX_TRAIN_SAMPLES     — pilot runs (e.g. 500). Default empty (full set).
#   MAX_EVAL_SAMPLES      — subset eval set. Default 1000 (full eval = 14k records,
#                           ~50 min per round on L40S; 1000 = ~3 min, stable loss).
#   UNSLOTH_IMAGE         — default unsloth/unsloth:latest

set -euo pipefail

REGION="${AWS_REGION:-eu-north-1}"
AVAIL_ZONE="${AVAIL_ZONE:-eu-north-1b}"
INSTANCE_TYPE="${INSTANCE_TYPE:-g6e.xlarge}"
MARKET_TYPE="${MARKET_TYPE:-spot}"
SPOT_MAX_PRICE="${SPOT_MAX_PRICE:-1.00}"
TEACHER_HF_ID="${TEACHER_HF_ID:-unsloth/gemma-4-31B-it-unsloth-bnb-4bit}"
V3_DATA_S3_PREFIX="${V3_DATA_S3_PREFIX:-assembled/v3_chat}"
V3_OUTPUT_S3_PREFIX="${V3_OUTPUT_S3_PREFIX:-v3/teacher}"
MAX_TRAIN_SAMPLES="${MAX_TRAIN_SAMPLES:-}"
MAX_EVAL_SAMPLES="${MAX_EVAL_SAMPLES:-1000}"
UNSLOTH_IMAGE="${UNSLOTH_IMAGE:-unsloth/unsloth:latest}"

: "${BUCKET:?BUCKET env var required}"
: "${IAM_INSTANCE_PROFILE:?IAM_INSTANCE_PROFILE env var required}"
HF_TOKEN="${HF_TOKEN:-}"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
GIT_COMMIT="$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || echo unknown)"
REPO_KEY="code/gpf-v3-teacher-${TIMESTAMP}.tar.gz"
RUN_PREFIX="${V3_OUTPUT_S3_PREFIX}/run-${TIMESTAMP}"
REPO_TAR="/tmp/gpf-v3-teacher-${TIMESTAMP}.tar.gz"

echo "[1/5] Pack repo (scripts/v3 + configs)"
tar -czf "${REPO_TAR}" -C "${REPO_ROOT}" \
    scripts/v3/ scripts/aws/ configs/ \
    LICENSING.md NOTICE ATTRIBUTION.txt \
    docs/V3_DISTILLATION_PLAN.md

echo "[2/5] Upload repo tar to s3://${BUCKET}/${REPO_KEY}"
aws s3 cp "${REPO_TAR}" "s3://${BUCKET}/${REPO_KEY}" --region "${REGION}"

echo "[3/5] Resolve Deep Learning Base GPU AMI (ships Docker + nvidia-container-toolkit)"
AMI_ID="$(aws ec2 describe-images --region "${REGION}" \
    --owners amazon \
    --filters \
        'Name=name,Values=Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 22.04)*' \
        'Name=state,Values=available' \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' --output text)"
echo "  AMI: ${AMI_ID}"

USERDATA_FILE="/tmp/gpf-v3-teacher-userdata-${TIMESTAMP}.sh"
cat > "${USERDATA_FILE}" <<EOF
#!/bin/bash
set -euxo pipefail
exec > /var/log/gpf-v3-teacher.log 2>&1

RUN_TIMESTAMP="${TIMESTAMP}"
RUN_BUCKET="${BUCKET}"
RUN_REGION="${REGION}"
RUN_PREFIX="${RUN_PREFIX}"
TEACHER_HF_ID="${TEACHER_HF_ID}"
V3_DATA_S3_PREFIX="${V3_DATA_S3_PREFIX}"
MAX_TRAIN_SAMPLES="${MAX_TRAIN_SAMPLES}"
MAX_EVAL_SAMPLES="${MAX_EVAL_SAMPLES}"
UNSLOTH_IMAGE="${UNSLOTH_IMAGE}"

if [ -n "${HF_TOKEN}" ]; then
  export HF_TOKEN="${HF_TOKEN}"
  export HUGGING_FACE_HUB_TOKEN="${HF_TOKEN}"
fi

# Tiny stamp helper — single-line marker uploaded to S3 at each major step.
_v3_stamp() {
  local label="\$1"
  local ts="\$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "[stamp] \${ts} \${label}" >> /var/log/gpf-v3-stamps.log
  aws s3 cp /var/log/gpf-v3-stamps.log \\
    "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/stamps.log" \\
    --region "\${RUN_REGION}" --quiet 2>/dev/null || true
}

_v3_log_pump() {
  while true; do
    [ -f /var/log/gpf-v3-teacher.log ] && \\
      aws s3 cp /var/log/gpf-v3-teacher.log \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/gpf-v3-teacher.live.log" \\
        --region "\${RUN_REGION}" --quiet || true
    sleep 30
  done
}

_v3_finalize() {
  set +e
  _v3_stamp "FINALIZE"
  kill \$_PUMP_PID 2>/dev/null || true
  echo "[finalize] uploading artefacts + logs"
  if [ -d /opt/gpf/artifacts/v3/teacher ]; then
    aws s3 sync /opt/gpf/artifacts/v3/teacher/ \\
      "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/artifacts/" \\
      --region "\${RUN_REGION}" --only-show-errors
  fi
  aws s3 cp /var/log/gpf-v3-teacher.log \\
    "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/gpf-v3-teacher.log" \\
    --region "\${RUN_REGION}" --only-show-errors
  aws s3 cp /var/log/cloud-init-output.log \\
    "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/cloud-init-output.log" \\
    --region "\${RUN_REGION}" --only-show-errors 2>/dev/null
  _v3_stamp "SHUTDOWN"
  shutdown -h now
}
trap _v3_finalize EXIT INT TERM
_v3_log_pump &
_PUMP_PID=\$!

# STS / IAM diagnostic dump (loud-fail if perms broken).
{
  echo "=== STS identity ==="
  aws sts get-caller-identity --output json 2>&1 || echo "STS_FAIL"
  echo "=== Instance metadata IAM ==="
  TOKEN="\$(curl -sS -X PUT 'http://169.254.169.254/latest/api/token' -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' 2>&1)"
  curl -sS -H "X-aws-ec2-metadata-token: \${TOKEN}" 'http://169.254.169.254/latest/meta-data/iam/info' 2>&1
  echo
} > /var/log/gpf-v3-sts.log 2>&1
aws s3 cp /var/log/gpf-v3-sts.log \\
  "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/sts.log" \\
  --region "\${RUN_REGION}" || true

_v3_stamp "BOOT"
aws s3 ls "s3://\${RUN_BUCKET}/" --region "\${RUN_REGION}" >/dev/null
_v3_stamp "S3_OK"

# 1. Verify Docker + nvidia-container-toolkit (Base DLAMI ships both;
# defensive install mirrors the existing ec2_spot_generate.sh pattern).
_v3_stamp "DOCKER_CHECK"
if ! command -v docker >/dev/null 2>&1; then
  apt-get update -q
  apt-get install -y --no-install-recommends docker.io
  systemctl enable --now docker
fi
if ! docker info 2>&1 | grep -qi "nvidia"; then
  distribution="\$(. /etc/os-release; echo \${ID}\${VERSION_ID})"
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \\
    gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -fsSL "https://nvidia.github.io/libnvidia-container/\${distribution}/libnvidia-container.list" | \\
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \\
    > /etc/apt/sources.list.d/nvidia-container-toolkit.list
  apt-get update -q
  apt-get install -y nvidia-container-toolkit
  nvidia-ctk runtime configure --runtime=docker
  systemctl restart docker
fi
docker info >/dev/null
nvidia-smi >/dev/null

# 2. Pull repo tar (only contains scripts + configs; no Python deps to install).
_v3_stamp "PULL_REPO"
mkdir -p /opt/gpf
cd /opt/gpf
aws s3 cp "s3://\${RUN_BUCKET}/${REPO_KEY}" /tmp/gpf-v3-teacher.tar.gz \\
  --region "\${RUN_REGION}"
tar -xzf /tmp/gpf-v3-teacher.tar.gz -C /opt/gpf/

# 3. Pull Unsloth Docker image (~13GB compressed, ~5 min on EC2 backbone).
# Wrap in `timeout 1500` (25 min) — past pulls hung indefinitely once. On
# timeout, retry once. If second attempt also fails, exit and let trap fire.
_v3_stamp "DOCKER_PULL"
if ! timeout 1500 docker pull "\${UNSLOTH_IMAGE}"; then
  echo "[docker] pull stalled, retrying"
  timeout 1500 docker pull "\${UNSLOTH_IMAGE}"
fi

# 4. Sync v3_chat data from S3 to a host dir bind-mounted into container.
_v3_stamp "SYNC_DATA"
mkdir -p /opt/gpf/data/processed/v3_chat /opt/gpf/artifacts/v3/teacher
aws s3 sync "s3://\${RUN_BUCKET}/\${V3_DATA_S3_PREFIX}/" \\
  /opt/gpf/data/processed/v3_chat/ \\
  --region "\${RUN_REGION}" --exclude "*" --include "train.jsonl" --include "validation.jsonl"

# Persistent HF cache on the DLAMI's ephemeral NVMe (faster + larger than
# the root EBS volume; 31B bnb-4bit weights are ~17GB).
HF_CACHE_DIR="/opt/dlami/nvme/hf-cache"
if [ ! -d /opt/dlami/nvme ]; then
  HF_CACHE_DIR="/opt/gpf/.hf-cache"
fi
mkdir -p "\${HF_CACHE_DIR}"
chmod 1777 "\${HF_CACHE_DIR}" /opt/gpf/artifacts /opt/gpf/data/processed

# 5. Run training inside the Unsloth container.
# --entrypoint /opt/venv/bin/python  bypasses the image's default
#                                    Jupyter-launching entrypoint.sh
# -u 0:0                             run as root so artifacts/ is writable
# --ipc=host --shm-size=8g           dataloader workers need shared memory
# HF cache + repo + artefacts dirs bind-mounted from host
_v3_stamp "TRAIN_START"
TRAIN_ARGS=()
if [ -n "\${MAX_TRAIN_SAMPLES}" ]; then
  TRAIN_ARGS+=( --max-train-samples "\${MAX_TRAIN_SAMPLES}" )
fi
if [ -n "\${MAX_EVAL_SAMPLES}" ]; then
  TRAIN_ARGS+=( --max-eval-samples "\${MAX_EVAL_SAMPLES}" )
fi
docker run --rm --gpus all --ipc=host --shm-size=8g \\
  -u 0:0 \\
  -v /opt/gpf:/workspace/gpf \\
  -v "\${HF_CACHE_DIR}":/workspace/.cache/huggingface \\
  -e HF_HOME=/workspace/.cache/huggingface \\
  -e HF_HUB_ENABLE_HF_TRANSFER=1 \\
  -e HF_TOKEN="\${HF_TOKEN:-}" \\
  -e HUGGING_FACE_HUB_TOKEN="\${HF_TOKEN:-}" \\
  --entrypoint /bin/bash \\
  "\${UNSLOTH_IMAGE}" \\
  /workspace/gpf/scripts/v3/_run_in_container.sh \\
  /workspace/gpf/scripts/v3/train_teacher.py \\
  --config /workspace/gpf/configs/v3_distillation.yaml \\
  --output-dir "/workspace/gpf/artifacts/v3/teacher/run-\${RUN_TIMESTAMP}" \\
  --train-jsonl /workspace/gpf/data/processed/v3_chat/train.jsonl \\
  --eval-jsonl /workspace/gpf/data/processed/v3_chat/validation.jsonl \\
  --model-override "\${TEACHER_HF_ID}" \\
  "\${TRAIN_ARGS[@]}"
_v3_stamp "TRAIN_DONE"

echo "TEACHER SFT COMPLETE"
EOF

# Build run-instances spec
SPEC_FILE="/tmp/gpf-v3-teacher-spec-${TIMESTAMP}.json"
USERDATA_B64="$(base64 -w 0 "${USERDATA_FILE}")"
cat > "${SPEC_FILE}" <<EOF
{
  "ImageId": "${AMI_ID}",
  "InstanceType": "${INSTANCE_TYPE}",
  "MaxCount": 1,
  "MinCount": 1,
  "Placement": {"AvailabilityZone": "${AVAIL_ZONE}"},
  "IamInstanceProfile": {"Name": "${IAM_INSTANCE_PROFILE}"},
  "UserData": "${USERDATA_B64}",
  "InstanceMarketOptions": {
    "MarketType": "spot",
    "SpotOptions": {"MaxPrice": "${SPOT_MAX_PRICE}", "SpotInstanceType": "one-time", "InstanceInterruptionBehavior": "terminate"}
  },
  "BlockDeviceMappings": [
    {"DeviceName": "/dev/sda1", "Ebs": {"VolumeSize": 200, "VolumeType": "gp3", "Iops": 16000, "Throughput": 1000, "DeleteOnTermination": true}}
  ],
  "TagSpecifications": [
    {"ResourceType": "instance", "Tags": [
      {"Key": "Name", "Value": "gpf-v3-teacher-${TIMESTAMP}"},
      {"Key": "Project", "Value": "Greek-Privacy-Filter"},
      {"Key": "Stage", "Value": "v3-teacher"},
      {"Key": "GitCommit", "Value": "${GIT_COMMIT}"}
    ]}
  ]
}
EOF

if [ "${MARKET_TYPE}" = "ondemand" ] || [ "${MARKET_TYPE}" = "on-demand" ]; then
  PY_HOST=""
  for cand in python python3 py; do
    if command -v "$cand" >/dev/null 2>&1 && "$cand" --version >/dev/null 2>&1; then
      PY_HOST="$cand"
      break
    fi
  done
  if [ -z "${PY_HOST}" ]; then
    echo "FAIL: no working Python found on host"
    exit 1
  fi
  "${PY_HOST}" -c "import json,sys; d=json.load(open(sys.argv[1])); d.pop('InstanceMarketOptions', None); json.dump(d, open(sys.argv[1],'w'))" "${SPEC_FILE}"
  echo "  market: on-demand (spot block removed)"
else
  echo "  market: spot (max-price=${SPOT_MAX_PRICE}) AZ=${AVAIL_ZONE}"
fi

echo "[4/5] Request EC2 instance"
SPEC_FILE_NATIVE="${SPEC_FILE}"
if command -v cygpath >/dev/null 2>&1; then
  SPEC_FILE_NATIVE="$(cygpath -w "${SPEC_FILE}")"
fi
INSTANCE_ID="$(aws ec2 run-instances --region "${REGION}" \
    --cli-input-json "file://${SPEC_FILE_NATIVE}" \
    --query 'Instances[0].InstanceId' --output text)"

echo "[4.5/5] Verify IAM profile attached"
sleep 8
ATTACHED_PROFILE="$(aws ec2 describe-instances --region "${REGION}" \
    --instance-ids "${INSTANCE_ID}" \
    --query 'Reservations[0].Instances[0].IamInstanceProfile.Arn' \
    --output text 2>/dev/null || echo None)"
if [ -z "${ATTACHED_PROFILE}" ] || [ "${ATTACHED_PROFILE}" = "None" ] || [ "${ATTACHED_PROFILE}" = "null" ]; then
  echo "FAIL: instance ${INSTANCE_ID} launched WITHOUT IAM profile (name='${IAM_INSTANCE_PROFILE}')."
  aws ec2 terminate-instances --region "${REGION}" --instance-ids "${INSTANCE_ID}" >/dev/null
  exit 1
fi
echo "  IAM profile: ${ATTACHED_PROFILE}"

echo "[5/5] Instance: ${INSTANCE_ID}"
echo
echo "Run ID:      ${TIMESTAMP}"
echo "Git commit:  ${GIT_COMMIT}"
echo "Image:       ${UNSLOTH_IMAGE}"
echo "Teacher HF:  ${TEACHER_HF_ID}"
echo "Data S3:     s3://${BUCKET}/${V3_DATA_S3_PREFIX}/"
echo "Output S3:   s3://${BUCKET}/${RUN_PREFIX}/"
echo
echo "Tail live log:"
echo "  aws s3 cp s3://${BUCKET}/${RUN_PREFIX}/logs/gpf-v3-teacher.live.log - --region ${REGION}"
echo
echo "Stamps log:"
echo "  aws s3 cp s3://${BUCKET}/${RUN_PREFIX}/logs/stamps.log - --region ${REGION}"
