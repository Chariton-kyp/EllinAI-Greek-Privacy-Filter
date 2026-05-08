# Licensing

This repository is a non-commercial public release.

## 1. Public-release licence

All project-authored material in this repository is released to third
parties under `LICENSE-NC`:

| Artefact | Public-release terms |
|---|---|
| Source code (`scripts/`, `configs/`, `src/`) | Non-commercial use only under `LICENSE-NC`. |
| Documentation (`docs/`, top-level `*.md`, `NOTICE`, `ATTRIBUTION.txt`) | Non-commercial use only under `LICENSE-NC`. |
| Reference data samples (`data/samples/*.jsonl`, `data/seed/golden_examples.jsonl`) | Non-commercial use only under `LICENSE-NC`. |
| Public audit evidence (`artifacts/manifest/*.json`, selected `artifacts/metrics/*.json`) | Non-commercial use only under `LICENSE-NC`; aggregate and provenance evidence only. |
| Fine-tuned model weights, adapters, or checkpoints produced by this project | Non-commercial use only under `LICENSE-NC`. |

No commercial license is granted by this public release. All commercial
rights in project-authored material are reserved by the copyright
holder, Chariton Kypraios.

## 2. Third-party components relied on

Third-party components retain their own licences. This repository does
not grant rights beyond those provided by the original licensors.

| Component | Licence / terms |
|---|---|
| `openai/privacy-filter` — Lite tier base + base for v1/v2 weights | Apache License, Version 2.0. |
| `google/gemma-4-31B-it` / `unsloth/gemma-4-31B-it-unsloth-bnb-4bit` — v3 teacher + Ultra tier base | Google Gemma terms as published by Google/Unsloth at acquisition time. |
| `google/gemma-4-E4B-it` / `unsloth/gemma-4-E4B-it-unsloth-bnb-4bit` — v3 Pro tier base | Google Gemma terms as published by Google/Unsloth at acquisition time. |
| `google/gemma-4-E2B-it` / `unsloth/gemma-4-E2B-it-unsloth-bnb-4bit` — v3 Mini tier base | Google Gemma terms as published by Google/Unsloth at acquisition time. |
| `Qwen/Qwen3-4B` — v3 Max tier base | Apache License, Version 2.0. |
| `unsloth/Qwen3.6-35B-A3B-GGUF` — local synthetic-data generator | Apache License, Version 2.0, subject to the upstream model card and distribution terms. |
| `ilsp/Meltemi-7B-Instruct-v1.5` — evaluated as an alternate generator | Apache License, Version 2.0. |
| `PleIAs/Greek-PD` — Greek public-domain carrier text | Public domain. |
| Mozilla Common Voice Greek text corpus — carrier text | CC0. |
| `AI-team-UoA/greek_legal_code` — Greek legal carrier text | CC-BY-4.0; attribution required. |

The public provenance chain is designed so that the project can be
audited without publishing raw operational records or full per-case
benchmark traces.

## 3. Attribution notice

The following attribution block is reproduced in `ATTRIBUTION.txt` and
should be retained with redistributed non-commercial copies:

```text
This model is derived from:
  - OpenAI Privacy Filter (Apache 2.0)
    https://huggingface.co/openai/privacy-filter
  - Qwen3.6-35B-A3B (Apache 2.0, Alibaba Qwen team; Unsloth Dynamic GGUF)
    https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF
  - PleIAs/Greek-PD (public domain)
  - Mozilla Common Voice Greek text corpus (CC0)
  - Greek Legal Code corpus (CC-BY-4.0)
    Papaloukas et al. 2021, AI Team, University of Athens
    https://huggingface.co/datasets/AI-team-UoA/greek_legal_code

Greek Privacy Filter project-authored material:
  Non-commercial public release under LICENSE-NC.
  Commercial rights reserved by the copyright holder.
```

## 4. Non-commercial definition

`LICENSE-NC` defines non-commercial use as use that is not primarily
intended for, or directed toward, commercial advantage or monetary
compensation. Academic research, classroom teaching, personal
experimentation, evaluation, and open-source contribution are
permitted when no paid service, paid product, hosted API, consulting
deliverable, or other commercial offering is principally powered by the
project-authored material.

## 5. Training data and GDPR

Training data is fully synthetic. No personal data is processed during
training; see `docs/DPIA_NOTE.md`. GDPR obligations that attach to the
processing of personal data are the responsibility of the deployer at
inference time.

## 6. Audit evidence

The public repository contains:

- dataset and sample manifests;
- curation and provenance reports;
- aggregate benchmark summaries;
- governance documentation and reproducibility notes.

Raw operational records, filled cloud identifiers, and full per-case
benchmark traces are not part of this public release. The maintainer
retains audit-supporting records outside public git history and can
make them available under an appropriate confidentiality process.
