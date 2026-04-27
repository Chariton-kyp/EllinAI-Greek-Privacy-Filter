#!/usr/bin/env bash
# ec2_spot_generate.sh — Launch an EC2 spot instance that runs the full
# Greek Privacy Filter data-build pipeline end-to-end with audit output.
#
# On the instance, the boot script (user-data):
#   1. Installs CUDA build of llama.cpp + Python deps
#   2. Downloads Qwen3.6-35B-A3B GGUF (quant configurable)
#   3. Starts llama-server with thinking disabled
#   4. Downloads carrier corpora (greek_legal_code + Common Voice EL)
#   5. Generates the main v2 synthetic corpus      → S3 checkpoint
#   6. Latinizes Greek email/URL spans
#   7. Generates diverse hard negatives via Qwen   → S3 checkpoint
#   8. Merges, curates, produces balanced splits   → S3 checkpoint
#   9. Runs provenance verification + SHA-256 manifest → S3 checkpoint
#  10. Final EXIT trap — s3 sync data + artifacts + logs, then terminate
#
# Data persistence model:
#   * Layer 1 (incremental): after each long-running stage, the
#     \`_gpf_checkpoint\` helper runs an idempotent \`aws s3 sync\` of
#     /opt/gpf/data/processed/ and /opt/gpf/artifacts/ to the run
#     prefix. Worst-case data loss is bounded to one stage's worth of
#     work even if the spot instance is reclaimed mid-pipeline.
#   * Layer 2 (terminal): an EXIT/INT/TERM trap (\`_gpf_finalize\`)
#     re-syncs everything on any exit path before \`shutdown -h now\`.
#     Combined with \`InstanceInitiatedShutdownBehavior: terminate\`,
#     this guarantees the instance is released and the EBS volume
#     deleted, even on Python errors or signal interrupts.
#
# All randomness is seed-controlled. Each run uploads a run_metadata.json
# with the git commit, instance ID, input parameters, and SHA-256s of
# the output JSONLs so the build is reproducible and auditable.
#
# Required env vars (or --flags):
#   BUCKET              — S3 bucket for outputs + intermediate repo tar
#   IAM_INSTANCE_PROFILE — IAM profile attached to EC2 (s3:GetObject for
#                         repo tar, s3:PutObject for outputs + logs)
#   AWS_REGION          — default us-east-1
#   INSTANCE_TYPE       — g6e.xlarge (L40S 48GB, recommended) or
#                         g5.2xlarge (A10G 24GB, fallback with offload)
#
# Optional:
#   SAMPLE_COUNT        — main-gen count, default 100000
#   HARDNEG_COUNT       — hard-neg count, default SAMPLE_COUNT/67 (~1.5%)
#   QUANT               — default UD-Q8_K_XL (alt: UD-Q4_K_S)
#   SPOT_MAX_PRICE      — default 1.00 ($/h ceiling)
#   SEED_MAIN           — default 2024
#   SEED_HARDNEG        — default 2024
#   SEED_LATINIZE       — default 1337
#   SEED_CURATE         — default 1337
#   SSH_KEY_NAME        — if set, attaches an EC2 keypair for debug SSH
#
# Usage:
#   export BUCKET=your-gpf-bucket
#   export IAM_INSTANCE_PROFILE=your-iam-role
#   bash scripts/aws/ec2_spot_generate.sh

set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
INSTANCE_TYPE="${INSTANCE_TYPE:-g6e.xlarge}"
SAMPLE_COUNT="${SAMPLE_COUNT:-100000}"
HARDNEG_COUNT="${HARDNEG_COUNT:-$(( SAMPLE_COUNT / 67 ))}"
SPOT_MAX_PRICE="${SPOT_MAX_PRICE:-1.00}"
QUANT="${QUANT:-UD-Q8_K_XL}"
SEED_MAIN="${SEED_MAIN:-2024}"
SEED_HARDNEG="${SEED_HARDNEG:-2024}"
SEED_LATINIZE="${SEED_LATINIZE:-1337}"
SEED_CURATE="${SEED_CURATE:-1337}"

: "${BUCKET:?BUCKET env var required (S3 bucket name)}"
: "${IAM_INSTANCE_PROFILE:?IAM_INSTANCE_PROFILE env var required}"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
GIT_COMMIT="$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || echo 'unknown')"
REPO_KEY="code/gpf-gen-${TIMESTAMP}.tar.gz"
RUN_PREFIX="generated/run-${TIMESTAMP}"
REPO_TAR="/tmp/gpf-gen-${TIMESTAMP}.tar.gz"

