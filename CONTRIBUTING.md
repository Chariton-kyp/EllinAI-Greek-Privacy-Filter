# Contributing to the Greek Privacy Filter

Thank you for your interest in contributing. This document explains how
contributions to this repository are licensed and what you agree to by
opening a pull request.

## Licence of contributions

By submitting a pull request, issue with a code/text patch, or any
other contribution to this repository, you agree that your
contribution is offered under the same public-release licence as the
corresponding artefact in the repository: `LICENSE-NC`.

Contributions to source code, documentation, or data **do not** entitle
you to any rights in fine-tuned model weights or other artefacts
produced from this repository. The copyright holder (Chariton Kypraios,
haritos19@gmail.com) retains all commercial rights in project-authored
material.

By contributing, you acknowledge that:

1. The maintainer may train, evaluate, and redistribute
   non-commercial public-release artefacts derived from a corpus that
   includes your contribution.
2. The maintainer may keep your contribution in the public
   non-commercial codebase indefinitely.
3. You are not entitled to compensation, royalties, or attribution in
   any downstream artefact built from those weights, beyond attribution
   expressly required by `LICENSE-NC`.

If you cannot agree to the above, please do not submit contributions.

## What you should NOT contribute

- Real personal data (real Greek names, real ΑΦΜ / ΑΜΚΑ / addresses,
  etc.). All sample data in this repo is synthetic. PRs adding real PII
  will be rejected.
- Code or text copied from sources whose licence is incompatible with
  this non-commercial public release. If you are unsure, open an issue
  first.
- Operational identifiers (AWS account IDs, real S3 bucket names, IAM
  user/role names, instance IDs). These must never be committed.
- Non-public benchmark material, including `data/realworld_benchmark/`,
  full benchmark traces, per-case predictions, expected spans,
  redacted text, failure-mining contexts, or benchmark-builder source
  files. Public benchmark evidence must be aggregate-only.

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
