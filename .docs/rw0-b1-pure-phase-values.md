# RW0-B1 private pure phase-entry values

Classification: CURRENT IMPLEMENTED CONTRACT after the bounded RW0-B1 source
tranche. This document governs only private, deterministic, no-I/O semantic
values and relations over supplied facts. It does not establish a durable
phase-entry fact, authenticate an external source, issue executable authority,
retrieve bytes, contact a host, run a worker, or close RW0 durably.

The accepted RW0-A operating model remains the target authority. The B1 source
contains the eight exact value families, their domain-separated identities,
and the pure relations frozen in the RW0-B1 implementation request. Its current
path-scope digest is a correlation over the exact validated C2A path tuple;
the C2A three-path set is a current compatibility edge, not enduring RW0 path
policy. C2A, C2B3D, and Section 41 keep their existing identities and grammar.

External standing policy and its verifier own the parent grant, family claim,
revocation, expiry, and source authenticity. The physical custodian owns byte
availability and retrieval events. The host owner owns readiness claims.
Coordinator owns only the inert subordinate proposal and pure qualification.
RW0-C owns guarded persistence, evidence membership and completeness, terminal
facts and readback. The bootstrap guard owner owns admitted-lineage scope and
immutable acceptance-fact semantics. RW0-B2-Wire owns representational
framing and process/result classification. RW0-B2-Capability owns only
provider- and mechanism-neutral declaration, supplied observation, and pure
qualification semantics. RW0-D/E own concrete CLI, App Server, provider,
credential, session, process, physical-custody, worker, capsule, and live-host
proof mechanics; ES keeps ES-route runtime authority. B1 schemas, relations,
identities, and nonclaims are unchanged; protected owner reconstruction and
occurrence-work budgets are hardened by this current contract.

No source, observation, effect, path, or schema enum in C2A is widened. B1
values never contain raw WorkSpec or plan bytes, bearer material, host details,
provider data, prompts, transcripts, stdout, stderr, or physical paths. A
syntactically valid digest proves identity only, not authenticity or permission.

Implementation must stop if a new public, durable, I/O, worker, Bridge, ES, or
provider dependency is needed, if an existing identity changes, or if a
frozen field or traversal budget mechanically undercounts the final schema.

## Current-contract registry

Only the bounded registry below is machine-authoritative for the facts that it
owns. Projection rows consume their named owner and create no second authority.

<!-- RW0_B1_CURRENT_CONTRACT_REGISTRY_BEGIN -->
Registry version: 3

| Fact | Value | Role | Source |
| --- | --- | --- | --- |
| component | RW0-B1 | authority | this_document |
| lifecycle_status | current_implemented | projection | .docs/rw0-remote-worker-contact-phase-entry.md |
| contract_class | private_pure_no_io_semantics | projection | .docs/rw0-remote-worker-contact-phase-entry.md |
| retrieval_event_sequence_work_maximum | 1285 | authority | this_document |
| sole_current_pure_cross_module_production_consumer | RW0-B2-Capability | authority | this_document |
| current_bounded_runtime_phase_construction_consumer | RW0-D1-pre-execution | authority | this_document |
| current_bounded_runtime_phase_evidence_consumer | RW0-D1-handback | authority | this_document |
| source_authentication | none | authority | this_document |
| executable_permission | none | authority | this_document |
| durable_persistence | none | authority | this_document |
| semantic_acceptance | none | authority | this_document |
| future_bootstrap_acceptance_guard_owner | RW0-C | projection | .docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md |
| future_durable_ingest_completeness_recovery_terminal_owner | RW0-C | projection | .docs/rw0-remote-worker-contact-phase-entry.md |
| future_physical_custody_transport_process_cancellation_owner | RW0-D | projection | .docs/rw0-remote-worker-contact-phase-entry.md |
| future_separately_authorized_live_proof_owner | RW0-E | projection | .docs/rw0-remote-worker-contact-phase-entry.md |
| es_admission_reliable_submit_runtime_identity_lifecycle_cancellation_results_owner | Execution Substrate | projection | .docs/rw0-remote-worker-contact-phase-entry.md |
<!-- RW0_B1_CURRENT_CONTRACT_REGISTRY_END -->

## Closed value grammar