echo "[1/5] Packing repo scripts + configs to ${REPO_TAR}"
tar -czf "${REPO_TAR}" \
    -C "${REPO_ROOT}" \
    scripts/ src/ configs/ data/seed/ LICENSING.md ATTRIBUTION.txt docs/

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

USERDATA_FILE="/tmp/gpf-userdata-${TIMESTAMP}.sh"
cat > "${USERDATA_FILE}" <<EOF
#!/bin/bash
set -euxo pipefail
exec > /var/log/gpf-run.log 2>&1

RUN_TIMESTAMP="${TIMESTAMP}"
RUN_BUCKET="${BUCKET}"
RUN_REGION="${REGION}"
RUN_PREFIX="${RUN_PREFIX}"

# Two-layer data-persistence + termination safety net.
#
# Layer 1 — incremental checkpoints (\`_gpf_checkpoint\`): after each major
# pipeline stage that writes data to disk, sync \`data/processed/\` and
# \`artifacts/\` to S3. Idempotent (\`s3 sync\` skips identical content).
# Bounds the worst-case data loss to one stage's worth of work even if
# the instance is reclaimed mid-pipeline.
#
# Layer 2 — exit trap (\`_gpf_finalize\`): on ANY exit (clean success,
# \`set -e\` abort on error, SIGINT, SIGTERM from spot reclaim), sync any
# data + artifacts that exist on disk, upload logs, then terminate.
# Without the trap, a mid-pipeline Python error would exit the script
# before reaching the final upload step, leaving the EBS-resident data
# to be deleted with the instance and the spot rate billing until manual
# termination. \`InstanceInitiatedShutdownBehavior: terminate\` (set on
# the spot request) converts \`shutdown -h now\` into a real terminate.
#
# AWS spot reclaim sends a 2-minute warning, then SIGTERM. The
# \`EXIT INT TERM\` trap fires on SIGTERM in time to upload ~100 MB of
# data (a few seconds at S3 internal-network throughput).
_gpf_checkpoint() {
    local stage="\$1"
    set +e
    [ -d /opt/gpf/data/processed ] && aws s3 sync /opt/gpf/data/processed/ \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/data/" \\
        --region "\${RUN_REGION}" --only-show-errors || true
    [ -d /opt/gpf/artifacts ] && aws s3 sync /opt/gpf/artifacts/ \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/artifacts/" \\
        --region "\${RUN_REGION}" --only-show-errors || true
    echo "[checkpoint] stage=\${stage} synced to S3 at \$(date -u +%H:%M:%S)"
    set -e
}

_gpf_finalize() {
    local exit_code=\$?
    set +e
    [ -d /opt/gpf/data/processed ] && aws s3 sync /opt/gpf/data/processed/ \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/data/" \\
        --region "\${RUN_REGION}" --only-show-errors || true
    [ -d /opt/gpf/artifacts ] && aws s3 sync /opt/gpf/artifacts/ \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/artifacts/" \\
        --region "\${RUN_REGION}" --only-show-errors || true
    [ -f /tmp/run_metadata.json ] && aws s3 cp /tmp/run_metadata.json \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/run_metadata.json" \\
        --region "\${RUN_REGION}" || true
    aws s3 cp /var/log/gpf-run.log \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/gpf-run.log" \\
        --region "\${RUN_REGION}" || true
    [ -f /var/log/llama-server.log ] && aws s3 cp /var/log/llama-server.log \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/llama-server.log" \\
        --region "\${RUN_REGION}" || true
    echo "[trap] exit_code=\${exit_code}; instance terminating now"
    shutdown -h now
}
trap _gpf_finalize EXIT INT TERM

# Live log streaming: background process that re-uploads /var/log/gpf-run.log
# (and llama-server.log if present) to S3 every 30 seconds. Operator can
# `aws s3 cp s3://.../logs/gpf-run.live.log -` from local to follow progress.
( while true; do
    aws s3 cp /var/log/gpf-run.log \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/gpf-run.live.log" \\
        --region "\${RUN_REGION}" --quiet 2>/dev/null || true
    [ -f /var/log/llama-server.log ] && aws s3 cp /var/log/llama-server.log \\
        "s3://\${RUN_BUCKET}/\${RUN_PREFIX}/logs/llama-server.live.log" \\
        --region "\${RUN_REGION}" --quiet 2>/dev/null || true
    sleep 30
  done ) &

