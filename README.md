# Greek Privacy Filter Fine-Tuning Repository

Repository για fine-tuning του OpenAI Privacy Filter με pinned upstream code + pinned Hugging Face checkpoint για reproducible runs.

## Project documentation

| File | Contents |
|---|---|
| `docs/DATASHEET.md` | Dataset record (Gebru et al. template) — sources, preprocessing, class distribution |
| `docs/MODEL_CARD.md` | Model record (Mitchell et al. template) — intended use, HITL requirement, metrics (post-fine-tune) |
| `docs/AUDIT_LOG.md` | Chronological build ledger with commit hashes |
| `docs/DPIA_NOTE.md` | GDPR data-protection note for deployers |
| `docs/GDPR_ART30_ROPA.md` | GDPR Article 30 Record-of-Processing-Activities template |
| `docs/EU_AI_ACT_ANNEX_IV.md` | EU AI Act Article 11 / Annex IV mapping |
| `docs/AIMS_STATEMENT.md` | ISO/IEC 42001:2023 AI management system statement |
| `docs/NIST_AI_RMF.md` | NIST AI Risk Management Framework 1.0 mapping |
| `LICENSING.md` | Licence chain for every component, commercial licence procedure |
| `ATTRIBUTION.txt` | Attribution block to ship with the weights |
| `NOTICE` | Apache 2.0 §4(d) NOTICE file |
| `SECURITY.md` | Vulnerability-disclosure process |
| `artifacts/metrics/provenance_report.json` | Per-split record-provenance audit (run `scripts/verify_provenance.py`) |
| `artifacts/manifest/manifest.json` | SHA-256 + line-count manifest (run `scripts/hash_manifest.py`) |

## End-to-end reproducible build

```powershell
# 1. Pull the synthetic-data generator (runs locally on CUDA)
ollama pull hf.co/unsloth/Qwen3.6-35B-A3B-GGUF:UD-Q4_K_S

# 2. Start llama-server (CUDA + CPU-MoE offload)
./external/llama.cpp/llama-server.exe `
    -m "$env:USERPROFILE\.ollama\models\blobs\sha256-<blob>" `
    -ngl 99 -c 8192 --port 8080 --host 127.0.0.1 --jinja --n-cpu-moe 40

# 3. Download carrier corpora (Greek legal + Common Voice EL)
python scripts/download_carrier_legal_code.py --max-sentences 10000 `
    --output data/raw/greek_legal_sentences.jsonl
python scripts/download_carrier_common_voice.py --max-sentences 5000 `
    --output data/raw/common_voice_el_sentences.jsonl
Get-Content data/raw/greek_legal_sentences.jsonl, `
            data/raw/common_voice_el_sentences.jsonl |
    Set-Content data/raw/blended_carriers.jsonl

# 4. Generate the main corpus (Qwen batched + rule + carrier + template)
python scripts/generate_commercial_safe_greek_pii.py `
    --output data/processed/greek_v2_raw.jsonl `
    --count 14500 --mode mix `
    --ollama-host http://127.0.0.1:8080 --llm-engine openai `
    --ollama-mode batch --ollama-batch-size 10 --ollama-fraction 0.5 `
    --carrier-jsonl data/raw/blended_carriers.jsonl --seed 2024

# 5. Latinize Greek-script email/URL spans (deterministic, reproducible)
python scripts/postprocess_latinize_contacts.py `
    --input data/processed/greek_v2_raw.jsonl `
    --output data/processed/greek_v2_fixed.jsonl --seed 1337

# 6. Generate diverse hard negatives via Qwen
python scripts/generate_qwen_hard_negatives.py `
    --output data/processed/hard_neg_qwen.jsonl --count 1500 --seed 2024

# 7. Merge + curate into balanced splits
Get-Content data/processed/greek_v2_fixed.jsonl, `
            data/processed/hard_neg_qwen.jsonl |
    Set-Content data/processed/greek_v2_final.jsonl
python scripts/curate_generated_dataset.py `
    --input data/processed/greek_v2_final.jsonl --output-dir data/processed `
    --train-size 10000 --val-size 1500 --test-size 1500 --hard-size 1500 `
    --seed 1337

# 8. Audit (provenance + manifest)
python scripts/verify_provenance.py `
    --inputs data/processed/train.jsonl data/processed/validation.jsonl `
             data/processed/test.jsonl data/processed/hard_test.jsonl