All eight classes are immutable slotted values in the private
`_rw0_phase_entry_semantic_values.py` module. They accept exact built-in dicts,
require all keys, reject unknown keys first, reconstruct nested input, and
return fresh built-in projections. Their final field is their sole self-digest.
Identity bytes are compact sorted-key UTF-8 JSON with no Unicode normalization,
and the digest is SHA-256 of schema ID plus `.identity`, NUL, and those bytes.
The module defines no JSON decoder; duplicate-key rejection belongs to a later
decoder.

| Value | Fields | Stored `S` | Construction `C` | Reconstruction `R=S+C` | Equality `2R` |
| --- | ---: | ---: | ---: | ---: | ---: |
| `RW0PhaseEntryBasisV1` | 26 | 122 | 174 | 296 | 592 |
| `RW0AuthorityVerificationObservationV1` | 39 | 78 | 124 | 202 | 404 |
| `RW0SubordinateAuthorizationProposalV1` | 29 | 62 | 92 | 154 | 308 |
| `RW0CustodyAvailabilityObservationV1` | 16 | 17 | 34 | 51 | 102 |
| `RW0RetrievalCapabilityEventObservationV1` | 37 | 38 | 76 | 114 | 228 |
| `RW0RemoteHostReadinessObservationV1` | 39 | 40 | 80 | 120 | 240 |
| `RW0EffectHostQualificationV1` | 45 | 46 | 92 | 138 | 276 |
| `RW0TerminalOutcomeV1` | 31 | 32 | 64 | 96 | 192 |

The schema suffixes, ordered fields, digest domains, and canonical bytes remain
exactly those already frozen below. `S` snapshots the exact stored graph and
reserves any nested owner tariff; `C` is the existing public constructor
limit. Every state-revealing surface reconstructs through the owning grammar
before reading semantic state. Valid copy and deepcopy remain identity-stable
only after that reconstruction succeeds. Ordinary `_values` access remains
hidden.

The exact ordered fields are listed below. Each `schema_id` is the full schema
ID from the table. The digest domain is that full ID followed by `.identity`.
`R` is the existing C2A 1–96 character ASCII safe ref; `H` is a lowercase
64-hex SHA-256; `T` is UTC seconds; `N` is an exact integer in 0 through
2^63−1; `R?` and
`H?` are nullable. `S41N` is 0 through 2^63−1. `BL` is 1 through 65,536 for
selected plans and 1 through 2^63−1 for WorkSpec assertions. `Q` is 0–2.
`L34` is the existing complete `CanonicalC2B3DLineage`; `K8` is its exact
Section 41 key; `C` is the existing fifteen-field `CeilingsV1`; `E` is a sorted
unique 1–5-element list of C2A effect classes. Boolean and integer subclasses
are never integers here.

The `N` bound is a B1 canonical and durable compatibility policy. It covers
every direct B1 integer field, the two integer leaves of reconstructed L34,
and all fifteen `CeilingsV1` leaves before canonical JSON conversion. It does
not change C2A or Section 41 owning validators, and it is not a wire,
allocation, process, token, output, or host-resource cap. One-over values
fail with `invalid_length_or_cardinality` independently of Python's integer
string conversion setting.

### Ordered fields

#### `RW0PhaseEntryBasisV1`

`schema_id`, `basis_ref`, `c2b3d_lineage`, `selection_key`, `selected_proposal_ref`, `selected_proposal_digest`, `selected_artifact_ref`, `selected_artifact_digest`, `selected_artifact_binding_digest`, `selected_plan_safe_projection_digest`, `disposition_ref`, `disposition_digest`, `disposition`, `selection_head_revision`, `selection_head_digest`, `current_effect_head_revision`, `current_effect_head_state`, `current_effect_head_digest`, `current_delivery_head_revision`, `current_delivery_head_state`, `current_delivery_head_digest`, `global_stop_ref`, `global_stop_version`, `global_stop_state`, `path_scope_digest`, `basis_digest`

#### `RW0AuthorityVerificationObservationV1`

