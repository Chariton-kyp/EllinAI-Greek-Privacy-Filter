# Audit log — Greek Privacy Filter build

This file is the authoritative chronological record of the commands
that produced each artefact in the repository. Each entry lists the
date, the actor, the command, the input, the output, and any seed
values used. Per-example provenance beyond what is captured here is
stamped into the `info.strategy` and `info.source` fields of every
record in the training splits.

Every commit referenced below is present in the repository's git
history and can be inspected with `git show <hash>`.

## 1. 2026-04-23 — Repository scaffolding

**Actor:** Chariton Kypraios.

- Created the baseline repository structure (`scripts/`, `configs/`,
  `src/`).
- Drafted the dual-licensing framework (`LICENSE`, `LICENSE-CODE`,
  `LICENSE-MODEL-NC`, `LICENSING.md`).
- Quarantined earlier experimental data generated with third-party
  APIs into `data/archive_pre_meltemi_2026-04-23/` (excluded from git
  via `.gitignore`). Scheduled permanent deletion: 2026-05-23.
- Initial git commit: `68940f1`.

## 2. 2026-04-24 — Switch to Qwen3.6 pipeline and audit-ready documentation

**Actor:** Chariton Kypraios, with Claude (Anthropic assistant) acting
as code author and mechanical executor of scripts. The section "Claude
involvement — scope of automation" at the end of this file records
the boundaries of that automation.

Commits introduced on this date, in order:

| Commit | Subject |
|---|---|
| `a87a690` | Qwen3.6 synthetic-data pipeline, curation script, first pass of audit docs. |
| `a9e61a7` | Full-pipeline AWS EC2 spot launcher and audit-ready documentation (datasheet, audit log, model card, DPIA note). |
| `0d5d858` | Generator v3 — register diversity, multi-PII items, zero prompt leakage. |
| `1d9d7ed` | Audit-agent findings incorporated (full Apache 2.0 text, NOTICE, EU AI Act Annex IV mapping, ADT span fix). |
| `0693051` | Audit evidence committed (100-record reference samples per split; SHA-256 manifests; curation, provenance, and baseline metric reports). |
| `e48f46c` | Second audit-agent findings incorporated (path sanitisation, neutral licence URL, `SECURITY.md`). |
| `6337c54` | Phase 3 audit completeness: `docs/AIMS_STATEMENT.md` (ISO/IEC 42001), `docs/NIST_AI_RMF.md`, `docs/GDPR_ART30_ROPA.md`. Full legal-grade tone pass on every existing audit document. |
| `affb0f9` | Cross-references of the three new audit documents in `README.md` docs table and `docs/EU_AI_ACT_ANNEX_IV.md` §5. |
| `6163add` | Regenerated `artifacts/metrics/curation_report.json` from the v2 final input (`data/processed/greek_v2_final.jsonl`, seed `1337`) so its stage-1/2/3 counts match the 8,088 / 1,217 / 1,217 / 1,219 split totals quoted in §2 step 8 and in `docs/DATASHEET.md` §2. Back-filled rows for `6337c54` and `affb0f9` in this ledger. |
| `11ce4d7` | Refreshed `artifacts/manifest/manifest.json` from a clean working tree so `git_commit` resolves to `6163add` and `git_dirty` is `false`. |
| `b0371f2` | Fourth-pass audit-ready-agent fixes. Corrected the per-class span table in `docs/DATASHEET.md` §2 so each row matches the stage-3 train `spans_per_class` in `artifacts/metrics/curation_report.json`. Fixed `configs/fine_tune_config.yaml` `hard_test_file` to `data/processed/hard_test.jsonl`. Renamed `artifacts/metrics/baseline_hard_test_2000_untyped_metrics.json` to `baseline_hard_test_untyped_metrics.json` for path consistency. |
| `dba0d7a` | Refreshed `artifacts/manifest/samples_manifest.json` from a clean working tree so it names commit `b0371f2` and `git_dirty` is `false`. |
| `061167f` | Moved the four baseline-metric files (`baseline_train_untyped_metrics.json`, `baseline_validation_untyped_metrics.json`, `baseline_test_metrics.json`, `baseline_hard_test_untyped_metrics.json`) to `artifacts/metrics/archive/` with descriptive filenames that record their prior-iteration record counts (`8000 / 1000 / 2000 / 2000`). Rationale: the current committed splits are `8088 / 1217 / 1217 / 1219` records, so the archived baselines are not usable as the "before" side of a before-vs-after comparison against any fine-tune run on the current splits. A fresh baseline will be produced by the fine-tune pipeline against the post-AWS-generated splits (output path fixed in `configs/fine_tune_config.yaml`). Added `artifacts/metrics/archive/README.md` to document this retention. Updated `docs/EU_AI_ACT_ANNEX_IV.md` §(h) accordingly. |

