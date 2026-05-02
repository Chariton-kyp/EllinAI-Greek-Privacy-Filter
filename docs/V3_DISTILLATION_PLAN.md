# v3 Distillation Plan — 5-tier Greek Privacy Filter ladder

**Status:** infrastructure committed; training not yet executed.

## 1. Goal

Push OOD-benchmark F1 from v2.13's 0.8373 toward **0.95 across at
least one production tier**, while keeping a small/cheap tier
(privacy-filter 1.4B) for edge deployment. Maintain full commercial
licensing throughout the data + training + redistribution chain.

## 2. Architecture

```
Teacher (Apache 2.0 base, fine-tuned by us, NOT shipped to third parties)
  └─► google/gemma-4-31B-it via Unsloth LoRA Q4 SFT
       │
       │ generate pseudo-labels on commercial-clean Greek corpus
       ▼
Pseudo-labelled corpus (Apache 2.0 derivative; data only, not shipped)
       │
       ├─► Lite     openai/privacy-filter 1.4B   (NC + commercial-for-owner)
       ├─► Mini     google/gemma-4-E2B-it        (NC + commercial-for-owner)
       ├─► Pro      google/gemma-4-E4B-it        (NC + commercial-for-owner)
       ├─► Max      Qwen/Qwen3-4B-Instruct       (NC + commercial-for-owner)
       └─► Ultra    google/gemma-4-31B-it teacher itself  (NC + commercial-for-owner)
```

## 3. Tier specifications

| tier  | base model            | params      | est OOD F1   | Q4 deploy size | inference VRAM |
|-------|-----------------------|-------------|--------------|----------------|----------------|
| Lite  | openai/privacy-filter | 1.4 B       | 0.88 – 0.92  | 2.6 GB         | 0.5 – 4 GB     |
| Mini  | gemma-4-E2B-it        | 5 B (PLE 2) | 0.89 – 0.92  | 2.5 GB         | 4 GB           |
| Pro   | gemma-4-E4B-it        | 8 B (PLE 4) | 0.92 – 0.95  | 5.0 GB         | 6 – 8 GB       |
| Max   | Qwen3-4B-Instruct     | 4 B dense   | 0.93 – 0.96  | 9.0 GB         | 12 GB          |
| Ultra | gemma-4-31B-it        | 31 B dense  | 0.95 – 0.97  | 18 GB          | 24 GB          |

## 4. License audit — commercial-use chain

### 4.1 Bases and tooling — all Apache 2.0 / MIT

| component                          | license     | role             | shipped? |
|------------------------------------|-------------|------------------|----------|
| google/gemma-4-31B-it              | Apache 2.0  | teacher / Ultra  | yes      |
| google/gemma-4-E4B-it              | Apache 2.0  | Pro              | yes      |
| google/gemma-4-E2B-it              | Apache 2.0  | Mini             | yes      |
| Qwen/Qwen3-4B-Instruct             | Apache 2.0  | Max              | yes      |
| openai/privacy-filter              | Apache 2.0  | Lite             | yes      |
| Unsloth core                       | Apache 2.0  | training         | no       |
| trl                                | Apache 2.0  | RL trainer       | no       |
| bitsandbytes                       | MIT         | Q4 quantisation  | no       |
| transformers / peft / accelerate   | Apache 2.0  | training stack   | no       |
| Final fine-tuned weights           | NC + commercial-for-owner | shipped | yes (4 tiers under our existing dual licence) |

All bases re-licensable into our existing dual-licence model. **Zero AGPL, zero non-commercial bases, zero proprietary dependencies.**

### 4.2 Data sources — strict commercial-clean default

| dataset                          | size              | license        | commercial-safe? | role                |
|----------------------------------|-------------------|----------------|------------------|---------------------|
| PleIAs/Greek-PD                  | 8 GB / 156 M words / 1,405 books | **Public Domain** | ✅ yes      | classical / formal Greek prose |
| Mozilla Common Voice Greek (text) | ~50 k sentences   | **CC0-1.0**    | ✅ yes           | conversational modern Greek |
| AI-team-UoA/greek_legal_code     | ~350 k records    | **CC-BY-4.0**  | ✅ yes (attribution in `ATTRIBUTION.txt`) | Greek legislation |

**Disabled by default — opt-in only with legal review:**

| dataset                          | license          | risk                                                                                             |
|----------------------------------|------------------|--------------------------------------------------------------------------------------------------|
| wikimedia/wikipedia 20231101.el | CC-BY-SA-4.0     | share-alike clause may obligate trained weights to inherit SA → conflicts with our NC + commercial scheme |
| allenai/c4 (mC4 Greek subset)    | ODC-BY-1.0       | underlying Common-Crawl content has mixed publisher copyrights; some publishers explicitly opt out |

After de-duplicated chunking (50–600 chars per chunk): ≈ 500 k records from the 3 commercial-safe sources alone.

### 4.3 Pseudo-labels chain

The teacher (gemma-4-31B-it Apache 2.0) produces label spans over the corpus above. Output JSONL is an Apache 2.0 derivative of an Apache 2.0 model run on commercial-clean data — no chain breakage. Used as training data only; never republished standalone.

