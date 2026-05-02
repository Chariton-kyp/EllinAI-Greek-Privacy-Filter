# v3 AWS handoff runbook

This document is the operator runbook for executing the v3 distillation
pipeline on AWS spot from Claude Code desktop. The laptop running data
generation can be closed at night; everything that follows runs on EC2
spot in `eu-north-1b`.

## State at handoff

| asset | location | status |
|---|---|---|
| v3 chat-format SFT data (144,372 records) | `s3://YOUR-GPF-BUCKET/assembled/v3_chat/` | ✅ uploaded |
| v3.13 OOD-benchmark champion checkpoint | `s3://YOUR-GPF-BUCKET/finetune/run-20260501T202431Z/` | ✅ in S3 |
| Greek corpus | will be downloaded on AWS during pseudo-label stage | ⏳ |
| Teacher LoRA adapter | will be produced by stage 1 | ⏳ |
| Pseudo-labels | will be produced by stage 2 | ⏳ |
| Student LoRA adapters (mini/pro/max) | will be produced by stage 3 | ⏳ |

## Repo state

All scripts and configs are committed at HEAD on `main`:

- `scripts/v3/convert_opf_to_chat.py` — already executed, output uploaded
- `scripts/v3/load_greek_corpus.py` — runs on AWS, fetches commercial-clean Greek text
- `scripts/v3/train_teacher.py` — Unsloth LoRA Q4 SFT trainer
- `scripts/v3/generate_pseudo_labels.py` — runs against vLLM endpoint
- `scripts/v3/train_student_distill.py` — parametrised student SFT
- `scripts/v3/benchmark_tiers.py` — final 5-tier OOD comparison
- `scripts/aws/ec2_v3_teacher.sh` — Stage 1 launcher
- `scripts/aws/ec2_v3_pseudo.sh` — Stage 2 launcher (corpus + pseudo-label)
- `scripts/aws/ec2_v3_distill.sh` — Stage 3 launcher (per tier)
- `configs/v3_distillation.yaml` — hyperparameters + tier definitions
- `requirements-unsloth.txt` — training deps (all Apache 2.0 / MIT)
- `docs/V3_DISTILLATION_PLAN.md` — architecture + license audit

## Required environment variables (every stage)

```bash
export BUCKET=YOUR-GPF-BUCKET
export IAM_INSTANCE_PROFILE=GreekPrivacyFilter-EC2
export AWS_REGION=eu-north-1
export AVAIL_ZONE=eu-north-1b   # confirmed capacity
```

## Pipeline stages — run in order

### Stage 1 — Teacher SFT (~12 h, $7-8 spot)

Trains gemma-4-31B-it via Unsloth LoRA Q4 SFT on the v3 chat data.

```bash
# Optional pilot first to verify pipeline (~30 min, $0.30):
MAX_TRAIN_SAMPLES=500 \
TEACHER_HF_ID=google/gemma-4-31B-it \
INSTANCE_TYPE=g6e.xlarge \
MARKET_TYPE=spot \
bash scripts/aws/ec2_v3_teacher.sh

# Full run after pilot is green:
TEACHER_HF_ID=google/gemma-4-31B-it \
INSTANCE_TYPE=g6e.xlarge \
MARKET_TYPE=spot \
bash scripts/aws/ec2_v3_teacher.sh
```

Output: `s3://${BUCKET}/v3/teacher/run-<TIMESTAMP>/artifacts/run-<TS>/lora_adapters/`

Tail log:
```bash
aws s3 cp s3://${BUCKET}/v3/teacher/run-<TS>/logs/gpf-v3-teacher.live.log - --region ${AWS_REGION}
```

The instance auto-terminates on completion (EXIT trap) — `shutdown -h now`.

### Stage 2 — Greek corpus + pseudo-labels (~6-10 h, $4-6 spot)

Downloads commercial-clean Greek corpus (PleIAs/Greek-PD + Common Voice + greek_legal_code), serves trained teacher via vLLM, generates pseudo-labels.

```bash
# Note the TEACHER_S3_PREFIX from Stage 1 output
TEACHER_S3_PREFIX=v3/teacher/run-<TS>/artifacts \
TEACHER_HF_ID=google/gemma-4-31B-it \
CORPUS_TARGET_RECORDS=500000 \
INSTANCE_TYPE=g6e.xlarge \
MARKET_TYPE=spot \
bash scripts/aws/ec2_v3_pseudo.sh
```

Output: `s3://${BUCKET}/v3/pseudo/run-<TS>/pseudo_labels.jsonl`

### Stage 3 — Student distillation (4 parallel, ~2-3 h each, $1-2 total spot)

Distills 3 causal-LM students in parallel + Lite tier separately.

```bash
# Confirm pseudo-label S3 prefix from Stage 2
export V3_PSEUDO_S3_PREFIX=v3/pseudo/run-<TS>

# Mini (gemma-4-E2B)
V3_TIER=mini  INSTANCE_TYPE=g6.xlarge MARKET_TYPE=spot \
  bash scripts/aws/ec2_v3_distill.sh

# Pro (gemma-4-E4B)
V3_TIER=pro   INSTANCE_TYPE=g6.xlarge MARKET_TYPE=spot \
  bash scripts/aws/ec2_v3_distill.sh

# Max (Qwen3-4B)
V3_TIER=max   INSTANCE_TYPE=g6.xlarge MARKET_TYPE=spot \
  bash scripts/aws/ec2_v3_distill.sh

# Lite (privacy-filter 1.4B token-classifier — uses different trainer)
# Reuses existing scripts/aws/ec2_spot_finetune.sh with v3 dataset.
DATASET_S3_PREFIX=assembled/v3_chat \
V1_RUN_ID=20260426T092703Z \
INSTANCE_TYPE=g6.xlarge MARKET_TYPE=spot \
bash scripts/aws/ec2_spot_finetune.sh
```