### Execution ledger

1. **Generator stack selection.** `ilsp/meltemi-instruct-v1.5` was
   trialled first and discarded because of persistent semantic
   mismatches on the original slot-template prompt. The project then
   moved to `unsloth/Qwen3.6-35B-A3B-GGUF` (Apache 2.0) served locally
   through the `llama.cpp` CUDA build. A documented Ollama issue with
   the multi-modal GGUF projector for this model required direct use
   of `llama-server` rather than Ollama. Qwen thinking mode was
   disabled through `chat_template_kwargs.enable_thinking = false`.

2. **Golden seed authoring.**
   `python scripts/build_golden_seeds.py` produced
   `data/seed/golden_examples.jsonl` (42 hand-authored examples
   authored by the provider under Apache 2.0). Currently used only as
   optional few-shot context for the legacy slot-template flow; not
   present in the production batch flow.

3. **First generation attempt (aborted).**
   `python scripts/generate_commercial_safe_greek_pii.py --count 14500
   --mode mix --llm-engine openai --ollama-mode batch
   --ollama-batch-size 10 --ollama-fraction 0.6 --seed 1337`
   halted at 9,541 records after `llama-server` encountered a Windows
   paging-file exhaustion during a parallel `torch` import from the
   Greek-PD downloader. Partial output archived as
   `data/processed/greek_v1_partial_9541.jsonl` and excluded from all
   subsequent training.

4. **Carrier corpora.** `python scripts/download_carrier_common_voice.py
   --max-sentences 5000` produced `data/raw/common_voice_el_sentences.jsonl`
   (CC0). `python scripts/download_carrier_legal_code.py
   --max-sentences 10000` produced `data/raw/greek_legal_sentences.jsonl`
   (CC-BY-4.0; attribution Papaloukas et al., 2021, AI Team, University
   of Athens). The Greek-PD downloader failed on this host for the
   same paging-file reason as the first generation attempt and was
   skipped; a `torch`-free reimplementation is tracked as a follow-up.

5. **v2 main generation.**
   `python scripts/generate_commercial_safe_greek_pii.py --count 14500
   --mode mix --llm-engine openai --ollama-mode batch
   --ollama-batch-size 10 --ollama-fraction 0.5
   --carrier-jsonl data/raw/blended_carriers.jsonl --seed 2024`
   produced `data/processed/greek_v2_raw.jsonl` (14,500 records).
   Strategy breakdown: Qwen batch 5,850 / templates 2,915 / hard
   negative 2,900 / carrier 2,835. Qwen batch acceptance rate
   97.3 percent (5,856 of 6,020 values requested).

6. **Latinisation post-processing.**
   `python scripts/postprocess_latinize_contacts.py --seed 1337
   --keep-greek-ratio 0.2` produced
   `data/processed/greek_v2_fixed.jsonl`, rewriting 2,161 email and
   URL spans from Greek to Latin script (ELOT 743) while retaining
   approximately 20 percent in Greek.

7. **Qwen-generated hard negatives.**
   `python scripts/generate_qwen_hard_negatives.py --count 1500
   --batch-size 10 --seed 2024` produced
   `data/processed/hard_neg_qwen.jsonl` (1,500 unique records across
   fourteen topic families).