`schema_id`, `observation_ref`, `source_ref`, `evidence_ref`, `evidence_digest`, `phase_basis_ref`, `phase_basis_digest`, `parent_grant_ref`, `parent_grant_digest`, `grant_family_ref`, `grant_family_digest`, `attempt_basis_ref`, `attempt_basis_digest`, `effect_basis_ref`, `effect_basis_digest`, `attempt_fence_ref`, `attempt_fence_digest`, `effect_fence_ref`, `effect_fence_digest`, `audience_ref`, `repository_ref`, `base_git_object_format`, `base_git_oid`, `path_scope_digest`, `allowed_effect_classes`, `effect_class`, `parent_ceilings`, `status`, `family_status`, `revocation_status`, `grant_expires_at`, `observed_at`, `observation_expires_at`, `current_effect_head_digest`, `current_delivery_head_digest`, `global_stop_ref`, `global_stop_version`, `global_stop_state`, `observation_digest`

#### `RW0SubordinateAuthorizationProposalV1`

`schema_id`, `proposal_ref`, `phase_basis_ref`, `phase_basis_digest`, `verification_ref`, `verification_digest`, `parent_grant_ref`, `parent_grant_digest`, `grant_family_ref`, `grant_family_digest`, `attempt_basis_ref`, `attempt_basis_digest`, `effect_basis_ref`, `effect_basis_digest`, `attempt_fence_ref`, `attempt_fence_digest`, `effect_fence_ref`, `effect_fence_digest`, `audience_ref`, `repository_ref`, `base_git_object_format`, `base_git_oid`, `path_scope_digest`, `effect_class`, `ceilings`, `expires_at`, `global_stop_ref`, `global_stop_version`, `proposal_digest`

#### `RW0CustodyAvailabilityObservationV1`

`schema_id`, `observation_ref`, `source_ref`, `evidence_ref`, `evidence_digest`, `phase_basis_ref`, `phase_basis_digest`, `subject_kind`, `subject_ref`, `subject_semantic_digest`, `content_sha256`, `byte_length`, `availability`, `observed_at`, `expires_at`, `observation_digest`

#### `RW0RetrievalCapabilityEventObservationV1`

`schema_id`, `event_ref`, `source_ref`, `evidence_ref`, `evidence_digest`, `phase_basis_ref`, `phase_basis_digest`, `safe_correlation_ref`, `subject_kind`, `subject_ref`, `subject_semantic_digest`, `content_sha256`, `byte_length`, `semantic_attempt_ref`, `attempt_fence_ref`, `attempt_fence_digest`, `effect_intent_ref`, `effect_fence_ref`, `effect_fence_digest`, `audience_ref`, `repository_ref`, `base_git_object_format`, `base_git_oid`, `path_scope_digest`, `authority_observation_ref`, `authority_observation_digest`, `subordinate_proposal_ref`, `subordinate_proposal_digest`, `custody_observation_ref`, `custody_observation_digest`, `event_kind`, `predecessor_event_ref`, `predecessor_event_digest`, `sequence_number`, `occurred_at`, `expires_at`, `event_digest`

#### `RW0RemoteHostReadinessObservationV1`

`schema_id`, `observation_ref`, `source_ref`, `evidence_ref`, `evidence_digest`, `safe_host_correlation_ref`, `status`, `platform`, `platform_profile_ref`, `platform_profile_digest`, `architecture_profile_ref`, `architecture_profile_digest`, `worker_artifact_ref`, `worker_artifact_digest`, `worker_protocol_ref`, `worker_protocol_digest`, `execution_identity_profile_ref`, `execution_identity_profile_digest`, `process_profile_ref`, `process_profile_digest`, `isolation_profile_ref`, `isolation_profile_digest`, `resource_profile_ref`, `resource_profile_digest`, `cancellation_profile_ref`, `cancellation_profile_digest`, `credential_handoff_profile_ref`, `credential_handoff_profile_digest`, `capsule_store_profile_ref`, `capsule_store_profile_digest`, `validation_tool_profile_ref`, `validation_tool_profile_digest`, `review_tool_profile_ref`, `review_tool_profile_digest`, `cleanup_profile_ref`, `cleanup_profile_digest`, `observed_at`, `expires_at`, `observation_digest`

#### `RW0EffectHostQualificationV1`

