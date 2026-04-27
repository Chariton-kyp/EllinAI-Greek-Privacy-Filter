# Reference samples

One hundred records per split are committed here so anyone cloning the
repository can inspect the training-data format, register coverage, and
label conventions without running the full 2-hour generation pipeline.

| File | Source |
|---|---|
| `train_sample_100.jsonl` | 100 random records from the train split of the v3 smoke build |
| `validation_sample_100.jsonl` | 100 random records from validation |
| `test_sample_100.jsonl` | 100 random records from test |
| `hard_test_sample_100.jsonl` | 100 random records from hard_test |

SHA-256 digests for these files are recorded in
`artifacts/manifest/samples_manifest.json`, and their provenance audit
is in `artifacts/metrics/samples_provenance_report.json`.

**The full 100,000-record dataset is not in this repository.** It is
released as a HuggingFace Dataset; the entry linked in
`docs/DATASHEET.md` §7 will include SHA-256 digests that let any auditor
verify the downloaded data matches the build that produced the
fine-tuned weights.

To reproduce the full dataset locally from this repository, see
`README.md` §"End-to-end reproducible build" or run
`scripts/aws/ec2_spot_generate.sh` for the cloud build.

## Note on `sk-...` strings and other PII-shaped values

Any `sk-...` tokens, 9-digit numbers, 11-digit numbers, `GR...` IBANs,
Greek-named emails, and street-address strings in these samples are
**synthetic ground-truth labels** produced by the rule-based generators
in `scripts/generate_commercial_safe_greek_pii.py`. They are not real
API keys, real VAT numbers, real identity-card numbers, real IBANs, or
real personal data. GitHub's automated secret scanning may flag some
`sk-...` patterns in this file — those are false positives by design
(the detector being trained on this data looks specifically for
`secret`-category tokens).