8. **Merge and stratified curation.**
   `cat greek_v2_fixed.jsonl hard_neg_qwen.jsonl > greek_v2_final.jsonl`
   and
   `python scripts/curate_generated_dataset.py --input greek_v2_final.jsonl
   --train-size 10000 --val-size 1500 --test-size 1500 --hard-size 1500
   --seed 1337`
   produced the splits published in `data/processed/` and the report
   in `artifacts/metrics/curation_report.json`. Stage 1 accepted
   15,884 of 16,000 records; Stage 2 removed 2,984 duplicates; Stage 3
   assigned 8,088 records to train, 1,217 each to validation and test,
   and 1,219 to hard-test, with 13 percent hard negatives per split.

9. **Generator v3 tightening (commit `0d5d858`).** Removed the Greek-
   qualifier prompt leakage (for example, "ελληνικό τηλέφωνο"), added
   a register pool of twelve styles (SMS, voicemail, call transcript,
   business email, medical chart, HR letter, government form, support
   ticket, formal document, bank notification, personal note, social-
   media post), and added multi-PII sampling with weights
   0.50 / 0.35 / 0.15 for one / two / three spans per item. The
   `ilsp/meltemi` path is retained for alternative use but is no
   longer the default.

10. **Sample-file regeneration.**
    `python scripts/hash_manifest.py` produced
    `artifacts/manifest/manifest.json` and
    `artifacts/manifest/samples_manifest.json`.
    `python scripts/verify_provenance.py` produced
    `artifacts/metrics/provenance_report.json` and
    `artifacts/metrics/samples_provenance_report.json`.
    Reference samples of 100 records per split committed to
    `data/samples/` for in-repository inspection.

### Claude involvement — scope of automation

Claude (the Anthropic assistant) was used as a code author and a
mechanical executor of the scripts above. Specifically, Claude:

- authored the Python, shell, and Markdown files added during this
  session;
- invoked the scripts with the arguments recorded in each ledger
  entry;
- committed the resulting files to git.

Claude did **not**:

- select which individual generated records enter the training splits
  (that is done algorithmically by `scripts/curate_generated_dataset.py`);
- rewrite the content of any record generated by Qwen or by the rule-
  based pipeline;
- hand-label any span;
- choose training hyperparameters outside the values recorded in
  `configs/fine_tune_config.yaml`.

Every decision that shapes the training data — filter rules, the
skeleton-duplicate cap, per-class quotas, seed values, carrier
composition — is expressed as code in this repository and is
reproducible from the git state alone.

## 3. 2026-04-26 — AWS v1 production build and first fine-tune

**Actor:** Chariton Kypraios, with Claude (Anthropic assistant) acting
as code author and mechanical executor of the AWS launchers and the
verification scripts. Same scope-of-automation boundary as §2 applies.

Commits introduced on this date, in order:

| Commit | Subject |
|---|---|
| `3b8c71a` | `ec2_spot_generate.sh`: trap EXIT/INT/TERM to guarantee instance termination on every exit path. |
| `6971c42` | `ec2_spot_generate.sh`: incremental S3 sync after each long stage; trap-based final sync. |
| `f02c28b` | `.gitignore`: `.playwright-mcp/` runtime cache. |
| `947dbc5` | `ec2_spot_generate.sh`: pass `run-instances` spec inline to AWS CLI (Windows Git Bash + AWS CLI v2 .exe path-resolution fix). |
| `42c8fed` | `ec2_spot_generate.sh`: build llama.cpp from source (later replaced by Docker). |
| `356cc51` | `ec2_spot_generate.sh`: switch to `ghcr.io/ggml-org/llama.cpp:server-cuda` Docker image; live log streaming. |
| `1427bf2` | `ec2_spot_generate.sh`: `_run_dl` wrapper tolerates `huggingface_hub` interpreter-shutdown abort. |
| `2d03393` | `generate_commercial_safe_greek_pii.py`: per-record `info.strategy` label changed from `ollama/...` to `llm-server/...` to match the actual generator stack (Qwen3.6-35B-A3B-GGUF served by `llama.cpp` Docker, not Ollama). Default `--ollama-model` updated to `unsloth/Qwen3.6-35B-A3B-GGUF`. |
| `e6c8dda` | `ec2_spot_generate.sh`: gp3 EBS boost (16k IOPS / 1000 MB/s) so loading the 30 GB Q8 model takes ~5 min instead of ~85 min. |

