# Licensing

This file records the licence applied to each artefact in the
repository and the terms on which the artefacts may be used by third
parties.

## 1. Artefacts released by this project

| Artefact | Licence |
|---|---|
| Source code (`scripts/`, `configs/`, `src/`) | Apache License, Version 2.0 (see `LICENSE-CODE`). |
| Documentation (`docs/`, top-level `*.md`, `NOTICE`, `ATTRIBUTION.txt`) | Apache License, Version 2.0 (see `LICENSE-CODE`). |
| Reference data samples (`data/samples/*.jsonl`, `data/seed/golden_examples.jsonl`) | Apache License, Version 2.0 (see `LICENSE-CODE`). |
| Real-world OOD evaluation benchmark (`data/realworld_benchmark/cases.jsonl`) | Apache License, Version 2.0. Hand-crafted synthetic Greek cases authored for this project; all PII values are randomly generated and do not reference real persons. |
| Public audit evidence (`artifacts/manifest/*.json`, `artifacts/metrics/*.json`) | Apache License, Version 2.0. SHA-256 dataset manifests and benchmark-triage metrics; reproducibility evidence containing no copyrighted content. |
| Fine-tuned model weights (when released at `artifacts/model/…` and published to HuggingFace) | Greek Privacy Filter Non-Commercial License v1.0 (see `LICENSE-MODEL-NC`). A separate commercial licence is available from the provider on request (haritos19@gmail.com). |

As the copyright holder of the fine-tuned weights, the provider
retains the right to use those weights commercially in his own
products and services. The non-commercial licence governs third-party
use only.

## 2. Third-party components relied on

| Component | Licence |
|---|---|
| `openai/privacy-filter` — Lite tier base + base for v1/v2 weights | Apache License, Version 2.0. |
| `google/gemma-4-31B-it` (via `unsloth/gemma-4-31B-it-unsloth-bnb-4bit`) — v3 teacher + Ultra tier base | Apache License, Version 2.0. |
| `google/gemma-4-E4B-it` (via `unsloth/gemma-4-E4B-it-unsloth-bnb-4bit`) — v3 Pro tier base | Apache License, Version 2.0. |
| `google/gemma-4-E2B-it` (via `unsloth/gemma-4-E2B-it-unsloth-bnb-4bit`) — v3 Mini tier base | Apache License, Version 2.0. |
| `Qwen/Qwen3-4B` — v3 Max tier base | Apache License, Version 2.0. |
| `unsloth/Qwen3.6-35B-A3B-GGUF` — local synthetic-data generator | Apache License, Version 2.0. |
| `ilsp/Meltemi-7B-Instruct-v1.5` — evaluated as an alternate generator | Apache License, Version 2.0. |
| `PleIAs/Greek-PD` — Greek public-domain carrier text | Public domain. |
| Mozilla Common Voice Greek text corpus — carrier text | CC0. |
| `AI-team-UoA/greek_legal_code` — Greek legal carrier text | CC-BY-4.0 (attribution required). |
| Rule-based PII generators in `scripts/generate_commercial_safe_greek_pii.py` | Apache License, Version 2.0 (this repository). |

The training-data chain is compatible with commercial reuse end-to-end.
The CC-BY-4.0 material (`greek_legal_code`) requires the attribution
shown in §3 below.

## 3. Attribution notice to ship with the weights

The following block is reproduced verbatim in `ATTRIBUTION.txt`. Any
redistribution of the fine-tuned weights must include it in the
`USAGE.txt` file emitted by `opf train`, in the HuggingFace model-card
README, or in a file named `ATTRIBUTION.txt` alongside the weights,
whichever is appropriate to the distribution channel.

```
This model is derived from:
  • OpenAI Privacy Filter (Apache 2.0)
    https://huggingface.co/openai/privacy-filter
  • Qwen3.6-35B-A3B (Apache 2.0, Alibaba Qwen team; Unsloth Dynamic GGUF)
    https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF
  • PleIAs/Greek-PD (public domain)
  • Mozilla Common Voice Greek text corpus (CC0)
  • Greek Legal Code corpus (CC-BY-4.0)
    Papaloukas et al. 2021, AI Team, University of Athens
    https://huggingface.co/datasets/AI-team-UoA/greek_legal_code

Base-model licence: Apache License, Version 2.0 (retained).
Fine-tuned weights licence: Greek Privacy Filter Non-Commercial
                            License v1.0, or a separate commercial
                            licence available on request.
```

The `USAGE.txt` emitted by the upstream `opf train` command is to be
preserved inside `artifacts/model/finetuned-opf/`.

## 4. Commercial licence procedure

A third party that wishes to use the fine-tuned weights commercially
must:

1. Contact the provider at `haritos19@gmail.com` with a description
   of the intended use (identity of the commercial entity, scope of
   deployment, estimated request volume, retention policy).
2. Sign a written commercial licence agreement supplied by the
   provider that supersedes `LICENSE-MODEL-NC` for the licensee only.
3. Include the attribution notice in §3 in the commercial product's
   user-facing documentation.

Until a written commercial licence is in place, third-party
commercial use is prohibited by `LICENSE-MODEL-NC` §4. Internal
evaluation by a commercial entity for the purpose of negotiating a
licence is permitted under `LICENSE-MODEL-NC` §2 provided no
production deployment results.

## 5. Non-commercial definition

`LICENSE-MODEL-NC` §2 defines "non-commercial" in terms substantially
similar to Creative Commons Attribution-NonCommercial 4.0: use that is
not primarily intended for or directed toward commercial advantage or
monetary compensation. Academic research, classroom teaching, personal
experimentation, open-source contribution, and pre-purchase evaluation
are non-commercial. Sale of a service principally powered by the model,
or its inclusion in a paid product, is commercial and requires a
licence under §4.

## 6. Revocability

`LICENSE-MODEL-NC` §1 grants a revocable non-commercial licence. The
revocability is intentional: it allows the provider to publish a
superseding version of the licence without tracking individual
downstream users, and to withdraw the licence from a specific party
that has materially breached `LICENSE-MODEL-NC` §4 or §3
(attribution). The provider does not otherwise intend to revoke
licences granted to compliant users.

## 7. Quarantined data

`data/archive_pre_meltemi_2026-04-23/` contains synthetic data from
earlier experimental runs that used third-party language-model APIs.
The directory is excluded from git via `.gitignore`. It must not be
re-used in training, seeding, or few-shot prompting. Scheduled
permanent deletion: 2026-05-23.

## 8. Training data and GDPR

Training data is fully synthetic. No personal data is processed
during training (see `docs/DPIA_NOTE.md` §1). GDPR obligations that
attach to the processing of personal data do not apply to the training
pipeline. Obligations on the data processed at inference time are the
deployer's responsibility; see `docs/DPIA_NOTE.md` §2 and the template
at `docs/GDPR_ART30_ROPA.md`.
