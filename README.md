# Greek Privacy Filter

A Greek PII detection pipeline shipped in three tiers — a 1.4 B token
classifier (Lite), a 2 B causal-LM (Mini), and a 31 B teacher (Ultra) —
built via knowledge distillation from a Gemma 4 31B teacher onto Greek-
specific PII span detection across **24 classes**. Fine-tuned on a fully
synthetic Greek corpus, validated against a locked 200-case OOD
evaluation set, and shipped with audit-grade governance documentation.

| Field            | Value                                              |
| ---------------- | -------------------------------------------------- |
| Latest release   | **v3** — 2026-05-07 (24 classes, distillation pipeline) |
| v1 (legacy)      | 2026-04-26 — 12 classes, OPF base, F1 0.9886 test  |
| Tiers shipped    | **Lite** (1.4 B token classifier) · **Mini** (Gemma 4 2B Q4 LoRA) · **Ultra** (31 B teacher LoRA) |
| Detection F1     | Lite v3: 0.99 in-dist · 0.78 OOD raw · Mini v3: 0.96 in-dist · 0.88 OOD raw |
| Languages        | Modern Greek (Latin transliterations, polytonic, dense multi-PII forms) |
| License          | Non-commercial public release; commercial rights reserved by the copyright holder — see `LICENSING.md` |
| Provider         | Chariton Kypraios — `haritos19@gmail.com`          |
| Public release   | Reproducible code, schemas, samples, manifests, governance docs, and aggregate metrics only |

## What the model detects

v3 covers **24 PII classes** organised in three families. Generic PII
inherited from the OPF base (English) and adapted to Greek text on the
left; Greek-specific identifiers in the middle; deterministic-format
identifiers added in v2 / v3 on the right.

| Generic              | Greek-specific  | Deterministic-format |
| -------------------- | --------------- | -------------------- |
| `private_person`     | `afm`           | `passport`           |
| `private_phone`      | `amka`          | `license_plate`      |
| `private_email`      | `adt`           | `vehicle_vin`        |
| `private_address`    | `iban_gr`       | `gemi`               |
| `private_url`        |                 | `ama`                |
| `private_date`       |                 | `card_pan`           |
| `account_number`     |                 | `cvv`                |
| `secret`             |                 | `imei`               |
|                      |                 | `ip_address`         |
|                      |                 | `mac_address`        |
|                      |                 | `driver_license`     |
|                      |                 | `pcn`                |

The v1 12-class label space lives at `configs/label_space.json`. The
v3 24-class schema lives at `configs/label_space_v3.json`.

## Inference example

```python
from opf import OPF

detector = OPF(model="path/to/finetuned/model", device="cuda")
result = detector.redact(
    "Είμαι ο Γιώργος Παπαδόπουλος, ΑΦΜ 234567890, και θέλω "
    "πληροφορίες για τη συνάντηση της 12/06/2025."
)
print(result.redacted_text)
# => "Είμαι ο [private_person], ΑΦΜ [afm], και θέλω
#     πληροφορίες για τη συνάντηση της [private_date]."
for span in result.detected_spans:
    print(span.label, span.text, span.start, span.end)
```

To run the public inference container against a downloaded checkpoint:

```bash
# Drop the downloaded fine-tuned checkpoint under
# data/processed/aws-ft-<RUN_ID>/model/   (already on the compose mount path)
docker compose build
docker compose run --rm gpf-inference \
    --checkpoint /workspace/data/processed/aws-ft-<RUN_ID>/model
```

The default path the inference script expects is
`data/processed/aws-ft-20260426T135853Z/model` (covered by the compose
`./data` mount). The fine-tuned checkpoint itself is not bundled with
this repository (2.6 GB); a deployer either reproduces it via the AWS
launchers in `scripts/aws/` or downloads it from the project's
HuggingFace Hub release once published.

The locked 200-case OOD benchmark used for v2.13-vs-v3 comparison is
not bundled in the public repository. Public benchmark reporting is
aggregate-only; per-case traces and full benchmark text are not part
of this public release.

## Repository layout

