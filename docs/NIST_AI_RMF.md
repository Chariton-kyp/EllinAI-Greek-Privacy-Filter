# NIST AI Risk Management Framework 1.0 — mapping

This document maps the four core functions of the NIST AI Risk
Management Framework 1.0 (January 2023) — **Govern**, **Map**,
**Measure**, **Manage** — to concrete artefacts in this repository.

The mapping is intentionally terse and cites files. The substantive
content lives in the referenced files; this page exists so a US-based
auditor or a procurement team can confirm in minutes that every RMF
function has a corresponding record.

## 1. Govern

Policies, accountability, and workforce structure for the AI System.

| NIST RMF Govern subcategory | Artefact |
|---|---|
| GOVERN 1.1 Legal and regulatory compliance | `LICENSING.md`, `LICENSE-CODE`, `LICENSE-MODEL-NC`, `NOTICE`, `ATTRIBUTION.txt` |
| GOVERN 1.2 Policies, processes, procedures | `docs/AIMS_STATEMENT.md`, `SECURITY.md` |
| GOVERN 1.5 Accountability structures | `docs/AIMS_STATEMENT.md` §3 (roles) |
| GOVERN 2.1 Workforce diversity, qualification | Not applicable — solo operator, disclosed in `docs/AIMS_STATEMENT.md` §3 |
| GOVERN 3 Stakeholder engagement | `SECURITY.md` (vulnerability reporting), commercial-licence channel in `LICENSE-MODEL-NC` §5 |
| GOVERN 4.1 Organizational AI-risk tolerance | `docs/MODEL_CARD.md` §"Ethical considerations" + §"Caveats" |
| GOVERN 5 Transparent record of AI decisions | `docs/AUDIT_LOG.md`, `artifacts/manifest/*.json` |
| GOVERN 6 Third-party risks | `LICENSING.md` §2 (third-party component licences) |

## 2. Map

Context, purpose, and downstream users of the AI System.

| NIST RMF Map subcategory | Artefact |
|---|---|
| MAP 1.1 Intended purpose and prohibited uses | `docs/MODEL_CARD.md` §"Intended use" / §"Out-of-scope" |
| MAP 1.2 Specific context of use | `docs/DATASHEET.md` §6; `docs/EU_AI_ACT_ANNEX_IV.md` §0 |
| MAP 2 Categorize the AI System | `docs/EU_AI_ACT_ANNEX_IV.md` §0 (risk classification) |
| MAP 3 AI capabilities, benefits, costs | `docs/MODEL_CARD.md` §"Model details" |
| MAP 4.1 Impact to individuals | `docs/DPIA_NOTE.md` §3 (automated-decision-making) |
| MAP 5 Identify stakeholders | `docs/DPIA_NOTE.md` §5 (deployer responsibilities) |

## 3. Measure

Quantitative and qualitative analysis of identified risks.

| NIST RMF Measure subcategory | Artefact |
|---|---|
| MEASURE 1 Test, evaluate, validate (TEV) | `scripts/run_opf_eval.py`, `scripts/run_post_train_evaluation.py`, `artifacts/metrics/baseline_*.json` |
| MEASURE 2.1 Evaluation metrics | `artifacts/metrics/finetuned_*_metrics.json` (populated post-fine-tune) |
| MEASURE 2.7 Trustworthiness characteristics (bias) | `docs/MODEL_CARD.md` §"Ethical considerations" (bias disclosures) |
| MEASURE 2.9 Explainability | Token-level spans output directly; architecture described in `docs/DATASHEET.md` |
| MEASURE 3 Data quality | `scripts/verify_provenance.py`, `scripts/validate_greek_pii_dataset.py`, `artifacts/metrics/provenance_report.json`, `curation_report.json` |
| MEASURE 4 Tracked metrics over time | Every release commits an updated `artifacts/metrics/finetuned_*_metrics.json` alongside a git tag |

## 4. Manage

Prioritize risks, mitigate, and document residual risk.

| NIST RMF Manage subcategory | Artefact |
|---|---|
| MANAGE 1.1 Risk prioritization | `docs/MODEL_CARD.md` §"Ethical considerations" (prioritized list) |
| MANAGE 2 Risk-response strategy | `docs/MODEL_CARD.md` §"Caveats and recommendations" (HITL mandate, calibration on customer data) |
| MANAGE 3 Third-party risks | `LICENSING.md` §2 (upstream licence obligations retained) |
| MANAGE 4.1 Post-deployment monitoring | `docs/DPIA_NOTE.md` §5 and `docs/EU_AI_ACT_ANNEX_IV.md` §3 (deployer responsibility; provider monitors through `SECURITY.md` reports) |
| MANAGE 4.3 Incident response | `SECURITY.md` (SLAs for acknowledgement, triage, and fix) |

## 5. Residual items

The following items will be populated only after the first commercial
release:

- Historical metrics under MEASURE 4 beyond the baseline currently in
  `artifacts/metrics/`.
- Post-deployment incident logs (reports received under the process
  defined in `SECURITY.md`).

These are expected workflow items, not gaps in the framework mapping.
