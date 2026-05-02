#!/usr/bin/env bash
# ec2_v3_distill.sh — Run student tier distillation inside the unsloth/unsloth
# Docker image on EC2 spot.
#
# Required env vars:
#   BUCKET                — S3 bucket
#   IAM_INSTANCE_PROFILE  — EC2 profile R/W
#   V3_TIER               — mini | pro | max
#
# Optional:
#   AWS_REGION            — default eu-north-1
#   AVAIL_ZONE            — default eu-north-1b
#   INSTANCE_TYPE         — default g6.xlarge (L4 24GB)
#   MARKET_TYPE           — spot (default) or ondemand
#   SPOT_MAX_PRICE        — default 0.50
#   STUDENT_HF_ID         — override student.hf_id
#   V3_CHAT_S3_PREFIX     — default assembled/v3_chat
#   V3_PSEUDO_S3_PREFIX   — default v3/pseudo
#   V3_OUTPUT_S3_PREFIX   — default v3/students
#   MAX_TRAIN_SAMPLES     — for pilot runs
#   UNSLOTH_IMAGE         — default unsloth/unsloth:latest

set -euo pipefail

REGION="${AWS_REGION:-eu-north-1}"
AVAIL_ZONE="${AVAIL_ZONE:-eu-north-1b}"
INSTANCE_TYPE="${INSTANCE_TYPE:-g6.xlarge}"
MARKET_TYPE="${MARKET_TYPE:-spot}"
SPOT_MAX_PRICE="${SPOT_MAX_PRICE:-0.50}"
V3_CHAT_S3_PREFIX="${V3_CHAT_S3_PREFIX:-assembled/v3_chat}"
V3_PSEUDO_S3_PREFIX="${V3_PSEUDO_S3_PREFIX:-v3/pseudo}"
V3_OUTPUT_S3_PREFIX="${V3_OUTPUT_S3_PREFIX:-v3/students}"
MAX_TRAIN_SAMPLES="${MAX_TRAIN_SAMPLES:-}"
STUDENT_HF_ID="${STUDENT_HF_ID:-}"
UNSLOTH_IMAGE="${UNSLOTH_IMAGE:-unsloth/unsloth:latest}"

: "${BUCKET:?BUCKET env var required}"
: "${IAM_INSTANCE_PROFILE:?IAM_INSTANCE_PROFILE env var required}"
: "${V3_TIER:?V3_TIER required: mini | pro | max}"
HF_TOKEN="${HF_TOKEN:-}"

case "${V3_TIER}" in
  mini|pro|max) ;;
  *) echo "FAIL: V3_TIER must be one of mini|pro|max (got '${V3_TIER}')"; exit 1 ;;
esac

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
GIT_COMMIT="$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || echo unknown)"
REPO_KEY="code/gpf-v3-${V3_TIER}-${TIMESTAMP}.tar.gz"
RUN_PREFIX="${V3_OUTPUT_S3_PREFIX}/${V3_TIER}/run-${TIMESTAMP}"
REPO_TAR="/tmp/gpf-v3-${V3_TIER}-${TIMESTAMP}.tar.gz"

echo "[1/5] Pack repo (scripts/v3 + configs)"
tar -czf "${REPO_TAR}" -C "${REPO_ROOT}" \
    scripts/v3/ scripts/aws/ configs/ \
    LICENSING.md NOTICE ATTRIBUTION.txt \
    docs/V3_DISTILLATION_PLAN.md

echo "[2/5] Upload repo tar to s3://${BUCKET}/${REPO_KEY}"
aws s3 cp "${REPO_TAR}" "s3://${BUCKET}/${REPO_KEY}" --region "${REGION}"

echo "[3/5] Resolve Deep Learning Base GPU AMI"
AMI_ID="$(aws ec2 describe-images --region "${REGION}" \
    --owners amazon \
    --filters \
        'Name=name,Values=Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 22.04)*' \
        'Name=state,Values=available' \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' --output text)"
echo "  AMI: ${AMI_ID}"

USERDATA_FILE="/tmp/gpf-v3-${V3_TIER}-userdata-${TIMESTAMP}.sh"
cat > "${USERDATA_FILE}" <<EOF
#!/bin/bash
set -euxo pipefail
exec > /var/log/gpf-v3-${V3_TIER}.log 2>&1

