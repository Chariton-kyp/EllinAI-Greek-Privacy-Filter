# AWS SageMaker fine-tuning

End-to-end flow for fine-tuning the Greek Privacy Filter on a managed
GPU instance with your $100 AWS credit.

## 1. One-time AWS setup

```powershell
pip install "sagemaker>=2.224" boto3
aws configure                  # access key, secret, region=us-east-1
```

You also need an IAM role that SageMaker can assume. Create
`AmazonSageMaker-ExecutionRole-*` in the IAM console with:

* Trust policy: Service principal `sagemaker.amazonaws.com`
* Attached policies: `AmazonSageMakerFullAccess`, an S3 policy limited
  to your training bucket.

Copy the role ARN — you'll pass it as `--role`.

Create an S3 bucket in `us-east-1` (cheapest egress):

```powershell
aws s3 mb s3://YOUR-GPF-BUCKET --region us-east-1
```

## 2. Upload data + base checkpoint

```powershell
$env:BUCKET="YOUR-GPF-BUCKET"
bash scripts/aws/upload_to_s3.sh
```

This uploads:

```
s3://BUCKET/greek-privacy-filter/data/train/train.jsonl
s3://BUCKET/greek-privacy-filter/data/validation/validation.jsonl
s3://BUCKET/greek-privacy-filter/data/test/test.jsonl
s3://BUCKET/greek-privacy-filter/data/labels/label_space.json
s3://BUCKET/greek-privacy-filter/checkpoint/...      (base HF checkpoint)
```

## 3. Smoke test (1 epoch, 500 examples, ~$0.20)

```powershell
python scripts/aws/sagemaker_train.py `
    --role arn:aws:iam::123456789012:role/AmazonSageMaker-ExecutionRole-xxxx `
    --bucket YOUR-GPF-BUCKET `
    --use-spot `
    --epochs 1 `
    --skip-test-eval
```

Watch the CloudWatch logs SageMaker links in its output. Kill the run if
you see the infamous `loss=nan` or `label mismatch` messages (see §6).

## 4. Full run

```powershell
python scripts/aws/sagemaker_train.py `
    --role arn:aws:iam::123456789012:role/AmazonSageMaker-ExecutionRole-xxxx `
    --bucket YOUR-GPF-BUCKET `
    --use-spot `
    --epochs 3 `
    --learning-rate 5e-5 `
    --n-ctx 256
```

Final `model.tar.gz` lands at
`s3://BUCKET/greek-privacy-filter/output/<job-name>/output/model.tar.gz`.
Download, extract, and point `opf redact --checkpoint` at the extracted
directory.

## 5. Hyperparameter sweep (optional, ~$20)

Run the loop in PowerShell / bash:

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

Compare `finetuned_test_metrics.json` produced by each job.

## 6. Cost & troubleshooting notes

* **Instance:** `ml.g5.xlarge` (1× A10G, 24 GB). Spot price fluctuates
  around $0.40-0.55/hour in us-east-1.
* **Per run cost (3 epochs, bs=4, gas=4, n_ctx=256, 8k examples):**
  ≈$0.70-$1.50. Your $100 = ~20 runs with headroom for a second
  iteration after you expand the dataset.
* **Region:** stay in `us-east-1`. Data transfer out to other regions
  or the internet is billed separately.
* **Spot interruptions:** SageMaker resumes automatically if
  `max_wait > max_run`. The defaults (`max_run=3h`, `max_wait=6h`)
  leave comfortable headroom.
* **OOM on g5.xlarge?** Drop `batch-size` to 2 and raise
  `grad-accum-steps` to 8 (effective batch stays 16).
* **CloudWatch logs** are free for the first 5 GB/month; watch the
  `/aws/sagemaker/TrainingJobs` log group.