```text
.
├── configs/
│   ├── fine_tune_config.yaml          Pinned upstream commit + training defaults
│   └── label_space.json               12-class label schema
├── data/
│   ├── seed/                          42 golden seed records (committed)
│   ├── samples/                       100-record reference samples per split (committed)
│   ├── raw/, processed/               Pipeline output (gitignored)
├── scripts/
│   ├── generate_commercial_safe_greek_pii.py   Main carrier-injection generator (Qwen via llama-server)
│   ├── generate_qwen_hard_negatives.py         Hard-negative generator
│   ├── build_golden_seeds.py                   Deterministic golden seeds
│   ├── curate_generated_dataset.py             5-stage curator + split writer
│   ├── download_carrier_greek_pd.py            Greek public-domain corpus pull
│   ├── download_carrier_common_voice.py        Mozilla Common Voice Greek pull
│   ├── download_carrier_legal_code.py          Greek legal-code corpus pull
│   ├── postprocess_latinize_contacts.py        Latin / Greek email-URL variation
│   ├── augment_greek_formats.py                Per-class format variation
│   ├── hash_manifest.py                        SHA-256 manifest writer
│   ├── verify_provenance.py                    Per-record provenance allow-list check
│   ├── validate_greek_pii_dataset.py           JSONL schema validator
│   ├── setup_opf_stack.py                      Clone + install upstream OPF at the pinned commit
│   ├── run_opf_train.py / run_opf_eval.py      Local-host training / evaluation wrappers
│   ├── aws/
│   │   ├── ec2_spot_generate.sh                AWS spot launcher: synthetic-data generation
│   │   ├── ec2_spot_finetune.sh                AWS spot launcher: fine-tune + eval
│   │   ├── iam_policy_ec2_gen.json             Inline-policy template (placeholder bucket)
│   │   ├── sagemaker_train.py                  Optional SageMaker entrypoint
│   │   └── README.md                           AWS operator guide (Parts A / B / C)
│   ├── prepare_dataset.py / split_dataset.py / convert_gemini_to_opf.py / check_readiness.py
├── src/privacy_filter_ft/                      Local utility package (transliteration, schema)
├── docs/                                       Audit-ready governance documentation (see below)
├── artifacts/
│   ├── manifest/                               manifest_v1.json (release) + manifest.json (smoke) + samples_manifest.json
│   ├── metrics/                                aggregate benchmark summary, curation/provenance reports + archive/
│   ├── logs/, model/, checkpoints/             gitignored run artefacts
├── Dockerfile.inference                        Local CUDA inference image (clones upstream OPF)
├── docker-compose.yml                          Single-service compose stack
├── requirements.txt                            Minimum top-level deps
├── requirements-aws.txt                        AWS-only deps (boto3, sagemaker)
└── (LICENSE, LICENSE-NC, NOTICE, ATTRIBUTION.txt, LICENSING.md, SECURITY.md)
```

## Documentation

| File                              | Contents                                                                  |
| --------------------------------- | ------------------------------------------------------------------------- |
| `docs/MODEL_CARD.md`              | Mitchell-template model card (intended use, metrics, ethical considerations) |
| `docs/DATASHEET.md`               | Gebru-template datasheet (composition, collection, recommended uses)      |
| `docs/AUDIT_LOG.md`               | Chronological build ledger with commit hashes                             |
| `docs/EU_AI_ACT_ANNEX_IV.md`      | Per-paragraph mapping to repository artefacts                             |
| `docs/AIMS_STATEMENT.md`          | ISO/IEC 42001 AI Management System statement                              |
| `docs/NIST_AI_RMF.md`             | NIST AI RMF 1.0 mapping                                                   |
| `docs/DPIA_NOTE.md`               | Public DPIA-status note (training stage processes no personal data)       |
| `docs/GDPR_ART30_ROPA.md`         | Deployer template (provider record kept private per Art. 30 guidance)    |
| `docs/V2_13_V3_COMPARISON.md`     | Aggregate v2.13-vs-v3 same-dataset comparison and metric caveats          |
| `LICENSING.md`                    | Non-commercial public-release terms and provenance guide                   |
| `SECURITY.md`                     | Vulnerability disclosure policy                                           |
| `NOTICE`, `ATTRIBUTION.txt`       | Apache 2.0 notice + per-data-source citations                             |

## Public Release Boundary

This repository is intentionally narrow. It contains the code,
configs, public samples, manifests, governance documents, and
aggregate-only benchmark summaries needed to inspect the project and
reproduce the public pipeline.

It does **not** contain:

- the locked 200-case OOD benchmark JSONL;
- per-case benchmark traces with raw text, expected spans, predictions,
  redacted text, or failure-mining contexts;
