# AI Management System statement (ISO/IEC 42001:2023)

## 1. Purpose and scope

This statement describes the AI management system (AIMS) that governs
the design, development, release, and post-release maintenance of the
Greek Privacy Filter (the "AI System"). It is issued pursuant to the
principles of ISO/IEC 42001:2023, adapted to a solo-operator project.

The AIMS covers:

- The source-code pipeline under `scripts/`, `src/`, and `configs/`.
- The fine-tuned model weights released under `LICENSE-MODEL-NC`.
- The accompanying documentation under `docs/`, `LICENSING.md`,
  `NOTICE`, and `ATTRIBUTION.txt`.

The AIMS does **not** cover any third-party deployment of the model.
Deployers are responsible for their own AIMS aligned with their use
case.

## 2. AI policy

The provider of the AI System commits to:

1. Release the AI System under licences that accurately reflect the
   permitted uses of every component (Apache 2.0 for code; non-
   commercial for weights unless a separate commercial licence is
   negotiated in writing).
2. Train the AI System exclusively on synthetic data so that no
   personal data is processed at the training stage (GDPR Article 5).
3. Document the data pipeline, model architecture, evaluation
   methodology, and known limitations in a form that a downstream
   deployer or auditor can independently verify.
4. Require human-in-the-loop verification of model output in any
   deployment that may produce legal effects on a data subject (see
   `docs/MODEL_CARD.md`).
5. Maintain an accurate audit ledger and cryptographic manifest so
   that any released artefact can be traced back to the code, the
   data, and the configuration that produced it.

## 3. Roles and responsibilities

The project is operated by a single individual:

| Role | Held by |
|---|---|
| Provider (under EU AI Act Article 3(3)) | Chariton Kypraios |
| Developer | Chariton Kypraios |
| Data-Protection contact (GDPR Article 13(1)(b)) | Chariton Kypraios — haritos19@gmail.com |
| Security contact (see `SECURITY.md`) | Chariton Kypraios — haritos19@gmail.com |

The provider acknowledges that all obligations of the provider role
rest on this individual and may not be delegated without a written
amendment to this document.

## 4. Objectives and performance indicators

The following objectives are established for each release of the
fine-tuned weights:

| Objective | Indicator | Target |
|---|---|---|
| Training data is synthetic | `info.source` value in every record | 100 % of records carry `commercial_safe_generator` or `golden_seeds` |
| Per-record provenance is complete | `scripts/verify_provenance.py` | Zero records with unknown `info.strategy` |
| Test-set class coverage | `artifacts/metrics/curation_report.json` stage-3 span counts | ≥ 30 spans per PII class |
| Hard-negative ratio in training | same report | 10 %–20 % per split |
| Licence chain is auditable | Apache 2.0 + NC commit present; SHA-256 manifest current | yes / yes |

## 5. AI lifecycle approach

Each release passes through four stages, each anchored to a git
commit:

1. **Design**: updates to `docs/DATASHEET.md`, `configs/*`, prompt
   templates, or the label space. Recorded in `docs/AUDIT_LOG.md`.
2. **Build**: synthetic-data generation, curation, and fine-tuning.
   All outputs are tied to a specific commit via the run-metadata JSON
   produced by `scripts/aws/ec2_spot_generate.sh`.
3. **Evaluation**: `scripts/run_post_train_evaluation.py` produces
   `artifacts/metrics/finetuned_*_metrics.json`. Any metric regression
   vs. the recorded baseline is grounds for holding the release.
4. **Release**: the fine-tuned weights are tagged in git, pushed to
   HuggingFace under `LICENSE-MODEL-NC`, and the release notes link to
   the exact commit hash and manifest.

## 6. Risk management

Residual risks are enumerated in `docs/MODEL_CARD.md` (Ethical
considerations; Caveats and recommendations) and are cross-referenced
from `docs/EU_AI_ACT_ANNEX_IV.md` §4. Each identified risk has at
least one documented mitigation (human-in-the-loop review, hard-
negative training, class-balanced sampling, script transliteration
diversity).

## 7. Change control

All changes to the pipeline are made through git commits that include
the motivation for the change in the commit message. No "silent"
changes to the training pipeline are permitted between releases. A
change that affects the data distribution (label space, template bank,
carrier source, quant level, seed values) requires a new entry in
`docs/AUDIT_LOG.md` and a rebuild of the affected artefacts with a new
manifest.

## 8. Internal audit and management review

Because the provider is a single individual, formal separation of
duties is not achievable. Instead:

- Prior to every release of new weights, the provider runs the
  `scripts/verify_provenance.py` and `scripts/hash_manifest.py`
  scripts and reviews their output.
- At least once per calendar year, the provider reviews this AIMS
  statement and `docs/EU_AI_ACT_ANNEX_IV.md` for currency and records
  the review date below.

### Review log

| Date | Reviewer | Outcome |
|---|---|---|
| 2026-04-24 | Chariton Kypraios | AIMS statement issued (v1.0). |

## 9. Reference documents

| Artefact | Role in AIMS |
|---|---|
| `LICENSING.md` | Licence chain of every component. |
| `docs/DATASHEET.md` | Dataset record. |
| `docs/MODEL_CARD.md` | Model record, intended use, limitations. |
| `docs/EU_AI_ACT_ANNEX_IV.md` | Regulatory mapping. |
| `docs/DPIA_NOTE.md` | GDPR note for deployers. |
| `docs/NIST_AI_RMF.md` | NIST AI RMF 1.0 mapping. |
| `docs/GDPR_ART30_ROPA.md` | Article 30 Record of Processing Activities template for deployers. |
| `docs/AUDIT_LOG.md` | Chronological build ledger. |
| `SECURITY.md` | Vulnerability-disclosure process. |
| `NOTICE`, `ATTRIBUTION.txt` | Apache 2.0 §4(d) and derivative attribution. |
| `artifacts/manifest/*.json` | SHA-256 cryptographic manifest. |
| `artifacts/metrics/*.json` | Baseline and evaluation records. |
