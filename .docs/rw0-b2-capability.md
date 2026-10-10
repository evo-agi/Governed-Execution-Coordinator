# RW0-B2-Capability

## Current implemented contract

<!-- RW0_B2_CAPABILITY_OWNER_BEGIN -->

RW0-B2-Capability is the sole detailed owner of a private, pure,
deterministic, no-I/O semantic layer for worker-mechanism capability. The
implemented layer consists of a candidate-worker-artifact-owner declaration,
an independently authored supplied observation, a Coordinator-owned
qualification value, and one pure qualification relation. It is a semantic
prerequisite for later RW0-D/E proof and future RW0-C durable projection. It
does not contact or execute a worker, provider, host, CLI, or App Server.

The implementation is private to
`ge_nwp_coordinator._rw0_worker_mechanism_capability_values`; its `__all__` is
empty and the package root exports none of its values. It performs no I/O and
introduces no public API, schema migration, durable state, process behavior,
network behavior, provider integration, credential handling, or runtime
authority.

### Closed values and identities

`RW0WorkerMechanismCapabilityDeclarationV1` has schema
`governed-execution.nwp-rw0-worker-mechanism-capability-declaration.v1` and
the same string followed by `.identity` as its digest domain. Its ordered
fields are:

1. `schema_id`
2. `capability_declaration_ref`
3. `declaration_source_kind`
4. `declaration_source_ref`
5. `worker_artifact_ref`
6. `worker_artifact_digest`
7. `wire_profile_ref`
8. `wire_profile_digest`
9. `noninteractive_operation`
10. `wire_command_input_only`
11. `wire_result_output_only`
12. `protocol_stdout_only`
13. `private_bounded_diagnostic_stderr`
14. `external_cancellation_control_supported`
15. `external_deadline_control_supported`
16. `invocation_bound_logical_context`
17. `private_history_non_authority`
18. `isolated_credential_use`
19. `private_interaction_material`
20. `zero_git_effects`
21. `restricted_network_access`
22. `external_session_non_authority`
23. `capability_declaration_digest`

Its source kind is exactly `worker_artifact_owner`. Each of the fourteen
dimensions is `supported`, `unsupported`, or `unknown`. The declaration is an
immutable claim for one worker-artifact/Wire-profile pair. It contains no
evidence or time field and does not authenticate its author.

`RW0WorkerMechanismCapabilityObservationV1` has schema
`governed-execution.nwp-rw0-worker-mechanism-capability-observation.v1` and
the same string followed by `.identity` as its digest domain. Its ordered
fields are:

1. `schema_id`
2. `capability_observation_ref`
3. `observation_source_kind`
4. `observation_source_ref`
5. `observation_source_invocation_ref`
6. `evidence_ref`
7. `evidence_digest`
8. `capability_declaration_ref`
9. `capability_declaration_digest`
10. `worker_artifact_ref`
11. `worker_artifact_digest`
12. `wire_profile_ref`
13. `wire_profile_digest`
14. `noninteractive_operation`
15. `wire_command_input_only`
16. `wire_result_output_only`
17. `protocol_stdout_only`
18. `private_bounded_diagnostic_stderr`
19. `external_cancellation_control_supported`
20. `external_deadline_control_supported`
21. `invocation_bound_logical_context`
22. `private_history_non_authority`
23. `isolated_credential_use`
24. `private_interaction_material`
25. `zero_git_effects`
26. `restricted_network_access`
27. `external_session_non_authority`
28. `observed_at`
29. `expires_at`
30. `capability_observation_digest`

Its source kind is exactly `independent_worker_mechanism_observer`. Each
dimension is `confirmed`, `contradicted`, or `unknown`. Its time window is
constructor-valid only when `observed_at < expires_at`. One supplied
observation participates in one qualification; RW0-C retains collection,
conflict, evidence-set completeness, and durable membership ownership.

`RW0WorkerMechanismCapabilityQualificationV1` has schema
`governed-execution.nwp-rw0-worker-mechanism-capability-qualification.v1` and
the same string followed by `.identity` as its digest domain. Its ordered
fields are:

