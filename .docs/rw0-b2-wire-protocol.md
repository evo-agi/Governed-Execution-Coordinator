# RW0-B2-Wire Private Protocol

## Current status and authority

RW0-B2-Wire currently implements one private, pure, no-I/O source module for NWPF v1 representational framing and canonical decoding, two safe unauthenticated source-claim values, a closed worker-result tuple, pure relations, a process/result classifier, and a fixed protocol profile. Physical transport framing and stream/process plumbing remain deferred. It adds no caller, package-root export, transport, source authentication, supervisor, worker, live process, filesystem, database, network, model, Codex, Git, publication, Bridge, ES call, executable permission, durable truth, acceptance, or ownership of the separately implemented Capability semantics.

RW0-B2-Wire also implements one additive private, pure, no-I/O cancellation-control evidence profile for the exact current `author_candidate`, `validate_candidate`, and `review_candidate` targets. It supplies bounded exact-current request, process-observation, and acknowledgement/rejection relations plus an `invalid`/`incomplete`/`finite` evidence classifier. This separate profile neither replaces nor enters NWPF v1 frames and does not widen Capability, B1, C2A, persistence, runtime, or authority ownership.

RW0-B2-Wire does not own or alter RW0-B1 or C2A schema,
canonical-identity, semantic-outcome, or authority contracts; their protected
owner reconstruction and occurrence-work accounting are hardened separately
for fail-closed Capability composition.

RW0-A remains the target phase-entry model; RW0-B1, RW0-B2-Wire, and
RW0-B2-Capability private semantics are current implemented contracts. RW0-C
owns future durable facts, evidence membership, recovery, and terminal outcome;
the bootstrap guard owner owns admitted-lineage scope and immutable acceptance-fact semantics. RW0-D/E own future offline process proof and separately
authorized live proof. Execution Substrate owns admission and runtime lifecycle
on the ES route. Direct-local and ES use the same semantic protocol without
selecting transport or provider. The separate Capability semantics are
implemented under `.docs/rw0-b2-capability.md` and do not widen Wire ownership.

## Canonical records and digests

Each source claim is an immutable, final, slotted, non-pickleable exact built-in mapping value. Ordinary construction is disabled; a private controlled path uses object allocation only after complete validation. Every public boundary reconstructs exact instances, rejects missing-slot or tampered bypass instances with a sealed finite error, and recomputes self-digests before semantic use. Each consumed C2A value first crosses a Wire-owned literal safe-extraction seam for exactly CeilingsV1, AttemptFenceV1, EffectFenceV1, WorkerCommandV1, DeliveryEnvelopeV1, or WorkerObservationV1. That seam requires the committed field inventory, reads every required slot directly, admits only the exact built-in scalar and bounded tuple shapes owned by that field, copies a permitted one-level CeilingsV1 mapping, and only then invokes the owning C2A reconstruction and relations; it never calls the supplied value's generic `to_mapping()` or `_external_value()` during preflight. Direct source mappings admit only exact built-in dictionaries, preflight cardinality in constant time, and bound every exact-string key to `MAX_SOURCE_MAPPING_KEY_CHARS = 37` before ASCII, normalization, privacy, or field comparison. A bounded unknown key is lowercased once: a private-fragment key fails with `privacy_forbidden_material`, while another unknown key fails with `unknown_field`; length/cardinality precedes privacy. All B2-defined safe refs use C2A's 1–96 ASCII alphanumeric/dot/hyphen grammar and forbidden prefixes, plus IPv4-shaped rejection. That IPv4 rule does not rewrite nested pre-existing C2A refs. Digests are exactly 64 lowercase hex characters. Times are whole-second UTC YYYY-MM-DDTHH:MM:SSZ. A claim's final digest is SHA-256 of its domain UTF-8 bytes, NUL, and compact sorted-key UTF-8 JSON of every other field, with no Unicode normalization, ASCII escaping, or NaN.

### Cancellation request claim

RW0WireCancellationRequestObservationV1 has schema governed-execution.nwp-rw0-wire-cancellation-request-observation.v1 and digest domain governed-execution.nwp-rw0-wire-cancellation-request-observation.v1.identity. Its exact ordered fields are:

1. schema_id, request_observation_ref, source_kind, source_ref, source_invocation_ref, evidence_ref, evidence_digest
2. program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, semantic_attempt_ref, candidate_ref
3. command_ref, command_digest, attempt_fence_ref, attempt_fence_digest
4. cancellation_effect_intent_ref, cancellation_effect_fence_ref, cancellation_effect_fence_digest, cancellation_delivery_attempt_ref, cancellation_delivery_envelope_digest
5. target_effect_intent_ref, target_effect_fence_ref, target_effect_fence_digest, target_delivery_attempt_ref, target_delivery_envelope_digest, observed_at, request_observation_digest

source_kind is exactly supervisor or execution_substrate. A direct-local cancellation delivery requires supervisor source; an ES cancellation delivery requires execution_substrate source. command_ref and command_digest name the original author command. There is no cancellation command or physical target process invocation field. The request names a source invocation claiming issuance; it proves no delivery, acknowledgement, signal, exit, teardown, reconciliation, semantic cancellation, permission, or acceptance.

### Process claim

RW0WireProcessObservationV1 has schema governed-execution.nwp-rw0-wire-process-observation.v1 and digest domain governed-execution.nwp-rw0-wire-process-observation.v1.identity. Its exact ordered fields are:

1. schema_id, process_observation_ref, source_kind, source_ref, source_invocation_ref, evidence_ref, evidence_digest, event_kind
2. program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, semantic_attempt_ref, candidate_ref
3. command_ref, command_digest, attempt_fence_ref, attempt_fence_digest, effect_intent_ref, effect_fence_ref, effect_fence_digest, delivery_attempt_ref, delivery_envelope_digest, observed_at, process_observation_digest

source_kind is exactly supervisor or operating_system; event_kind is exactly resource_limit_exceeded or signal_delivered. These are safe source claims, without signal number, resource measurement, PID, host, path, endpoint, handle, credential, log, stdout, stderr, provider, or session.

### Worker result and classifier value

RW0WireWorkerResultV1 stores exactly an immutable tuple of C2A WorkerObservationV1: (worker_started, worker_completed) or (worker_started, candidate_captured, worker_completed). All are worker-authored, share source ref and invocation and every command/delivery/fence/program/work/attempt coordinate, have unique refs and digests, and bind any captured candidate to the preassigned author candidate. Tuple position, never timestamp, is protocol order. It has no independent schema, ref, or digest.

RW0WireProcessResultClassificationV1 stores classification and reason only. Classifications are usable, unusable, invalid. The only usable reason is usable. Invalid reasons are invalid_input, unrelated_fact, duplicate_fact, conflicting_fact, and cancellation_graph_mismatch. Unusable reasons are resource_limit_exceeded, deadline_elapsed, signal_delivered, cancellation_request_pending, cancellation_acknowledged, cancellation_rejected, process_result_contradiction, process_failed, result_missing, result_invalid, and process_evidence_incomplete.

## Supplied graph relations

validate_wire_result_relation checks the closed result tuple, exact common source and lineage, unique identities, candidate binding, and each applicable C2A observation relation using actual supplied attempt and author-effect fences. It confers no process or semantic success.

validate_wire_cancellation_request_relation checks the request digest and type, C2A target delivery/effect relation, C2A cancel delivery/effect relation with the exact target as cancellation target, cancel effect class, immutable target triple, every exposed command/attempt/candidate/fence/delivery coordinate, and route/source ownership. A matching C2A acknowledgement or rejection can use a different source kind/ref/invocation. The exact cancellation graph joins them.

validate_wire_process_observation_relation checks the process digest and type, C2A target delivery/effect relation, and every exposed target coordinate. It does not authenticate a source or prove process action. All relations fail closed with content-free errors. A public Wire error is raised only after any foreign exception and caller-supplied object have left the active handler and boundary frame; its cause and context are `None`, and neither its object nor retained traceback locals expose supplied payloads.

## Frame and canonical JSON

The eight-byte header is:

| Offset | Size | Content |
| --- | ---: | --- |
| 0 | 4 | ASCII NWPF |
| 4 | 1 | version 0x01 |
| 5 | 1 | command 0x01 or worker result 0x02 |
| 6 | 2 | unsigned big-endian payload length |