`schema_id`, `qualification_ref`, `phase_basis_ref`, `phase_basis_digest`, `effect_intent_ref`, `effect_fence_ref`, `effect_fence_digest`, `verification_ref`, `verification_digest`, `readiness_ref`, `readiness_digest`, `required_scenario_profile_ref`, `required_scenario_profile_digest`, `required_platform_profile_ref`, `required_platform_profile_digest`, `required_architecture_profile_ref`, `required_architecture_profile_digest`, `required_worker_artifact_ref`, `required_worker_artifact_digest`, `required_worker_protocol_ref`, `required_worker_protocol_digest`, `required_execution_identity_profile_ref`, `required_execution_identity_profile_digest`, `required_process_profile_ref`, `required_process_profile_digest`, `required_isolation_profile_ref`, `required_isolation_profile_digest`, `required_resource_profile_ref`, `required_resource_profile_digest`, `required_cancellation_profile_ref`, `required_cancellation_profile_digest`, `required_credential_handoff_profile_ref`, `required_credential_handoff_profile_digest`, `required_capsule_store_profile_ref`, `required_capsule_store_profile_digest`, `required_validation_tool_profile_ref`, `required_validation_tool_profile_digest`, `required_review_tool_profile_ref`, `required_review_tool_profile_digest`, `required_cleanup_profile_ref`, `required_cleanup_profile_digest`, `result`, `reason`, `evaluated_at`, `qualification_digest`

#### `RW0TerminalOutcomeV1`

`schema_id`, `outcome_value_ref`, `phase_basis_ref`, `phase_basis_digest`, `branch`, `outcome`, `decision_ref`, `decision_digest`, `decision_kind`, `program_head_revision`, `program_head_digest`, `work_item_head_revision`, `work_item_head_digest`, `selection_head_revision`, `selection_head_digest`, `effect_head_revision`, `effect_head_digest`, `delivery_head_revision`, `delivery_head_digest`, `global_stop_ref`, `global_stop_version`, `global_stop_state`, `evidence_set_ref`, `evidence_set_digest`, `latch_postimage_ref`, `latch_postimage_digest`, `reconciliation_ref`, `reconciliation_digest`, `mismatch_ref`, `mismatch_digest`, `outcome_value_digest`

### Finite domains and local shape

Phase disposition is exactly `selected_for_dispatch_gates`. Effect and
delivery head states use the current six C2B states each. Global stop is
`clear` or `active`. Authority status is `verified`, `denied`, or `unknown`;
family is `compatible`, `incompatible`, or `unknown`; revocation is
`unrevoked`, `revoked`, or `unknown`. Effects use the existing deliverable C2A
classes. Custody subject is `work_spec` or `selected_plan`, and availability is
`available`, `unavailable`, or `unknown`. Retrieval kinds are `issued`,
`redeemed`, `consumed`, `expired`, `revoked`, `failed`, and `unknown`. Readiness
status is `ready`, `unready`, or `unknown`; platform is `linux`. Qualification
result is `qualified`, `blocked`, or `unknown`, with reasons `qualified`,
`readiness_unready`, `readiness_unknown`, `readiness_expired`,
`authority_not_verified`, `authority_denied_or_revoked`, `authority_expired`,
`phase_or_effect_mismatch`, `worker_artifact_mismatch`,
`worker_protocol_mismatch`, `platform_or_architecture_mismatch`,
`profile_mismatch`, `global_stop_active`, or `unknown`. Qualified pairs only
with qualified, unknown only with unknown, and blocked only with one of the
other twelve reasons.

Terminal branches are `normal`, `active_cancel_reconciled`,
`active_cancel_unresolved`, and `pre_effect_cancel_basis_unusable`. Outcomes
and decision kinds are `accept`, `repair`, `replan`, `terminal_reject`, `block`,
or `cancel`. The normal accept branch requires the legacy pair; normal same-kind
repair, replan, terminal reject, or block forbids all optional pairs. Reconciled
cancel maps cancel to cancel with reconciliation. Unresolved active cancel maps
cancel to block with reconciliation. Unusable pre-effect cancel basis maps
cancel to block with mismatch. Other optional pairs are absent in each row.

All optional ref/digest pairs are jointly present or jointly absent. Fresh
observation windows require `observed_at < expires_at`; verified progression
uses `observed_at <= now_utc < expires_at`. Equal-time expiry fails. A
syntactically valid denied, unknown, unavailable, unready, blocked, failed, or
revoked value remains representable; it grants no progression.