python scripts/hash_manifest.py `
    --inputs data/processed/train.jsonl data/processed/validation.jsonl `
             data/processed/test.jsonl data/processed/hard_test.jsonl
```

The same pipeline runs unattended on AWS via
`scripts/aws/ec2_spot_generate.sh` (see `scripts/aws/README.md`).

## Τι έχει ήδη ρυθμιστεί

- **Upstream code source:** `https://github.com/openai/privacy-filter`
- **Pinned upstream commit:** `f7f00ca7fb869683eb732c010299d901457f19c3`
- **HF model source:** `openai/privacy-filter`
- **Pinned HF revision:** `7ffa9a043d54d1be65afb281eddf0ffbe629385b`

Όλα τα παραπάνω βρίσκονται στο `configs\fine_tune_config.yaml`.

## Δομή

```text
.
├── configs/
│   └── fine_tune_config.yaml
├── data/
│   ├── raw/
│   └── processed/
├── scripts/
│   ├── setup_opf_stack.py
│   ├── run_opf_train.py
│   ├── run_opf_eval.py
│   ├── prepare_dataset.py
│   └── validate_dataset.py
└── requirements.txt
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\setup_opf_stack.py --install-opf
```

Τι κάνει το `setup_opf_stack.py`:
1. Κάνει clone/update το upstream repo στο `external\privacy-filter`
2. Κάνει checkout στο pinned commit
3. Κάνει install το local `opf` package (με `--install-opf`)
4. Κατεβάζει το pinned checkpoint από HF στο `checkpoints\base\privacy-filter`

## Dataset preparation / validation

Παράδειγμα μετατροπής CSV με χαρακτήρες offsets σε OPF JSONL:

```powershell
python scripts\prepare_dataset.py --input data\raw\sample_train.csv --output data\processed\sample_train.jsonl --text-column text --category-column category --start-column start --end-column end --example-id-column example_id --info-columns source
```

Validation OPF schema:

```powershell
python scripts\validate_dataset.py --input data\processed\sample_train.jsonl
```

Για Gemini output (`span_text` format) χρησιμοποίησε:

```powershell
python scripts\convert_gemini_to_opf.py --input data\raw\gemini_raw.jsonl --output data\processed\greek_all.jsonl
python scripts\validate_greek_pii_dataset.py --input data\processed\greek_all.jsonl
python scripts\split_dataset.py --input data\processed\greek_all.jsonl --train-out data\processed\train.jsonl --validation-out data\processed\validation.jsonl --test-out data\processed\test.jsonl --train-ratio 0.7 --validation-ratio 0.15 --test-ratio 0.15
```

Για γρήγορο synthetic σετ 200 δειγμάτων:

```powershell
python scripts\generate_synthetic_greek_pii.py --output data\processed\greek_all_200.jsonl --count 200
python scripts\validate_greek_pii_dataset.py --input data\processed\greek_all_200.jsonl
python scripts\split_dataset.py --input data\processed\greek_all_200.jsonl --train-out data\processed\train.jsonl --validation-out data\processed\validation.jsonl --test-out data\processed\test.jsonl
python scripts\run_baseline.py --eval-mode untyped
```

Για curriculum set αυξανόμενης δυσκολίας (500-1000):

```powershell
python scripts\generate_curriculum_greek_pii.py --output data\processed\greek_curriculum_720.jsonl --count 720
python scripts\validate_greek_pii_dataset.py --input data\processed\greek_curriculum_720.jsonl
python scripts\split_dataset.py --input data\processed\greek_curriculum_720.jsonl --train-out data\processed\train.jsonl --validation-out data\processed\validation.jsonl --test-out data\processed\test.jsonl
python scripts\run_baseline.py --eval-mode untyped
```

## Baseline-first workflow (recommended)

1. Βάλε τα datasets:
   - `data\processed\train.jsonl`
   - `data\processed\validation.jsonl`
   - `data\processed\test.jsonl` (μένει κλειδωμένο, μόνο για τελική αξιολόγηση)

2. Τρέξε baseline στο test set με το base μοντέλο:

```powershell
python scripts\run_baseline.py
```

Θα γραφτεί στο `artifacts\metrics\baseline_test_metrics.json`.

