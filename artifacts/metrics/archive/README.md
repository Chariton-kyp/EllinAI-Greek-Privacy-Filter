# Archived baseline metrics

The four JSON files in this directory were produced by
`scripts/run_opf_eval.py` against an earlier iteration of the
training / validation / test / hard-test splits (8,000 / 1,000 /
2,000 / 2,000 records respectively). They evaluate the unmodified
`openai/privacy-filter` base checkpoint at
`checkpoints\base\privacy-filter`, before any fine-tune.

The current committed splits in `data/processed/` contain
8,088 / 1,217 / 1,217 / 1,219 records. Because the record counts do
not match, these archived baselines cannot be used as the
"before" side of a before-vs-after comparison against any fine-tune
run on the current splits. A fresh baseline will be produced as the
first step of the next fine-tune pipeline run against the
post-AWS-generated splits; its output file will be written to
`artifacts/metrics/baseline_test_metrics.json` per
`configs/fine_tune_config.yaml` field `output.baseline_metrics_file`.

These files are retained unchanged in this archive directory as
historical evidence of the earlier iteration and as a provenance
record of the pipeline's evolution.
