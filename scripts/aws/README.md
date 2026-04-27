# AWS operator guide — Greek Privacy Filter

Three independent AWS workflows live here:

| Workflow | Entry point | Purpose |
|---|---|---|
| **Synthetic data generation** | `ec2_spot_generate.sh` | Spin up an EC2 spot GPU, run the full pipeline (Qwen-batch → latinize → hard-neg → curate → audit), upload artefacts to S3, self-terminate. |
| **Fine-tuning (EC2 spot)** | `ec2_spot_finetune.sh` | Spin up an EC2 spot GPU, run baseline-eval + train + finetuned-eval against the v1 splits and the upstream `openai/privacy-filter` checkpoint, upload artefacts to S3, self-terminate. **This is the path actually used for the v1 release.** |
| **Fine-tuning (SageMaker)** | `sagemaker_train.py` | Alternative managed-training path against the pinned OPF stack on the curated data. Reserved for hyper-parameter sweeps and large-scale runs. |

The flows are chained manually: generate with #1 → download + verify
locally → run #2 (or #3).

---

## Part A — Synthetic data generation (`ec2_spot_generate.sh`)

### A.1 One-off AWS setup

```bash
# 1. Bucket
aws s3 mb s3://your-gpf-bucket --region us-east-1

# 2. IAM role + instance profile for the EC2 that will run the pipeline
aws iam create-role --role-name your-iam-role \
    --assume-role-policy-document '{
      "Version":"2012-10-17",
      "Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]
    }'
aws iam put-role-policy --role-name your-iam-role \
    --policy-name your-inline-policy \
    --policy-document file://scripts/aws/iam_policy_ec2_gen.json
aws iam create-instance-profile --instance-profile-name your-iam-role
aws iam add-role-to-instance-profile \
    --instance-profile-name your-iam-role \
    --role-name your-iam-role
```

Adjust the ARN `YOUR-GPF-BUCKET` in
`scripts/aws/iam_policy_ec2_gen.json` before applying.

### A.2 Launch a run

```bash
export BUCKET=your-gpf-bucket
export IAM_INSTANCE_PROFILE=your-iam-role
export AWS_REGION=us-east-1
# optional:
# export INSTANCE_TYPE=g6e.xlarge   # L40S 48GB (default) or g5.2xlarge
# export SAMPLE_COUNT=100000
# export QUANT=UD-Q8_K_XL            # or UD-Q4_K_S for faster/cheaper
# export SPOT_MAX_PRICE=1.00

bash scripts/aws/ec2_spot_generate.sh
```

The script prints the run ID, instance ID, git commit, and the S3
prefix under which every artefact will land. The instance auto-terminates
on completion.

### A.3 Download + audit locally

```bash
aws s3 sync "s3://${BUCKET}/generated/run-<RUN_ID>/" \
    "data/processed/aws-<RUN_ID>/" --region "${AWS_REGION}"
```

Layout under each run prefix:

```
s3://${BUCKET}/generated/run-<RUN_ID>/
├── data/
│   ├── train.jsonl, validation.jsonl, test.jsonl, hard_test.jsonl
│   └── greek_v2_raw.jsonl, greek_v2_fixed.jsonl, hard_neg_qwen.jsonl
├── artifacts/
│   ├── metrics/curation_report.json, provenance_report.json
│   └── manifest/manifest.json
├── run_metadata.json   ← run ID, instance ID, git commit, seeds, model, quant
└── logs/gpf-run.log, llama-server.log
```

Data persistence guarantees: the user-data script syncs `data/` and
`artifacts/` to this prefix incrementally after each long-running stage
(main generation, hard negatives, curation, manifest), and again from
its EXIT/INT/TERM trap on any termination path including spot reclaim.
Worst-case data loss is therefore bounded to one stage's worth of
work; a clean run produces all artefacts above.

### A.4 Cost envelope

| Instance | VRAM | Spot $/h | 100k ETA | 100k cost |
|---|---:|---:|---:|---:|
| `g5.2xlarge` (A10G) | 24 GB | ~$0.50 | ~5 h | ~$2.50 |
| `g6e.xlarge` (L40S) | 48 GB | ~$0.70 | ~2 h | ~$1.50 |

Default: `g6e.xlarge` (Q8 fits fully in VRAM, no offload penalty).

---

## Part B — Fine-tuning, EC2 spot path (`ec2_spot_finetune.sh`)

This is the path used for the v1 release on 2026-04-26 (run
`20260426T135853Z`).

### B.1 One-off setup beyond Part A

The same IAM role and bucket created in Part A are re-used; the
inline policy `your-inline-policy` already grants `s3:GetObject` on
`generated/*` and `checkpoints/*` plus `s3:GetObject` /
`s3:PutObject` on `finetune/*`. Two artefacts are uploaded once:

```bash
# 1. Base checkpoint (download with huggingface-cli or pip-installed opf
#    locally first; then sync to S3).
aws s3 sync checkpoints/base/privacy-filter/ \
    s3://${BUCKET}/checkpoints/base/privacy-filter/ \
    --region ${AWS_REGION} --exclude '.cache/*'

# 2. Label space (12 PII + O).
aws s3 cp configs/label_space.json \
    s3://${BUCKET}/finetune/label_space.json --region ${AWS_REGION}
```

### B.2 Launch a fine-tune

```bash
export BUCKET=your-gpf-bucket
export IAM_INSTANCE_PROFILE=your-iam-role
export AWS_REGION=eu-north-1
export V1_RUN_ID=20260426T092703Z   # whichever generation run you want to train against

bash scripts/aws/ec2_spot_finetune.sh
```

The script prints the run ID, instance ID, git commit, the dataset
S3 path it will pull from, and the S3 prefix under which every
artefact will land. The instance auto-terminates on completion.