### Execution ledger — v1 generation run

> Operational identifiers below (AWS account ID, S3 bucket name, IAM
> user / role / inline-policy names, EC2 spot instance IDs, exact S3
> paths, support-case numbers) are recorded in the controller-private
> file `private/audit_operational.md` and are reproduced in full to a
> supervisory authority, notified body, or notarised auditor on
> documented request. The placeholders used here (`<aws-account-id>`,
> `<gpf-bucket>`, `<iam-user>`, `<iam-role>`, `<inline-policy>`,
> `<spot-instance-id>`) refer to those private values one-to-one. See
> `private/README.md` for the public/private-split rationale.

11. **AWS account provisioning.** A new AWS account (`<aws-account-id>`)
    was created in the `eu-north-1` (Stockholm) region with a
    controller-controlled root e-mail. A scoped IAM user (`<iam-user>`)
    was created via the AWS console with `IAMFullAccess`,
    `AmazonEC2FullAccess`, and `AmazonS3FullAccess` attached, plus
    `EC2InstanceConnectInline` for ephemeral SSH debug. An S3 bucket
    (`<gpf-bucket>`) was provisioned in the same region. An IAM role
    (`<iam-role>`) and matching instance profile attached the inline
    policy `<inline-policy>`, resource-scoped to the bucket. The policy
    document is `scripts/aws/iam_policy_ec2_gen.json`.