Exactly one frame is admitted. Command payload has root keys command and delivery, containing complete existing C2A WorkerCommandV1 and DeliveryEnvelopeV1 mappings. Worker-result payload has sole root key observations, an ordered array of complete existing C2A WorkerObservationV1 mappings. No outer semantic identity, checksum, signature, profile, or competing schema appears in a frame.

encode_wire_command_frame, decode_wire_command_frame, encode_wire_result_frame, and decode_wire_result_frame accept exact completely revalidated objects and separately supplied actual fences. Decode requires exact built-in bytes, strict UTF-8, no BOM, no duplicate key, no float or constant, no oversized integer, one exact closed root, exact nested records, and byte-identical canonical re-encoding. JSON parsing preserves every raw object pair and completes shared raw-pair accounting during parse: every pair, including duplicates, is charged; duplicates and bounded key-shape invalidity are recorded without raising so a later syntax failure still wins. After complete syntax succeeds, duplicate failure is selected before one shape traversal. That traversal uses bounded iterator/descent frames proportional only to nesting depth, checks each collection's cardinality before child iteration or output construction, processes one child at a time, never bulk-enqueues siblings, and stops building immediately at the first structural overflow. It requires exact-string object keys no longer than 29 characters (the longest accepted framed field name), bounds shape, and reconstructs a fresh ordinary tree; syntax outranks duplicate, duplicate outranks structural failures, and structural failures outrank the final work-limit check. The hostile tree is never traversed a second time for shape accounting. Canonical re-encoding operates on reconstructed safe values. JSON uses ensure_ascii=False, allow_nan=False, sort_keys=True, separators comma/colon, and no normalization.

| Bound | Command | Worker result |
| --- | ---: | ---: |
| Payload bytes | 5,898 | 16,627 |
| Whole frame bytes | 5,906 | 16,635 |
| Depth | 3 | 4 |
| Containers | 5 | 8 |
| Key pairs | 71 | 77 |
| Scalar leaves | 70 | 169 |
| Hostile work units | 23,746 | 66,770 |

Framed integers are exact built-in int with owning lower bounds and maximum 9,223,372,036,854,775,807. The upper bound is applied to every literal C2A integer leaf during fixed safe extraction, before owner reconstruction, owner canonical identity or digest work, Wire canonicalization, or payload construction; field-specific lower bounds remain owner-enforced. This is Wire representation, not an execution ceiling. Declared over-cap length is rejected before payload allocation or decoding. Hostile work is eight header units plus four per payload byte (UTF-8 decode, JSON tokenize, canonical re-encode, canonical compare), one per key pair, one per container, and one per scalar leaf. A container list member counts as a container only. Closed relation loops are not attacker-expandable work.

Decoder error priority is: invalid_outer_type, short_header, bad_magic, unsupported_version, unsupported_kind, declared_length_over_cap, truncated_payload, trailing_data, invalid_utf8, bom_forbidden, json_token_invalid, duplicate_key, invalid_root_or_scalar, unknown_field, missing_field, nested_record_invalid, noncanonical_payload, relation_mismatch, work_limit_exceeded. Construction and relation errors are invalid_field_type, invalid_field_value, unknown_field, missing_field, invalid_length_or_cardinality, digest_mismatch, privacy_forbidden_material, relation_mismatch. `privacy_forbidden_material` belongs only to direct B2 source-claim construction and relation handling; source claims are classifier inputs, not command/result frame payloads. Nested framed C2A reconstruction therefore remains `nested_record_invalid`, and the fixed decoder reason inventory is unchanged. Errors reveal no supplied content.

## Pure process/result classifier

classify_wire_process_result accepts only C2A adapter facts cancellation_acknowledged, cancellation_rejected, deadline_elapsed, and process_exited, at most one each. It accepts at most two process claims (one per event), one request, and a result of two or three worker facts; total facts are at most ten. Delivery outcomes are excluded. After exact type and cardinality preflight, the classifier captures bounded original object identities but reconstructs and validates every result observation, adapter observation, request, process observation, and supplied fence/delivery value before inspecting any identity, ref, digest, kind, conflict, lineage, or cancellation semantics. Any incomplete, tampered, wrong-digest, or relation-invalid fact is therefore `invalid_input` before duplicate semantics. Only validated facts can make a repeated original object identity, safe ref, or safe digest `duplicate_fact`. Distinct validated identities occupying one at-most-one adapter or process-supplement kind, and acknowledgement plus rejection, are `conflicting_fact`; in particular, two distinct process exits conflict regardless of exit code. All facts must be unique, related, and noncontradictory before usable classification.