3. Τρέξε fine-tuning:

```powershell
python scripts\run_opf_train.py
```

4. Τρέξε post-train αξιολόγηση + σύγκριση baseline/finetuned:

```powershell
python scripts\run_post_train_evaluation.py
```

Θα γράψει `artifacts\metrics\finetuned_test_metrics.json` και θα εμφανίσει metric deltas.

## RTX 4080 12GB mobile (safe starter settings)

Για αρχικό local run (smoke test):

```powershell
python scripts\run_opf_train.py --device cuda --n-ctx 256 --batch-size 1 --grad-accum-steps 16 --epochs 1 --max-train-examples 500
```

Αν δεν έχεις OOM, αύξησε σταδιακά `epochs` / `n-ctx` / `batch-size`.

## AWS SageMaker fine-tuning (recommended για το $100 credit)

Πλήρης οδηγός: `scripts/aws/README.md`.

Quick start:

```powershell
pip install "sagemaker>=2.224" boto3
aws configure   # region=us-east-1

# 1. Upload data + base checkpoint to S3
$env:BUCKET="YOUR-GPF-BUCKET"
bash scripts/aws/upload_to_s3.sh

# 2. Launch training job (spot g5.xlarge ~ $0.40-0.55/hr)
python scripts/aws/sagemaker_train.py `
    --role arn:aws:iam::123456789012:role/AmazonSageMaker-ExecutionRole-xxxx `
    --bucket YOUR-GPF-BUCKET --use-spot --epochs 3 --learning-rate 5e-5
```

Κόστος ανά run (3 epochs, 8k examples, bs=4, gas=4, n_ctx=256): **~$0.70-$1.50**.
Σε $100 χωράνε **~20 full runs** ή ένα sweep + refinements.

## Greek format augmentation

Για να καλύψεις παραλλαγές σε AMKA / AFM / ADT / IBAN_GR / τηλέφωνα:

```powershell
python scripts\augment_greek_formats.py --input data\processed\train.jsonl --output data\processed\train_augmented.jsonl --per-example-variants 2
cat data\processed\train.jsonl data\processed\train_augmented.jsonl > data\processed\train_combined.jsonl
```

Το script ΔΕΝ εισάγει νέα PII - απλώς αλλάζει τη μορφή υπαρχόντων spans
(spaces, dashes, Greek/Latin lookalikes, prefixes) και ξαναυπολογίζει
σωστά τα character offsets.

## External Greek datasets for data expansion

> **Commercial-use warning.** Most publicly-available Greek NER corpora
> are released under non-commercial licenses (CC-BY-NC-SA). If you plan
> to sell the fine-tuned model or use it in a commercial product, **do
> NOT** include any non-commercial dataset in your training data. See
> [LICENSING.md](LICENSING.md) for the full provenance and attribution
> guide.

### Commercial-safe sources (OK to train on and ship commercially)