1. `schema_id`
2. `capability_qualification_ref`
3. `capability_declaration_ref`
4. `capability_declaration_digest`
5. `capability_observation_ref`
6. `capability_observation_digest`
7. `worker_artifact_ref`
8. `worker_artifact_digest`
9. `wire_profile_ref`
10. `wire_profile_digest`
11. `phase_basis_ref`
12. `phase_basis_digest`
13. `authority_observation_ref`
14. `authority_observation_digest`
15. `readiness_observation_ref`
16. `readiness_observation_digest`
17. `host_qualification_ref`
18. `host_qualification_digest`
19. `effect_intent_ref`
20. `effect_fence_ref`
21. `effect_fence_digest`
22. `result`
23. `reason`
24. `evaluated_at`
25. `capability_qualification_digest`

Its result is `qualified`, `blocked`, or `unknown`. Constructor-valid pairs
are: `qualified/qualified`; `unknown/b1_host_qualification_unknown`;
`unknown/capability_unknown`; and `blocked` with one of
`b1_binding_mismatch`, `b1_host_qualification_blocked`,
`declaration_observation_mismatch`, `self_observation`,
`observation_expired`, `worker_artifact_mismatch`, `wire_profile_mismatch`,
`declaration_unsupported`, or `observation_nonconformant`.

Each value stores one exact ordered tuple of exact built-in strings. Values
are final, immutable, non-hashable, non-pickleable, copy-stable, and closed to
ordinary construction. Their sole semantic surface is `from_mapping`,
declared readable field attributes, `to_mapping`, `identity_mapping`,
`canonical_identity_bytes`, `computed_digest`, and exact-class equality. Each
operation safely reconstructs existing values before semantic use; no public
semantic method calls another. Identity excludes only the final self-digest,
uses sorted compact UTF-8 JSON without Unicode normalization, and hashes the
UTF-8 digest domain, one NUL byte, and the canonical identity bytes with
SHA-256.

### Fixed Wire binding

The module loads the accepted RW0-B2-Wire owner mapping exactly once during
module initialization and retains only the profile pair
`rw0-wire-nwpf-v1` /
`470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454`.
The owner output must be an exact dictionary in `schema_id`, `profile_ref`,
`manifest`, `profile_digest` order, with schema
`governed-execution.nwp-rw0-wire-protocol-profile.v1` and an exact dictionary
manifest. Before any comparison or lookup, all four keys must be proven exact
built-in strings. Module initialization uses two stages. The capture stage
receives the owner callable, invokes it exactly once, catches only ordinary
exceptions, and returns only the finite status `valid` or `invalid` plus an
optional safe ref/digest pair. Its `finally` cleanup clears the callable,
owner mapping, manifest, key, and value locals. The module then deletes the
imported callable binding on both success and failure before a separate
argument-free stage raises the content-free import-time invariant
`RW0WorkerMechanismCapabilityWireOwnerInvariant`. The 4,021-byte manifest is
neither copied nor retained. Failed initialization retains no hostile callable,
mapping, manifest, key, value, or foreign exception through Capability-owned
traceback frames, globals, defaults, or closures. The invariant has no cause or
context. `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit` propagate
unchanged after cleanup. Caller substitution cannot replace the retained pair.

RW0-B2-Wire continues to own NWPF framing, hostile decoding, worker-result
grammar, source-claim values, and process/result classification. Capability
does not reinterpret or modify Wire bytes.

### B1 composition and qualification precedence

`validate_worker_mechanism_capability_qualification(...)` safely reconstructs
the declaration, observation, and qualification, validates `now_utc`, and
calls B1's private host-validation snapshot seam exactly once. B1 reconstructs
the complete basis, authority, readiness, qualification, current-effect, and
nested C2A/lineage graph through their protected owners, then returns only five
fresh validated built-in projections. Capability uses those projections and
its own reconstructed locals; it never reads the original supplied B1/C2A
objects after the seam. A bare B1 `qualified` field pair is not trusted. B1
exceptions are sanitized as `relation_mismatch`. The Capability qualification
must identify the supplied declaration and observation by their own ref/digest
pairs before result evaluation.

After successful B1 validation, the expected result/reason is selected in
this exact precedence:

1. `blocked/b1_binding_mismatch` when a phase-basis, authority-observation,
   readiness-observation, host-qualification, current-effect, or evaluation
   time coordinate differs from the supplied graph.
