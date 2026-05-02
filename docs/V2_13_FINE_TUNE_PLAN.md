# v2.13 Fine-Tune Plan

Goal: improve the single fine-tuned OPF model only, without cascade layers
and without using OpenAI output as bulk training data.

## Guardrails

- Use `configs/label_space_v2.json` for every 24-class v2 run.
- Keep generated training records produced by local, commercial-safe
  generators only.
- Use OpenAI/Codex assistance for code, analysis, prompts, validation, and
  tooling, not as the source of the released training corpus.
- Keep the locked 200-case OOD benchmark fixed. Add data based on failure
  classes and failure types, not copied benchmark text.

## Current v2.12 Priorities

Generated from:

```bash
python scripts/mine_benchmark_failures.py \
  --triage artifacts/metrics/benchmark_triage_v2_12.json
```

Top measured priorities:

1. `private_person`: 32 missed, 8 boundary, 2 confusion.
2. `private_email`: 14 missed, 3 boundary, 2 confused as `secret`.
3. `private_phone`: 7 confused as `account_number`, 6 missed.
4. `amka`: 11 missed.
5. `afm`: 8 missed.
6. `ip_address`: 6 missed.
7. `mac_address`: 3 confusions, 2 boundary issues.

Full report:

- `artifacts/metrics/failure_mining_v2_12.json`
- `artifacts/metrics/failure_mining_v2_12.md`

## v2.13 Pack Order

### Local Qwen server

Claude's earlier successful setup used `llama.cpp` Docker, not Ollama, for
this GGUF. The server should expose the OpenAI-compatible API on
`127.0.0.1:8080`.

```bash
docker run -d \
  --gpus all \
  --name llama-server \
  -p 127.0.0.1:8080:8080 \
  -v /path/to/models:/models:ro \
  ghcr.io/ggml-org/llama.cpp:server-cuda \
  -m /models/Qwen3.6-35B-A3B-UD-Q4_K_S.gguf \
  -ngl 99 -c 8192 \
  --port 8080 --host 0.0.0.0 --jinja

curl -sf http://127.0.0.1:8080/health
```

If the model is actually served by Ollama instead, use `--engine ollama`,
`--host http://127.0.0.1:11434`, and the exact Ollama model tag.

Run these as separate ablations. Do not merge every pack at once until each
has been evaluated.

Start with a 40-record smoke pack before the 500+ record ablations:

```bash
python scripts/data_packs/generate_qwen_contrastive_v2_13_pack.py \
  --engine openai \
  --host http://127.0.0.1:8080 \
  --model qwen \
  --pack phone_account \
  --output data/processed/v2_13_smoke_phone_account.jsonl \
  --target-count 40 \
  --batch-size 4
```

```bash
python scripts/data_packs/generate_qwen_contrastive_v2_13_pack.py \
  --engine openai \
  --pack phone_account \
  --output data/processed/v2_13_phone_account.jsonl \
  --target-count 500 \
  --host http://127.0.0.1:8080

python scripts/data_packs/generate_qwen_contrastive_v2_13_pack.py \
  --engine openai \
  --pack email_secret \
  --output data/processed/v2_13_email_secret.jsonl \
  --target-count 500 \
  --host http://127.0.0.1:8080

python scripts/data_packs/generate_qwen_contrastive_v2_13_pack.py \
  --engine openai \
  --pack mac_ip_vin \
  --output data/processed/v2_13_mac_ip_vin.jsonl \
  --target-count 500 \
  --host http://127.0.0.1:8080

python scripts/data_packs/generate_qwen_contrastive_v2_13_pack.py \
  --engine openai \
  --pack person_admin_dense \
  --output data/processed/v2_13_person_admin_dense.jsonl \
  --target-count 800 \
  --host http://127.0.0.1:8080
```

## Validation

```bash
python scripts/validate_label_space.py \
  --label-space configs/label_space_v2.json \
  --inputs data/processed/v2_combined/train.jsonl \
           data/processed/v2_combined/validation.jsonl
```

The same validator should fail if a v2 dataset is checked against
`configs/label_space.json`, which only covers the original 12 classes.

## Training

Use the v2 config so the 24-class label space is explicit:

```bash
python scripts/run_opf_train.py --config configs/fine_tune_config_v2.yaml
python scripts/run_benchmark_triage.py \
  --checkpoint artifacts/model/finetuned-opf-v2 \
  --metrics-out artifacts/metrics/benchmark_triage_v2_13.json
```

Selection rule: keep a pack only if the locked OOD benchmark improves or if
it fixes a target failure without a larger regression in another class.

## Local Generation Run Notes

2026-05-01 local RTX 4080 Laptop run through Docker `llama.cpp`:

- `data/processed/v2_13_phone_account.jsonl`: 500 records, validated,
  provenance OK. Generation: 500 accepted, 1 skipped, 22.1 minutes.
- `data/processed/v2_13_email_secret.jsonl`: 500 records, validated,
  provenance OK. Generation: 500 accepted, 2 skipped, 23.5 minutes.
- `data/processed/v2_13_mac_ip_vin.jsonl`: 365 records, validated,
  provenance OK, but do not use directly yet. Quality audit found 74 rows
  containing copied internal label names such as `mac_address`, `ip_address`,
  and `vehicle_vin`.

After the MAC/IP/VIN issue, the v2.13 generator was updated to show
human-readable Greek field names in prompts and to support `--resume` plus
`--max-tokens`. Regenerate or filter the MAC/IP/VIN pack before training.