| Dataset | Use case | License |
|---|---|---|
| [PleIAs/Greek-PD](https://huggingface.co/datasets/PleIAs/Greek-PD) | Public-domain Greek prose (~156M words). Use as carrier text with `scripts/generate_commercial_safe_greek_pii.py --mode carrier`. | Public domain |
| [Mozilla Common Voice — Greek (text corpus)](https://commonvoice.mozilla.org/en/datasets) | CC0 Greek sentences. Same usage pattern. | CC0 |
| [bigcode/bigcode-pii-dataset](https://huggingface.co/datasets/bigcode/bigcode-pii-dataset) | PII in source code (emails, keys, IPs). English but useful for `code_comments` + `secret`. | Apache-2.0 |
| Your own synthetic data | Generate with `scripts/generate_commercial_safe_greek_pii.py` — all PII is rule-based, all carrier text is public domain or your own templates. | Yours |
| Local open-weight LLM output (Llama 3.1, Mistral, Gemma, Qwen 2.5) via `--mode ollama` | Regenerate synthetic data with no third-party ToS concerns. | Apache 2.0 / Llama CL / Gemma ToU |

### Non-commercial sources (research / evaluation only — do NOT include in commercial train data)

| Dataset | Notes | License |
|---|---|---|
| [joelniklaus/greek_legal_ner](https://huggingface.co/datasets/joelniklaus/greek_legal_ner) | Real Greek legal text with PERSON, GPE, FACILITY, LOCATION. | CC-BY-NC-SA-4.0 |
| [nmpartzio/elNER](https://github.com/nmpartzio/elNER) | 21k Greek news sentences, 4/18-class NER. | Academic, verify |
| [UD_Greek-GDT](https://github.com/UniversalDependencies/UD_Greek-GDT) | Real Greek sentences with named-entity morphology. | CC-BY-NC-SA-3.0 |
| [ai4privacy/pii-masking-*](https://huggingface.co/datasets/ai4privacy/pii-masking-400k) | 27 PII classes, 6 languages (no Greek). Schema reference only. | CC-BY-NC-4.0 |

### Commercial-safe data generation workflow

Quick start — zero external dependencies, 100% commercial-safe:

```powershell
python scripts\generate_commercial_safe_greek_pii.py `
    --output data\processed\greek_commercial_safe.jsonl `
    --count 5000 --mode mix
```

With public-domain Greek carrier text (Greek-PD / Common Voice) for more
natural-sounding examples:

```powershell
# 1. Download Greek-PD once, extract a sentences JSONL into data/raw/
# 2. Generate:
python scripts\generate_commercial_safe_greek_pii.py `
    --output data\processed\greek_commercial_safe.jsonl `
    --count 5000 --mode carrier `
    --carrier-jsonl data\raw\greek_pd_sentences.jsonl
```

With a locally-running open-weight model (fully yours, no API-TOS
concerns):

```powershell
ollama pull llama3.1:8b
python scripts\generate_commercial_safe_greek_pii.py `
    --output data\processed\greek_commercial_safe.jsonl `
    --count 5000 --mode ollama --ollama-model llama3.1:8b
```

## Fine-tuning run (manual)

Με έτοιμα train/validation JSONL:

```powershell
python scripts\run_opf_train.py
```

Το output γράφεται στο `artifacts\model\finetuned-opf` (ρυθμιζόμενο από config).

## Evaluation run (manual)

Base checkpoint στο test set:

```powershell
python scripts\run_opf_eval.py --dataset test --checkpoint base --metrics-out baseline
```

Finetuned checkpoint στο test set:

```powershell
python scripts\run_opf_eval.py --dataset test --checkpoint finetuned --metrics-out finetuned
```

Για εναλλακτική ταξινομία labels:

```powershell
python scripts\run_opf_eval.py --dataset test --checkpoint base --eval-mode untyped
```

## Readiness check

```powershell
python scripts\check_readiness.py
```

## Dataset schema για OPF

Για `opf train`/`opf eval` χρησιμοποίησε schema συμβατό με το upstream, π.χ.:

```json
{"text":"Quindle Testwick ...","spans":{"private_person: Quindle Testwick":[[0,16]]}}
```

Αν έχεις διαφορετική ταξινομία labels, χρησιμοποίησε `--label-space-json` μέσω custom command ή επέκταση του wrapper script. Το `configs/fine_tune_config.yaml` το κάνει αυτόματο μέσω του `label_space.path` field.

## Tuned hyperparameters (why the defaults look the way they do)

- **`epochs: 3`** — 1 epoch δεν συγκλίνει τα 4 νέα heads (`amka`, `afm`, `adt`, `iban_gr`). Το upstream demo τρέχει 40 epochs σε 1-example toy data, οπότε για 8k examples το 3-5 είναι ο σωστός χώρος.
- **`learning_rate: 5e-5`** — 2e-5 είναι πολύ συντηρητικό για supervised finetune αυτού του μεγέθους· 2e-4 (demo) είναι ρίσκο overfit. 5e-5 είναι η ασφαλής μεσαία τιμή, με `1e-4` σαν upper sweep point.
- **`n_ctx: 256`** — Μέσο μήκος κειμένου ~156 chars (~50 tokens). 512 tokens ήταν καθαρή σπατάλη GPU χρόνου.
- **`batch_size: 4, grad_accum_steps: 4`** — Effective batch 16, καλύτερη χρήση του A10G vs. `bs=1, gas=16`.
- **`output_param_dtype: bf16`** — Ίδιο dtype με το base checkpoint, ~1/2 disk size.
- **`label_space.path`** — Explicit pointer στο `configs/label_space.json` ώστε τα custom classes να μην πέσουν silently στο default 8-class taxonomy.