2. `blocked/b1_host_qualification_blocked` when B1 is constructor-valid and
   blocked.
3. `unknown/b1_host_qualification_unknown` when B1 is `unknown/unknown`.
4. `blocked/declaration_observation_mismatch` when the observation names a
   different declaration pair.
5. `blocked/self_observation` when declaration and observation source refs are
   equal. Unequal refs prove structural non-collapse only, never source
   authenticity or organizational independence.
6. `blocked/observation_expired` unless
   `observed_at <= now_utc < expires_at`.
7. `blocked/worker_artifact_mismatch` unless declaration, observation,
   Capability qualification, B1 readiness, and B1 host qualification carry
   the same artifact pair.
8. `blocked/wire_profile_mismatch` unless declaration, observation,
   Capability qualification, the fixed Wire owner pair, B1 readiness, and B1
   host qualification carry the same Wire pair.
9. `blocked/declaration_unsupported` when any declaration dimension is
   `unsupported`.
10. `blocked/observation_nonconformant` when no declaration dimension is
    unsupported and any observation dimension is `contradicted`.
11. `unknown/capability_unknown` when no earlier predicate applies and any
    declaration or observation dimension is `unknown`.
12. `qualified/qualified` only when every declaration dimension is
    `supported`, every observation dimension is `confirmed`, and all earlier
    relations hold.

The Capability-local relation counter is exactly 249 units: 72 for declaration
safe reconstruction, 93 for observation safe reconstruction, 78 for
qualification safe reconstruction, and six leaves for the five B1 snapshots
and current time. B1 independently enforces the exact 863-unit host-owner
budget. The successful composed accounting is therefore `863 + 249 = 1112`
through separately enforced counters, with no extra snapshot pass.
Construction limits are 48, 62, and 52;
safe-existing-value limits are 72, 93, and 78; same-class equality limits are
144, 186, and 156.

### Dimensions and later-owner seams

The fourteen dimensions are mechanism-neutral:

- `noninteractive_operation` excludes synchronous prompts, TTYs, and user
  approval; concrete flags or RPC methods remain RW0-D/E work.
- `wire_command_input_only` and `wire_result_output_only` bind only the outer
  committed Wire frames; any provider-native inner format remains private and
  later-owned.
- `protocol_stdout_only` reserves stdout for no bytes or one protocol result.
- `private_bounded_diagnostic_stderr` requires private, redacted, bounded
  diagnostics; numeric caps, retention, and truncation remain RW0-D/E work.
- `external_cancellation_control_supported` and
  `external_deadline_control_supported` require outside control but do not
  choose timer, signal, transport, or termination mechanics.
- `invocation_bound_logical_context` prevents hidden progression state while
  leaving physical process reuse for later proof.
- `private_history_non_authority` prevents history from determining identity,
  replay, retry, or acceptance.
- `isolated_credential_use` forbids Coordinator credential exposure; live
  handoff remains RW0-E/Execution-Substrate-owned.
- `private_interaction_material` keeps prompt, transcript, reasoning,
  response, and JSONL outside Wire, durable, and report surfaces.
- `zero_git_effects` permits no commit, ref, push, pull-request, merge, or
  publication effect.
- `restricted_network_access` grants no egress and leaves any later network
  use separately authorized and bounded.
- `external_session_non_authority` makes any provider session private and
  non-authoritative.

No numeric process, resource, or capture limit is introduced. RW0-D/E retain
the CLI/App Server/provider choice, credentials, sessions, invocation,
supervision, physical observation, process limits, and live proof. Execution
Substrate retains admission and runtime authority on the ES route. RW0-C
retains durable evidence membership and completeness, recovery, terminal
facts. The bootstrap guard owner owns admitted-lineage scope and immutable
acceptance-fact semantics; Capability supplies no durable guard authority.

### Closure, privacy, freshness, and failures

All external fields and stored members are exact built-in strings. Safe refs
are ASCII, 1..96 characters, match `[A-Za-z0-9][A-Za-z0-9.-]*`, exclude the
reserved `connector-`, `tunnel-`, `workspace-`, `org-`, `organization-`, and
`user-` prefixes case-insensitively, and reject IPv4-shaped literals. Digests
are exactly 64 lowercase hexadecimal characters. Times are valid whole-second
UTC `YYYY-MM-DDTHH:MM:SSZ` strings.

