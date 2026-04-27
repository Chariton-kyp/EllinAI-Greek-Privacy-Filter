# private/ — controller-private records

This directory holds records that are kept by the controller for
internal purposes and for production on request to a supervisory
authority, but that are NOT appropriate for a public-facing repository.
The directory itself is gitignored (see `.gitignore`); this README is
the only file inside `private/` that is tracked in version control.

The split between `docs/` (public) and `private/` (internal) follows
guidance from:

- The Irish Data Protection Commission's RoPA guidance under GDPR
  Article 30, which classifies the Records of Processing Activities as
  internal records available to the controller and to a supervisory
  authority on request, not as a public publication.
- EU AI Act Articles 11 and 18, which require providers of high-risk AI
  systems to keep technical documentation and to make it available to
  national competent authorities and notified bodies, without obliging
  the provider to publish every operational detail.
- ISO/IEC 42001 Annex A controls A.8 and A.9, which require
  confidentiality, integrity, and change management of AI-management-
  system documentation.

## What lives here

| File                                | Purpose                                                                                                         |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `audit_operational.md`              | Detailed operational record of the AWS infrastructure that produced the released artefacts: account ID, S3 bucket name, IAM user / role / inline-policy names, EC2 spot instance IDs, S3 paths, exact run commands. Cross-referenced from `docs/AUDIT_LOG.md`. |
| `ropa_provider.md`                  | The provider-side filled GDPR Article 30 record. The public deployer template is `docs/GDPR_ART30_ROPA.md`.     |
| `dpia_full.md` (optional, if added) | Any future full-form DPIA prepared by the controller. The public summary explanation lives at `docs/DPIA_NOTE.md`. |
| `incident_log.md` (optional)        | Future security-incident records, if any.                                                                        |

## How to reproduce on a fork

A third party reproducing the build pipeline on their own AWS account
needs to populate `private/` with their own equivalent records. The
public `docs/AUDIT_LOG.md` references the redacted-placeholder names
(`<aws-account-id>`, `<gpf-bucket>`, etc.) and lists exactly which
operational identifiers the forker should fill into their own
`private/audit_operational.md`.

The controller of this repository will furnish the actual operational
identifiers to a supervisory authority, notified body, or notarised
auditor on a documented request and within the access controls
required by the relevant regulation (GDPR Article 30, EU AI Act
Article 18, ISO/IEC 42001 A.8/A.9).

## Why this matters

Public exposure of an AWS account ID materially lowers the cost of
targeted social-engineering and resource-enumeration attacks against
the account. Public exposure of bucket names enables enumeration of
the bucket's structure (even with strict policies in place) and
reveals controller identity. Both are routinely treated as
moderate-sensitivity identifiers by AWS, the major cloud-security
frameworks, and standards bodies (NIST SP 800-53, CIS AWS Benchmark).

Keeping these identifiers in `private/` is a low-cost, high-impact
hygiene choice that does not weaken the audit trail: every
operational detail is retained, just not published.
