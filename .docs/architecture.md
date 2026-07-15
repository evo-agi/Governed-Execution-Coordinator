# NWP Coordinator Architecture

The canonical component name is NWP Coordinator.

Current repository name: Governed Execution Coordinator. This operational
repository name is provisional. It may change without changing schema, authority, or durable identifiers.
Repository naming must not affect schema, authority, or durable identifiers.

## Scope

A2-P1 establishes a local Coordinator skeleton for future A2 coding-work
state. It contains domain models, deterministic identity contracts, a pure
state transition engine, and non-authoritative report projections.

P1 versioned inputs are closed-world contracts. Unknown keys, duplicate JSON
object keys, misspelled keys, and unversioned extension bags fail before
canonicalization or digest verification.

P1 is not an executable coordinator slice. It has no worker invocation path,
no scheduler, no daemon, no queue consumer, no production store, no sandbox,
no repair executor, no local commit behavior, and no publication behavior.
It also has no production future-stage enablement policy or configuration.

## Authorities

The future NWP Coordinator owns only future A2 coding-work durable state.
Bridge remains a guarded worker/evidence adapter. Codex remains a worker only.
Control Plane remains product workflow authority. Execution Substrate remains
product admission/runtime authority. Maintenance Agent remains maintenance
authority. Infrastructure Manager remains readiness, provenance, and
diagnostics authority.

Operator/repo policy owns lease issuance and global stop. The Coordinator
observes and enforces those decisions but cannot issue them, clear them,
weaken them, reinterpret them, or self-authorize.

ChatGPT, connector state, API request/session context, Symphony, reports,
Bridge ledgers, Bridge reports, and local runner evidence remain adapters or
projections. They are not durable A2 state.

## P1 Package

The implementation namespace is `ge_nwp_coordinator`. That package name is an
implementation detail, not a durable identity and not a promise about the
repository display name.

Runtime code uses only the Python standard library. Test-only fakes live under
`tests/`; production code provides only fail-closed authorization and a
state-store protocol.

Report projections are closed typed models. They expose safe refs, enums,
bounded counters, global-stop status, and a fixed non-authority notice only;
they are not generic sanitized payloads and do not carry private, endpoint,
path, platform, credential, or trust material.
