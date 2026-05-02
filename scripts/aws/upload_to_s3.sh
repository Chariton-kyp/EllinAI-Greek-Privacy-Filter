#!/usr/bin/env bash
# Upload Greek Privacy Filter data + base checkpoint to S3 in the
# layout expected by scripts/aws/sagemaker_train.py.
#
# Usage:
#   BUCKET=my-gpf-bucket PREFIX=greek-privacy-filter bash scripts/aws/upload_to_s3.sh
#
# Requires: aws CLI configured (aws configure) with write access to $BUCKET.
set -euo pipefail

BUCKET="${BUCKET:?Set BUCKET=your-s3-bucket}"
PREFIX="${PREFIX:-greek-privacy-filter}"
REGION="${REGION:-us-east-1}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATA="${DATA:-${REPO_ROOT}/data/processed}"
CKPT="${REPO_ROOT}/checkpoints/base/privacy-filter"
LABELS="${LABELS:-${REPO_ROOT}/configs/label_space.json}"

for required in \
  "${DATA}/train.jsonl" \
  "${DATA}/validation.jsonl" \
  "${DATA}/test.jsonl" \
  "${LABELS}" \
  "${CKPT}"; do
  if [ ! -e "${required}" ]; then
    echo "Missing: ${required}" >&2
    exit 2
  fi
done

echo "Region: ${REGION}"
echo "Bucket: s3://${BUCKET}/${PREFIX}"
echo "Labels: ${LABELS}"

aws s3 cp  "${DATA}/train.jsonl"       "s3://${BUCKET}/${PREFIX}/data/train/train.jsonl"           --region "${REGION}"
aws s3 cp  "${DATA}/validation.jsonl"  "s3://${BUCKET}/${PREFIX}/data/validation/validation.jsonl" --region "${REGION}"
aws s3 cp  "${DATA}/test.jsonl"        "s3://${BUCKET}/${PREFIX}/data/test/test.jsonl"             --region "${REGION}"
aws s3 cp  "${LABELS}"                 "s3://${BUCKET}/${PREFIX}/data/labels/label_space.json"     --region "${REGION}"
aws s3 sync "${CKPT}/"                 "s3://${BUCKET}/${PREFIX}/checkpoint/"                      --region "${REGION}" --exclude '*.git*'

echo "Done. Point sagemaker_train.py at --bucket ${BUCKET} --prefix ${PREFIX}"
