# Security policy

## Supported versions

The fine-tuned model weights and the repository code are offered on a
best-effort basis under the licences documented in `LICENSING.md`. Only
the current `main` branch receives security updates. Older git tags or
weights releases are not patched.

## Reporting a vulnerability

If you believe you have found a security issue — in the training
pipeline, in the released weights, or in a document that could cause a
privacy / compliance regression — please report it privately by email:

- **haritos19@gmail.com**
- Subject line should begin with `[SECURITY]`.

Please include:

- A description of the issue.
- Step-by-step reproduction instructions where applicable.
- The git commit hash of the affected code, or the release tag of the
  affected weights.
- Your suggested severity (low / medium / high).

Please do **not** file a public GitHub issue for a security report, and
please do not share a proof-of-concept exploit publicly until a fix has
been released.

## Response commitments

- Acknowledgement: within 7 calendar days of receiving the report.
- Triage decision (accepted / declined / needs-more-info): within 14
  calendar days.
- Fix timeline: proportional to severity. High-severity issues that
  affect the released weights will be addressed before any new
  commercial licence issuance.

## Scope

This policy covers:

- The source code in this repository.
- The Greek Privacy Filter fine-tuned model weights released under
  `LICENSE-MODEL-NC`.
- Documentation in `docs/`, `LICENSING.md`, `ATTRIBUTION.txt`, and
  `NOTICE`.

It does **not** cover:

- Third-party upstream components (`openai/privacy-filter`,
  `unsloth/Qwen3.6-35B-A3B-GGUF`, llama.cpp, HuggingFace libraries).
  Report those issues to their respective maintainers.
- Deployer-side deployments of the model. A deployer is responsible
  for their own security review and for GDPR-Article-32 technical
  measures in production — see `docs/DPIA_NOTE.md` §2.

## No bug bounty

This is a solo-maintained project. There is no paid bug-bounty
programme. Credit in the release notes is offered for accepted reports
at the reporter's option.
