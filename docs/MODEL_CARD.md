# Model card — Greek Privacy Filter

This model card follows the structure of Mitchell et al., "Model Cards
for Model Reporting" (FAT* 2019). Quantitative sections are populated
from `artifacts/metrics/finetuned_test_metrics.json` and
`artifacts/metrics/finetuned_hard_test_metrics.json` produced by the
v1 fine-tune run on 2026-04-26.

## 1. Model details

- **Model name:** Greek Privacy Filter.
- **Model version:** v1 (first fine-tuned release).
- **Model date:** 2026-04-26.
- **Model type:** token-level classifier derived from
  `openai/privacy-filter` by fine-tuning on a Greek synthetic corpus.
- **Base model:** `openai/privacy-filter` (Apache 2.0), pinned to
  upstream commit `f7f00ca7fb869683eb732c010299d901457f19c3`. HuggingFace
  revision recorded in `configs/fine_tune_config.yaml`.
- **Architecture:** 8-layer mixture-of-experts encoder, 128 experts of
  which 4 are routed per token, hidden_size 640, vocab 200,064
  (o200k_base tokenizer), bidirectional left/right context 128 each.
  Total ~1.4 B parameters; checkpoint size 2.6 GB in bfloat16. See
  `external/privacy-filter` for the upstream reference implementation.
- **Label space:** twelve PII categories — eight inherited from the
  upstream base and four added for Greek (`amka`, `afm`, `adt`,
  `iban_gr`). Full list in `configs/label_space.json`.
- **Training data:** v1 production splits, 32,061 records total
  (21,124 train / 3,173 validation / 3,171 test / 4,593 hard test).
  See `docs/DATASHEET.md` §2 and AUDIT_LOG.md §3 for the full
  generation provenance and SHA-256 hashes.
- **Training run:** AWS EC2 spot run `20260426T135853Z` on
  `g6e.xlarge` (L40S 48 GB) in `eu-north-1`. 3 epochs, batch size 4,
  gradient accumulation 4 (effective batch 16), learning rate 5e-5,
  weight decay 0.01, max grad norm 1.0, seed 1337, n_ctx 256, output
  dtype bfloat16. Wall clock ~6 min main training plus ~10 min
  evaluation; cost ~$0.27.
- **Training code:** `scripts/aws/ec2_spot_finetune.sh` (EC2 spot
  launcher) wrapping `python -m opf train` from the upstream package.
- **Licence of the fine-tuned weights:** Greek Privacy Filter
  Non-Commercial License v1.0 (`LICENSE-MODEL-NC`). A separate
  commercial licence is available from the provider on request
  (`haritos19@gmail.com`).
- **Contact:** Chariton Kypraios, `haritos19@gmail.com`.

## 2. Intended use

- **Primary intended uses.** Research and non-commercial deployments
  that need token-level detection of PII in Modern Greek text.
- **Primary intended users.** NLP researchers, privacy-engineering
  teams, and downstream builders preparing GDPR-compliant pipelines.
- **Out-of-scope uses.** Automated redaction, deletion, publication,
  legal disclosure, or any other irreversible action on personal data
  taken on the basis of the model's output alone. Any such action
  requires a human-in-the-loop review (see §6).

## 3. Factors

- **Language.** Modern Greek. The training corpus spans commercial,
  legal, medical, HR, banking, administrative, telephonic, and code-
  comment registers; see `docs/DATASHEET.md` §3 for the full register
  list.
- **Script.** Person and address spans remain in Greek script; emails
  and URLs are skewed approximately 80 / 20 toward Latin
  transliteration, reflecting real-world usage.

## 4. Metrics

All numbers below are produced by `python -m opf eval` (upstream tool)
on the v1 fine-tune run `20260426T135853Z`. The baseline column is the
unmodified `openai/privacy-filter` checkpoint evaluated with
`--eval-mode untyped` (its label scheme does not include `amka`,
`afm`, `adt`, or `iban_gr`); the finetuned column is the v1 weights
evaluated with `--eval-mode typed` (per-class match required). Raw
JSON: `artifacts/metrics/{baseline,finetuned}_{test,hard_test}_metrics.json`.

### 4.1 Detection (any-PII, span-level)

| split | metric | baseline | finetuned | delta |
|---|---|---:|---:|---:|
| test | precision | 0.8417 | 0.9865 | +0.1448 |
| test | recall | 0.7208 | 0.9907 | +0.2699 |
| test | F1 | 0.7766 | **0.9886** | +0.2120 |
| hard_test | precision | 0.8114 | 0.9862 | +0.1748 |
| hard_test | recall | 0.7268 | 0.9873 | +0.2605 |
| hard_test | F1 | 0.7668 | **0.9868** | +0.2200 |

