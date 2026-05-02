#!/usr/bin/env bash
# ec2_v3_pseudo.sh — AWS GPU spot to (a) download Greek corpus, (b) chunk
# it, (c) run trained teacher LoRA over it via local vLLM/llama.cpp, (d)
# upload pseudo-labelled JSONL to S3.
#
# Pipeline (user-data on the instance):
#   1. Install Unsloth + datasets + vllm
#   2. Pull repo tar
#   3. Run scripts/v3/load_greek_corpus.py to fetch + chunk corpus
#   4. Sync teacher LoRA adapter from S3
#   5. Start vLLM serving the teacher on localhost:8080 (OpenAI-compatible)
#   6. Run scripts/v3/generate_pseudo_labels.py against localhost:8080
#   7. Upload pseudo-labels to S3
#
# Required env vars:
#   BUCKET                — S3 bucket
#   IAM_INSTANCE_PROFILE  — EC2 profile R/W to BUCKET
#   TEACHER_S3_PREFIX     — path to LoRA adapters under BUCKET (e.g. v3/teacher/run-XXX/artifacts)
#
# Optional:
#   AWS_REGION            — default eu-north-1
#   AVAIL_ZONE            — default eu-north-1b
#   INSTANCE_TYPE         — default g6e.xlarge
#   MARKET_TYPE           — spot (default) or ondemand
#   SPOT_MAX_PRICE        — default 1.00
#   TEACHER_HF_ID         — base model id (default google/gemma-4-31B-it)
#   V3_OUTPUT_S3_PREFIX   — default v3/pseudo
#   CORPUS_TARGET_RECORDS — default 500000

set -euo pipefail

REGION="${AWS_REGION:-eu-north-1}"
AVAIL_ZONE="${AVAIL_ZONE:-eu-north-1b}"
INSTANCE_TYPE="${INSTANCE_TYPE:-g6e.xlarge}"
MARKET_TYPE="${MARKET_TYPE:-spot}"
SPOT_MAX_PRICE="${SPOT_MAX_PRICE:-1.00}"
TEACHER_HF_ID="${TEACHER_HF_ID:-unsloth/gemma-4-31B-it-unsloth-bnb-4bit}"
V3_OUTPUT_S3_PREFIX="${V3_OUTPUT_S3_PREFIX:-v3/pseudo}"
CORPUS_TARGET_RECORDS="${CORPUS_TARGET_RECORDS:-500000}"

: "${BUCKET:?BUCKET env var required}"
: "${IAM_INSTANCE_PROFILE:?IAM_INSTANCE_PROFILE env var required}"
: "${TEACHER_S3_PREFIX:?TEACHER_S3_PREFIX env var required (e.g. v3/teacher/run-XXX/artifacts)}"
# HF_TOKEN optional (Unsloth mirrors are public)
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
    requirements-unsloth.txt LICENSING.md NOTICE ATTRIBUTION.txt \
    docs/V3_DISTILLATION_PLAN.md

echo "[2/5] Upload repo tar"
aws s3 cp "${REPO_TAR}" "s3://${BUCKET}/${REPO_KEY}" --region "${REGION}"

echo "[3/5] Resolve AMI"
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

if [ -n "${HF_TOKEN}" ]; then
  export HF_TOKEN="${HF_TOKEN}"
  export HUGGING_FACE_HUB_TOKEN="${HF_TOKEN}"
fi
export HF_HUB_ENABLE_HF_TRANSFER=1

_pump() {
  while true; do
    [ -f /var/log/gpf-v3-pseudo.log ] && \\
      aws s3 cp /var/log/gpf-v3-pseudo.log \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/gpf-v3-pseudo.live.log" \\
        --region "\${RUN_REGION}" --quiet || true
    sleep 30
  done
}
_pump &
_PUMP_PID=\$!

_finalize() {
  set +e
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
  shutdown -h now
}
trap _finalize EXIT INT TERM

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

# Install deps
python3 -m venv /opt/gpf/.venv
source /opt/gpf/.venv/bin/activate
pip install --upgrade pip wheel
pip install -r /opt/gpf/requirements-unsloth.txt
pip install vllm pyyaml