RUN_GIT_COMMIT="${GIT_COMMIT}"
SAMPLE_COUNT=${SAMPLE_COUNT}
HARDNEG_COUNT=${HARDNEG_COUNT}
QUANT="${QUANT}"
SEED_MAIN=${SEED_MAIN}
SEED_HARDNEG=${SEED_HARDNEG}
SEED_LATINIZE=${SEED_LATINIZE}
SEED_CURATE=${SEED_CURATE}

INSTANCE_ID="\$(curl -s http://169.254.169.254/latest/meta-data/instance-id || echo unknown)"

# 1. Basics
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3-pip unzip wget curl awscli jq

pip install -q --break-system-packages huggingface_hub datasets

# 2. Fetch repo tar + unpack
mkdir -p /opt/gpf
aws s3 cp "s3://\${RUN_BUCKET}/${REPO_KEY}" /opt/gpf/repo.tar.gz --region "\${RUN_REGION}"
tar -xzf /opt/gpf/repo.tar.gz -C /opt/gpf
cd /opt/gpf

# 3. Pull pre-built llama.cpp Docker image with CUDA. Upstream stopped
#    publishing static ubuntu-cuda binaries, and a from-source build of the
#    ggml-cuda backend takes 2-3 hours on a 4-vCPU instance because of
#    template-instance compile fan-out. Pulling the official Docker image
#    eliminates the build phase entirely.
LLAMACPP_BUILD="b8902"
LLAMACPP_IMAGE="ghcr.io/ggml-org/llama.cpp:server-cuda"

# Deep Learning Base GPU AMI ships Docker + nvidia-container-toolkit.
# Verify and install if missing (defensive).
if ! command -v docker >/dev/null 2>&1; then
    apt-get install -y --no-install-recommends docker.io
    systemctl enable --now docker
fi
if ! docker info 2>&1 | grep -q -i "nvidia"; then
    distribution="\$(. /etc/os-release; echo \${ID}\${VERSION_ID})"
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \\
        gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -fsSL "https://nvidia.github.io/libnvidia-container/\${distribution}/libnvidia-container.list" | \\
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \\
        > /etc/apt/sources.list.d/nvidia-container-toolkit.list
    apt-get update
    apt-get install -y nvidia-container-toolkit
    nvidia-ctk runtime configure --runtime=docker
    systemctl restart docker
fi

docker pull "\${LLAMACPP_IMAGE}"

# 4. Download Qwen3.6-35B-A3B Q<N> GGUF
mkdir -p /models
python3 -c "
from huggingface_hub import hf_hub_download
path = hf_hub_download(
    repo_id='unsloth/Qwen3.6-35B-A3B-GGUF',
    filename='Qwen3.6-35B-A3B-\${QUANT}.gguf',
    local_dir='/models',
)
print('downloaded', path)
"

# 5. Start llama-server inside Docker container with GPU access
GGUF=\$(ls /models/Qwen3.6-35B-A3B-*.gguf | head -1)
GGUF_NAME=\$(basename "\${GGUF}")
docker rm -f llama-server 2>/dev/null || true
docker run -d \\
    --gpus all \\
    --name llama-server \\
    -p 127.0.0.1:8080:8080 \\
    -v /models:/models:ro \\
    --restart no \\
    --log-driver json-file \\
    --log-opt max-size=50m --log-opt max-file=2 \\
    "\${LLAMACPP_IMAGE}" \\
    -m "/models/\${GGUF_NAME}" \\
    -ngl 99 -c 8192 \\
    --port 8080 --host 0.0.0.0 --jinja

# Stream container logs to the same file the trap uploads
( docker logs -f llama-server > /var/log/llama-server.log 2>&1 ) &

echo "Waiting for llama-server..."
until curl -sf http://127.0.0.1:8080/health >/dev/null; do sleep 3; done
echo "llama-server ready"

# 6. Download carrier corpora
cd /opt/gpf
mkdir -p data/raw data/processed artifacts/metrics artifacts/manifest