The explicitly supplied cancellation effect fence and delivery, joined to the exact author target graph, are the single authoritative cancellation graph. The classifier validates that graph, then any request, then every acknowledgement or rejection against the same graph. A mismatch in any orientation is `cancellation_graph_mismatch`; cancellation responses are not first reduced to generic `unrelated_fact`. `unrelated_fact` is reserved for non-cancellation facts whose ordinary author lineage is unrelated. Request and response source kind, ref, and invocation remain distinct claims.

Priority is: invalid type/cardinality or malformed reconstruction, duplicate, unrelated, conflict, graph mismatch; resource limit; deadline; signal; matching request with acknowledgement, rejection, or pending; response without request; nonzero exit with result contradiction or without result as process failure; zero exit without result; result failure; valid result without process exit; then valid result plus exactly one zero exit as usable. Within invalid facts, reasons order invalid_input, duplicate_fact, unrelated_fact, conflicting_fact, cancellation_graph_mismatch. C2A defines exit range -255..255; B2 treats exact zero as successful exit only for this classifier. No classification implies teardown, reconciliation, semantic cancellation, terminal outcome, durable fact, permission, or acceptance.

## Fixed profile

wire_profile_mapping returns fresh keys in order schema_id, profile_ref, manifest, profile_digest. The profile is rw0-wire-nwpf-v1, schema governed-execution.nwp-rw0-wire-protocol-profile.v1, digest domain governed-execution.nwp-rw0-wire-protocol-profile.v1.identity, canonical identity length 4,021 bytes, digest 470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454. Its manifest fixes authority booleans, frame, JSON, integer, caps, work meter, result grammar, request/process source kinds, and classifier grammar. The profile is absent from frames and proves no authenticity, permission, acceptance, or mechanism choice.

## Additive cancellation-control value

`RW0WireCancellationControlClassificationV1` is a final, slotted, immutable, noncopyable, non-deepcopyable, non-pickleable private value with exactly the ordered fields `classification` and `reason`. Its closed classifications are `invalid`, `incomplete`, and `finite`. Invalid reasons are `invalid_input`, `duplicate_fact`, `unrelated_fact`, `conflicting_fact`, and `cancellation_graph_mismatch`; incomplete reasons are `process_evidence_incomplete`, `resource_limit_exceeded`, `deadline_elapsed`, `signal_delivered`, `cancellation_acknowledged`, and `cancellation_request_pending`; finite reasons are `cancellation_rejected` and `target_process_exited`. The value has no schema, ref, digest, canonical identity, equality override, nullable field, or hidden payload. `finite` is only a supplied control-evidence state for later C2 reasoning, not semantic cancellation, success, teardown, terminality, permission, acceptance, or durable truth.

## Exact-current cancellation-control relations

`validate_wire_exact_current_cancellation_request_relation` validates the target delivery against the exact target fence, validates the cancellation delivery against the cancellation fence and exact target, binds every request target/cancellation coordinate, and binds the request source to the cancellation delivery route. `validate_wire_exact_current_process_observation_relation` validates the target delivery, binds the process claim to the exact target fence/delivery, and admits only the closed supervisor or operating-system resource-limit/signal claims. `validate_wire_exact_current_cancellation_response_relation` first proves the complete request graph and then validates one acknowledgement or rejection against the exact cancellation fence/delivery and target. Direct-local request claims use `supervisor` and responses use `direct_local_adapter`; ES request claims use `execution_substrate` and responses use `es_adapter`. Source refs and invocation refs need not match, and timestamps do not order semantics.

For `author_candidate`, the capsule operand is exactly omitted and both target and cancellation portable capsule digests are null. For `validate_candidate` and `review_candidate`, one exact safely reconstructed `CandidateCapsuleManifestV1` is required and both portable capsule digests equal that manifest. Explicit `None` is not omission.

## Supplied cancellation-control classifier

