# v2.13 vs v3 comparison

This note records the public-safe aggregate comparison between the final
v2 token-classifier baseline and the current v3 line.

The private 200-case OOD benchmark is not committed to the public
repository. The aggregate results below were produced locally from the
locked benchmark file `<locked_200_case_ood.jsonl>`, which
contains 200 OPF-format records and validates against the 24-class
label space in `configs/label_space_v2.json`.

## Same-dataset OPF comparison

These two runs use the same factors:

- Dataset: `<locked_200_case_ood.jsonl>`
- Cases: 200
- Classes: 24
- Eval mode: typed
- Decoder: Viterbi
- Context window: `n_ctx=256`
- Span metric space: character
- Device: CUDA
- `OPF_MOE_TRITON=0` because Triton is not installed on this host

| Model | Checkpoint | Detection span precision | Detection span recall | Detection span F1 | Token accuracy |
|---|---|---:|---:|---:|---:|
| v2.13 token classifier | `artifacts/finetune-v2-13-20260501T202431Z/model` | 0.9037 | 0.8138 | **0.8564** | 0.9299 |
| v3 Lite token classifier | `artifacts/v3/students/lite-v3-local` | 0.8853 | 0.7465 | **0.8100** | 0.9126 |

Result: under identical OPF token-classifier evaluation settings, v2.13
currently beats v3 Lite on exact span detection. v3 Lite may still be
useful as a distilled small tier, but it should not be represented as
better than v2.13 on this exact OPF benchmark without the private
additional calibration layer.

## v3 causal-LM tiers

v3 Mini and Ultra are causal-LM tiers, so they do not run through
`python -m opf eval`. Existing private harness results on the same
200-case benchmark are:

| Model | Harness | F1 |
|---|---|---:|
| v3 Mini | private causal-LM JSON-span harness | 0.8796 |
| v3 Ultra teacher | private causal-LM JSON-span harness | 0.9588 |

Those figures are useful for product direction, but they are not the
same OPF token-classifier evaluation as the v2.13 vs v3 Lite table
above. For release claims, keep the metric family explicit.

## Commands used

```bash
python scripts/validate_label_space.py \
  --label-space configs/label_space_v2.json \
  --inputs <locked_200_case_ood.jsonl>

OPF_MOE_TRITON=0 python -m opf eval <locked_200_case_ood.jsonl> \
  --checkpoint artifacts/finetune-v2-13-20260501T202431Z/model \
  --device cuda \
  --n-ctx 256 \
  --eval-mode typed \
  --decode-mode viterbi \
  --metrics-out artifacts/v3/compare/v2_13_same_200_metrics.json \
  --predictions-out artifacts/v3/compare/v2_13_same_200_predictions.jsonl \
  --preprocess-workers 1 \
  --preprocess-chunksize 16 \
  --window-batch-size 1

OPF_MOE_TRITON=0 python -m opf eval <locked_200_case_ood.jsonl> \
  --checkpoint artifacts/v3/students/lite-v3-local \
  --device cuda \
  --n-ctx 256 \
  --eval-mode typed \
  --decode-mode viterbi \
  --metrics-out artifacts/v3/compare/v3_lite_same_200_metrics.json \
  --predictions-out artifacts/v3/compare/v3_lite_same_200_predictions.jsonl \
  --preprocess-workers 1 \
  --preprocess-chunksize 16 \
  --window-batch-size 1
```

The metrics JSONs and prediction JSONLs above are private trace
artefacts because they reference the locked benchmark file. Keep them
under `artifacts/v3/` or the non-public audit records, not in the
public repository.
