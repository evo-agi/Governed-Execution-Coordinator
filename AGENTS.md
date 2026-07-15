# NWP Coordinator Agent Rules

If `.docs/` exists, always treat `.docs/` as the source of truth.

## Ownership

This repository owns the future A2 coding-work durable state contract only.
Current P1 code has no production durable store and no active durable writer.

Bridge remains the guarded worker/evidence adapter. Control Plane remains
product workflow authority. Execution Substrate remains product admission and
runtime authority. Maintenance Agent remains maintenance authority.
Infrastructure Manager remains readiness, provenance, and diagnostics
authority.

Operator/repo policy owns lease issuance and global stop. The coordinator
cannot self-authorize, cannot mint authorization, and cannot treat a valid
digest as execution permission.

Reports are projections only. They are not durable state, authorization,
acceptance, publication, or product truth.

Versioned Coordinator input schemas are closed-world in P1. Unknown fields,
misspelled fields, duplicate JSON object keys, and unversioned extension or
metadata bags must fail before canonicalization or digest comparison.

## P1 Prohibitions

P1 must not implement worker execution, a scheduling loop, a queue consumer, a
daemon, repair, local commit behavior, publication, production storage, a
validation sandbox, executable lease authorization, signing, keys, trust roots,
or a trusted-local/allow-all production authorization path.

P1 public state and report models must not include private briefs, raw prompts,
raw logs, credentials, secrets, local absolute paths, endpoints, platform
identifiers, or trust material.

P1 report projections must be closed typed models. Do not add a generic
sanitize-and-keep payload boundary.

## Change Rules

Before changing authority-sensitive behavior, identify the governing invariant
in `.docs/` and keep architectural and security boundaries intact.

Do not bypass governance layers. Surface conflicts instead of working around
them.

Docs, tests, and code must change together for authority-sensitive behavior.
After changes, update `.docs/` to reflect reality and ensure there is no drift
between code and documentation.