`classify_wire_exact_current_cancellation_control` accepts zero or one request, an exact built-in tuple of zero to four adapter observations, and an exact built-in tuple of zero to two process observations, for at most seven supplied facts. The singleton roles are request, acknowledgement, rejection, deadline, exit, resource limit, and signal; acknowledgement and rejection conflict. Every occurrence is reconstructed before duplicate classification. Exact precedence is malformed input; duplicate; unrelated role or target; singleton conflict; cancellation-graph mismatch; request absence; rejection; target exit; resource limit; deadline; signal; acknowledgement; request pending. Rejection outranks exit, while exit outranks acknowledgement, signal, resource limit, and deadline. Target process facts without a request remain incomplete; acknowledgement or rejection without a request is a graph mismatch. Exit codes `-255`, `0`, and `255` are equally finite target-process exit evidence, and zero has no cancellation-success meaning.

## Cancellation-control profile identity

`cancellation_control_profile_mapping` returns a fresh exact built-in outer dictionary ordered `schema_id`, `profile_ref`, `manifest`, `profile_digest`, with a fresh complete manifest graph. The schema is `governed-execution.nwp-rw0-wire-cancellation-control-profile.v1`, the profile ref is `rw0-wire-cancellation-control-v1`, the digest domain is `governed-execution.nwp-rw0-wire-cancellation-control-profile.v1.identity`, the canonical manifest is 12,014 bytes, the canonical outer identity is 12,154 bytes, and the profile digest is `4d6f84552b852a4c4073b4238591afd271072f648424eca9e744def436165288`. This profile is additive and never appears in NWPF v1 frames; Capability continues to bind only `rw0-wire-nwpf-v1`.

## Cancellation-control reconstruction and work bounds

Every supplied occurrence is charged before exact safe reconstruction, including repeated aliases. The fixed tariffs are 62 units for `RW0WireCancellationRequestObservationV1`, 54 for `RW0WireProcessObservationV1`, 116 for `WorkerCommandV1`, 92 for `AttemptFenceV1`, 102 for `EffectFenceV1`, 32 for `DeliveryEnvelopeV1`, 124 for `WorkerObservationV1`, and 98 for `CandidateCapsuleManifestV1`. Author/validation-or-review operation maxima are respectively 640/738 for request, 498/596 for process, 764/862 for response, and 1,244/1,342 for the classifier. A relation one unit below maximum fails with content-free `work_limit_exceeded`; classifier exhaustion is `invalid`/`invalid_input`. The manifest and its nested entries use the existing bounded C2A owner reconstruction; Wire values continue to use their existing reconstruction paths. Common graph operands are reconstructed exactly once per operation, and the owning C2A relations remain authoritative for graph coherence.

## Cancellation-control nonclaims

The additive profile and its pure functions perform no I/O and add no public export or production caller. They do not authenticate sources, issue authority, deliver cancellation, launch or control a process, send a signal, select a provider, contact a worker, persist evidence, decide acceptance, reconcile runtime state, or implement RW0-C, RW0-D, RW0-E, Bridge, or Execution Substrate behavior. RW0-C remains future and blocked pending separately governed entry; D/E retain later proof and provider/process responsibilities, and Execution Substrate retains admission and runtime ownership.

## Privacy boundary and later owners

Private key fragments include hostname, host_key, ip_address, endpoint, username, bearer, token, secret, signature, trust_root, prompt, transcript, stdout, stderr, provider, environment_value, absolute_path, workspace_path, and store_path. Direct B2 source-claim values do not admit those fields; frame payloads remain the exact pre-existing C2A mappings and closed Wire roots. Safe refs and digests are correlation claims only. Future physical transport framing, stream/process plumbing, pre-read allocation, supervisor/worker implementation, cancellation delivery, concrete direct-local or ES wrapper/correlation mechanics, source authentication, host verification, credential custody, provider/session behavior, process targeting, live process proof, persistence, result ingest, CLI/App Server integration, and acceptance require their owning RW0-C/D/E and ES contracts.

<!-- RW0_C1_CURRENT_STATUS_BEGIN -->
**RW0-C1 consumer status.**