## Pure relation inventory

Each validator is keyword-only, returns `None` on success, uses only supplied
exact owner values, and raises sealed `RW0PhaseValueError` otherwise.
`now_utc` is a caller-supplied time, not clock authority.

| Relation | Bound facts | Maximum B1 units |
| --- | --- | ---: |
| `validate_phase_entry_basis` | Exact L34/K8, selected proposal/artifact/disposition/head postimage, WorkSpec and C2A authoring/delivery, current heads/stop/path | 891 |
| `validate_authority_observation` | Verified compatible unrevoked fresh claim, complete verified-parent containment of attempt/author/current fences, phase and per-fence lineage, scope, heads/stop, C2A current effect relation | 1151 |
| `validate_per_fence_basis` | Two role-specific basis pairs and both fence identities | 550 |
| `validate_external_common_family_claim` | Verifier family compatibility, matching parent family claim, each fence basis; no independent ancestry proof | 550 |
| `validate_subordinate_narrowing` | Current claim, exact attempt/current-effect origin, complete verified-parent containment, and strict effect-set, ceiling, or expiry reduction within parent and both fences | 891 |
| `validate_custody_binding` | Exact phase/semantic subject, selected-plan byte length, live available assertion | 520 |
| `validate_retrieval_event_sequence` | One to three events, current narrowing and complete supplied-parent containment, exact authority/proposal/custody/fence/scope/correlation, predecessor, time and legal sequence | 1285 |
| `validate_host_qualification` | One effect-bound supplied claim, available phase/attempt/current-effect lineage and parent containment, deterministic precedence, profiles and current path | 863 |
| `validate_terminal_outcome_binding` | Decision and current heads/stop, dispatched branch shape; evidence-set binding only | 496 |
| Each of four standalone shape validators | Its exact branch row and decision kind | 97 |

Path correlation is
`SHA256("governed-execution.nwp-rw0-current-path-scope-binding.v1.identity" + NUL + compact JSON of the exact validated C2A path tuple)`.
B1 owns no path list or path policy. The current three-member C2A tuple is a
compatibility edge. Subordinate narrowing uses effect set, ceilings, or expiry,
not path-subset mechanics.

Current authority progression requires a clear basis and observation stop,
exact current stop refs and versions on the attempt, author, and current effect
fences, and exact current effect and delivery head digests. The supplied attempt
fence ref/digest and semantic attempt equal phase-basis L34. A current effect's
semantic attempt and originating attempt-fence pair equal that same basis and
the supplied attempt fence; the observation and proposal attempt pairs do too.
The author fence is checked against L34 and the owning C2A effect relation even
when the caller supplies the same object in both author and current roles. A
later current effect may have a distinct effect-fence identity only within the
same semantic attempt and originating attempt fence. Stable candidate lineage
is the exact L34 `candidate_ref`. Current `EffectFenceV1.command_ref` and
`command_digest` equal L34 `author_command_ref` and `author_command_digest`.
No candidate digest exists or is introduced. Narrowing and its composed
retrieval relation reject candidate-ref or command-lineage drift with
`relation_mismatch`; semantic-attempt or originating-attempt-fence drift retains
`per_fence_basis_mismatch`. B1 validates supplied identities only and grants no
authority. The observation's current
effect pair and effect class, and the proposal's pair and class when supplied,
equal the supplied current effect. The external family compatibility claim
remains supplied verifier evidence; B1 does not infer grant ancestry from
matching digests.

The observation's verified parent pair bounds the supplied attempt, author,
and current effect fences and the proposal where present. The complete attempt
allowed-effect set is a subset of the parent's allowed-effect set. Every
applicable author/current effect class belongs to both sets, and the proposal
effect belongs to both. Each applicable attempt, author, and current fence
ceiling is componentwise no greater than the verified parent ceiling; each
fence expiry is no later than the parent grant expiry. Proposal ceilings and
expiry fit within the parent, attempt fence, and current effect fence.
Where the attempt fence is supplied, the current effect's ceilings also fit
componentwise within the attempt ceilings and its expiry is no later than the
attempt expiry, even when the verified parent is broader. Equality and stricter
current bounds are valid; violations fail `scope_or_ceiling_mismatch`.

