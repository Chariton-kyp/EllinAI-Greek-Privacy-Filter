#!/usr/bin/env bash
# ec2_v3_distill.sh — Launch AWS EC2 instance to distill ONE v3 student tier.
#
# Required env vars:
#   BUCKET                — S3 bucket holding v3_chat + v3_pseudo data
#   IAM_INSTANCE_PROFILE  — EC2 profile with R/W access to BUCKET
#   V3_TIER               — one of: mini | pro | max
#                            (lite uses scripts/run_opf_train.py — different path)
#                            (ultra ships teacher itself — no extra training)
#
# Optional:
#   AWS_REGION            — default eu-north-1
#   AVAIL_ZONE            — default eu-north-1b
#   INSTANCE_TYPE         — default g6.xlarge (L4 24GB)
#   MARKET_TYPE           — spot (default) or ondemand
#   SPOT_MAX_PRICE        — default 0.50
#   STUDENT_HF_ID         — override student.hf_id from yaml
#   V3_CHAT_S3_PREFIX     — default assembled/v3_chat
#   V3_PSEUDO_S3_PREFIX   — default v3/pseudo
#   V3_OUTPUT_S3_PREFIX   — default v3/students
#   MAX_TRAIN_SAMPLES     — for pilot runs
#
# Example: train all 3 causal-LM students in parallel
#   for tier in mini pro max; do
#     V3_TIER=$tier bash scripts/aws/ec2_v3_distill.sh &
#   done

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

: "${BUCKET:?BUCKET env var required}"
: "${IAM_INSTANCE_PROFILE:?IAM_INSTANCE_PROFILE env var required}"
: "${V3_TIER:?V3_TIER required: mini | pro | max}"
# HF_TOKEN optional (Unsloth mirrors are public)
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

if [ -n "${HF_TOKEN}" ]; then
  export HF_TOKEN="${HF_TOKEN}"
  export HUGGING_FACE_HUB_TOKEN="${HF_TOKEN}"
fi
export HF_HUB_ENABLE_HF_TRANSFER=1

_v3_log_pump() {
  while true; do
    [ -f /var/log/gpf-v3-\${V3_TIER}.log ] && \\
      aws s3 cp /var/log/gpf-v3-\${V3_TIER}.log \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/gpf-v3-\${V3_TIER}.live.log" \\
        --region "\${RUN_REGION}" --quiet || true
    sleep 30
  done
}
_v3_log_pump &
_PUMP_PID=\$!

_v3_finalize() {
  set +e
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
  shutdown -h now
}
trap _v3_finalize EXIT INT TERM

# Install AWS CLI if missing
if ! command -v aws >/dev/null 2>&1; then
  curl -sSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
  unzip -q /tmp/awscliv2.zip -d /tmp/
  /tmp/aws/install
fi

# Pull repo
mkdir -p /opt/gpf
cd /opt/gpf
aws s3 cp "s3://\${RUN_BUCKET}/${REPO_KEY}" /tmp/gpf-v3.tar.gz \\
  --region "\${RUN_REGION}"
tar -xzf /tmp/gpf-v3.tar.gz -C /opt/gpf/

# Install Unsloth
python3 -m venv /opt/gpf/.venv
source /opt/gpf/.venv/bin/activate
pip install --upgrade pip wheel
pip install -r /opt/gpf/requirements-unsloth.txt
pip install pyyaml

# Sync v3_chat (gold) + v3_pseudo (teacher pseudo-labels)
mkdir -p /opt/gpf/data/processed/v3_chat /opt/gpf/data/processed/v3_pseudo
aws s3 sync "s3://\${RUN_BUCKET}/\${V3_CHAT_S3_PREFIX}/" \\
  /opt/gpf/data/processed/v3_chat/ \\
  --region "\${RUN_REGION}" --exclude "*" --include "train.jsonl" --include "validation.jsonl"
aws s3 sync "s3://\${RUN_BUCKET}/\${V3_PSEUDO_S3_PREFIX}/" \\
  /opt/gpf/data/processed/v3_pseudo/ \\
  --region "\${RUN_REGION}" --exclude "*" --include "pseudo_labels.jsonl" || true

# Convert pseudo-labels (OPF span format) to chat format BEFORE concatenation
# (gold train is already chat format; pseudo is OPF — they are NOT compatible
# without this conversion, would crash trainer with KeyError 'messages').
mkdir -p /opt/gpf/data/processed/v3_pseudo_chat
PSEUDO_RAW="\$(ls /opt/gpf/data/processed/v3_pseudo/*.jsonl 2>/dev/null | head -1)"
if [ -n "\${PSEUDO_RAW}" ]; then
  # NOTE: do NOT pass --shuffle-spans here. Pseudo-labels were generated by the
  # teacher in document order; the strict-cursor resolver in generate_pseudo_labels.py
  # already enforces that. Shuffling here would reorder spans and the student would
  # learn an output ordering that contradicts the teacher's. (Reviewer C-NEW-3.)
  python3 /opt/gpf/scripts/v3/convert_opf_to_chat.py \\
    --input  "\${PSEUDO_RAW}" \\
    --output /opt/gpf/data/processed/v3_pseudo_chat/pseudo_chat.jsonl \\
    --label-space /opt/gpf/configs/label_space_v2.json
  cat /opt/gpf/data/processed/v3_chat/train.jsonl \\
      /opt/gpf/data/processed/v3_pseudo_chat/pseudo_chat.jsonl \\
      > /opt/gpf/data/processed/train_with_pseudo.jsonl
else
  # No pseudo-labels available — train on gold only (still useful for ablation)
  cp /opt/gpf/data/processed/v3_chat/train.jsonl \\
     /opt/gpf/data/processed/train_with_pseudo.jsonl
fi

# Train student
mkdir -p /opt/gpf/artifacts/v3/students
TRAIN_ARGS=()
if [ -n "\${MAX_TRAIN_SAMPLES}" ]; then
  TRAIN_ARGS+=( --max-train-samples "\${MAX_TRAIN_SAMPLES}" )
fi
python3 /opt/gpf/scripts/v3/train_student_distill.py \\
  --config /opt/gpf/configs/v3_distillation.yaml \\
  --tier "\${V3_TIER}" \\
  --output-dir "/opt/gpf/artifacts/v3/students/\${V3_TIER}-\${RUN_TIMESTAMP}" \\
  --train-jsonl /opt/gpf/data/processed/train_with_pseudo.jsonl \\
  --eval-jsonl /opt/gpf/data/processed/v3_chat/validation.jsonl \\
  "\${TRAIN_ARGS[@]}"

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
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); d.pop('InstanceMarketOptions', None); json.dump(d, open(sys.argv[1],'w'))" "${SPEC_FILE}"
fi

echo "[4/5] Request EC2 instance (tier=${V3_TIER}, ${INSTANCE_TYPE} ${MARKET_TYPE})"
INSTANCE_ID="$(aws ec2 run-instances --region "${REGION}" \
    --cli-input-json "file://${SPEC_FILE}" \
    --query 'Instances[0].InstanceId' --output text)"

echo "[5/5] Instance: ${INSTANCE_ID}"
echo "Tier:        ${V3_TIER}"
echo "Run ID:      ${TIMESTAMP}"
echo "Output S3:   s3://${BUCKET}/${RUN_PREFIX}/"
echo "Tail log:    aws s3 cp s3://${BUCKET}/${RUN_PREFIX}/logs/gpf-v3-${V3_TIER}.live.log - --region ${REGION}"
