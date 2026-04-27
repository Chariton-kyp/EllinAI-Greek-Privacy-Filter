# Manifest directory

SHA-256 + line-count manifests for every dataset built by this
repository. Each manifest is produced by `scripts/hash_manifest.py`
and is the authoritative cryptographic record that ties a JSONL split
to a specific git commit.

## Files

| File                  | Describes                                                                                                                                                            |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `manifest_v1.json`    | **v1 production release** (AWS spot generation run `20260426T092703Z`). 32,061 records: 21,124 train / 3,173 validation / 3,171 test / 4,593 hard_test.              |
| `manifest_v1_1.json`  | **v1.1 release** — same 32,061 records as v1 with AFM span boundaries cleaned by `scripts/relabel_afm_spans.py` (4,440 AFM spans, all reduced to digit-only form). Same line-counts as v1; SHA-256 hashes differ because the JSONL bytes change wherever an AFM `start`/`end` integer was rewritten. |
| `manifest.json`       | Reference seed-build manifest used for development sanity checks (8,088 / 1,217 / 1,217 / 1,219 records). Pre-dates the v1 release; retained as a fixture.            |
| `samples_manifest.json` | Manifest for the four 100-record reference samples under `data/samples/`. Lets a downstream consumer verify the samples without running the full pipeline.           |

## Reproducing

The split files referenced by `manifest_v1.json` live under
`data/processed/aws-v1-20260426T092703Z/` after a clone has run the
AWS-pipeline replay documented in `scripts/aws/README.md` Part A.
The directory itself is gitignored to keep the repository small.

To verify a downloaded copy:

```bash
python scripts/hash_manifest.py \
    --inputs data/processed/aws-v1-20260426T092703Z/data/train.jsonl \
             data/processed/aws-v1-20260426T092703Z/data/validation.jsonl \
             data/processed/aws-v1-20260426T092703Z/data/test.jsonl \
             data/processed/aws-v1-20260426T092703Z/data/hard_test.jsonl \
    --output - | diff - artifacts/manifest/manifest_v1.json
```

If the diff is empty the local copy matches the published manifest.
