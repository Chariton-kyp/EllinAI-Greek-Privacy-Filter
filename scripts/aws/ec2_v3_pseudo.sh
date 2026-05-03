#!/usr/bin/env bash
# ec2_v3_pseudo.sh — Run teacher pseudo-label generation inside the
# unsloth/unsloth Docker image on EC2 spot.
#
# Pipeline (user-data on the instance):
#   1. Pull unsloth/unsloth:latest
#   2. Pull repo tar + sync teacher LoRA adapter from S3
#   3. Container A: load + chunk Greek corpus (commercial-clean sources)
#   4. Container B: run generate_pseudo_labels_unsloth.py
#      (Unsloth FastLanguageModel direct inference: bnb-4bit + LoRA)
#   5. Upload pseudo_labels.jsonl + corpus + logs to S3
#
# Required env vars:
#   BUCKET                — S3 bucket
#   IAM_INSTANCE_PROFILE  — EC2 profile R/W to BUCKET
#   TEACHER_S3_PREFIX     — path to LoRA adapters under BUCKET
#                           (e.g. v3/teacher/run-XXX/artifacts)
#
# Optional:
#   AWS_REGION            — default eu-north-1
#   AVAIL_ZONE            — default eu-north-1b
#   INSTANCE_TYPE         — default g6e.xlarge
#   MARKET_TYPE           — spot (default) or ondemand
#   SPOT_MAX_PRICE        — default 1.00
#   TEACHER_HF_ID         — base model id
#   V3_OUTPUT_S3_PREFIX   — default v3/pseudo
#   CORPUS_TARGET_RECORDS — default 500000
#   UNSLOTH_IMAGE         — default unsloth/unsloth:latest

set -euo pipefail

REGION="${AWS_REGION:-eu-north-1}"
AVAIL_ZONE="${AVAIL_ZONE:-eu-north-1b}"
INSTANCE_TYPE="${INSTANCE_TYPE:-g6e.xlarge}"
MARKET_TYPE="${MARKET_TYPE:-spot}"
SPOT_MAX_PRICE="${SPOT_MAX_PRICE:-1.00}"
TEACHER_HF_ID="${TEACHER_HF_ID:-unsloth/gemma-4-31B-it-unsloth-bnb-4bit}"
V3_OUTPUT_S3_PREFIX="${V3_OUTPUT_S3_PREFIX:-v3/pseudo}"
CORPUS_TARGET_RECORDS="${CORPUS_TARGET_RECORDS:-500000}"
UNSLOTH_IMAGE="${UNSLOTH_IMAGE:-unsloth/unsloth:latest}"

: "${BUCKET:?BUCKET env var required}"
: "${IAM_INSTANCE_PROFILE:?IAM_INSTANCE_PROFILE env var required}"
: "${TEACHER_S3_PREFIX:?TEACHER_S3_PREFIX env var required}"
HF_TOKEN="${HF_TOKEN:-}"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
GIT_COMMIT="$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || echo unknown)"
REPO_KEY="code/gpf-v3-pseudo-${TIMESTAMP}.tar.gz"
RUN_PREFIX="${V3_OUTPUT_S3_PREFIX}/run-${TIMESTAMP}"
REPO_TAR="/tmp/gpf-v3-pseudo-${TIMESTAMP}.tar.gz"

echo "[1/5] Pack repo"
tar -czf "${REPO_TAR}" -C "${REPO_ROOT}" \
    scripts/v3/ scripts/aws/ configs/ \
    LICENSING.md NOTICE ATTRIBUTION.txt \
    docs/V3_DISTILLATION_PLAN.md

echo "[2/5] Upload repo tar"
aws s3 cp "${REPO_TAR}" "s3://${BUCKET}/${REPO_KEY}" --region "${REGION}"

echo "[3/5] Resolve Deep Learning Base GPU AMI"
AMI_ID="$(aws ec2 describe-images --region "${REGION}" \
    --owners amazon \
    --filters \
        'Name=name,Values=Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 22.04)*' \
        'Name=state,Values=available' \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' --output text)"
echo "  AMI: ${AMI_ID}"

USERDATA_FILE="/tmp/gpf-v3-pseudo-userdata-${TIMESTAMP}.sh"
cat > "${USERDATA_FILE}" <<EOF
#!/bin/bash
set -euxo pipefail
exec > /var/log/gpf-v3-pseudo.log 2>&1

RUN_TIMESTAMP="${TIMESTAMP}"
RUN_BUCKET="${BUCKET}"
RUN_REGION="${REGION}"
RUN_PREFIX="${RUN_PREFIX}"
TEACHER_HF_ID="${TEACHER_HF_ID}"
TEACHER_S3_PREFIX="${TEACHER_S3_PREFIX}"
CORPUS_TARGET_RECORDS="${CORPUS_TARGET_RECORDS}"
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

_pump() {
  while true; do
    [ -f /var/log/gpf-v3-pseudo.log ] && \\
      aws s3 cp /var/log/gpf-v3-pseudo.log \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/gpf-v3-pseudo.live.log" \\
        --region "\${RUN_REGION}" --quiet || true
    sleep 30
  done
}