### B.2.1 Training against a relabelled or blended dataset

Set `DATASET_S3_PREFIX` to override the default
`generated/run-${V1_RUN_ID}/data` path. Useful for fine-tuning
against the AFM-relabelled v1.1 splits (produced locally by
`scripts/relabel_afm_spans.py` and uploaded to S3) or against a
blended dataset assembled from multiple generation runs.

```bash
# Upload the v1.1 splits once
aws s3 cp data/processed/v1_1/ \
    s3://${BUCKET}/relabelled/v1_1/ --recursive --region ${AWS_REGION}

# Train against them
export DATASET_S3_PREFIX=relabelled/v1_1
bash scripts/aws/ec2_spot_finetune.sh
```

`V1_RUN_ID` is still required (the launcher uses it as a tag in
`run_metadata.json`) but the JSONL splits will come from the
override prefix instead.

### B.3 Layout under each run prefix

```
s3://${BUCKET}/finetune/run-<RUN_ID>/
├── artifacts/
│   ├── metrics/baseline_test_metrics.json
│   ├── metrics/baseline_hard_test_metrics.json
│   ├── metrics/finetuned_test_metrics.json
│   ├── metrics/finetuned_hard_test_metrics.json
│   └── logs/train.log
├── model/
│   ├── model.safetensors             ← fine-tuned weights (~2.6 GB)
│   ├── config.json
│   ├── label_space.json
│   ├── finetune_summary.json
│   └── USAGE.txt
├── run_metadata.json                 ← run ID, instance ID, git commit, hyperparameters
└── logs/gpf-ft.log
```

### B.4 Sync locally and inspect

```bash
aws s3 sync "s3://${BUCKET}/finetune/run-<RUN_ID>/" \
    "data/processed/aws-ft-<RUN_ID>/" --region "${AWS_REGION}"
```

### B.5 Cost envelope

| Phase | Wall-clock on g6e.xlarge |
|---|---:|
| Boot + apt + pip + git clone opf + pull data/ckpt | ~6 min |
| Baseline eval (test 3,171 + hard_test 4,593) | ~5 min |
| Train (3 epochs × 21,124 records, bs=4 gas=4) | ~6 min |
| Finetuned eval | ~2 min |
| **Total** | **~19 min, ~$0.27** |

Re-running on `g5.xlarge` (A10G 24 GB) is feasible but tighter on
VRAM headroom; `g6e.xlarge` (L40S 48 GB) is the conservative default.

### B.6 Two CLI mismatches to be aware of

`opf eval` does **not** accept `--label-space-json`; only `train`
does. `opf eval --eval-mode typed` requires the checkpoint label
scheme to match the dataset; the unmodified base checkpoint contains
the upstream 33-class set without the four Greek extensions, so
baseline eval is forced to `--eval-mode untyped`. The launcher
already handles both.

---

## Part C — Fine-tuning, SageMaker path (`sagemaker_train.py`)

### C.1 One-off setup

```powershell
pip install "sagemaker>=2.224" boto3
aws configure
```

Create a SageMaker execution role (`AmazonSageMaker-ExecutionRole-*`)
with `AmazonSageMakerFullAccess` plus an S3 policy scoped to your
training bucket. Copy the role ARN.

### C.2 Upload curated data + base checkpoint

```powershell
$env:BUCKET="YOUR-GPF-BUCKET"
bash scripts/aws/upload_to_s3.sh
```

Uploads:

```
s3://BUCKET/greek-privacy-filter/data/train/train.jsonl
s3://BUCKET/greek-privacy-filter/data/validation/validation.jsonl
s3://BUCKET/greek-privacy-filter/data/test/test.jsonl
s3://BUCKET/greek-privacy-filter/data/labels/label_space.json
s3://BUCKET/greek-privacy-filter/checkpoint/...      (base HF checkpoint)
```

### C.3 Smoke test (1 epoch, ~$0.20)

```powershell
python scripts/aws/sagemaker_train.py `
    --role arn:aws:iam::123456789012:role/AmazonSageMaker-ExecutionRole-xxxx `
    --bucket YOUR-GPF-BUCKET --use-spot `
    --epochs 1 --skip-test-eval
```

Watch CloudWatch logs; kill on `loss=nan` or label-mismatch.

### C.4 Full fine-tune

```powershell
python scripts/aws/sagemaker_train.py `
    --role arn:aws:iam::123456789012:role/AmazonSageMaker-ExecutionRole-xxxx `
    --bucket YOUR-GPF-BUCKET --use-spot `
    --epochs 3 --learning-rate 5e-5 --n-ctx 256
```

Final `model.tar.gz` lands at
`s3://BUCKET/greek-privacy-filter/output/<job-name>/output/model.tar.gz`.

### C.5 Cost notes

- `ml.g5.xlarge` spot ≈ $0.40–0.55/h.
- Per full run (3 epochs, ~8k examples): ≈$0.70–$1.50.
- Spot interruption: SageMaker auto-resumes if `max_wait > max_run`.
- Region: stay in `us-east-1`.
- CloudWatch logs: free up to 5 GB/month under
  `/aws/sagemaker/TrainingJobs`.

### C.6 Hyperparameter sweep (~$20 for 9-cell grid)

```bash
for lr in 2e-5 5e-5 1e-4; do
  for ep in 2 3 5; do
    python scripts/aws/sagemaker_train.py \
        --role "$ROLE" --bucket "$BUCKET" --use-spot \
        --learning-rate "$lr" --epochs "$ep" \
        --job-name "gpf-lr${lr}-ep${ep}"
  done
done
```

Compare the `finetuned_test_metrics.json` per job.