- filled AWS/account/bucket/IAM/instance identifiers;
- non-public v3 training traces, calibration assets, or
  release-candidate artefact pointers.

Audit-supporting records that are not safe for public release are
retained by the maintainer outside public git history and can be
reviewed under an appropriate confidentiality process.

Before publishing from this repository, run:

```bash
python scripts/check_public_boundary.py --check-json
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate            # PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/setup_opf_stack.py --install-opf
```

`setup_opf_stack.py` clones `openai/privacy-filter` at the pinned
commit into `external/privacy-filter/`, pip-installs it in editable
mode, and downloads the pinned base checkpoint from Hugging Face into
`checkpoints/base/privacy-filter/`. Both directories are gitignored.

To run the AWS launchers locally add `pip install -r requirements-aws.txt`.

## Reproducing v1

The v1 release is the result of a single AWS spot run documented in
`docs/AUDIT_LOG.md` §3 and reproducible from the launchers under
`scripts/aws/`:

1. **One-off AWS setup** — bucket, IAM role, instance profile, inline
   policy. Step-by-step in `scripts/aws/README.md` Part A.1.
2. **Synthetic-data generation** — `bash scripts/aws/ec2_spot_generate.sh`
   produces a 50 000-record raw set, runs the curator, the provenance
   verifier and the manifest hasher, syncs everything to S3, and
   self-terminates the spot instance. ~$2.30 spot + ~$0.10 storage at
   `g6e.xlarge` pricing.
3. **Fine-tune + evaluation** — `bash scripts/aws/ec2_spot_finetune.sh`
   pulls the v1 splits and the base checkpoint, runs the OPF baseline
   eval (`--eval-mode untyped`), trains for 3 bf16 epochs at lr 5e-5
   and `n_ctx=256`, runs the finetuned eval (`--eval-mode typed`), and
   syncs every artefact (model + four metric JSONs + run_metadata.json)
   back to S3. ~$0.27 spot + ~$0.02 storage.
4. **Local audit** — `python scripts/hash_manifest.py` against the
   downloaded splits should match `artifacts/manifest/manifest_v1.json`
   byte-for-byte; `python scripts/verify_provenance.py` should pass
   with all-OK on every record.

The pinned hyperparameters live in `configs/fine_tune_config.yaml`
and the rationale for each is captured in
`docs/MODEL_CARD.md` §4 and the inline comments of that YAML.

A local-only Linux Docker stack reproduces the same inference path on
a workstation GPU (`Dockerfile.inference` + `docker-compose.yml`) for
running a downloaded checkpoint.

## Greek-format augmentation

The augmenter at `scripts/augment_greek_formats.py` produces format
variations of existing AMKA / AFM / ADT / IBAN_GR / phone spans
(spaces, dashes, Greek-Latin lookalikes, prefix-form variation) without
introducing new PII values. Useful for closing residual recall gaps:

```bash
python scripts/augment_greek_formats.py \
    --input data/processed/train.jsonl \
    --output data/processed/train_augmented.jsonl \
    --per-example-variants 2
```

## External Greek datasets — commercial-use note

> **Commercial-use warning.** Most publicly-available Greek NER corpora
> are released under non-commercial licenses (CC-BY-NC-SA). Do not
> include any non-commercial dataset in training data for a
> commercial deployment. See `LICENSING.md` for the full provenance
> and attribution guide.