### 4.4 Final fine-tuned weights

All 5 tier weights ship under the project's existing dual licence:

- third parties: **Greek Privacy Filter Non-Commercial v1.0** (`LICENSE-MODEL-NC`)
- maintainer: full commercial rights reserved (`LICENSING.md` §1)

`ATTRIBUTION.txt` extended to enumerate gemma-4 + Qwen3 base models and their Apache 2.0 licences.

## 5. Cost estimate (AWS spot eu-north-1b)

| stage                                        | instance      | duration   | $/h     | cost          |
|----------------------------------------------|---------------|------------|---------|---------------|
| Build SFT data converter + corpus loader     | local         | 2 h        | $0      | $0            |
| Pseudo-label 500 k Greek corpus              | local Qwen3.6 | 8 – 12 h   | $0      | $0            |
| Teacher SFT (gemma-4-31B LoRA Q4)            | g6e.xlarge spot | 12 h     | $0.63   | $7 – 9        |
| Optional teacher GRPO (span-F1 reward)       | g6e.xlarge spot | 6 – 8 h  | $0.63   | $4 – 5        |
| Student distill × 4 (mini/pro/max/lite)      | g6.xlarge spot  | 2 – 3 h  | $0.25   | $1 – 2        |
| Benchmark + docs                             | local         | 2 h        | $0      | $0            |
| **Total 5-tier launch**                       | mix           | ~24 h spot | mix     | **$8 – 15**   |

## 6. Files in this commit

| path                                                       | role                                  |
|------------------------------------------------------------|---------------------------------------|
| `scripts/v3/convert_opf_to_chat.py`                        | OPF JSONL → Unsloth chat format       |
| `scripts/v3/load_greek_corpus.py`                          | strict-commercial Greek corpus loader |
| `scripts/v3/train_teacher.py`                              | Unsloth LoRA Q4 SFT trainer           |
| `scripts/v3/generate_pseudo_labels.py`                     | teacher → pseudo-labels via OpenAI-compatible endpoint |
| `scripts/v3/train_student_distill.py`                      | parametrised student trainer          |
| `scripts/v3/benchmark_tiers.py`                            | 5-tier OOD benchmark runner           |
| `requirements-unsloth.txt`                                 | training dependencies (all Apache 2.0/MIT) |
| `configs/v3_distillation.yaml`                             | hyperparameters, tier definitions     |
| `docs/V3_DISTILLATION_PLAN.md`                             | this document                         |

## 7. Sequencing

1. **Smoke**: convert v2.13 chat data ✅ (this commit) — `144 372` records, `190 k` spans, 24 classes verified.
2. **Pseudo-label corpus**: download Greek-PD + Common Voice + greek_legal_code via `load_greek_corpus.py`; run `generate_pseudo_labels.py` against local Qwen3.6-35B-A3B (already cached) until we train a proper gemma-4-31B teacher.
3. **Teacher train**: AWS g6e.xlarge spot, 12 h.
4. **Re-pseudo-label** with the trained teacher (replaces step 2's first pass).
5. **Distill all 4 students in parallel** on AWS g6.xlarge spots.
6. **Benchmark** all 5 tiers against the locked 200-case OOD harness.
7. **HF release**: 5 model cards under our existing dual-licence template.

## 8. What we are NOT doing

- **Training on Wikipedia** — share-alike clause too risky for the NC + commercial weight scheme.
- **Training on mC4 / Common Crawl** — uncontrollable underlying publisher copyrights.
- **Using DeepSeek-V3 / R1 as teacher** — DeepSeek licence has an AUP that could chain to our weights.
- **Gemma 1/2/3 (older terms)** — gemma-4 changed to standard Apache 2.0.
- **Shipping Unsloth Studio (AGPL-3.0)** — only the Apache 2.0 core library is used, never the UI.

## 9. Risks and mitigations

| risk                                              | mitigation                                                                  |
|---------------------------------------------------|-----------------------------------------------------------------------------|
| Teacher's Greek pretraining underperforms         | benchmark teacher F1 before pseudo-labelling; fall back to Qwen3.6-35B      |
| Pseudo-label noise contaminates students          | confidence-filter + offset-resolution drop on any unparseable span          |
| Spot capacity rejected                             | g6.xlarge / g5.xlarge fallback chain; on-demand worst-case ($1.05/h)        |
| 1.4 B student capacity-capped at 0.91             | accept ceiling; ship Mini (gemma-4-E2B 2.5 GB) as alternative free tier      |
| HF release attribution                             | extend `ATTRIBUTION.txt` to list gemma-4 + Qwen3 + greek_legal_code citation |

## 10. Open questions before launch

1. Pick teacher: **gemma-4-31B-it** (recommended — dense, easier RL) or **Qwen3.6-35B-A3B** (cached locally, MoE). Default = gemma-4-31B-it.
2. Skip GRPO and rely on pseudo-label distillation + student SFT only (faster, $7-8 saved), or run optional GRPO (+0.02–0.04 F1 on teacher).
3. Drop Pro tier (gemma-4-E4B-it) and replace with Qwen3-1.7B for size diversity, or keep gemma family throughout for brand consistency.

These are answered when training begins; current commit just lands the infra.