Direct mapping closure is exact-dictionary only, rejects more than one extra
entry in O(1), bounds keys to 1..39 ASCII characters, recognizes accepted
field names before privacy fragments, aggregates unknown findings independent
of insertion order, gives private-material rejection precedence over ordinary
unknown fields, and reports missing fields only after closure. Bytes-like
objects are private material. Traversal has cumulative work limits,
active-object cycle detection, and charges repeated non-active aliases again.
Generic `session` and all session-bearing unknown keys are private material;
the exact accepted field `external_session_non_authority` is recognized before
privacy-fragment scanning and remains valid.

The public, content-free `RW0WorkerMechanismCapabilityError` has only one
semantic property, `reason`. Its closed reasons are `invalid_field_type`,
`missing_field`, `unknown_field`, `invalid_enum`, `malformed_ref`,
`malformed_digest`, `invalid_timestamp_window`,
`invalid_length_or_cardinality`, `digest_mismatch`, `graph_cycle`,
`cumulative_work_exhausted`, `privacy_forbidden_material`,
`relation_mismatch`, and `qualification_reason_mismatch`. It is sealed,
weak-referenceable, immutable, and non-pickleable. Capability accepts an error
reason only when it is an exact built-in string in that finite set, then
retrieves the module-owned canonical string for storage. An equal non-string,
a `str` subclass, and an unknown exact string are rejected before registry
insertion. The reason is held only in a module-private weak-key identity
registry whose values are canonical closed reason strings, never caller
payloads. The private construction token and reason are not passed to
`BaseException.__new__` or `BaseException.__init__`; actual inherited
`BaseException.args` is empty.

Read-only data descriptors make `reason` and the compatibility observation
`_reason` identical. Ordinary assignment and deletion are unavailable,
ordinary and direct base-object `__dict__` observation is hidden, `str` and
`repr` are constant and content-free, equality and hashing retain identity
semantics, and copy, deepcopy, pickling, and serialization remain disabled.
Registry entries disappear when the exact error identity is no longer live.
There is no payload registry, and no supplied payload is retained through
Capability-owned traceback locals, globals, defaults, or closures.

Capability first raises its public error outside its internal foreign-exception
handlers and uses `from None`. When the public boundary is invoked outside an
externally active exception handler, the actual inherited `BaseException`
cause and context are both `None`. Capability does not mask those
interpreter-owned slots: if a caller invokes the boundary, or re-raises a caught
Capability error, while an unrelated exception is active, Python may attach
that exception as `BaseException.__context__`. Deliberate mutation through
base-class descriptors, C-level memory tools, or equivalent unsupported
interpreter reflection is likewise outside the sanitization guarantee. Those
external operations are not accepted semantic inputs and create no permission,
authority, equality, serialization, or qualification effect.

No declaration, observation, qualification, digest, profile, provenance, or
report authenticates a source, grants permission, proves physical behavior,
authorizes contact, supplies semantic acceptance, persists a fact, or becomes
durable program truth.

RW0-C1 consumes these unchanged Capability contracts as evidence ranks 7, 8,
and 9. It reconstructs the existing values and invokes the existing
qualification relation at the persisted rank-9 semantic instant; it neither
changes Capability schemas/digests nor grants the evidence executable
authority.



### Governing-reset identity review

P08/P11/P12/P13 protected identities are deliberately superseded only for the
bootstrap guard governing reset: C2A support retains the ordered expansion and
migration-review gate; AGENTS retains repository authority and nonimplementation;
README retains product/status nonclaims; progression retains pure/non-authorizing
boundaries. Their replacement guards verify admitted lineage, cross-program
one-shot permanence, explicit mutable-target supersession, separate non-replenishing
ES operation, and absence of implementation. P01–P07/P09–P10 remain exact.
Wire and Capability own no admission, durable guard, acceptance, B1 schema,
decision, replay/recovery, or runtime truth.

<!-- RW0_B2_CAPABILITY_OWNER_END -->