Narrowing reconstructs both exact fence leaves through their C2A owning
`from_mapping` contracts, including stored self-digests, and uses C2A's
`_ceilings_at_most`, `_local_git_effect_ceilings`, and
`_non_git_effect_ceilings` predicates. Its shared core enforces the available
C2A attempt/current-effect equalities for parent, originating attempt,
program/version/intent/work/revision, semantic attempt, repository/base, path,
and stop, with program identity supplying the B1 audience binding. It checks
the permitted effect class and stable candidate/command lineage supplied by
L34. This is the available-object projection of the owning relation; narrowing
has no author-command object, author-fence object, capsule, or cancellation
target and cannot validate those absent graphs. `validate_authority_observation`
retains the full C2A `validate_effect_relation` call with those supplied objects.
Retrieval composes narrowing once with the same budget; owner reconstruction of
already charged external leaves neither resets nor adds B1 traversal charges.
Strictness is measured only against the verified parent: a one-effect proposal
with equal ceilings and expiry is not narrower when the parent permits only
that effect. All supplied stop coordinates, current heads, and current path
binding must match the clear phase basis; `now_utc` must be strictly before
each applicable expiry.

A B1 traversal unit is a value, container, or member occurrence charged before
descent. Active-object identity detects cycles. Shared aliases are charged on
every occurrence. Before any semantic read, raw B1 storage is inspected only
through exact owner-known slots with a non-recursive stack. Nested C2A and L34
values reserve their full owner tariff in the outer counter and are then
independently reconstructed by their owners. Construction retains its existing
independent `C` meter. The common closed-mapping path first requires an exact
built-in dict and checks its cardinality in O(1), before caller-key iteration,
aliasing, materialization, sorting, or copying. A mapping larger than its exact
allowed field count necessarily contains an unknown key and fails immediately
with content-free `unknown_field`, even if an excess key names private material.
For remaining mappings, one key pass scans at most the fixed field count;
non-exact key types retain type-error precedence, and the first unknown key's
existing classification precedes missing-field rejection. Once all keys are
known, a smaller cardinality is missing-only. Maximum valid mappings retain
their existing construction budgets, schema identities, and canonical bytes.
Relation budgets have one shared exact outer counter, including terminal shape
dispatch. The maximum formulas are
`296+70+4+172+92+102+116+32+3+4=891`,
`296+202+92+102+102+116+98+102+1+4+30+6=1151`,
`202+154+92+102=550` for each two-fence relation,
`296+202+154+92+102+1+8+30+6=891`,
`296+51+172+1=520`,
`296+51+202+154+3*114+1+92+102+1+8+30+6=1285`,
`296+202+120+138+102+1+4=863`,
`296+96+7+96+1=496`, and `96+1=97` respectively. The terminal
binding intentionally reconstructs the outcome again in its nested shape
check. If these limits cannot accommodate the exact frozen fields under
faithful traversal, implementation stops rather than increasing a limit.

The private `_validate_host_qualification_with_snapshots(...)` seam performs
the complete 863-unit validation once and returns only fresh validated built-in
projections for basis, authority, readiness, qualification, and current effect.
The public validator delegates to that core and still returns `None`.
RW0-B2-Capability is the seam's sole cross-module production consumer.

The Section 41 owner supplies a private exact
`CanonicalC2B3DLineage` reconstruction helper with raw graph work 35 and
complete tariff 70. It reads the exact L34 slots without recursion and returns
a fresh exact lineage plus a fresh plain projection. B1 reserves that full
tariff before calling the independently metered owner helper. The L34 field
inventory, route meaning, canonical bytes, and authority posture do not change.

This is an occurrence-work contract, not a finite integer-bit-length,
serialized-byte, or wall-clock bound. It adds no C2A integer upper limit and no
SQLite-width restriction.