# Carrier download scripts use huggingface_hub which on some Python builds
# raises "Bad file descriptor" + "PyGILState_Release: auto-releasing thread
# state" during interpreter shutdown (exit code 134 / SIGABRT) AFTER the
# output file has been written successfully. We tolerate that crash but
# require the output JSONL to exist and be non-empty.
_run_dl() {
    local script="\$1"
    local out="\$2"
    shift 2
    set +e
    python3 "\$script" --output "\$out" "\$@"
    local rc=\$?
    set -e
    if [ ! -s "\$out" ]; then
        echo "[carrier-download] FAIL: \$out missing or empty (rc=\$rc)"
        return 1
    fi
    echo "[carrier-download] OK \$out (rc=\$rc, lines=\$(wc -l < "\$out"))"
}

_run_dl scripts/download_carrier_legal_code.py \\
    data/raw/greek_legal_sentences.jsonl --max-sentences 20000

_run_dl scripts/download_carrier_common_voice.py \\
    data/raw/common_voice_el_sentences.jsonl --max-sentences 8000

cat data/raw/greek_legal_sentences.jsonl data/raw/common_voice_el_sentences.jsonl \\
    > data/raw/blended_carriers.jsonl

# 7. Main synthetic generation (longest stage; check-point on completion)
python3 scripts/generate_commercial_safe_greek_pii.py \\
    --output data/processed/greek_v2_raw.jsonl \\
    --count "\${SAMPLE_COUNT}" --mode mix \\
    --ollama-host http://127.0.0.1:8080 --llm-engine openai \\
    --ollama-model "unsloth/Qwen3.6-35B-A3B-GGUF:\${QUANT}" \\
    --ollama-mode batch --ollama-batch-size 10 --ollama-fraction 0.5 \\
    --carrier-jsonl data/raw/blended_carriers.jsonl \\
    --seed "\${SEED_MAIN}"
_gpf_checkpoint "after_main_gen"

# 8. Latinize Greek-script email / URL spans
python3 scripts/postprocess_latinize_contacts.py \\
    --input data/processed/greek_v2_raw.jsonl \\
    --output data/processed/greek_v2_fixed.jsonl \\
    --seed "\${SEED_LATINIZE}" --keep-greek-ratio 0.2

# 9. Hard-negatives via Qwen (long; check-point on completion)
python3 scripts/generate_qwen_hard_negatives.py \\
    --output data/processed/hard_neg_qwen.jsonl \\
    --count "\${HARDNEG_COUNT}" --batch-size 10 \\
    --host http://127.0.0.1:8080 \\
    --seed "\${SEED_HARDNEG}"
_gpf_checkpoint "after_hard_negatives"

# 10. Merge
cat data/processed/greek_v2_fixed.jsonl data/processed/hard_neg_qwen.jsonl \\
    > data/processed/greek_v2_final.jsonl

# 11. Stratified curation
TRAIN_SIZE=\$(( SAMPLE_COUNT * 10000 / 14500 ))
VAL_SIZE=\$(( SAMPLE_COUNT * 1500 / 14500 ))
TEST_SIZE=\$(( SAMPLE_COUNT * 1500 / 14500 ))
HARD_SIZE=\$(( SAMPLE_COUNT * 1500 / 14500 ))

python3 scripts/curate_generated_dataset.py \\
    --input data/processed/greek_v2_final.jsonl \\
    --output-dir data/processed \\
    --train-size "\${TRAIN_SIZE}" \\
    --val-size "\${VAL_SIZE}" \\
    --test-size "\${TEST_SIZE}" \\
    --hard-size "\${HARD_SIZE}" \\
    --seed "\${SEED_CURATE}"
_gpf_checkpoint "after_curation"

# 12. Provenance + manifest
python3 scripts/verify_provenance.py \\
    --inputs data/processed/train.jsonl data/processed/validation.jsonl \\
             data/processed/test.jsonl data/processed/hard_test.jsonl

python3 scripts/hash_manifest.py \\
    --inputs data/processed/train.jsonl data/processed/validation.jsonl \\
             data/processed/test.jsonl data/processed/hard_test.jsonl
_gpf_checkpoint "after_manifest"

