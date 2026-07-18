# Lease Identity And Authorization

The standing lease schema id is:

`governed-execution.nwp-standing-lease.v1`

The identity contract includes schema/version, lease id, issuer label,
issuance time, valid-from, expiry, revocation state/reference, subject, repo
identity, branch policy, allowed paths, forbidden-path policy identity, task
classes, risk lanes, finite backlog reference/digest, max work items, max
concurrency, max attempts, max repairs, compute/API budget, wall-clock budget,
validation requirements, audit requirements, local-commit permission,
publication permission, cross-repo permission, maintenance permission, cleanup
requirements, reporting cadence, retention policy, global-stop reference,
canonical-digest metadata, and authorization-mechanism descriptor.

The v1 lease input schema is closed-world. The top-level lease object and all
nested identity objects have exact allowed-key sets. Unknown fields, misspelled
fields, duplicate JSON object keys, and unversioned extension or metadata bags
are rejected before canonicalization and before digest comparison. Schema
evolution requires a new schema version or an explicitly versioned compatible
change.

Canonicalization uses UTF-8 JSON, sorted object keys, compact separators, and
deterministic primitive encoding. Ordered arrays preserve caller order.
Explicitly set-like string arrays reject duplicates and are sorted
lexicographically. The digest is SHA-256 over the canonical identity payload.

The parse sequence is decode input, reject duplicate keys, validate
schema/version, reject unknown keys recursively, validate field types and
bounded values, construct the normalized model, construct the canonical
mapping, and then compute or verify the digest. Unknown input is never accepted
as though it were absent from the canonical identity.

Identity validation returns a typed `LeaseIdentityValidation` with safe
`ValidationIssue` entries. It proves only:

- schema validity;
- canonical form;
- digest match;
- time-window shape;
- bounded field shape;
- finite-backlog binding shape.

Identity validation never returns executable authorization. The typed
`AuthorizationDecision` is a contract object for external operator/repo policy
truth. The production/default provider remains separate and fail-closed because
no issuer trust, verifier trust root, signing authority, key owner, custody
model, or alternative operator-local authorization mechanism is selected in
P1/P1.1.

Production code must contain no allow-all provider, local-dev bypass,
environment-variable bypass, unsigned-fixture execution path, or implicit
trusted-local authority.

Permission-shaped fields in the identity contract do not grant P1 execution.
`publication_permission`, `cross_repo_permission`, `maintenance_permission`,
`local_commit_permission`, `max_repairs`, and `max_concurrency` remain identity
fields only unless a future exact authorization and execution contract says
otherwise.

Transition evaluation consumes typed lease identity, lease runtime,
authorization, dependency, and global-stop decisions. Raw caller booleans are
not authority.

## B3a Lease Runtime

B3a replaces loose `lease_expired` and `lease_revoked` transition-context
booleans with `LeaseRuntimeDecision`. The decision contains a safe lease ref,
one exact UTC evaluated-at timestamp, a closed `LeaseRuntimeStatus`, and a
closed reason. Status values are `active`, `not_yet_valid`, `expired`,
`revoked`, and `revocation_unknown`.

`derive_lease_runtime_decision` is pure. It parses the stored `StandingLease`
with the same timezone-aware ISO timestamp grammar used by identity validation,
then parses a transaction UTC timestamp. Lease timestamps may use `Z`,
`+00:00`, or another explicit offset and are normalized only for comparison.
Naive or malformed timestamps fail. The transaction timestamp serializes in
exact `Z` form in `LeaseRuntimeDecision.evaluated_at`. It derives status with
this precedence: revoked, revocation unknown, not yet valid, expired, active.
A revoked lease may transition to the explicit canceled-revoked terminal state
where the state machine permits it. An expired lease may transition to the
explicit lease-expired terminal state where permitted. Revocation unknown fails
closed and is not treated as not revoked.

B3a adds no current lease-status row. Transition events carry the complete
`LeaseRuntimeDecision` mapping so the transaction timestamp and runtime status
that affected acceptance or domain rejection are integrity-bound by event
identity. Any future mutable revocation or live lease-status authority requires
a separate accepted contract.

## B3a Authorization Receipt Binding

`AuthorizationDecision` includes `lease_identity_decision_ref`. The canonical
authorization decision JSON and digest cover schema id, decision ref, lease
ref, lease-identity-decision ref, lease-identity validity, authorization model,
authorized, executable, and reason.

The decision is internally coherent: `executable` implies `authorized`,
`accepted` is the only authorized reason, and an invalid lease identity forces
both authorization flags false.

`authorization_model=unsupported` is the only currently supported production
posture and remains fail-closed. `authorization_model=operator_policy` remains
schema vocabulary only; B3a adds no verifier, trust root, executable authority,
or production allow provider. Future B3 transition apply must treat an
operator-policy authorization receipt as `validation_failed` until a separate
authorization architecture is accepted.