Retrieval first checks the current clear-stop, verified and fresh authority,
strict parent-based subordinate narrowing, compatible current fences, and a
live available custody assertion under the same traversal budget.
The retrieval limit is 1285 B1 units: 296 basis + 51 custody + 202 authority
observation + 154 proposal + 3×114 retrieval events + 1 sequence container +
92 attempt-fence reconstruction + 102 current-effect-fence reconstruction + 1
supplied time + 8 current-path occurrences + 30 external ceiling-member
occurrences + 6 external effect-set occurrences. The narrowing helper charges
those final 36 occurrences exactly once against the retrieval caller's shared
budget; it neither resets that budget nor treats uncharged work as charged.
Legal retrieval prefixes are `issued`, `issued -> redeemed`, and
`issued -> redeemed -> consumed`; expired, revoked, failed, or unknown may
terminate an issued or redeemed prefix. Singleton failed or unknown is
diagnostic. Issuance, redemption, and consumption require live asserted
custody, verification, proposal, grant, and fences. Expiry may be recorded at
or after the one immutable expiry for the safe correlation. Every event ref in
the sequence is unique, no predecessor is self-referential, and a later event
cannot extend that expiry. Revoked, failed, and unknown may occur on either
side of expiry but are terminal. A terminal event does not permit reuse or retry.

Host qualification precedence is phase/effect/fence mismatch, active global
stop, denied/revoked authority, expired authority, unknown authority, family
claim or parent/current-fence incompatibility, expired readiness, unready readiness, unknown readiness,
worker artifact, worker protocol, platform or architecture, other required
profile, then qualified. The required scenario profile is a Coordinator
context binding without a readiness counterpart.

Qualification binds the observation attempt-fence pair and attempt basis to
L34, the current effect's semantic attempt and originating attempt pair to
L34, the exact current `candidate_ref` to L34 `candidate_ref`, and current
`command_ref`/`command_digest` to L34 `author_command_ref`/`author_command_digest`.
It reconstructs the current fence through its C2A owner and binds
the observation current-effect pair/class to the supplied fence, and the
available parent pair, allowed effect class, current-fence ceilings/expiry,
heads, path, and clear stop. Its signature has no `AttemptFenceV1` object, so
it cannot recheck the absent attempt fence's effect-set, ceilings, or expiry,
authenticate the grant, or reconstruct that fence. Identity drift computes
`blocked/phase_or_effect_mismatch`; structurally invalid parent containment
computes `blocked/authority_not_verified` after higher-precedence cases.

## Failures, privacy, and consumers

The sealed error reasons are `invalid_field_type`, `missing_field`,
`unknown_field`, `duplicate_field` (reserved for a future decoder),
`invalid_enum`, `malformed_ref`, `malformed_digest`,
`invalid_timestamp_window`, `invalid_length_or_cardinality`, `graph_cycle`,
`cumulative_work_exhausted`, `relation_mismatch`,
`observation_stale_or_expired`, `authority_denied_or_revoked`,
`per_fence_basis_mismatch`, `common_family_unverified`,
`scope_or_ceiling_mismatch`, `path_scope_binding_mismatch`,
`current_head_or_global_stop_mismatch`, `custody_subject_mismatch`,
`retrieval_transition_invalid`, `readiness_profile_mismatch`,
`qualification_reason_mismatch`, `terminal_branch_mismatch`, and
`privacy_forbidden_material`. Messages contain only reason and fixed field
label, with no supplied value or foreign chain.

No B1 value, canonical input, error, projection, or accepted-value test fixture may contain
raw WorkSpec/plan bytes, bearer or credential material, signature or trust
material, hostname, IP, endpoint, key, username, absolute or mutable path,
prompt, transcript, hidden reasoning, Codex JSONL, stdout/stderr, provider
session or account data, or IM bundle body. Safe digests are assertions of
identity; authenticity and permission remain with their external owners.

B1 has no address, endpoint, or hostname field. After exact string/type and
C2A-safe-ref syntax validation, every B1 `R` field, including nested L34 and K8
refs, rejects four dot-separated ASCII decimal components of one to three
digits each with `privacy_forbidden_material`, before storage or
canonicalization. This IPv4-shaped raw-literal check includes leading zeros
and out-of-range components. Dotted opaque refs such as `host.profile.v1`,
`artifact.ref.1`, and `192.0.2.ref` remain valid. It adds no hostname heuristic.
C2A-safe syntax and this B1 check do not prove semantic privacy: source-ingest
owners must ensure opaque refs do not disguise private host, endpoint,
credential, bearer, or other private material. IPv6 and URI syntax remain
outside the current C2A safe-ref grammar where prohibited by that owner;
B1 does not widen it. Synthetic address-shaped rejection probes are test-only
negative inputs and never accepted B1 values.

