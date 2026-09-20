# RW0-B2-Wire Private Protocol

## Current status and authority

RW0-B2-Wire currently implements one private, pure, no-I/O source module for NWPF v1 representational framing and canonical decoding, two safe unauthenticated source-claim values, a closed worker-result tuple, pure relations, a process/result classifier, and a fixed protocol profile. Physical transport framing and stream/process plumbing remain deferred. It adds no caller, package-root export, transport, source authentication, supervisor, worker, live process, filesystem, database, network, model, Codex, Git, publication, Bridge, ES call, executable permission, durable truth, acceptance, or Capability implementation.

RW0-A remains the target phase-entry model; RW0-B1's pure phase-entry values and C2A's semantic values and six relations are unchanged. RW0-C owns any future durable facts, evidence membership, recovery, terminal outcome, and acceptance latch. RW0-D/E own offline process proof and separately authorized live proof. Execution Substrate owns admission and runtime lifecycle on the ES route. Direct-local and ES use the same semantic protocol without selecting transport or provider. Capability remains seam-bounded and unimplemented.

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

## Privacy boundary and later owners

Private key fragments include hostname, host_key, ip_address, endpoint, username, bearer, token, secret, signature, trust_root, prompt, transcript, stdout, stderr, provider, environment_value, absolute_path, workspace_path, and store_path. Direct B2 source-claim values do not admit those fields; frame payloads remain the exact pre-existing C2A mappings and closed Wire roots. Safe refs and digests are correlation claims only. Future physical transport framing, stream/process plumbing, pre-read allocation, supervisor/worker implementation, cancellation delivery, concrete direct-local or ES wrapper/correlation mechanics, source authentication, host verification, credential custody, provider/session behavior, process targeting, live process proof, persistence, result ingest, CLI/App Server integration, and acceptance require their owning RW0-C/D/E and ES contracts.
