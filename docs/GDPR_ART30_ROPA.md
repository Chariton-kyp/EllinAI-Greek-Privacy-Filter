# GDPR Article 30 — Deployer template

Article 30 of Regulation (EU) 2016/679 requires each controller (and,
where applicable, each processor) to maintain a written record of
processing activities under its responsibility. Per guidance from the
Irish Data Protection Commission and the European Data Protection
Board, that record is an **internal** document available to the
controller and to a supervisory authority on documented request, not
a public publication.

This file therefore contains only the deployer template. A deployer
who fine-tunes, redistributes, or runs the released model on real
Greek text is a controller (or processor) in their own right and must
maintain their own Article 30 record. The template below is intended
to be copied into the deployer's internal compliance file and
completed before any production use.

The provider's own filled record (covering the training and release
stages of this project) is held privately by the controller per
GDPR Article 30 guidance and is produced to a supervisory authority,
notified body, or notarised auditor on documented request. A summary
of the provider's analysis is publicly available in `docs/DPIA_NOTE.md`,
which records that the training stage processed no personal data and
therefore did not engage the Article 30 obligations on the provider
side.

## Part A — Deployer controller record (fill per deployment)

A deployer **must** complete the following template — or an
equivalent record in their own governance tooling — before running
the model on production input. The provider does **not** complete
these fields on the deployer's behalf.

```text
1. Deployer controller details
   1.1 Name of controller:                             _______________
   1.2 Controller's contact address:                   _______________
   1.3 Controller's representative in the EU (if any): _______________
   1.4 Data Protection Officer (if required):          _______________

2. Processing activity
   2.1 Name of activity:                               _______________
   2.2 Purpose of processing (Art. 30(1)(b)):          _______________
   2.3 Legal basis (Art. 6, and Art. 9 where relevant):_______________
   2.4 Description of the deployment of the Greek Privacy Filter:
                                                        _______________

3. Data subjects and data categories (Art. 30(1)(c))
   3.1 Categories of data subjects:                    _______________
   3.2 Categories of personal data processed:          _______________
   3.3 Categories of special-category data (Art. 9):   _______________

4. Recipients (Art. 30(1)(d))
   4.1 Internal recipients:                            _______________
   4.2 Processors (incl. hosting / inference vendors): _______________
   4.3 Third-country recipients and safeguards:        _______________

5. Retention (Art. 30(1)(f))
   5.1 Retention period for inputs:                    _______________
   5.2 Retention period for model outputs:             _______________
   5.3 Erasure mechanism (Art. 17):                    _______________

6. Technical and organisational measures (Art. 30(1)(g))
   6.1 Access control to the model endpoint:           _______________
   6.2 Logging of inputs / outputs:                    _______________
   6.3 Human-in-the-loop review before irreversible
       action on the model's output:                   _______________
   6.4 Incident-response contact:                      _______________

7. DPIA (Art. 35)
   7.1 Was a DPIA conducted for this deployment?       yes / no
   7.2 Reference to DPIA document:                     _______________

8. Reviewer and date
   8.1 Reviewer name:                                  _______________
   8.2 Date of last review:                            _______________
```

## Part B — Processor template (optional, if applicable)

If the deployer is a processor acting on a controller's instructions,
Article 30(2) applies instead of 30(1). The controller's identity and
instructions must be recorded along with the fields in Part A §§3–6.

## Notes for deployers

- Deploying the model on real Greek text triggers your own Article 30
  obligations; this template is a starting point, not a substitute
  for your own legal review.
- Where the deployment qualifies as high-risk under EU AI Act Annex
  III, the Annex IV technical documentation must also be maintained;
  see `docs/EU_AI_ACT_ANNEX_IV.md` for the provider's mapping of
  provider-side artefacts.
- A DPIA under Article 35 is required where the processing is likely
  to result in a high risk to the rights and freedoms of data
  subjects; `docs/DPIA_NOTE.md` gives the provider's starting analysis.
