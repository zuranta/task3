<!--
Sync Impact Report
- Version change: [TEMPLATE] → 1.0.0 (initial ratification)
- Modified principles: n/a (first concrete adoption; all 5 slots filled from template placeholders)
  - [PRINCIPLE_1_NAME] → I. Code Quality
  - [PRINCIPLE_2_NAME] → II. Secure Credential Handling
  - [PRINCIPLE_3_NAME] → III. Automated Testing Discipline
  - [PRINCIPLE_4_NAME] → IV. CI Enforcement (Quality Gates)
  - [PRINCIPLE_5_NAME] → V. Incremental, Reviewable Delivery
- Added sections:
  - Technology & Security Standards (was [SECTION_2_NAME])
  - Development Workflow & Quality Gates (was [SECTION_3_NAME])
  - Governance (amendment procedure, versioning policy, compliance review)
- Removed sections: none
- Templates requiring follow-up: none checked automatically by this command (out of scope per
  Scope Guard); recommend reviewing .specify/templates/plan-template.md,
  spec-template.md, tasks-template.md, and checklist-template.md next time they are
  used, to confirm they reference these principles (e.g. testing gate, CI gate) consistently.
- Deferred items:
  - TODO(PROJECT_NAME): No project name was available in the repository (no README,
    package manifest, or prior constitution content). Replace once known.
  - TODO(RATIFICATION_DATE): No prior ratification date exists; set to the date this
    constitution was first adopted (today) unless the project has an earlier, undocumented
    adoption date the user can supply.
-->

# [PROJECT_NAME] Constitution

## Core Principles

### I. Code Quality
Code MUST be clear, self-documenting, and consistent with the project's established
style; comments MUST explain non-obvious *why*, never restate *what* the code already
says. Functions and modules MUST have a single, well-defined responsibility — duplication
across a few similar lines is preferred over a premature abstraction. All code MUST pass
linting and formatting checks (Principle IV) before it is considered done; a feature is
not complete until it is clean.
**Rationale**: Consistent, well-structured code lowers review cost and defect rate, and
keeps the codebase approachable as it grows and as contributors change.

### II. Secure Credential Handling
Hardcoded secrets, API keys, connection strings, or tokens MUST NEVER be committed to
source control, configuration files, container images, or code comments, in any
environment. All calls to Azure services MUST authenticate using Managed Identity (or
workload identity federation) rather than shared access keys, connection strings, or
service principal secrets; the only accepted local-development exception is a
credential chain (e.g. `DefaultAzureCredential` falling back to developer CLI login)
that never persists a secret to disk or history. Any credential that has no
managed-identity equivalent (e.g. a third-party API key) MUST live in a managed secret
store (such as Azure Key Vault) and be resolved at runtime, never inlined or passed as a
plain environment literal in checked-in files. Automated secret scanning (Principle IV)
is the backstop, not the primary control.
**Rationale**: Leaked credentials are among the most common and costly sources of
security incidents; mandating managed identity for Azure removes an entire class of
secret-management risk instead of merely detecting it after the fact.

### III. Automated Testing Discipline
Every feature and bug fix MUST be covered by automated tests written with pytest. Test
suites MUST exercise both success paths and failure paths, explicitly including empty
inputs, malformed or invalid inputs, and boundary conditions — not only the happy path.
Unit tests MUST be deterministic and MUST NOT depend on live external services or
network access; use fakes, mocks, or recorded fixtures, reserving real calls for
clearly separated integration tests. A change that introduces new behavior without
corresponding test coverage MUST NOT be merged.
**Rationale**: Malformed and empty input are the most common real-world triggers of
production incidents; requiring explicit failure-case coverage catches these before
release rather than after.

### IV. CI Enforcement (Quality Gates)
Every pull request MUST pass the following automated CI checks before it can be merged:
linting, formatting verification, the full pytest suite, and secret scanning. A failure
in any gate MUST block merge; there is no manual override, and reviewers MUST NOT
approve a PR with a red CI run. CI configuration itself is part of the codebase and any
change to it MUST go through the same review process as application code.
**Rationale**: Enforcing gates in CI, rather than relying on local discipline or human
review alone, guarantees every merged change meets the same bar regardless of author or
review-time pressure.

### V. Incremental, Reviewable Delivery
Work MUST be delivered in small, coherent stages, each captured as its own commit;
commits MUST NOT bundle unrelated changes. Each stage MUST leave the project in a
working state — building and running, with all existing tests passing — rather than
deferring functionality to a later, larger commit. A pull request MUST be opened as
soon as a stage's quality gates (Principle IV) pass, instead of accumulating multiple
stages into one large PR at the end.
**Rationale**: Small, working, independently reviewable increments reduce review burden,
make regressions easy to bisect, and ensure the project is never in a broken or
unreviewable state for an extended period.

## Technology & Security Standards

Azure service integrations MUST use the official Azure SDK credential chain
(`DefaultAzureCredential` or an explicit managed-identity credential) rather than
hand-rolled key handling. Configuration MUST separate non-secret settings (environment
variables, app config) from secrets (Key Vault references); repositories MUST include
only `.env.example`-style templates, never populated `.env` files with real values.
Dependency versions MUST be pinned and reviewed like any other code change. These
standards operationalize Principle II and are verified by the secret-scanning gate in
Principle IV.

## Development Workflow & Quality Gates

Every pull request MUST correspond to one delivery stage (Principle V) and MUST show
green CI (Principle IV: lint, format, tests, secret scan) before it is eligible for
review or merge. At least one reviewer MUST confirm the PR complies with the Core
Principles above; any deviation (e.g., an unavoidable temporary broken state, a
justified exception to managed identity) MUST be called out explicitly in the PR
description with a rationale. Branch protection MUST require CI success and review
approval before merge — neither may be bypassed except by explicit, documented
maintainer decision.

## Governance

This constitution supersedes any conflicting team practice, template default, or prior
informal convention. Amendments are made by editing this file via a pull request that:
(1) states the proposed change and rationale, (2) is reviewed and approved the same as
any other change under Principle IV, and (3) updates the version and Sync Impact Report
per the versioning policy below. Versioning follows semantic versioning: MAJOR for
backward-incompatible governance or principle removals/redefinitions, MINOR for a new
principle or materially expanded guidance, PATCH for wording clarifications and
non-semantic fixes. Every PR review MUST verify compliance with the Core Principles;
unresolved deviations MUST be justified in the PR description or the PR MUST NOT be
merged. Use this document, not memory or tribal knowledge, as the source of truth for
runtime development guidance.

**Version**: 1.0.0 | **Ratified**: 2026-07-30 | **Last Amended**: 2026-07-30
</content>
</invoke>