| Dataset | Use case | License |
|---|---|---|
| [PleIAs/Greek-PD](https://huggingface.co/datasets/PleIAs/Greek-PD) | Public-domain Greek prose (~156 M words). Used as carrier text via `--mode carrier`. | Public domain |
| [Mozilla Common Voice — Greek](https://commonvoice.mozilla.org/en/datasets) | CC0 Greek sentence corpus. Same usage pattern. | CC0 |
| [AI-team-UoA/greek_legal_code](https://huggingface.co/datasets/AI-team-UoA/greek_legal_code) | Greek legislation excerpts for legal-text register carriers. | CC-BY-4.0 |
| Locally-hosted open-weight LLM output (Qwen 3.6 / Llama 3.1 / Mistral / Gemma) | Used to assemble PII-bearing sentences around rule-generated values. | Apache 2.0 / Llama CL / Gemma ToU |
| Your own synthetic data via `generate_commercial_safe_greek_pii.py` | Fully commercial-safe — every PII value is rule-based and every carrier is permissively licensed. | Yours |

## Status and roadmap

v1 is the foundational release: 32 061 records, 12 PII classes, span
F1 ≥ 0.94 across every class, audit-ready governance documentation,
reproducible build pipeline.

### v2 progression — out-of-distribution benchmark

v2 extends coverage to **24 PII classes** (12 new Tier-1 deterministic-
format classes added: `passport`, `license_plate`, `vehicle_vin`,
`gemi`, `ama`, `card_pan`, `cvv`, `imei`, `ip_address`, `mac_address`,
`driver_license`, `pcn`).

Each iteration is evaluated on a **locked 200-case real-world
Greek benchmark** with hand-graded spans across 24 registers: tax-office
letters, medical referrals, formal legal text, polytonic, Greeklish,
dialect, dense multi-PII forms, etc. The benchmark is held out — the
model never sees it during training. The exact benchmark file is
not included in this public release; aggregate numbers and methodology
are reported here, while full traces are retained as non-public audit
evidence.

| Version | Aggregate F1 | Precision | Recall | Notes |
| ------- | -----------: | --------: | -----: | ----- |
| v2.6 (Tier-1 baseline) | 0.815 | 0.848 | 0.784 | 24 classes; 6 weak (secret 0.70, dl 0.42, person 0.69, address 0.61, ip 0.74, pcn 0.82) |
| v2.7 (template targeting) | 0.814 | 0.834 | 0.794 | dl +0.33, ip +0.10, pcn +0.09; secret regressed |
| v2.8 (template + neg) | 0.758 | 0.842 | 0.689 | empty-label records destroyed recall globally |
| v2.9 (neg labelling fixed) | **0.826** | **0.907** | 0.758 | best-precision; secret 0.83, address 0.89, person 0.80 |
| v2.10 (recall-boost templates) | 0.777 | 0.901 | 0.683 | over-formulaic templates; ama 0.13→0.47 but other classes lost recall |
| v2.11 (Qwen narrative, 1.5k records) | 0.814 | 0.865 | 0.769 | Qwen3.6-35B-A3B-Q4 served locally; ama 0.13→0.60 (+0.47), gemi 0.59→0.93; private_phone 0.86→0.53 (12 confusions); net F1 −0.012 vs v2.9 |
| v2.12 (data audit + phone-anchor) | 0.8266 | 0.881 | 0.778 | filtered 118 phone-shape account_number records from base; +300 Qwen phone-anchor records with explicit `τηλ./κιν./📞` markers; ama 0.13→0.78 (+0.65), gemi 0.59→0.97, pcn 0.95→1.00, dl 0.67→0.82; phone confusions 12→7 |
| v2.13 (Qwen contrastive packs) | **0.8373** | **0.888** | **0.792** | +500 phone_account, +107 email_secret (clean), +291 mac_ip_vin (clean); leakage filter dropped 467 records where Qwen regurgitated label IDs ("secret", "mac_address", "ip_address", "vehicle_vin"); generator patched to use Greek-readable labels ("κλειδί API", "διεύθυνση MAC"); mac_address 0.58→0.88 (+0.30), secret 0.73→0.91, vehicle_vin 1.00, afm 0.98; final v2 comparison baseline |

Public per-iteration benchmark aggregates are kept in
`artifacts/metrics/benchmark_summary.json`.
Per-iteration dataset SHA-256 manifests at `artifacts/manifest/manifest_v2_*.json`.

### Lessons learned (template-only ceiling)

- Template packs work for **deterministic-format classes** (`afm`,
  `amka`, `pcn`, `driver_license`, `vehicle_vin`, `card_pan`,
  `iban_gr`, `gemi`) — strong markers transfer to OOD prose.
- Template packs **do not transfer** for **semantic classes**
  (`private_person`, `private_address`, `secret`) — model overfits to
  carrier sentence patterns; benchmark uses real Greek narrative.
- Negative examples (text without addresses) **must label other PII**
  in the record. Empty-label records collapse recall globally —
  the model learns "when in doubt, predict O".
- Single-pass token accuracy ≥ 0.999 does **not** imply OOD F1 ≥ 0.85.
  Validation-set token accuracy is too easy. The locked 200-case OOD
  bench is the main signal used for v2.13-vs-v3 comparison.

### v3 — latest test line (released 2026-05-07)

v3 is a teacher–student distillation pipeline that breaks the
single-model v2.13 ceiling without re-training the base from scratch.

```text
Greek corpus (PD/CC0/CC-BY) ─┬─► Gemma 4 31B SFT (teacher) ─┐
                             │                              │
v2.13 gold (111k records,   │   24-class span tagger, OOD   │
24-class, 142k spans)  ──────┘   F1 0.978                   │
                                                            │
                                                            ▼
                                  100k pseudo-labels  ──► Mini SFT (Gemma 4 2B Q4 LoRA)
                                   over Greek corpus  ──► Lite SFT (privacy-filter 1.4B token)
```

| Tier  | Base model                       | Method        | F1 in-dist | F1 OOD raw |
| ----- | -------------------------------- | ------------- | ---------: | ---------: |
| Lite  | `katanemo/privacy-filter` (1.4B) | OPF token cls + distill | 0.99 | 0.78 |
| Mini  | `unsloth/gemma-4-E2B-it`         | Unsloth LoRA Q4 + distill | 0.96 | 0.88 |
| Ultra | Gemma 4 31B (teacher)            | Unsloth LoRA Q4 SFT | n/a | **0.978** |

For public comparison, treat v2.13 as the final v2 baseline and v3 as
the latest test line. Aggregate-only comparison data is published in
`artifacts/metrics/benchmark_summary.json`; per-case traces,
reviewer notes, and calibration details are not part of this public
release.

| Comparison target | OOD F1 raw | Notes |
| --- | ---: | --- |
| v2.13 OPF eval, same 200 cases | 0.8564 | Final v2 baseline, 24 classes, typed OPF eval, Viterbi, `n_ctx=256`. |
| v3 Lite OPF eval, same 200 cases | 0.8100 | Same dataset and factors as v2.13; this token tier trails v2.13 before additional non-public calibration. |
| v2.13 triage harness | 0.8373 | Earlier aggregate from the triage harness; retained for historical continuity. |
| v3 Mini raw | 0.88 | Distilled causal-LM tier; current public aggregate beats v2.13 raw. |
| v3 Ultra teacher raw | 0.978 | Teacher tier used for distillation and upper-bound calibration. |

Real-world validation: against an independent reviewer (Anthropic
Opus 4.7) on 10 hand-crafted Greek documents spanning 10 registers
(corporate email, support chat, court decision, medical record, bank
notification, vehicle insurance, tax form, HR contract, informal
chat, government decree), Lite v3 achieved **79% exact-span agreement
and 91% partial-span agreement** with the reviewer, 24/24 classes
above F1 0.55, 18/24 classes above F1 0.85.

Per-iteration training metrics for `mini-local` and `lite-v3-local`
(per-class breakdown, predictions, confusion analysis) are retained as
non-public audit evidence.

### Training infrastructure

The full distillation pipeline runs end-to-end on AWS EC2 spot:

- `scripts/v3/train_teacher.py` — Unsloth Gemma 4 31B Q4 LoRA SFT,
  pre-tokenized for TRL ≥ 0.21 + transformers 5.x compatibility.
- `scripts/v3/generate_pseudo_labels_unsloth.py` — teacher inference
  over the Greek corpus at ~140 records/min on g6e.xlarge.
- `scripts/v3/train_student_distill.py` — parametrised SFT trainer
  for the Mini / Pro / Max student tiers.
- `scripts/v3/prep_lite_dataset.py` — dataset combiner with neg-pos
  ratio sampling (gold + pseudo → balanced train set).
- `scripts/aws/ec2_v3_{teacher,pseudo,distill}.sh` — spot launchers
  with SSM artifact pump (S3 sync κάθε 5 min for spot resilience),
  AVAIL_ZONE rotation for capacity, EBS provisioning for fast
  checkpoint I/O.

Additional calibration and post-processing experiments are not part of
this public release. Public metrics should be interpreted exactly as
reported in `artifacts/metrics/benchmark_summary.json`.

Open issues and security questions go via `SECURITY.md`.

## Ethics

Use the model as a triage tool, never as the sole basis for an
irreversible action on personal data. A human-in-the-loop review is
part of the model's intended-use definition (see `docs/MODEL_CARD.md`
§6). Re-evaluate the model on a labelled sample drawn from your own
production distribution before deploying it. Complete the deployer
template in `docs/GDPR_ART30_ROPA.md` and consult `docs/DPIA_NOTE.md`
before processing real Greek personal data.
