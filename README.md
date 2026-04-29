# Greek Privacy Filter

A 1.4-billion-parameter mixture-of-experts span detector for Greek
personal-information text, fine-tuned from
[`openai/privacy-filter`](https://github.com/openai/privacy-filter) on a
fully synthetic Greek corpus and shipped with audit-grade governance
documentation. The v1 release detects twelve PII classes — eight
inherited from the upstream English-language base plus four added for
Greek (AMKA, AFM, ADT, IBAN_GR) — at span F1 ≥ 0.94 across every
class, with overall span F1 of **0.9886** on the held-out test set
and **0.9868** on the harder edge-case set.

| Field            | Value                                              |
| ---------------- | -------------------------------------------------- |
| Status           | v1 released 2026-04-26                             |
| Model size       | ~1.4 B parameters (8 layers × 128 experts × 4 routed/token, hidden 640), 2.6 GB bf16 |
| Detection F1     | 0.9886 test · 0.9868 hard_test (span level, typed) |
| Token F1         | 0.9972 test · 0.9942 hard_test                     |
| Per-class F1 floor | 0.9486 (afm) — see `docs/MODEL_CARD.md` §4        |
| Languages        | Modern Greek (with Latin-transliterated contact fields) |
| License          | Code: Apache 2.0; weights: dual-licensed (NC + commercial) — see `LICENSING.md` |
| Provider         | Chariton Kypraios — `haritos19@gmail.com`          |

## What the model detects

| Class             | Format                                             |
| ----------------- | -------------------------------------------------- |
| `private_person`  | Personal names                                     |
| `private_phone`   | Greek phones (10-digit; mobile prefix 69x)         |
| `private_email`   | Email addresses (Greek-script local-part supported) |
| `private_address` | Street addresses                                   |
| `private_url`     | URLs and social-media handles                      |
| `private_date`    | Dates in numeric and verbose form                  |
| `account_number`  | Bank account numbers                               |
| `secret`          | API tokens, passwords, private keys                |
| `afm`             | Greek tax number (9 digits)                        |
| `amka`            | Greek social-security number (11 digits)           |
| `adt`             | Greek ID-card number (1–2 letters + 6 digits)      |
| `iban_gr`         | Greek IBAN (`GR` + 25 digits)                      |

The full label-space schema lives at `configs/label_space.json`.

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

To reproduce the v1 metrics on the realworld test passages bundled with
the repository:

```bash
# Drop the downloaded fine-tuned checkpoint under
# data/processed/aws-ft-<RUN_ID>/model/   (already on the compose mount path)
docker compose build
docker compose run --rm gpf-inference \
    --checkpoint /workspace/data/processed/aws-ft-<RUN_ID>/model
```

The default path the realworld script expects is
`data/processed/aws-ft-20260426T135853Z/model` (covered by the compose
`./data` mount). The fine-tuned checkpoint itself is not bundled with
this repository (2.6 GB); a deployer either reproduces it via the AWS
launchers in `scripts/aws/` or downloads it from the project's
HuggingFace Hub release once published.

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
│   ├── test_finetuned_realworld.py             10-case realworld inference test (with P/R/F1)
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
│   ├── metrics/                                curation, provenance, samples_provenance, realworld_inference reports + archive/
│   ├── logs/, model/, checkpoints/             gitignored run artefacts
├── Dockerfile.inference                        Local CUDA inference image (clones upstream OPF)
├── docker-compose.yml                          Single-service compose stack
├── requirements.txt                            Minimum top-level deps
├── requirements-aws.txt                        AWS-only deps (boto3, sagemaker)
└── (LICENSE, LICENSE-CODE, LICENSE-MODEL-NC, NOTICE, ATTRIBUTION.txt, LICENSING.md, SECURITY.md)
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
| `LICENSING.md`                    | Dual-license rationale + commercial-license procedure                     |
| `SECURITY.md`                     | Vulnerability disclosure policy                                           |
| `NOTICE`, `ATTRIBUTION.txt`       | Apache 2.0 notice + per-data-source citations                             |

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
a workstation GPU (`Dockerfile.inference` + `docker-compose.yml`) and
is the recommended path for running `scripts/test_finetuned_realworld.py`
against a downloaded checkpoint.

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

Each iteration is evaluated on a **locked 200-case real-world Greek
benchmark** (`data/realworld_benchmark/cases.jsonl`) with hand-graded
spans across 24 registers: tax-office letters, medical referrals,
formal legal text, polytonic, Greeklish, dialect, dense multi-PII
forms, etc. The benchmark is held out — the model never sees it during
training.

| Version | Aggregate F1 | Precision | Recall | Notes |
| ------- | -----------: | --------: | -----: | ----- |
| v2.6 (Tier-1 baseline) | 0.815 | 0.848 | 0.784 | 24 classes; 6 weak (secret 0.70, dl 0.42, person 0.69, address 0.61, ip 0.74, pcn 0.82) |
| v2.7 (template targeting) | 0.814 | 0.834 | 0.794 | dl +0.33, ip +0.10, pcn +0.09; secret regressed |
| v2.8 (template + neg) | 0.758 | 0.842 | 0.689 | empty-label records destroyed recall globally |
| v2.9 (neg labelling fixed) | **0.826** | **0.907** | 0.758 | best-precision; secret 0.83, address 0.89, person 0.80 |
| v2.10 (recall-boost templates) | 0.777 | 0.901 | 0.683 | over-formulaic templates; ama 0.13→0.47 but other classes lost recall |
| v2.11 (Qwen narrative, 1.5k records) | 0.814 | 0.865 | 0.769 | Qwen3.6-35B-A3B-Q4 served locally; ama 0.13→0.60 (+0.47), gemi 0.59→0.93; private_phone 0.86→0.53 (12 confusions); net F1 −0.012 vs v2.9 |

Per-iteration benchmark JSONs at `artifacts/metrics/benchmark_triage_v2_*.json`.
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
  Validation-set token accuracy is too easy. The 200-case OOD bench
  is the only signal that correlates with real deployment.

### v2 path forward

- **Qwen narrative pack** (v2.11+, in progress): generate diverse Greek
  prose locally via Qwen3.6-35B-A3B served on consumer GPU. Each
  record has authored PII slot values + LLM-written carrier prose;
  spans labelled deterministically by substring search. ~25 records/min
  on RTX 4080 Mobile.
- **Hard-negative mining**: predict on real Greek prose, harvest
  false positives, re-train.
- **Cascade architecture** (planned): regex Layer 1 + transformer
  Layer 2 + contextual Layer 3 — break the single-model 0.83 ceiling.

Open issues, security questions and commercial-license requests go via
`SECURITY.md`.

## Ethics

Use the model as a triage tool, never as the sole basis for an
irreversible action on personal data. A human-in-the-loop review is
part of the model's intended-use definition (see `docs/MODEL_CARD.md`
§6). Re-evaluate the model on a labelled sample drawn from your own
production distribution before deploying it. Complete the deployer
template in `docs/GDPR_ART30_ROPA.md` and consult `docs/DPIA_NOTE.md`
before processing real Greek personal data.
