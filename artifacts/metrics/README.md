# Metrics artefact policy

This directory keeps public, non-sensitive audit evidence.

Allowed public files:

- aggregate benchmark summaries, such as `benchmark_summary.json`;
- dataset curation reports;
- provenance reports;
- archived aggregate baseline metrics.

Do not commit full private benchmark traces here. Files named
`benchmark_triage*.json`, `failure_mining*.json`, and `realworld*.json`
are ignored because they can contain private OOD case text, expected
spans, predictions, redacted text, or failure-mining contexts.

Public releases should remain aggregate-only
repository.