# Step A: Download + chunk Greek corpus (commercial-clean sources only)
mkdir -p /opt/gpf/data/v3_corpus
python3 /opt/gpf/scripts/v3/load_greek_corpus.py \\
  --output /opt/gpf/data/v3_corpus/greek_corpus.jsonl \\
  --target-records "\${CORPUS_TARGET_RECORDS}" \\
  --sources greek_pd common_voice greek_legal

# Step B: Download teacher LoRA adapter from S3
mkdir -p /opt/gpf/teacher_adapter
aws s3 sync "s3://\${RUN_BUCKET}/\${TEACHER_S3_PREFIX}/" \\
  /opt/gpf/teacher_adapter/ \\
  --region "\${RUN_REGION}"

# Find the lora_adapters dir (could be nested under run-XXX)
ADAPTER_DIR="\$(find /opt/gpf/teacher_adapter -name lora_adapters -type d | head -1)"
if [ -z "\${ADAPTER_DIR}" ]; then
  echo "FAIL: no lora_adapters/ found under teacher S3 prefix"
  exit 1
fi
export ADAPTER_DIR
export TEACHER_HF_ID
echo "Using LoRA adapter: \${ADAPTER_DIR}"

# Step C: Merge LoRA adapter into base BEFORE serving (vLLM bnb+lora-modules
# is unsupported as of v0.20). Merged checkpoint is bf16 ~60GB on disk for
# 31B model — fits the 250GB EBS provisioned for this instance.
mkdir -p /opt/gpf/teacher_merged
python3 - <<'PYEOF'
import os
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

base_id = os.environ["TEACHER_HF_ID"]
adapter = os.environ["ADAPTER_DIR"]
out = "/opt/gpf/teacher_merged"

tok = AutoTokenizer.from_pretrained(base_id)
base = AutoModelForCausalLM.from_pretrained(base_id, dtype=torch.bfloat16, device_map="auto")
peft = PeftModel.from_pretrained(base, adapter)
merged = peft.merge_and_unload()
merged.save_pretrained(out, safe_serialization=True)
tok.save_pretrained(out)
print("merged ->", out)
PYEOF

nohup python3 -m vllm.entrypoints.openai.api_server \\
  --model /opt/gpf/teacher_merged \\
  --max-model-len 4096 \\
  --gpu-memory-utilization 0.92 \\
  --port 8080 \\
  > /var/log/vllm.log 2>&1 &
VLLM_PID=\$!

# Wait for vLLM ready
echo "Waiting for vLLM..."
for i in \$(seq 1 60); do
  if curl -sf http://127.0.0.1:8080/v1/models >/dev/null; then
    echo "vLLM ready"
    break
  fi
  sleep 10
done

# Step D: Generate pseudo-labels
mkdir -p /opt/gpf/data/v3_pseudo
python3 /opt/gpf/scripts/v3/generate_pseudo_labels.py \\
  --engine openai-server \\
  --host http://127.0.0.1:8080 \\
  --teacher-id "\${TEACHER_HF_ID}" \\
  --model /opt/gpf/teacher_merged \\
  --input /opt/gpf/data/v3_corpus/greek_corpus.jsonl \\
  --output /opt/gpf/data/v3_pseudo/pseudo_labels.jsonl \\
  --max-records "\${CORPUS_TARGET_RECORDS}"

kill \$VLLM_PID 2>/dev/null || true
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
    {"DeviceName": "/dev/sda1", "Ebs": {"VolumeSize": 250, "VolumeType": "gp3", "DeleteOnTermination": true}}
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
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); d.pop('InstanceMarketOptions', None); json.dump(d, open(sys.argv[1],'w'))" "${SPEC_FILE}"
fi

echo "[4/5] Request EC2 instance"
INSTANCE_ID="$(aws ec2 run-instances --region "${REGION}" \
    --cli-input-json "file://${SPEC_FILE}" \
    --query 'Instances[0].InstanceId' --output text)"

echo "[5/5] Instance: ${INSTANCE_ID}"
echo "Run ID:        ${TIMESTAMP}"
echo "Teacher LoRA:  s3://${BUCKET}/${TEACHER_S3_PREFIX}"
echo "Output S3:     s3://${BUCKET}/${RUN_PREFIX}/"
echo "Tail log:      aws s3 cp s3://${BUCKET}/${RUN_PREFIX}/logs/gpf-v3-pseudo.live.log - --region ${REGION}"
