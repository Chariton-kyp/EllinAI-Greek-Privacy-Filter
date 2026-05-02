#!/usr/bin/env bash
# ec2_v3_teacher.sh — Launch AWS EC2 instance to train v3 teacher.
#
# Pipeline (user-data on the instance):
#   1. Install Unsloth + trl + bitsandbytes + transformers stack
#   2. Pull repo tar (uploaded by this launcher) + sync v3_chat data from S3
#   3. Run scripts/v3/train_teacher.py
#        - LoRA Q4 SFT on gemma-4-31B-it (or override via TEACHER_HF_ID)
#        - configs/v3_distillation.yaml hyperparameters
#   4. Sync trained LoRA adapters + metrics → S3
#   5. EXIT trap: final sync + shutdown -h now (terminates spot instance)
#
# Required env vars:
#   BUCKET                — S3 bucket holding v3_chat data + receiving outputs
#   IAM_INSTANCE_PROFILE  — EC2 profile with R/W access to BUCKET
#
# Optional:
#   AWS_REGION            — default eu-north-1
#   AVAIL_ZONE            — default eu-north-1b (g6e.xlarge has reliable capacity here)
#   INSTANCE_TYPE         — default g6e.xlarge (L40S 48GB)
#   MARKET_TYPE           — spot (default) or ondemand
#   SPOT_MAX_PRICE        — default 1.00
#   TEACHER_HF_ID         — override teacher.hf_id from yaml (e.g. Qwen/Qwen3.6-35B-A3B-Instruct)
#   V3_DATA_S3_PREFIX     — default assembled/v3_chat (under BUCKET)
#   V3_OUTPUT_S3_PREFIX   — default v3/teacher (under BUCKET)
#   MAX_TRAIN_SAMPLES     — for pilot runs, e.g. 500. Default empty (all 111k records)
#
# Recommended for full run: g6e.xlarge spot eu-north-1b, ~12 h, $7-8.
# Pilot run: MAX_TRAIN_SAMPLES=500 reduces to ~30 min for sanity check.

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

: "${BUCKET:?BUCKET env var required}"
: "${IAM_INSTANCE_PROFILE:?IAM_INSTANCE_PROFILE env var required}"
# HF_TOKEN: only needed if TEACHER_HF_ID points to gated google/gemma-4-*
# (Unsloth mirrors `unsloth/gemma-4-*-unsloth-bnb-4bit` are PUBLIC, no token).
HF_TOKEN="${HF_TOKEN:-}"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
GIT_COMMIT="$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || echo unknown)"
REPO_KEY="code/gpf-v3-teacher-${TIMESTAMP}.tar.gz"
RUN_PREFIX="${V3_OUTPUT_S3_PREFIX}/run-${TIMESTAMP}"
REPO_TAR="/tmp/gpf-v3-teacher-${TIMESTAMP}.tar.gz"

echo "[1/5] Pack repo (scripts/v3 + configs + requirements)"
tar -czf "${REPO_TAR}" -C "${REPO_ROOT}" \
    scripts/v3/ scripts/aws/ configs/ \
    requirements-unsloth.txt LICENSING.md NOTICE ATTRIBUTION.txt \
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

# HuggingFace optional auth (only needed for gated google/* mirrors;
# unsloth/* mirrors are public, so empty token works fine).
if [ -n "${HF_TOKEN}" ]; then
  export HF_TOKEN="${HF_TOKEN}"
  export HUGGING_FACE_HUB_TOKEN="${HF_TOKEN}"
fi
export HF_HUB_ENABLE_HF_TRANSFER=1

# Sync log every 30s for live monitoring
_v3_log_pump() {
  while true; do
    [ -f /var/log/gpf-v3-teacher.log ] && \\
      aws s3 cp /var/log/gpf-v3-teacher.log \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/gpf-v3-teacher.live.log" \\
        --region "\${RUN_REGION}" --quiet || true
    sleep 30
  done
}
_v3_log_pump &
_PUMP_PID=\$!

# EXIT trap: always sync final artefacts + logs, then shutdown
_v3_finalize() {
  set +e
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
  shutdown -h now
}
trap _v3_finalize EXIT INT TERM

# 1. Install AWS CLI v2 if missing (DLAMI usually has it)
if ! command -v aws >/dev/null 2>&1; then
  curl -sSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
  unzip -q /tmp/awscliv2.zip -d /tmp/
  /tmp/aws/install
fi

# 2. Pull repo tar
mkdir -p /opt/gpf
cd /opt/gpf
aws s3 cp "s3://\${RUN_BUCKET}/${REPO_KEY}" /tmp/gpf-v3-teacher.tar.gz \\
  --region "\${RUN_REGION}"
tar -xzf /tmp/gpf-v3-teacher.tar.gz -C /opt/gpf/

# 3. Install Unsloth + deps in a fresh venv
python3 -m venv /opt/gpf/.venv
source /opt/gpf/.venv/bin/activate
pip install --upgrade pip wheel
pip install -r /opt/gpf/requirements-unsloth.txt
pip install pyyaml

# 4. Sync v3_chat data from S3
mkdir -p /opt/gpf/data/processed/v3_chat
aws s3 sync "s3://\${RUN_BUCKET}/\${V3_DATA_S3_PREFIX}/" \\
  /opt/gpf/data/processed/v3_chat/ \\
  --region "\${RUN_REGION}" --exclude "*" --include "train.jsonl" --include "validation.jsonl"

# 5. Train teacher
mkdir -p /opt/gpf/artifacts/v3/teacher
TRAIN_ARGS=()
if [ -n "\${MAX_TRAIN_SAMPLES}" ]; then
  TRAIN_ARGS+=( --max-train-samples "\${MAX_TRAIN_SAMPLES}" )
fi
python3 /opt/gpf/scripts/v3/train_teacher.py \\
  --config /opt/gpf/configs/v3_distillation.yaml \\
  --output-dir "/opt/gpf/artifacts/v3/teacher/run-\${RUN_TIMESTAMP}" \\
  --train-jsonl /opt/gpf/data/processed/v3_chat/train.jsonl \\
  --eval-jsonl /opt/gpf/data/processed/v3_chat/validation.jsonl \\
  --model-override "\${TEACHER_HF_ID}" \\
  "\${TRAIN_ARGS[@]}"

# 6. Final sync + auto-shutdown via EXIT trap
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
    {"DeviceName": "/dev/sda1", "Ebs": {"VolumeSize": 200, "VolumeType": "gp3", "DeleteOnTermination": true}}
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
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); d.pop('InstanceMarketOptions', None); json.dump(d, open(sys.argv[1],'w'))" "${SPEC_FILE}"
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

echo "[5/5] Instance: ${INSTANCE_ID}"
echo
echo "Run ID:      ${TIMESTAMP}"
echo "Git commit:  ${GIT_COMMIT}"
echo "Teacher HF:  ${TEACHER_HF_ID}"
echo "Data S3:     s3://${BUCKET}/${V3_DATA_S3_PREFIX}/"
echo "Output S3:   s3://${BUCKET}/${RUN_PREFIX}/"
echo
echo "Tail live log:"
echo "  aws s3 cp s3://${BUCKET}/${RUN_PREFIX}/logs/gpf-v3-teacher.live.log - --region ${REGION}"
echo
echo "Watch instance:"
echo "  aws ec2 describe-instances --region ${REGION} --instance-ids ${INSTANCE_ID}"