Each instance auto-terminates on completion.

### Stage 4 — Benchmark all tiers

After all student adapters land in S3:

```bash
# Sync all adapters back to laptop (or run on a small CPU spot if laptop closed)
mkdir -p artifacts/v3
aws s3 sync s3://${BUCKET}/v3/students/ artifacts/v3/students/ --region ${AWS_REGION}
aws s3 sync s3://${BUCKET}/v3/teacher/  artifacts/v3/teacher/  --region ${AWS_REGION}

# Serve each via vLLM locally or on a g6e.xlarge, then run:
python scripts/v3/benchmark_tiers.py \
  --benchmark data/realworld_benchmark/cases.jsonl \
  --tiers '[{"name":"mini","kind":"causal-lm","host":"http://localhost:8080","model":"mini"}, ...]' \
  --output artifacts/metrics/benchmark_v3_tiers.json
```

Lite tier benchmarked separately via existing `scripts/run_benchmark_triage.py`.

## Cost summary

| stage | instance | duration | $/h | cost |
|---|---|---|---|---|
| Pilot teacher SFT (500 samples) | g6e.xlarge spot | ~30 min | 0.63 | ~$0.30 |
| Full teacher SFT | g6e.xlarge spot | ~12 h | 0.63 | $7-8 |
| Corpus + pseudo-labels | g6e.xlarge spot | ~6-10 h | 0.63 | $4-6 |
| Student × 3 (mini/pro/max) | g6.xlarge spot × 3 | ~2-3 h each | 0.25 | $2-3 |
| Lite token-classifier finetune | g6.xlarge spot | ~2 h | 0.25 | $0.50 |
| Benchmark (CPU spot or local) | t3.large or local | 1 h | 0.08 | $0.10 |
| **Total** | | ~25 h | | **$15-20** |

## License chain reminder

All bases Apache 2.0. All datasets PD/CC0/CC-BY (no Wikipedia SA, no mC4). Final weights ship under existing dual-licence (NC + commercial-for-owner). See `docs/V3_DISTILLATION_PLAN.md` §4 for full audit.

## Failure modes + recovery

| failure | symptom | recovery |
|---|---|---|
| Spot capacity rejected | `InsufficientInstanceCapacity` | switch `MARKET_TYPE=ondemand` (~$1.05/h) |
| AZ-specific shortage | Stage launches fail in 1b | try `AVAIL_ZONE=eu-north-1a` |
| OOM during teacher SFT | training crashes mid-step | reduce `per_device_batch_size` to 2 in yaml |
| pseudo-labels script slow | <50 records/min on vLLM | reduce `CORPUS_TARGET_RECORDS` to 100k pilot |
| Spot interrupt mid-train | unexpected termination | rerun Stage 1; logs preserved in S3 |
| Wrong teacher_id | pseudo-label gen fails | confirm `TEACHER_HF_ID` matches what teacher was trained with |

## Continuous monitoring (laptop closed)

Each instance writes live logs to S3 every 30 seconds. From any device:

```bash
aws s3 cp s3://${BUCKET}/v3/teacher/run-<TS>/logs/gpf-v3-teacher.live.log - --region eu-north-1 | tail -30
aws ec2 describe-instances --region eu-north-1 --instance-ids <ID>
```

Instances auto-terminate on completion. No need to manually stop them.

## Quickstart for next operator (Claude Code desktop)

```bash
# 1. Verify env
echo "$BUCKET $IAM_INSTANCE_PROFILE $AWS_REGION"
aws sts get-caller-identity

# 2. Pilot teacher (cheap, fast verification)
MAX_TRAIN_SAMPLES=500 bash scripts/aws/ec2_v3_teacher.sh

# 3. Watch
aws s3 cp s3://${BUCKET}/v3/teacher/<latest-run>/logs/gpf-v3-teacher.live.log - --region eu-north-1 | tail

# 4. If pilot OK: full run
bash scripts/aws/ec2_v3_teacher.sh

# 5. After Stage 1 done: launch Stage 2
TEACHER_S3_PREFIX=v3/teacher/<TS>/artifacts bash scripts/aws/ec2_v3_pseudo.sh

# 6. After Stage 2 done: launch Stage 3 (4 parallel)
V3_TIER=mini bash scripts/aws/ec2_v3_distill.sh &
V3_TIER=pro  bash scripts/aws/ec2_v3_distill.sh &
V3_TIER=max  bash scripts/aws/ec2_v3_distill.sh &
DATASET_S3_PREFIX=assembled/v3_chat V1_RUN_ID=20260426T092703Z bash scripts/aws/ec2_spot_finetune.sh &
wait

# 7. Benchmark
python scripts/v3/benchmark_tiers.py ...
```