12. **Service Quotas.** Quota `L-3819A6DF` ("All G and VT Spot
    Instance Requests") was zero by default for the new account. A
    manual support case (recorded in `private/audit_operational.md`)
    was filed in the Service Quotas console; AWS support approved 4
    vCPUs after manual review, enough for a single `g6e.xlarge` (4
    vCPUs, L40S 48 GB).

13. **v1 generation run.** The launcher
    `scripts/aws/ec2_spot_generate.sh` was invoked at HEAD `e6c8dda`
    requesting 50,000 records at quantisation `UD-Q8_K_XL` (full
    command line in `private/audit_operational.md`). It launched a
    single spot instance (`<spot-instance-id>`) at 2026-04-26 09:27:12
    UTC. Wall clock 2 h 40 min; cost ~$2.30 spot + ~$0.10 storage.
    Produced under `s3://<gpf-bucket>/generated/run-20260426T092703Z/`
    50,000 raw records, 50,746 final-merged records, 4 split files
    (21,124 / 3,173 / 3,171 / 4,593 records), a curation report, and a
    provenance report. Trap-based clean shutdown at 2026-04-26 12:07:30
    UTC. Local copy synchronised to
    `data/processed/aws-v1-20260426T092703Z/`.

14. **Provenance verifier patch.** `scripts/verify_provenance.py`
    failed during the v1 run because `KNOWN_STRATEGY_PREFIXES` only
    contained `ollama/`; the v1 records use `llm-server/` per
    commit `2d03393`. The unrecoverable exit propagated to `set -e`
    and triggered the trap before `scripts/hash_manifest.py` could
    run. The patch (this commit) adds `llm-server/` to the prefix
    tuple. Re-running the verifier locally against the synchronised
    splits yielded all-OK; `scripts/hash_manifest.py` was then run
    locally to produce
    `data/processed/aws-v1-20260426T092703Z/artifacts/manifest/manifest.json`
    with the SHA-256 hashes recorded below:

| File | Bytes | SHA-256 |
|---|---:|---|
| `train.jsonl` | 9,431,592 | `7d6c746f2ac78723154f051ac464c1ca51acb4d029f8a64a9a9bcdd6beee79d0` |
| `validation.jsonl` | 1,412,221 | `65e5e09ef0fd6581046b393d818bfafc04222f852ac7577a9a615e00611d92a0` |
| `test.jsonl` | 1,412,294 | `415930a4c05025b65ebed8a5ff2c0a5d9ad1e7526ddc460e89c52714a43cbfa6` |
| `hard_test.jsonl` | 2,119,219 | `41f43e8ed35fbf999a893f69209d729a0acd175a3e192c466026c583d1927741` |

15. **AWS fine-tune launcher.** `scripts/aws/ec2_spot_finetune.sh`
    (new this commit) parallels `ec2_spot_generate.sh` for the
    fine-tune phase: pulls v1 splits + base checkpoint + label
    space from S3, clones `openai/privacy-filter` at the pinned
    upstream commit, runs `python -m opf train` and
    `python -m opf eval` baseline + finetuned, syncs all artefacts
    to S3 under `finetune/run-<timestamp>/`, and self-terminates
    via the same trap pattern. Two upstream-CLI mismatches were
    discovered the first two attempts and patched: (a) `opf eval`
    does not accept `--label-space-json` (only `train` does), and
    (b) `--eval-mode typed` requires the checkpoint label scheme
    to match the dataset; the base checkpoint label scheme is the
    upstream 33-class set and does not contain the four Greek
    extensions, so baseline eval is forced to `--eval-mode untyped`
    while finetuned eval (whose checkpoint contains
    `label_space.json`) uses `--eval-mode typed`.

16. **IAM policy extension.**
    `scripts/aws/iam_policy_ec2_gen.json` was extended in this
    commit to add `s3:GetObject` on `generated/*`, `checkpoints/*`,
    and `finetune/*`, and `s3:PutObject` / `s3:PutObjectAcl` on
    `finetune/*`. Applied to the live IAM role (`<iam-role>`)
    inline policy (`<inline-policy>`).

17. **Pre-uploaded once-only artefacts.** The
    `openai/privacy-filter` base checkpoint
    (`config.json`, `dtypes.json`, `viterbi_calibration.json`,
    `model.safetensors` 2.6 GB) was uploaded to
    `s3://<gpf-bucket>/checkpoints/base/privacy-filter/`
    so each fine-tune launch can `aws s3 sync` it instead of
    re-downloading from HuggingFace. `configs/label_space.json`
    was uploaded to `s3://<gpf-bucket>/finetune/label_space.json`.

18. **v1 fine-tune run.** The launcher
    `scripts/aws/ec2_spot_finetune.sh` was invoked at HEAD `e6c8dda`
    against v1 run `20260426T092703Z` (full command line in
    `private/audit_operational.md`). It launched a single spot
    instance (`<spot-instance-id>`) at 2026-04-26 13:58:53 UTC. Wall
    clock ~19 min total; cost ~$0.27 spot + ~$0.02 storage (and
    ~$0.22 for three prior aborted attempts that surfaced the two
    upstream-CLI mismatches above). Produced under
    `s3://<gpf-bucket>/finetune/run-20260426T135853Z/` the fine-tuned
    checkpoint (`model/model.safetensors` 2.6 GB),
    `model/config.json`, `model/label_space.json`,
    `model/finetune_summary.json`, the four metric files
    (`baseline_test_metrics.json`,
    `baseline_hard_test_metrics.json`,
    `finetuned_test_metrics.json`,
    `finetuned_hard_test_metrics.json`), the train log, and
    `run_metadata.json`. Trap-based clean shutdown at 2026-04-26
    14:17:57 UTC. Local copy synchronised to
    `data/processed/aws-ft-20260426T135853Z/`.

19. **Hyperparameters used (v1 fine-tune).** epochs=3,
    batch_size=4, grad_accum_steps=4, learning_rate=5e-5,
    weight_decay=0.01, max_grad_norm=1.0, n_ctx=256, seed=1337,
    output_param_dtype=bf16. Identical to the values pinned in
    `configs/fine_tune_config.yaml` so any rerun against the same
    inputs yields the same weights.

20. **v1 metrics summary.** Test split detection.span.f1
    0.7766 → 0.9886 (+0.2120). Hard-test detection.span.f1
    0.7668 → 0.9868 (+0.2200). All twelve PII classes finished
    above F1 0.94. Lowest typed F1 was `afm` (0.9486); highest
    `private_url` (1.0000). Full per-class breakdown in
    `docs/MODEL_CARD.md` §4 and the four metric JSONs.
