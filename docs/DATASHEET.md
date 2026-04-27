# Datasheet — Greek Privacy Filter training dataset

This datasheet follows the structure of Gebru et al., "Datasheets for
Datasets" (Communications of the ACM, 2021), adapted to the scope of a
synthetic fine-tuning corpus.

## 1. Motivation

The dataset exists to fine-tune `openai/privacy-filter`, a token-level
PII classifier, on Modern Greek text. It adds four Greek-specific
label classes (`amka`, `afm`, `adt`, `iban_gr`) to the eight
categories inherited from the upstream base model.

The provider funded the creation of the dataset. No external grant or
third-party data contribution was received.

## 2. Composition

Each record is a JSON object with three top-level fields:

- `text` — a Greek sentence between 30 and 300 characters.
- `label` — a list of `{category, start, end}` span annotations.
  An empty list denotes a hard-negative record containing no PII.
- `info` — the provenance metadata `{difficulty, domain, source,
  strategy}` written at generation time.

The label space is: `amka`, `afm`, `adt`, `iban_gr`,
`private_person`, `private_phone`, `private_address`, `private_email`,
`private_date`, `private_url`, `account_number`, `secret`.

Split sizes after the latest curation run are recorded in
`artifacts/metrics/curation_report.json`. For the v3 smoke build
(reference samples committed to `data/samples/`):

- Train: 8,088 records.
- Validation: 1,217 records.
- Test: 1,217 records.
- Hard test: 1,219 records.
- Total: 11,741 records.

The v1 production build (run `20260426T092703Z`, AWS eu-north-1,
g6e.xlarge spot, Qwen3.6-35B-A3B Q8) was produced on 2026-04-26 from
50,000 generated samples plus 746 hard-negatives, with a 33% post-merge
deduplication ratio:

- Train: 21,124 records.
- Validation: 3,173 records.
- Test: 3,171 records.
- Hard test: 4,593 records.
- Total: 32,061 records.

The v1 build is the dataset against which the released fine-tuned
checkpoint is evaluated. SHA-256 hashes for each split are recorded
in `artifacts/manifest/manifest_v1.json` (committed) and reproducible
locally with `scripts/hash_manifest.py` against the synced run
artefacts under `data/processed/aws-v1-20260426T092703Z/`.

Span counts per class in the train split of the reference (smoke)
build (authoritative source: `artifacts/metrics/curation_report.json`
stage 3):

| Class | Spans (smoke) |
|---|---:|
| `private_person` | 1,203 |
| `private_address` | 1,136 |
| `_hard_negative` (records with no PII) | 1,041 (13 % of records) |
| `private_email` | 951 |
| `amka` | 939 |
| `private_phone` | 937 |
| `private_date` | 876 |
| `iban_gr` | 833 |
| `adt` | 828 |
| `afm` | 759 |
| `account_number` | 756 |
| `secret` | 584 |
| `private_url` | 580 |

Span counts per class in the v1 train split (54,668 spans across
21,124 records, balanced by design):

| Class | Spans (v1) |
|---|---:|
| `private_person` | 3,465 |
| `private_address` | 3,192 |
| `private_date` | 3,107 |
| `private_email` | 2,998 |
| `amka` | 2,967 |
| `private_phone` | 2,918 |
| `iban_gr` | 2,875 |
| `account_number` | 2,853 |
| `adt` | 2,754 |
| `afm` | 2,717 |
| `private_url` | 2,433 |
| `secret` | 2,389 |
| `_hard_negative` | 518 (records with empty label) |

## 3. Collection process

All data is synthetic. No personal data is collected or processed at
any stage of the pipeline. Three origins contribute to the output:

1. **Rule-based PII generators** in
   `scripts/generate_commercial_safe_greek_pii.py` produce the PII
   values themselves (names, AMKA, AFM, ADT, IBAN_GR, phones, emails,
   URLs, addresses, dates, and secrets). These generators are
   authored in their entirety by the provider.
2. **Carrier text** drawn from commercial-safe Greek corpora (listed
   in §5) is used as the surrounding context into which the PII
   values are injected.
3. **Local language-model generation** using
   `unsloth/Qwen3.6-35B-A3B-GGUF` served over `llama.cpp`. Qwen is
   given a list of `(category, value)` pairs and a register directive
   (one of twelve registers, including phone-call transcripts, SMS,
   voicemail, business email, medical chart, HR letter, government
   form, support ticket, and social-media post); it writes numbered
   Greek sentences that embed each value verbatim. Output is parsed
   and labelled algorithmically; there is no human-in-the-loop
   selection of individual sentences.

**Hard negatives.** `scripts/generate_qwen_hard_negatives.py` prompts
Qwen for Greek sentences that contain PII-adjacent surface features
(numeric statistics, dates, identifiers, company names) but no
personal data. Fourteen topic families are rotated per batch so the
hard-negative pool is lexically and topically diverse.

**Latinisation of contact fields.** A deterministic post-processing
step (`scripts/postprocess_latinize_contacts.py`) transliterates
approximately eighty percent of Greek-script email and URL spans to
Latin script using ELOT 743, leaving approximately twenty percent in
Greek. This reflects real-world Greek usage, in which email local-parts
and URL slugs are predominantly Latin.

## 4. Pre-processing

The curation pipeline (`scripts/curate_generated_dataset.py`) applies
three deterministic, seed-controlled stages:

1. **Quality filter.** Text length in [30, 300] characters; Greek
   character ratio ≥ 0.4 of the alphabetic characters; no chat-model
   artefact patterns (for example, `Here's a`, `<think>`, or
   `Παράδειγμα:`); span sanity (offsets inside the text, strict order,
   no empty spans, no duplicate `(category, start, end)` triples).
2. **Duplicate removal.** Exact-text deduplication after whitespace
   normalisation, followed by a per-skeleton cap of 300 records
   (skeleton = text with each span replaced by its category
   placeholder) to prevent any single template from dominating the
   output.
3. **Stratified split.** Class-balanced allocation to train,
   validation, test, and hard-test splits by proportional-remaining-
   quota scoring. Records flagged `difficulty=hard` are routed to
   hard-test first, subject to per-class quotas.

Each stage emits its own statistics to
`artifacts/metrics/curation_report.json`.

## 5. Sources and their licences

| Source | Licence | Role |
|---|---|---|
| `openai/privacy-filter` | Apache License 2.0 | Fine-tune base model. |
| `unsloth/Qwen3.6-35B-A3B-GGUF` | Apache License 2.0 | Synthetic-sentence generator (local inference). |
| `PleIAs/Greek-PD` | Public domain | Carrier text. Downloader in `scripts/download_carrier_greek_pd.py`; on-host disabled in the current run because of a Windows paging-file limitation — see `docs/AUDIT_LOG.md` §2 item 4. Re-enabled on AWS. |
| Mozilla Common Voice Greek text corpus | CC0 | Carrier text. |
| `AI-team-UoA/greek_legal_code` | CC-BY-4.0 | Carrier text (legal register). |
| Rule-based generators in this repository | Apache License 2.0 | PII values and template skeletons. |

Attribution for the CC-BY-4.0 material: Papaloukas, C., Chalkidis, I.,
Athinaios, K., Pantazi, D.-A., and Koubarakis, M., 2021. "Multi-
granular Legal Topic Classification on Greek Legislation." Natural
Legal Language Processing Workshop. The full attribution block
appears in `LICENSING.md` §3 and `ATTRIBUTION.txt`.

## 6. Intended uses

The dataset is intended for fine-tuning `openai/privacy-filter` on
Greek text for research and non-commercial deployments. The first
release (v1, dataset run `20260426T092703Z`, 32,061 records) was used
on 2026-04-26 to produce the v1 fine-tuned weights documented in
`docs/MODEL_CARD.md` §1 and §4 (run `20260426T135853Z`). Commercial
use of the fine-tuned weights requires a separate licence; see
`LICENSING.md` §4.

The dataset is not intended for any of the following uses, and the
provider does not warrant that it is suitable for any of them:

- Training a general-purpose Greek language model.
- Deploying a standalone automated-redaction system that acts on the
  model's output without human review.
- Making legal determinations about the presence or absence of
  personal data in a document.

## 7. Distribution

The artefacts are released on three publishing surfaces:

| Artefact | Hosting | Licence |
|---|---|---|
| Source code, configurations, documentation, audit evidence (manifests and reports), and 100-record reference samples per split | GitHub (this repository) | Apache License 2.0. |
| Full train, validation, test, and hard-test splits — v1 release is 32,061 records (50 k input, 33 % deduplication ratio); the larger production target remains 100,000 records | HuggingFace Dataset repository, tagged to the git commit that produced them | Apache License 2.0 on the JSONL records; the carrier text inherits its upstream licence as listed in §5. |
| Fine-tuned model weights | HuggingFace Model repository, tagged to the git commit and to the dataset tag | Greek Privacy Filter Non-Commercial License v1.0 (see `LICENSE-MODEL-NC`). |

SHA-256 digests of the full dataset files are recorded in the per-run
`manifest.json` uploaded to S3 by
`scripts/aws/ec2_spot_generate.sh` and then committed to
`artifacts/manifest/` at the time of release. An auditor can verify
that any file downloaded from HuggingFace matches the git commit that
produced it.

Commercial licensing of the fine-tuned weights is described in
`LICENSING.md` §4.

## 8. Maintenance

The scripts under `scripts/` are the authoritative build process.
Re-running them with the seeds recorded in `docs/AUDIT_LOG.md`
reproduces the dataset bit-for-bit from a given git commit.

Per-record provenance is stored in every record's `info` field and is
verified at release time by `scripts/verify_provenance.py`.

Changes to the pipeline are recorded chronologically in
`docs/AUDIT_LOG.md` and tied to the corresponding git commit hash.

## 9. Ethical considerations

- **No real personal data is processed.** All PII values are
  rule-generated; carrier text is from public-domain or permissively-
  licensed corpora.
- **Name-bank bias.** The rule-based name generator draws from a
  small curated list of common Greek given and family names; minority,
  diaspora, and foreign-origin names are under-represented and the
  fine-tuned model is likely to detect them at a lower rate than names
  in the bank.
- **Surface-form bias.** Emails and URLs are skewed approximately
  80 / 20 toward Latin transliteration. This reflects real-world Greek
  usage but may under-represent Greek-script internationalised-domain
  variants.
- **Human-in-the-loop requirement.** The detector trained on this
  dataset is not guaranteed to find all PII, nor to avoid all false
  positives. Outputs must be reviewed by a human before any action is
  taken on real personal data. See `docs/MODEL_CARD.md` §6.