V3_TIER="${V3_TIER}"
RUN_TIMESTAMP="${TIMESTAMP}"
RUN_BUCKET="${BUCKET}"
RUN_REGION="${REGION}"
RUN_PREFIX="${RUN_PREFIX}"
STUDENT_HF_ID="${STUDENT_HF_ID}"
V3_CHAT_S3_PREFIX="${V3_CHAT_S3_PREFIX}"
V3_PSEUDO_S3_PREFIX="${V3_PSEUDO_S3_PREFIX}"
MAX_TRAIN_SAMPLES="${MAX_TRAIN_SAMPLES}"
UNSLOTH_IMAGE="${UNSLOTH_IMAGE}"

if [ -n "${HF_TOKEN}" ]; then
  export HF_TOKEN="${HF_TOKEN}"
  export HUGGING_FACE_HUB_TOKEN="${HF_TOKEN}"
fi

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
    [ -f /var/log/gpf-v3-\${V3_TIER}.log ] && \\
      aws s3 cp /var/log/gpf-v3-\${V3_TIER}.log \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/gpf-v3-\${V3_TIER}.live.log" \\
        --region "\${RUN_REGION}" --quiet || true
    sleep 30
  done
}

_v3_finalize() {
  set +e
  _v3_stamp "FINALIZE"
  kill \$_PUMP_PID 2>/dev/null || true
  echo "[finalize] uploading artefacts + logs"
  if [ -d /opt/gpf/artifacts/v3/students ]; then
    aws s3 sync /opt/gpf/artifacts/v3/students/ \\
      "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/artifacts/" \\
      --region "\${RUN_REGION}" --only-show-errors
  fi
  aws s3 cp /var/log/gpf-v3-\${V3_TIER}.log \\
    "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/gpf-v3-\${V3_TIER}.log" \\
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

# STS / IAM diagnostic dump.
{
  echo "=== STS identity ==="
  aws sts get-caller-identity --output json 2>&1 || echo "STS_FAIL"
} > /var/log/gpf-v3-sts.log 2>&1
aws s3 cp /var/log/gpf-v3-sts.log \\
  "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/sts.log" \\
  --region "\${RUN_REGION}" || true

_v3_stamp "BOOT"
aws s3 ls "s3://\${RUN_BUCKET}/" --region "\${RUN_REGION}" >/dev/null
_v3_stamp "S3_OK"

# 1. Verify Docker + nvidia-container-toolkit (Base DLAMI ships both).
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

# 2. Pull repo.
_v3_stamp "PULL_REPO"
mkdir -p /opt/gpf
cd /opt/gpf
aws s3 cp "s3://\${RUN_BUCKET}/${REPO_KEY}" /tmp/gpf-v3.tar.gz \\
  --region "\${RUN_REGION}"
tar -xzf /tmp/gpf-v3.tar.gz -C /opt/gpf/

# 3. Pull Unsloth Docker image.
_v3_stamp "DOCKER_PULL"
docker pull "\${UNSLOTH_IMAGE}"

# 4. Sync v3_chat (gold) + v3_pseudo (teacher pseudo-labels).
_v3_stamp "SYNC_DATA"
mkdir -p /opt/gpf/data/processed/v3_chat /opt/gpf/data/processed/v3_pseudo
mkdir -p /opt/gpf/data/processed/v3_pseudo_chat /opt/gpf/artifacts/v3/students
aws s3 sync "s3://\${RUN_BUCKET}/\${V3_CHAT_S3_PREFIX}/" \\
  /opt/gpf/data/processed/v3_chat/ \\
  --region "\${RUN_REGION}" --exclude "*" --include "train.jsonl" --include "validation.jsonl"
aws s3 sync "s3://\${RUN_BUCKET}/\${V3_PSEUDO_S3_PREFIX}/" \\
  /opt/gpf/data/processed/v3_pseudo/ \\
  --region "\${RUN_REGION}" --exclude "*" --include "pseudo_labels.jsonl" || true

# Persistent HF cache on DLAMI's NVMe.
HF_CACHE_DIR="/opt/dlami/nvme/hf-cache"
if [ ! -d /opt/dlami/nvme ]; then
  HF_CACHE_DIR="/opt/gpf/.hf-cache"
fi
mkdir -p "\${HF_CACHE_DIR}"
chmod 1777 "\${HF_CACHE_DIR}" /opt/gpf/data/processed /opt/gpf/artifacts

# 5. Convert pseudo-labels (OPF span format) to chat format BEFORE concat.
# Reviewer C-NEW-3: do NOT pass --shuffle-spans here. Pseudo-labels were
# generated by the teacher in document order and the strict-cursor resolver
# in generate_pseudo_labels.py already enforces that ordering.
_v3_stamp "CONVERT_PSEUDO"
PSEUDO_RAW="\$(ls /opt/gpf/data/processed/v3_pseudo/*.jsonl 2>/dev/null | head -1)"
if [ -n "\${PSEUDO_RAW}" ]; then
  PSEUDO_RAW_REL="\${PSEUDO_RAW#/opt/gpf/}"
  # convert_opf_to_chat.py uses only stdlib — skip the transformers upgrade.
  docker run --rm \\
    -u 0:0 \\
    -v /opt/gpf:/workspace/gpf \\
    -e SKIP_TRANSFORMERS_UPGRADE=1 \\
    --entrypoint /bin/bash \\
    "\${UNSLOTH_IMAGE}" \\
    /workspace/gpf/scripts/v3/_run_in_container.sh \\
    /workspace/gpf/scripts/v3/convert_opf_to_chat.py \\
    --input  "/workspace/gpf/\${PSEUDO_RAW_REL}" \\
    --output /workspace/gpf/data/processed/v3_pseudo_chat/pseudo_chat.jsonl \\
    --label-space /workspace/gpf/configs/label_space_v2.json
  cat /opt/gpf/data/processed/v3_chat/train.jsonl \\
      /opt/gpf/data/processed/v3_pseudo_chat/pseudo_chat.jsonl \\
      > /opt/gpf/data/processed/train_with_pseudo.jsonl
else
  cp /opt/gpf/data/processed/v3_chat/train.jsonl \\
     /opt/gpf/data/processed/train_with_pseudo.jsonl
fi

# 6. Train student inside Unsloth container.
_v3_stamp "TRAIN_START"
TRAIN_ARGS=()
if [ -n "\${MAX_TRAIN_SAMPLES}" ]; then
  TRAIN_ARGS+=( --max-train-samples "\${MAX_TRAIN_SAMPLES}" )
fi
docker run --rm --gpus all --ipc=host --shm-size=8g \\
  -u 0:0 \\
  -v /opt/gpf:/workspace/gpf \\
  -v "\${HF_CACHE_DIR}":/workspace/.cache/huggingface \\
  -e HF_HOME=/workspace/.cache/huggingface \\
  -e HF_HUB_ENABLE_HF_TRANSFER=1 \\
  -e HF_TOKEN="\${HF_TOKEN:-}" \\
  --entrypoint /bin/bash \\
  "\${UNSLOTH_IMAGE}" \\
  /workspace/gpf/scripts/v3/_run_in_container.sh \\
  /workspace/gpf/scripts/v3/train_student_distill.py \\
  --config /workspace/gpf/configs/v3_distillation.yaml \\
  --tier "\${V3_TIER}" \\
  --output-dir "/workspace/gpf/artifacts/v3/students/\${V3_TIER}-\${RUN_TIMESTAMP}" \\
  --train-jsonl /workspace/gpf/data/processed/train_with_pseudo.jsonl \\
  --eval-jsonl /workspace/gpf/data/processed/v3_chat/validation.jsonl \\
  "\${TRAIN_ARGS[@]}"
_v3_stamp "TRAIN_DONE"

echo "STUDENT \${V3_TIER} DISTILL COMPLETE"
EOF

SPEC_FILE="/tmp/gpf-v3-${V3_TIER}-spec-${TIMESTAMP}.json"
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
    {"DeviceName": "/dev/sda1", "Ebs": {"VolumeSize": 150, "VolumeType": "gp3", "DeleteOnTermination": true}}
  ],
  "TagSpecifications": [
    {"ResourceType": "instance", "Tags": [
      {"Key": "Name", "Value": "gpf-v3-${V3_TIER}-${TIMESTAMP}"},
      {"Key": "Project", "Value": "Greek-Privacy-Filter"},
      {"Key": "Stage", "Value": "v3-student-${V3_TIER}"},
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
fi

echo "[4/5] Request EC2 instance (tier=${V3_TIER}, ${INSTANCE_TYPE} ${MARKET_TYPE})"
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
echo "Tier:        ${V3_TIER}"
echo "Run ID:      ${TIMESTAMP}"
echo "Image:       ${UNSLOTH_IMAGE}"
echo "Output S3:   s3://${BUCKET}/${RUN_PREFIX}/"
echo "Tail log:    aws s3 cp s3://${BUCKET}/${RUN_PREFIX}/logs/gpf-v3-${V3_TIER}.live.log - --region ${REGION}"
