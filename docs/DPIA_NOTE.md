# Data-protection note (GDPR)

This note records the General Data Protection Regulation analysis of
the provider's training pipeline for the Greek Privacy Filter. It is
not a Data Protection Impact Assessment in the sense of Regulation (EU)
2016/679 Article 35 — a DPIA is required only where processing is
likely to result in a high risk to the rights and freedoms of natural
persons, and the training stage described here processes no personal
data. A deployer running inference on real Greek text must perform
its own assessment; this note is offered as a starting point for that
assessment, not as a substitute for it.

## 1. Training data

**Personal data processed during training: none.**

The training corpus is synthetic:

- PII values (names, AMKA, AFM, ADT, IBAN_GR, phones, emails, URLs,
  addresses, dates, and secrets) are generated deterministically by
  `scripts/generate_commercial_safe_greek_pii.py` from random seeds.
  No value is drawn from any public register or real dataset.
- Carrier text is taken from sources that contain no personal data:
  `PleIAs/Greek-PD` (public domain — works published before 1884 whose
  authors have been deceased for more than seventy years), Mozilla
  Common Voice Greek text corpus (CC0), and
  `AI-team-UoA/greek_legal_code` (CC-BY-4.0; excerpts of Greek
  legislation).
- The language model (`unsloth/Qwen3.6-35B-A3B-GGUF`, Apache 2.0) that
  assembles sentences around each PII value is executed locally. No
  prompt, intermediate output, or final sentence is transmitted to a
  third party during training.

Articles 5 to 11 of the Regulation impose obligations on the processing
of personal data. Because no personal data is processed during
training, those obligations do not apply to the training stage.

## 2. Inference and deployment

Running the fine-tuned model on real Greek text will, by design,
process personal data. That processing is the responsibility of the
deployer, not the provider.

- A deployer that uses the released weights on real documents is a
  controller under Article 4(7) (or a processor under 4(8), if acting
  on another controller's instructions).
- The deployer must establish a lawful basis under Article 6 (and,
  where special categories are processed, Article 9) for each
  processing purpose.
- The deployer must carry out a DPIA under Article 35 where the
  processing is likely to result in a high risk to the rights and
  freedoms of data subjects (for example, large-scale systematic
  monitoring of employees, automated screening of job applicants, or
  categorisation of medical records).
- The model weights are distributed under
  [`LICENSE-MODEL-NC`](../LICENSE-MODEL-NC), which prohibits commercial
  deployment absent a separate commercial licence. Commercial licensees
  receive this note together with `ATTRIBUTION.txt` at the time the
  licence is issued.

## 3. Automated individual decision-making (Article 22)

The model is not designed to produce a decision that has a legal
effect, or a similarly significant effect, on a data subject in the
absence of human intervention. `docs/MODEL_CARD.md` records a
mandatory human-in-the-loop review requirement for any action taken
on the basis of the model's output. A deployer that removes that
requirement assumes the associated Article 22 responsibilities.

## 4. Data-subject rights (Articles 13 to 22)

Because the training corpus contains no personal data, the rights of
access, rectification, erasure, restriction, objection, and
portability do not attach to any record in the training corpus. The
same rights attach in full to any deployer's runtime data and must be
honoured by that deployer in respect of that data.

## 5. Recommended actions for a deployer

1. Complete the Article 30 record template in
   `docs/GDPR_ART30_ROPA.md` Part B before placing the deployment in
   production.
2. Conduct a DPIA under Article 35 where applicable.
3. Document the deployment's prompts, thresholds, escalation logic,
   logging, and retention schedule.
4. Implement the human-in-the-loop requirement specified in
   `docs/MODEL_CARD.md`.
5. Do not rely on the model as the sole basis for an irreversible
   action on personal data.
