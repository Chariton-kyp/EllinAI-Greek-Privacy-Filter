# Greek PII Public Benchmark v1

A 100-case hand-crafted Greek-language benchmark for evaluating PII
detection systems against 24 PII classes. All values are **synthetic**
(format-realistic but fictional) — no real personal data is included.

## Purpose

There is no public Greek PII benchmark dataset that covers the 24-class
taxonomy used by the Greek Privacy Filter project (after a thorough
review of CLARIN-EL, ILSP/Athena RC, ELRC, ELRA, HuggingFace
ai4privacy, Piiranha, Nemotron-PII — none cover Greek with this
breadth). This benchmark fills that gap with a **public-safe**, 
**reproducible**, **license-clean** evaluation set.

It is **independent** from any proprietary benchmark used for
commercial calibration. Anyone can clone the repo and reproduce the
metrics published in the v3 release notes.

## Methodology

- **100 cases** across 10 registers (10 cases each):
  1. Tax / Government (ΑΑΔΕ, ΔΟΥ, ΕΦΚΑ letters)
  2. Medical / Healthcare (referrals, prescriptions, diagnoses)
  3. Banking / Financial (statements, transfers, alerts)
  4. Court / Legal (decisions, summons, proceedings)
  5. HR / Employment (contracts, payroll, ESHARES-style notes)
  6. Customer Support (chat logs, ticket replies)
  7. Insurance (vehicle, health policies)
  8. Vehicle / Driving (registration, license renewals)
  9. Education / School (enrollment, grades)
  10. Informal / SMS (everyday Greek text messages)

- **24 PII classes covered** with minimum 4-5 cases each. Spans are
  hand-graded by exact label + start/end character offsets.

- **All synthetic values**:
  - AFM: 9-digit fictional (random, no checksum)
  - AMKA: 11-digit (DDMMYY-prefix realistic)
  - ADT: Greek 2-letter prefix + 6 digits
  - IBAN: GR-prefix + 25 chars (random)
  - Phones: Greek format (mobile 69x or landline 21x)
  - Names: synthetic Greek-format names
  - Emails: example.com / firm.gr / aade.gr-style fictional
  - Dates: 2024-2026 range

## Files

- `cases.jsonl` — final benchmark artifact (built from sources)
- `cases_part_1.py` ... `cases_part_4.py` — Python source modules with 25 cases each
- `build.py` — validator + JSONL writer (run after editing parts)
- `LICENSE` — CC-BY-4.0 (free use with attribution)

## Usage

```bash
# Rebuild the JSONL artifact from the Python sources:
python benchmarks/greek_pii_public_v1/build.py

# Run the 4-way model comparison:
python scripts/v3/local_4way_benchmark.py \
    --benchmark benchmarks/greek_pii_public_v1/cases.jsonl \
    --output artifacts/metrics/benchmark_4way_local.json
```

## Class semantic conventions

For two classes that may seem ambiguous, the benchmark uses these
fixed conventions — important for typed F1 interpretation:

- **`secret`** covers all credential-like opaque strings: API tokens,
  passwords, AWS-style access keys, OTP codes, telehealth meeting
  codes, password-reset temporaries. If a string is "presented to a
  machine for authorisation", it is a `secret`.
- **`account_number`** covers all non-IBAN account-shape identifiers:
  bank account numbers, transaction reference IDs, order IDs (ORD-…),
  insurance policy numbers (HEALTH-…, AUTO-…, TRV-…), student
  registry numbers (ΠΑ-/ΠΚ-/2026-AT-…), library card numbers, research
  grant references. Anything that names a record-identifier in a
  system, except IBANs (separate class).
- **`private_person`** uses the surface form as it appears in the
  text (vocative, genitive, nominative all valid). For doctor / lawyer
  names, the title (Δρ., κ.) is **not** part of the span; the labelled
  span is the surname-only when no first name appears, and full-name
  when both appear.

These conventions affect F1 interpretation: a model that segments
identical strings into different "right" classes will be penalised
even if the segmentation is semantically reasonable.

## Audit notes (v1)

- **Provenance**: Cases were drafted with AI assistance (Claude API)
  and curated, validated, and refined by the maintainer (Chariton
  Kypraios). Anthropic Commercial Terms assign Output rights to
  the API customer — see Anthropic's commercial terms of service.
- **Duplicates**: Each PII value (AFM, AMKA, IBAN, passport, VIN,
  plate, driver_license) appears in **at most 2 cases** to limit
  memorisation-driven F1 inflation.
- **Class N (small samples warning)**: `pcn` (n=6), `imei` (n=3),
  `cvv` (n=6 with 3 unique values), `mac_address` (n=6) — per-class
  F1 on these is statistically noisy. Treat aggregate F1 as primary.
- **Geographic distribution**: Greek landlines include Athens (210),
  Thessaloniki (2310), Patras (2610), Heraklion (2810), Larissa
  (2410), and Piraeus (210).

## License

The benchmark text and annotations are released under
**Creative Commons Attribution 4.0 (CC-BY-4.0)**. The synthetic PII
values are fictional and carry no personal-data restrictions.

If you publish results using this benchmark, please cite this
repository.

## Citation

```bibtex
@misc{kypraios2026greekpiipublicbenchmark,
  author = {Chariton Kypraios},
  title  = {Greek PII Public Benchmark v1},
  year   = {2026},
  url    = {https://github.com/Chariton-kyp/EllinAI-Greek-Privacy-Filter}
}
```
