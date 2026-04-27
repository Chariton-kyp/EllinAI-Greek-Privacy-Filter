# EU AI Act Article 11 / Annex IV — Technical documentation

Regulation (EU) 2024/1689 ("AI Act") requires providers of high-risk AI
systems to keep technical documentation aligned with Annex IV. This file
maps each Annex IV requirement to the specific artefacts in this
repository.

## 0. Scope and classification context

- **System name:** Greek Privacy Filter (fine-tune of
  `openai/privacy-filter`).
- **Intended purpose:** token-level detection of Greek-language PII
  (12 categories: `amka`, `afm`, `adt`, `iban_gr`, `private_person`,
  `private_phone`, `private_address`, `private_email`, `private_date`,
  `private_url`, `account_number`, `secret`).
- **Risk classification:** **to be determined per deployer.** The
  standalone model is distributed under a non-commercial licence and is
  not itself placed on the market as a high-risk AI system. A deployer
  that integrates it into, e.g., an automated GDPR-compliance pipeline
  or a large-scale personal-data-management service may fall under
  Annex III. This documentation is therefore structured to support a
  deployer's conformity assessment rather than to assert that the
  standalone fine-tune is high-risk.
- **Deployer obligations:** see `docs/DPIA_NOTE.md` §2 and §5.

---

## Annex IV §1 — General description

| Annex IV §1 item | Artefact |
|---|---|
| (a) Intended purpose, provider, version | `docs/MODEL_CARD.md`, `README.md` |
| (b) Developer / supplier info | `LICENSE-MODEL-NC` §5, `README.md` |
| (c) Date of system development | `docs/AUDIT_LOG.md` |
| (d) Versions of software / hardware / firmware used | `configs/fine_tune_config.yaml` (pinned upstream commit `f7f00ca7fb869683eb732c010299d901457f19c3` + HF revision), per-run `run_metadata.json` (git commit, instance ID, hyperparameters, seeds, generator quant, llama.cpp Docker image), `artifacts/manifest/manifest_v1.json` (SHA-256 of the v1 split files; the split files themselves live under `data/processed/aws-v1-20260426T092703Z/` after a clone runs the AWS-pipeline replay documented in `scripts/aws/README.md` Part A), `requirements.txt` and `requirements-aws.txt`. |
| (e) Where the system is to be placed on the market / put into service | Released on HuggingFace under non-commercial licence; commercial deployment via separate commercial licence only. |
| (f) Hardware on which the system runs | RTX 4080 12 GB / AWS g6e.xlarge (L40S 48 GB) for data generation; `ml.g5.xlarge` (A10G 24 GB) for fine-tune (see `configs/fine_tune_config.yaml` §aws). |
| (g) Description of the system architecture | `README.md`, `docs/DATASHEET.md`, upstream `openai/privacy-filter` architecture (token classifier). |

## Annex IV §2 — Detailed description of elements and development process

| Annex IV §2 item | Artefact |
|---|---|
| (a) Methods and steps used for development | `docs/AUDIT_LOG.md` (chronological build ledger), `scripts/` (the complete build pipeline is the documentation). |
| (b) Design specifications and assumptions | `docs/DATASHEET.md` §3 (collection process), `docs/MODEL_CARD.md` (intended use, out-of-scope). |
| (c) Description of system architecture | upstream `openai/privacy-filter` + our 4 added label heads (`configs/label_space.json`). |
| (d) Data requirements (data sheets) | `docs/DATASHEET.md` (follows Gebru et al. "Datasheets for Datasets" template). |
| (e) Where applicable, human oversight measures | `docs/MODEL_CARD.md` "Ethical considerations" §: HITL verification **required** before any action on real personal data. |
| (f) Description of pre-determined changes | Seeds and hyperparameters are pinned in `configs/fine_tune_config.yaml`. Any re-run with identical seeds, identical data, and identical git commit yields bit-identical artefacts. |
| (g) Validation and testing procedures | `scripts/run_opf_eval.py`, `scripts/validate_greek_pii_dataset.py`, `scripts/verify_provenance.py`, `scripts/hash_manifest.py`, and `scripts/curate_generated_dataset.py` (see the `stage1 / stage2 / stage3` pipeline). `artifacts/metrics/curation_report.json` is produced automatically per run. |
| (h) Test logs and reports | v1 production fine-tune (run `20260426T135853Z`) produces baseline (`--eval-mode untyped`) and finetuned (`--eval-mode typed`) metrics on both the held-out `test.jsonl` (3,171 records) and the harder `hard_test.jsonl` (4,593 records). Headline span-F1 transcribed in `docs/MODEL_CARD.md` §4: test 0.7766 → 0.9886 (+0.2120); hard_test 0.7668 → 0.9868 (+0.2200). The four raw metric JSONs (`baseline_test_metrics.json`, `baseline_hard_test_metrics.json`, `finetuned_test_metrics.json`, `finetuned_hard_test_metrics.json`) are written to `artifacts/metrics/` by `scripts/aws/ec2_spot_finetune.sh` after each run; in this repository they are produced as run artefacts by replaying the launcher and are not bundled with the public clone (see `scripts/aws/README.md` Part B). Earlier-iteration baselines against prior smoke splits (8,000 / 1,000 / 2,000 / 2,000 records) are retained unchanged as historical evidence in `artifacts/metrics/archive/`. |

