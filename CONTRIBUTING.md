# Contributing to the Greek Privacy Filter

Thank you for your interest in contributing. This document explains how
contributions to this repository are licensed and what you agree to by
opening a pull request.

## Licence of contributions

By submitting a pull request, issue with a code/text patch, or any
other contribution to this repository, you agree that your
contribution is offered under the same licences as the corresponding
artefact in the repository:

- **Source code** (`scripts/`, `configs/`, `src/`, `*.py`, `*.sh`,
  `*.yaml`) — Apache License, Version 2.0 (see `LICENSE-CODE`).
- **Documentation** (`docs/`, top-level `*.md`, `NOTICE`,
  `ATTRIBUTION.txt`) — Apache License, Version 2.0.
- **Reference data samples** (`data/samples/`, `data/seed/`,
  `data/realworld_benchmark/`) — Apache License, Version 2.0.
- **Public audit evidence** (`artifacts/manifest/`,
  `artifacts/metrics/`) — Apache License, Version 2.0.

This is the standard "inbound = outbound" model used by Apache 2.0
projects. You retain copyright in your contribution; you grant the
project (and downstream users) the rights set out in Apache 2.0,
including the patent grant in Section 3.

## Fine-tuned model weights

Contributions to source code, documentation, or data **do not** entitle
you to any rights in the fine-tuned model weights produced from this
repository. The fine-tuned weights are released under the **Greek
Privacy Filter Non-Commercial License v1.0** (see `LICENSE-MODEL-NC`)
for third-party use, and the copyright holder
(Chariton Kypraios, haritos19@gmail.com) retains the exclusive right to
license those weights commercially.

By contributing, you acknowledge that:

1. The maintainer may train, redistribute, and commercially license
   model weights derived from a corpus that includes your contribution.
2. The maintainer may keep your contribution in the public Apache 2.0
   codebase indefinitely while still offering paid commercial licences
   for fine-tuned weights derived from it.
3. You are not entitled to compensation, royalties, or attribution in
   any commercial product built on those weights, beyond the standard
   Apache 2.0 NOTICE-file attribution that ships with the source code.

If you cannot agree to the above, please do not submit contributions.

## What you should NOT contribute

- Real personal data (real Greek names, real ΑΦΜ / ΑΜΚΑ / addresses,
  etc.). All sample data in this repo is synthetic. PRs adding real PII
  will be rejected.
- Code or text copied from sources whose licence is incompatible with
  Apache 2.0 (GPL-only, AGPL, proprietary). If you are unsure, open an
  issue first.
- Operational identifiers (AWS account IDs, real S3 bucket names, IAM
  user/role names, instance IDs). These belong in `private/` (which is
  gitignored), never in committed files.

## How to contribute

1. Fork the repository and create a topic branch.
2. Make your change. Run any tests or checks the README documents.
3. Open a pull request against `main`. Describe the motivation and any
   trade-offs.
4. Maintainer review may request changes. Once approved, the maintainer
   will merge.

## Reporting security issues

Do not open a public issue for security vulnerabilities. Email
haritos19@gmail.com directly with details.