_finalize() {
  set +e
  _v3_stamp "FINALIZE"
  kill \$_PUMP_PID 2>/dev/null || true
  echo "[finalize] uploading pseudo-labels + logs"
  if [ -f /opt/gpf/data/v3_pseudo/pseudo_labels.jsonl ]; then
    aws s3 cp /opt/gpf/data/v3_pseudo/pseudo_labels.jsonl \\
      "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/pseudo_labels.jsonl" \\
      --region "\${RUN_REGION}" --only-show-errors
  fi
  if [ -f /opt/gpf/data/v3_corpus/greek_corpus.jsonl ]; then
    aws s3 cp /opt/gpf/data/v3_corpus/greek_corpus.jsonl \\
      "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/greek_corpus.jsonl" \\
      --region "\${RUN_REGION}" --only-show-errors
  fi
  aws s3 cp /var/log/gpf-v3-pseudo.log \\
    "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/gpf-v3-pseudo.log" \\
    --region "\${RUN_REGION}" --only-show-errors
  aws s3 cp /var/log/cloud-init-output.log \\
    "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/cloud-init-output.log" \\
    --region "\${RUN_REGION}" --only-show-errors 2>/dev/null
  _v3_stamp "SHUTDOWN"
  shutdown -h now
}
trap _finalize EXIT INT TERM
_pump &
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

# 3. Pull Unsloth Docker image (with timeout + retry against pull hang).
_v3_stamp "DOCKER_PULL"
if ! timeout 1500 docker pull "\${UNSLOTH_IMAGE}"; then
  echo "[docker] pull stalled, retrying"
  timeout 1500 docker pull "\${UNSLOTH_IMAGE}"
fi

# 4. Sync teacher LoRA adapter from S3.
_v3_stamp "SYNC_ADAPTER"
mkdir -p /opt/gpf/teacher_adapter /opt/gpf/data/v3_corpus /opt/gpf/data/v3_pseudo
aws s3 sync "s3://\${RUN_BUCKET}/\${TEACHER_S3_PREFIX}/" \\
  /opt/gpf/teacher_adapter/ \\
  --region "\${RUN_REGION}"

# Resolve canonical adapter path (output_dir/lora_adapters from train_teacher.py).
ADAPTER_DIR=""
for cand in /opt/gpf/teacher_adapter/run-*/lora_adapters \\
            /opt/gpf/teacher_adapter/lora_adapters \\
            /opt/gpf/teacher_adapter/artifacts/run-*/lora_adapters; do
  for d in \$cand; do
    if [ -d "\$d" ] && [ -f "\$d/adapter_config.json" ]; then
      ADAPTER_DIR="\$d"
      break 2
    fi
  done
done
if [ -z "\${ADAPTER_DIR}" ]; then
  echo "FAIL: no lora_adapters/ with adapter_config.json found under teacher S3 prefix"
  ls -laR /opt/gpf/teacher_adapter
  exit 1
fi
echo "Using LoRA adapter: \${ADAPTER_DIR}"
ADAPTER_REL="\${ADAPTER_DIR#/opt/gpf/}"

# Persistent HF cache on DLAMI's NVMe.
HF_CACHE_DIR="/opt/dlami/nvme/hf-cache"
if [ ! -d /opt/dlami/nvme ]; then
  HF_CACHE_DIR="/opt/gpf/.hf-cache"
fi
mkdir -p "\${HF_CACHE_DIR}"
chmod 1777 "\${HF_CACHE_DIR}" /opt/gpf/data /opt/gpf/teacher_adapter

# 5. Step A: Greek corpus (commercial-clean sources only).
_v3_stamp "CORPUS"
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
  /workspace/gpf/scripts/v3/load_greek_corpus.py \\
  --output /workspace/gpf/data/v3_corpus/greek_corpus.jsonl \\
  --target-records "\${CORPUS_TARGET_RECORDS}" \\
  --sources greek_pd common_voice greek_legal

# 6. Step B: pseudo-label generation via Unsloth direct inference.
# (Reviewer C-NEW-1/C-NEW-2: vLLM merge+serve OOMs L40S 48GB; bnb-4bit
# merge_and_unload is unreliable. FastLanguageModel runs bnb-4bit + LoRA
# natively in ~22GB VRAM, batched.)
_v3_stamp "PSEUDO_GEN"
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
  /workspace/gpf/scripts/v3/generate_pseudo_labels_unsloth.py \\
  --base-model "\${TEACHER_HF_ID}" \\
  --lora-adapter "/workspace/gpf/\${ADAPTER_REL}" \\
  --input /workspace/gpf/data/v3_corpus/greek_corpus.jsonl \\
  --output /workspace/gpf/data/v3_pseudo/pseudo_labels.jsonl \\
  --batch-size 8 \\
  --max-records "\${CORPUS_TARGET_RECORDS}"
_v3_stamp "PSEUDO_DONE"

echo "PSEUDO-LABEL GENERATION COMPLETE"
EOF

SPEC_FILE="/tmp/gpf-v3-pseudo-spec-${TIMESTAMP}.json"
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
    {"DeviceName": "/dev/sda1", "Ebs": {"VolumeSize": 250, "VolumeType": "gp3", "Iops": 16000, "Throughput": 1000, "DeleteOnTermination": true}}
  ],
  "TagSpecifications": [
    {"ResourceType": "instance", "Tags": [
      {"Key": "Name", "Value": "gpf-v3-pseudo-${TIMESTAMP}"},
      {"Key": "Project", "Value": "Greek-Privacy-Filter"},
      {"Key": "Stage", "Value": "v3-pseudo"},
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
echo "Run ID:        ${TIMESTAMP}"
echo "Image:         ${UNSLOTH_IMAGE}"
echo "Teacher LoRA:  s3://${BUCKET}/${TEACHER_S3_PREFIX}"
echo "Output S3:     s3://${BUCKET}/${RUN_PREFIX}/"
echo "Tail log:      aws s3 cp s3://${BUCKET}/${RUN_PREFIX}/logs/gpf-v3-pseudo.live.log - --region ${REGION}"