## Annex IV §3 — Monitoring and post-market surveillance

- **Measure:** Post-market monitoring is the deployer's responsibility
  per the non-commercial licence distribution model. See
  `docs/DPIA_NOTE.md` §5.
- **Measure:** Bugs or concerns about the released weights should be
  reported under the process in `SECURITY.md`.
- **Measure:** Material changes to the data pipeline or to the fine-tune
  protocol are recorded as new entries in `docs/AUDIT_LOG.md`, tied to a
  git commit hash.

## Annex IV §4 — Risk management

- **Residual risks** are documented in `docs/MODEL_CARD.md` §"Ethical
  considerations" and §"Caveats and recommendations":
  1. False negatives (missed PII) — mitigation: HITL review.
  2. False positives on legitimate numeric text — mitigation: hard-
     negative training (1,500+ Qwen-generated records) and precision
     reporting per class.
  3. Bias toward common Greek given / family names — mitigation flagged
     in model card; diaspora name variants are under-represented.
  4. Greek-script-only coverage of Latin-transliterated contact fields —
     mitigation: 80/20 Latin/Greek email + URL split at training time.

## Annex IV §5 — Harmonised standards / common specifications

No harmonised standards have been formally applied. The following
published standards and templates informed the development:

- ISO/IEC 42001:2023 AI Management System — `docs/AIMS_STATEMENT.md`.
- NIST AI Risk Management Framework 1.0 — `docs/NIST_AI_RMF.md`.
- "Model Cards for Model Reporting" (Mitchell et al., 2019) —
  `docs/MODEL_CARD.md`.
- "Datasheets for Datasets" (Gebru et al., 2018) —
  `docs/DATASHEET.md`.
- GDPR Article 30 Record-of-Processing-Activities template —
  `docs/GDPR_ART30_ROPA.md`.
- ELOT 743 / ISO 843 Greek-Latin transliteration —
  `src/privacy_filter_ft/transliteration.py`.
- Apache 2.0 licence compliance workflow — `LICENSE-CODE`, `NOTICE`,
  `ATTRIBUTION.txt`.

## Annex IV §6 — Conformity declaration

Not applicable at this stage. The standalone fine-tune is not placed on
the market as a high-risk AI system (see §0 above). If a deployer
integrates this model into a high-risk system under Annex III, the
deployer must perform their own conformity assessment and issue their
own declaration; this documentation is provided in support of that
assessment.

---

## Summary for an auditor

Every Annex IV clause has a clear pointer to a concrete file in this
repository. The repository is fully reproducible from the current git
commit plus the synthetic-data pipeline's recorded seeds. Data
provenance per record is stamped in the `info.strategy` field of every
JSONL example, and a cryptographic manifest links every split file to
a specific build of the code.

The only items that depend on downstream action are:

1. `docs/MODEL_CARD.md` quantitative metrics (populated after the first
   fine-tune run).
2. Deployer-specific conformity assessment (Annex IV §6).

Both are expected workflow items, not gaps in the documentation
structure.