The registry's RW0-B2-Capability pure-consumer row names its bounded
host-qualification snapshot seam. It does not enumerate the separate C1,
post-execution, or D1 consumers described below. C may
persist projections and prove evidence completeness under separately accepted guard and decision contracts; D may
consume values for offline worker/custody proof; E may consume them for
live-host proof. ES owns ES-route admission, reliable submit, lifecycle,
cancellation, runtime identity, and retained results. None of B1's assertions
performs those effects.

Direct tests pin ordered fields, independent canonical vectors, privacy and
immutability, budgets, relation matrices, and source boundaries. Existing C2A,
Section 41, architecture, and runtime non-authority tests must remain green.
Stop if implementation needs new public/durable/I/O/worker/Bridge/ES/provider
surface, alters an existing owner identity, or widens the frozen budget.

<!-- RW0_C1_CURRENT_STATUS_BEGIN -->
**RW0-C1 consumer status.**

RW0-D1 pre-execution and handback are bounded current runtime consumers of
`RW0PhaseEntryBasisV1`. Pre-execution alone constructs the basis for the
existing guarded C1 phase command. Handback directly imports only that B1
class to validate and retain the exact already constructed, C1-established
phase evidence; forming the handback constructs no basis and performs no C1
write. Neither D1 consumer calls `_validate_host_qualification_with_snapshots`,
authenticates source, grants executable permission, persists B1 state, or
decides semantic acceptance. C1 remains the sole durable phase establishment
and verification owner. The Capability pure cross-module consumer remains the
sole owner of its host-validation snapshot seam.

RW0-C1 now privately reconstructs B1 phase and supplied-evidence values and
invokes the existing B1 owner relations without altering this module. Phase
establishment binds the exact B1 basis relation plus fourteen operands; ranks
1-4 and 6 use the exact owner temporal contracts, and committed verification
reuses persisted semantic time rather than the current clock. A C1 record is
durable evidence only, never B1 source authentication, currentness at a later
C2 decision, permission, completeness, or execution authority.

The post-execution evidence-value layer is a bounded private, pure, no-I/O
consumer of B1 values and relations. It does not alter this document's machine
registry or become a second consumer of
`_validate_host_qualification_with_snapshots`. The complete post-execution
pure-owner tranche has no production caller; performs no runtime or I/O; makes
and writes no durable post-execution decision; adds no migration or SQLite
widening; creates no public export; and acquires no external authority or
custody. It implements no C2B progression, terminal outcome, RW0-D/E, or
Execution Substrate work.
<!-- RW0_C1_CURRENT_STATUS_END -->

## Bootstrap guard legacy compatibility edge

Classification: `BOUNDED COMPATIBILITY EDGE`; explicit target semantic supersession.
The exact v1 names `latch_postimage_ref` and `latch_postimage_digest` remain legacy
representation names. Their replacement-target binding is the immutable
bootstrap-acceptance fact identity/digest under
`.docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md`. They imply no mutable
preimage, available/consumed state, transition, revision, or separate classifier.
Current B1 validates pair presence/absence and supplied-value coherence only.
It proves no lineage scope, standing-policy admission, uniqueness, commitment,
atomic family membership, or recovery truth. No new target implementation may
consume the pair as durable guard proof until a separately accepted safe-value
compatibility/versioning decision. Source, schema ID, field order, nullability,
canonical bytes, digest domain, and budgets are unchanged. Rename/removal, new
field grammar, or proof responsibility requires a separate private safe-value
versioning tranche.

The accepted-target `.docs/rw0-c2-private-value-versioning.md` fixes the
guarded decision boundary: its future writer must not read or consume either
`latch_postimage_ref` or `latch_postimage_digest`. This pair proves supplied
representation and pair coherence only; it is not admission, acceptance,
uniqueness, family membership, continuity, replay, or recovery proof. Current
names, order, nullability, bytes, domains, and budgets remain exactly as they
are. A later terminal consumer requires its own separately accepted safe-value
compatibility/versioning contract; this tranche defines no B1 successor value.