### 4.2 Detection (any-PII, token-level)

| split | metric | baseline | finetuned | delta |
|---|---|---:|---:|---:|
| test | precision | 0.9282 | 0.9964 | +0.0682 |
| test | recall | 0.7797 | 0.9981 | +0.2184 |
| test | F1 | 0.8475 | **0.9972** | +0.1497 |
| hard_test | precision | 0.9213 | 0.9939 | +0.0726 |
| hard_test | recall | 0.7967 | 0.9944 | +0.1977 |
| hard_test | F1 | 0.8545 | **0.9942** | +0.1397 |

### 4.3 Per-class span F1 — finetuned model on test split

| class | precision | recall | F1 |
|---|---:|---:|---:|
| `private_url` | 1.0000 | 1.0000 | **1.0000** |
| `amka` | 0.9977 | 1.0000 | **0.9989** |
| `adt` | 1.0000 | 0.9974 | **0.9987** |
| `private_email` | 0.9978 | 1.0000 | **0.9989** |
| `private_date` | 0.9957 | 1.0000 | **0.9979** |
| `iban_gr` | 0.9954 | 1.0000 | **0.9977** |
| `secret` | 0.9946 | 0.9973 | **0.9959** |
| `private_person` | 0.9961 | 0.9942 | **0.9952** |
| `private_address` | 0.9915 | 0.9979 | **0.9947** |
| `account_number` | 0.9575 | 0.9817 | **0.9694** |
| `private_phone` | 0.9770 | 0.9573 | **0.9671** |
| `afm` | 0.9341 | 0.9634 | **0.9486** |

Lowest typed F1 is `afm` at 0.9486 — a 9-digit numeric identifier
that surface-level resembles `account_number` and 9-digit `phone`
fragments. This is the class where the most performance is left on
the table for a hyperparameter sweep or a v1.5 data-augmentation
pass.

### 4.4 Training trajectory

| epoch | train_loss | val_loss | val_token_accuracy |
|---|---:|---:|---:|
| 1 | 0.0594 | 0.0121 | 0.9958 |
| 2 | 0.0083 | **0.0095** | 0.9969 |
| 3 | 0.0056 | 0.0104 | 0.9970 |

Validation loss reached its minimum after epoch 2 with a small uptick
at epoch 3 (slight overfitting — magnitude small, no reduction in
test metrics). An earlier-stopping point at epoch 2 would be the
default selection if the run were repeated.

## 5. Evaluation data

- **Test set.** `data/processed/test.jsonl` — held out for release-
  time reporting only.
- **Hard-test set.** `data/processed/hard_test.jsonl` — enriched with
  edge cases and Qwen-generated hard negatives that present PII-
  adjacent surface features.

Both derive from the synthetic pipeline documented in
`docs/DATASHEET.md`. A provenance audit over every split is produced
by `scripts/verify_provenance.py` and stored in
`artifacts/metrics/provenance_report.json`.

## 6. Ethical considerations

- **Mandatory human-in-the-loop review.** The detector is not
  guaranteed to recall all PII and is not guaranteed to avoid all
  false positives. A downstream system that acts on the model's output
  must include a human review step before any irreversible action is
  taken on a data subject's personal data.
- **Synthetic training data.** No real personal data is used to train
  the model. Surface features observed in production may therefore be
  under-represented; re-evaluation against a customer-specific labelled
  sample is recommended before production deployment.
- **Bias.** The rule-based name generator draws from a small curated
  list of common Greek given and family names. Minority, diaspora,
  and foreign-origin names are under-represented; the model is likely
  to detect them at a lower rate than names drawn from the generator's
  list.
- **Transliteration.** An 80 / 20 split between Latin-transliterated
  and Greek-script contact fields reflects real-world Greek usage but
  may under-represent the long tail of internationalised-domain
  variants.

## 7. Caveats and recommendations

- Use the model as a triage tool. It is not designed to be the sole
  basis for a legal-disclosure determination.
- Re-evaluate on a labelled sample drawn from the deployer's own data
  before placing the model in production.
- Monitor distributional drift: real-world Greek text will differ from
  the synthetic distribution documented in `docs/DATASHEET.md` §2.
- Review `docs/DPIA_NOTE.md` and complete the Article 30 record in
  `docs/GDPR_ART30_ROPA.md` before deploying the model on real Greek
  personal data.