# 13. Run metadata
cat > /tmp/run_metadata.json <<META
{
  "run_id": "\${RUN_TIMESTAMP}",
  "instance_id": "\${INSTANCE_ID}",
  "instance_type": "${INSTANCE_TYPE}",
  "region": "\${RUN_REGION}",
  "git_commit": "\${RUN_GIT_COMMIT}",
  "quant": "\${QUANT}",
  "sample_count": \${SAMPLE_COUNT},
  "hardneg_count": \${HARDNEG_COUNT},
  "seeds": {
    "main": \${SEED_MAIN},
    "hardneg": \${SEED_HARDNEG},
    "latinize": \${SEED_LATINIZE},
    "curate": \${SEED_CURATE}
  },
  "llama_cpp_build": "\${LLAMACPP_BUILD}",
  "generator_model": "unsloth/Qwen3.6-35B-A3B-GGUF",
  "generated_at_utc": "\$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
META

# 14. Final checkpoint + shutdown
# All artefact uploads are handled by the _gpf_finalize EXIT trap
# defined at the top of this user-data script. The trap performs an
# \`s3 sync\` of /opt/gpf/data/processed/ and /opt/gpf/artifacts/ to the
# S3 run prefix, plus the run-metadata file and both log files, then
# runs \`shutdown -h now\`. The same trap fires on error or signal, so
# this is the single source of truth for upload + termination.
#
# We exit cleanly here so the trap fires its success path.
_gpf_checkpoint "before_shutdown"
exit 0
EOF

USERDATA_B64="$(base64 -w0 < "${USERDATA_FILE}")"

echo "[4/5] Requesting EC2 spot instance"

SPEC_FILE="/tmp/gpf-spot-spec-${TIMESTAMP}.json"
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
      "Ebs": {"VolumeSize": 200, "VolumeType": "gp3", "Iops": 16000, "Throughput": 1000, "DeleteOnTermination": true}
    }
  ],
  "TagSpecifications": [
    {
      "ResourceType": "instance",
      "Tags": [
        {"Key": "Name", "Value": "gpf-gen-${TIMESTAMP}"},
        {"Key": "Project", "Value": "greek-privacy-filter"},
        {"Key": "Purpose", "Value": "synthetic-data-generation"},
        {"Key": "GitCommit", "Value": "${GIT_COMMIT}"}
      ]
    }
  ]
}
EOF

if [ -n "${SSH_KEY_NAME:-}" ]; then
  python3 -c "import json; d=json.load(open('${SPEC_FILE}')); d['KeyName']='${SSH_KEY_NAME}'; json.dump(d, open('${SPEC_FILE}','w'))"
fi

# Pass spec inline instead of file:// — avoids POSIX-vs-Windows path
# resolution issues when the host shell is Git Bash but the AWS CLI is
# the Windows binary (which does not understand /tmp/...).
SPEC_JSON="$(cat "${SPEC_FILE}")"
INSTANCE_ID="$(aws ec2 run-instances --region "${REGION}" \
    --cli-input-json "${SPEC_JSON}" \
    --query 'Instances[0].InstanceId' --output text)"

echo "[5/5] Spot instance requested: ${INSTANCE_ID}"
echo
echo "Run ID: ${TIMESTAMP}"
echo "Git commit: ${GIT_COMMIT}"
echo "Outputs will land at: s3://${BUCKET}/${RUN_PREFIX}/"
echo "Expected layout (synced incrementally + at trap-fired exit):"
echo "  data/      train.jsonl / validation.jsonl / test.jsonl / hard_test.jsonl"
echo "             greek_v2_raw.jsonl / greek_v2_fixed.jsonl / hard_neg_qwen.jsonl"
echo "  artifacts/ metrics/curation_report.json / metrics/provenance_report.json"
echo "             manifest/manifest.json"
echo "  run_metadata.json (seeds, instance, git commit)"
echo "  logs/gpf-run.log + logs/llama-server.log"
echo
echo "Per-stage check-points fire after main-gen, hard-negatives, curation,"
echo "and manifest. The exit trap re-syncs everything on success or any"
echo "error/signal (including spot reclaim) before terminating the instance."
echo
echo "Instance auto-terminates on completion. To watch progress:"
echo "  aws ec2 describe-instances --region ${REGION} --instance-ids ${INSTANCE_ID} \\"
echo "    --query 'Reservations[0].Instances[0].State.Name' --output text"
echo
echo "Download to local after completion:"
echo "  aws s3 sync s3://${BUCKET}/${RUN_PREFIX}/ data/processed/aws-${TIMESTAMP}/ --region ${REGION}"

rm -f "${REPO_TAR}" "${SPEC_FILE}" "${USERDATA_FILE}"