RW0-C1 now privately persists the supplied Wire request/process claims, C2A
worker observations, worker-result binding, and process-result classification
binding as ranks 10-14. Finite-failure classification is attested at admission
and never recreates an `RW0WireProtocolError` during replay; present and absent
branches are recomputable. C1 neither changes NWPF v1 nor persists frame bytes,
complete manifests, private blob maps, exceptions, stdout/stderr, process
handles, or cancellation-control classification. Earlier statements that RW0-C
persistence was wholly future are superseded only for this bounded evidence
surface; physical transport and RW0-D/E remain future.
<!-- RW0_C1_CURRENT_STATUS_END -->

Bootstrap guard target routing belongs to
`.docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md`. Wire remains pure
representation/classification and owns no admission, guard, B1 schema, acceptance,
durable decision, replay, recovery, or runtime truth.

<!-- RW0_D1_CURRENT_STATUS_BEGIN -->
RW0-D1 is a current private artificial offline process and capsule proof. The guarded Coordinator program-initialization, C2B3D author-effect, Section 41 selection, and RW0-C1 phase writers remain the sole durable owners. A separate fake planner and fake coding worker run under the bounded D1 supervisor; the parent captures one temporary candidate, builds and independently verifies a CandidateCapsuleManifestV1, removes the mutable workspace, and returns a transient typed handback with separate parent-only disposable-state custody. The preassigned fixture base_git_oid is a WorkSpec coordinate, not Git authentication. RW0-D2 validation/review/model closure is next; RW0-C2 physical decision persistence follows D2. D1 grants no live provider/credential or source authentication, ES route, Git/publication effect, terminal acceptance, public service/CLI, or RW0-E runtime authority. The detailed implementation owner is .docs/rw0-d1-offline-process-and-capsule-spine.md.
<!-- RW0_D1_CURRENT_STATUS_END -->

<!-- RW0_D2_CURRENT_STATUS_BEGIN -->
RW0-D2 now contains a bounded private offline source candidate for the two
guarded validation/review effects, checked C1 evidence, separate fake
validator/reviewer/model processes, exact nine-role input, and transient
preadmission handback. This successor updates only the earlier D2-next status.
It adds no durable post-execution Section 41 proposal family, C1 rank-15
admission, C2 decision/acceptance/terminal writer, migration 0005, live model,
ES runtime, or production adapter. External-copy validation and independent
audit remain pending. The detailed owner is
`.docs/rw0-d2-offline-evidence-and-review.md`.
<!-- RW0_D2_CURRENT_STATUS_END -->

<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->
**Current C2 cross-stage status successor.**

Wire remains pure representation/classification and owns no persistence,
admission, decision, acceptance, or runtime. The earlier statements that all
RW0-C durability or C2 persistence was future remain exact stage snapshots;
later separate C2 owners now implement private artificial-offline P0/P1 durable
families. Physical transport, process plumbing, live source authentication,
provider, credentials, ES routing, terminal outcome, and RW0-E remain future.

The independently accepted, bounded private artificial-offline P0→P1 source is
Git tree `161ed4b544baf970cc26428b9805a106ea0f3edf`, locally committed as
`8704e6c7988250598809f3a0daf88c3e11493488` with sole parent
`4519630d0db967066beb21b4ace5004e76827716`. Its exact-byte local gate
recorded 9,473 collected/executed/JUnit/passed, zero failures, errors, and
skips, and three known Python 3.13 multithreaded-fork `DeprecationWarning`s.
That gate performed no push, upstream creation, PR, merge, publication,
deployment, or product effect. Git objects and refs remain commit and
publication truth; audit, validation, provenance, reports, and status prose
are evidence only.

The separate current C2 implementation records P0 immutable admission history,
never current permission. P1 persists one of five durable decision branches and
creates an acceptance fact only on `candidate_acceptance`; the fact is not
terminal truth, executable permission, live custody, runtime admission, or
deployment authority. Decision Basis v2, guarded-command-digest v2, the
historical work-head witness, universal disclosure posture, and acceptance-only
eligibility are current private mechanics. F03 and F05 remain open nonblocking
observations. There is no live enrollment/custody supplier, terminal outcome,
production provider/worker, ES/Bridge route, product Git effect, public service,
queue, scheduler, deployment, or autonomous loop.
<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->
