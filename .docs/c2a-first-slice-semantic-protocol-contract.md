# C2A First-Slice Semantic Protocol Contract

Status: accepted semantic contract with current C2A1 pure-value layer

Current implementation: C2A1 pure internal values and six pure coherence validators only

Source authorization: bounded C2A1 internal no-I/O module only

Schema/migration authorization: none in C2A

External process authorization: none in C2A

Git-effect authorization: none in C2A

This record is the authoritative field-level and semantic protocol contract for
the first software-development slice. It composes with, and does not replace,
the C1 composition authority in
`.docs/autonomous-software-development-operating-model.md`, the authority roles
in `.docs/authority-boundaries.md`, the progression semantics in
`.docs/software-development-progression-boundary.md`, the process and adapter
boundary in `.docs/worker-execution-boundary.md`, or the current durable-state
truth in `.docs/durable-state-model.md`.

## C2A-PROTO-001 — Status, Classification, Layering, And Non-Implementation

Classification: PROCESS-ONLY GOVERNANCE

Required before: any source

C2A freezes the authoritative semantic contract. C2A1 implements one
internal pure no-I/O semantic-value source module and the six named pure
coherence validators under the owner-local contract in
`.docs/c2a1-pure-semantic-values.md`. The seven schema identifiers in this
record are semantic schema identifiers. They are not SQLite schemas, network
protocols, process-framing protocols, service APIs, MCP tools, ES public APIs,
or executable authorization.

The current implementation remains bounded SQLite transition and coding
`global_stop` mutation through the guarded `WriterSession` authority boundary,
including receipt verification, writer fencing, idempotency, compare-and-swap,
exact replay, commit uncertainty, and explicit retry. `FiniteBacklog`,
standing-lease identity, disabled-stage behavior, and coding `global_stop`
remain unchanged compatibility or current contracts.

C2B3D now privately consumes the unchanged C2A authoring, effect, delivery,
and redelivery value/relation contracts while establishing and verifying one
durable author-effect family. This is a C2B implementation fact: it changes no
C2A schema, identity, digest, vector, relation, package export, or authority.

When the C2A contract was originally frozen, the current physical application
generation was 1 and the terminal migration was `0001_initial`. That is the
historical C2A freeze baseline, not the current physical repository state. The
current physical application generation is 2 and the current terminal migration
is `0002_development_program_and_effect_state`. Migration `0001_initial` remains
the preserved historical schema-v1 migration; migration 0002 is implemented by
C2B2 Slice 1.

C2A did not create or own migration 0002. C2A semantic fields, values,
identities, relations, and pure-value source do not themselves create durable
C2A tables or durable C2A runtime rows. The generation-2 physical schema is a
C2B2 Slice-1 implementation fact. C2A/C2A1 semantic authority remains distinct
from C2B2 physical-schema authority.

C2A1 implements only the nine immutable internal values, exact mapping and
identity mechanics, two pure factories, and six pure coherence validators. It
implements no durable state, schema, migration, packaging, dependency, package
export, entry point, worker, supervisor, process launch, filesystem capsule
effect, SQLite state, model/provider or Codex invocation, validation/review
executor, Git effect, ES adapter, Bridge integration, service, API, IPC,
scheduler, queue, or autonomous loop. It authorizes no external effect.

The accepted target keeps initial worker source and release ownership in the
Coordinator repository while worker execution occurs in a separate OS process.
This ownership and process statement is not current implementation.

The documentation authority hierarchy is:

1. `.docs/autonomous-software-development-operating-model.md` owns C1
   composition.
2. This record owns first-slice field-level and semantic protocol detail.
3. `.docs/c2a1-pure-semantic-values.md` owns the current internal Python value,
   API, mapping, immutability, error/privacy, pure-relation, and no-I/O layer.
4. `.docs/authority-boundaries.md` owns authority source, durable writer, fact
   source, custody, and projection.
5. `.docs/software-development-progression-boundary.md` owns attempt, effect,
   observation, review, decision, repair, replan, and publication semantics.
6. `.docs/worker-execution-boundary.md` owns worker/process/adapter boundaries
   and direct-local/ES conformance.
7. `.docs/durable-state-model.md` owns current durable-state truth and the
   target no-schema boundary.
8. `.docs/architecture.md`, `AGENTS.md`, and `README.md` remain summaries and
   navigation, not duplicate field-level authorities.

## C2A-PROTO-002 — Identity Non-Collapse And One-Writer, Source, Recorder, And Custody Roles

Classification: ACCEPTED STRATEGIC TARGET

Required before: any source

`program_ref` and `program_version_ref` are mandatory in every first-slice
semantic record that binds productive work. The following values are distinct
nominal identities even when one record correlates them:

### Nominal identity inventory

| Order | Identity | Meaning |
| ---: | --- | --- |
| 1 | `program_ref` | governed software-development program |
| 2 | `program_version_ref` | Coordinator concurrency coordinate for the program |
| 3 | `accepted_intent_revision_ref` | immutable accepted-intent revision |
| 4 | `work_item_ref` | governed work item |
| 5 | `work_item_revision_ref` | immutable work-item revision |
| 6 | `semantic_attempt_ref` | Coordinator-created productive attempt |
| 7 | `effect_intent_ref` | durable intended external effect |
| 8 | `delivery_attempt_ref` | one transport delivery of an effect |
| 9 | `source_invocation_ref` | source-authored invocation or run correlation |
| 10 | `observation_ref` | source observation identity |
| 11 | `candidate_ref` | candidate-byte lineage identity |
| 12 | `capsule_manifest_ref` | sealed manifest identity |
| 13 | `portable_capsule_digest` | portable content digest of the sealed capsule |
| 14 | `validation_observation_ref` | validation fact identity |
| 15 | `independent_review_ref` | independent review observation or proposal identity |
| 16 | `model_proposal_ref` | non-authoritative model proposal identity |
| 17 | `coordinator_decision_ref` | Coordinator semantic-decision identity |
| 18 | `git_effect_intent_ref` | separately authorized local Git effect identity |

The mandatory non-equivalences are:

- program version != accepted-intent revision;
- accepted-intent revision != work-item revision;
- work-item revision != base Git OID;
- semantic attempt != effect intent;
- effect intent != delivery attempt;
- delivery attempt != source invocation;
- observation != candidate;
- candidate != capsule manifest;
- capsule manifest != portable digest;
- validation observation != independent review;
- independent review != model proposal;
- model proposal != Coordinator decision;
- Coordinator acceptance != Git effect intent;
- Git effect intent != commit OID; and
- commit OID != publication state.

`TransitionCommand.command_ref`, `TransitionEvent.event_ref`, transition
idempotency keys, `FiniteBacklog.backlog_id`, current `attempt_count`, current
`repair_count`, and a standing-lease digest must not be reused as any identity
above.

One-writer, source, recorder, and custody roles remain separate:

### One-writer, source, recorder, and custody matrix

| Fact or material | Semantic source or authority | Durable recorder | Physical custodian or safe holder |
| --- | --- | --- | --- |
| Standing grant, expiry, or revocation | external standing-policy authority | external authority; Coordinator may record only a verified safe binding | external authority |
| Program versions, semantic attempts, effect intents, fences, cancellation intents, and semantic decisions | Coordinator under a verified parent grant | guarded Coordinator writer boundary | Coordinator durable state may retain only safe material |
| Delivery and reconciliation decision | Coordinator | guarded Coordinator writer boundary | Coordinator |
| Direct-local invocation fact | direct-local supervisor | future source-attributed Coordinator observation only | supervisor process evidence |
| ES admission, lifecycle, cancellation, and retained result | Execution Substrate | ES | ES; Coordinator may retain safe references |
| Candidate bytes | worker invocation | not Coordinator program truth | mutable worker workspace until seal |
| Canonical capsule manifest, blobs, and portable digest | capsule builder | private immutable capsule store | private worker-side capsule store |
| Validation result | validator or repository test executor | source observation; future Coordinator binding only | validator evidence system |
| Independent review | independent reviewer | source observation/proposal; future Coordinator binding only | reviewer evidence system |
| Model proposal | model invocation | non-authoritative proposal binding only | model/provider under its own contract |
| Git object and local ref | Git effect handler and Git | Git | Git object database and refs |
| Public report | no semantic authority | no authoritative fact writer | projection only |

Persistence of a source observation does not transfer authorship. The worker,
adapter, supervisor, reviewer, model adapter, capsule component, Git component,
and ES adapter receive no `WriterSession`, writer proof, Coordinator database
path, or unrestricted Coordinator credential.

## C2A-PROTO-003 — Closed Semantic Schemas, Canonical Encoding, And Digest Domains

Classification: FUTURE IMPLEMENTATION DETAIL

Required before: any source

### Semantic schema and digest-domain inventory

| Order | Semantic schema ID | Model | Unique digest domain |
| ---: | --- | --- | --- |
| 1 | `governed-execution.nwp-work-spec.v1` | `WorkSpecV1` | `governed-execution.nwp-work-spec.v1.identity` |
| 2 | `governed-execution.nwp-attempt-fence.v1` | `AttemptFenceV1` | `governed-execution.nwp-attempt-fence.v1.identity` |
| 3 | `governed-execution.nwp-effect-fence.v1` | `EffectFenceV1` | `governed-execution.nwp-effect-fence.v1.identity` |
| 4 | `governed-execution.nwp-worker-command.v1` | `WorkerCommandV1` | `governed-execution.nwp-worker-command.v1.identity` |
| 5 | `governed-execution.nwp-delivery-envelope.v1` | `DeliveryEnvelopeV1` | `governed-execution.nwp-delivery-envelope.v1.identity` |
| 6 | `governed-execution.nwp-worker-observation.v1` | `WorkerObservationV1` | `governed-execution.nwp-worker-observation.v1.identity` |
| 7 | `governed-execution.nwp-candidate-capsule-manifest.v1` | `CandidateCapsuleManifestV1` | `governed-execution.nwp-candidate-capsule-manifest.v1.identity` |

The auxiliary authorized-path-set digest domain is
`governed-execution.nwp-authorized-path-scope.v1.identity`. It hashes the
canonical sorted path array and is not another top-level schema.

### Canonical encoding and validation rules

Every v1 full record is one strict UTF-8 JSON object with its exact allowed key
set. Unknown, missing, misspelled, or duplicate keys fail before digest
comparison. There is no extension or metadata bag. JSON arrays are required
where tables specify arrays; tuples are not an external form. Integers are
exact JSON integers and booleans fail integer validation. Integers are
non-negative unless a field table gives a narrower or signed range;
`process_exit_code` is the sole signed v1 integer and is bounded from -255
through 255. Floats, NaN, and infinity are prohibited.

Canonical identity bytes are produced with lexicographically sorted object
keys, no insignificant whitespace, separators `,` and `:`, UTF-8 without a
byte-order mark, and JSON strings preserved by exact Unicode code point. No
Unicode normalization is performed. First-slice repository paths are ASCII
POSIX relative paths and therefore reject case-fold or Unicode-normalization
collisions.

Safe references match `[A-Za-z0-9][A-Za-z0-9.-]*`, are 1 through 96 characters,
and case-insensitively reject the exact prefixes `connector-`, `tunnel-`,
`workspace-`, `org-`, `organization-`, and `user-`. SHA-256 values are exactly
64 lowercase hexadecimal characters. The first-slice Git object format is the
single value `sha1`; a base OID is exactly 40 lowercase hexadecimal characters.
Every `base_git_oid` is first required to be an exact built-in JSON string;
string subclasses, integers, booleans, arrays, mappings, and objects that only
produce a matching value through string conversion are invalid before the
lowercase-hex check. No relation validator may coerce a supplied value with
`str(...)`.
Whole-second timestamps are exactly 20 ASCII characters in
`YYYY-MM-DDTHH:MM:SSZ` form with a literal uppercase `Z`. Fractional seconds,
numeric offsets, lowercase `z`, and leading or trailing whitespace are
forbidden. The date and clock must be valid under Python `datetime`'s
proleptic Gregorian calendar, and parsing then formatting must reproduce the
exact original string. A timestamp remains source evidence and has no ordering
or acceptance authority.

A safe repository-relative path is 1 through 160 characters, contains no C0 or
DEL control character, begins with neither `/`, `\\`, nor `~`, contains no
backslash, colon, `//`, empty segment, `.` segment, or `..` segment, and is not
URI-like. C2A additionally admits only the exact three ASCII paths in
C2A-PROTO-008. Path arrays and other set-like arrays reject duplicates and are
sorted by exact code point. `allowed_effect_classes` is non-empty. Safe evidence
reference arrays contain 0 through 32 unique sorted safe refs.

Private objective, requirement, and exclusion strings are each 1 through 512
Unicode code points with no C0 or DEL control character. Requirements and
exclusions each contain 1 through 32 unique strings and preserve their declared
order. No string is trimmed, case-folded, or Unicode-normalized.

For schema digest domain `D` and canonical identity bytes `B`, the record
digest is exactly `SHA256(UTF8(D) || 0x00 || B)`. A self-digest field is required
in the full record but excluded from `B`. A full record is valid only when the
stored digest equals the recomputed domain-separated digest.

Omission and an explicitly supplied related-record value are distinct in every
test-only relation. Core relation validators represent omission only with one
private missing sentinel, receive actual records, and never select golden
fixtures. Only an explicitly named test convenience wrapper may replace that
sentinel with a canonical fixture. It must not replace explicit `null`, an
empty or malformed mapping, an empty array or string, zero, or false. For these
closed test records, every value must satisfy `type(value) is dict` before any
mapping access; dict subclasses and mapping-like non-dicts reject without an
uncontrolled exception.

The `cancellation_target` argument follows that rule through effect-fence,
delivery, both redelivery sides, observation, observation-relation,
unknown-outcome, and cancellation validation. A current `cancel_effect`
requires an actual exact target record. A current non-cancellation effect
requires the argument to remain omitted and its three protocol target fields
to remain JSON `null`; explicit `null` is not omission and any explicitly
supplied target is rejected rather than ignored. Manifest, capsule, and other
related-record paths likewise validate explicitly supplied values exactly as
supplied. Canonical omitted convenience remains test-only and confers no
authority.

`WorkerCommandV1` uses an acyclic post-binding rule. Its identity contains
`effect_fence_ref` but excludes both `effect_fence_digest` and
`command_digest`. The command digest is computed first; `EffectFenceV1` then
binds that command digest; the resulting effect-fence digest is placed in the
complete command. Exact replay requires the same command reference, command
digest, and excluded effect-fence digest. Any mismatch is conflict.

### CeilingsV1 object

The `aggregate_ceilings` and `effect_ceilings` objects have exactly these
required non-negative integer fields in normative order:

| Order | Field | Meaning |
| ---: | --- | --- |
| 1 | `max_active_invocations` | concurrent source-invocation ceiling |
| 2 | `max_candidate_bytes` | aggregate after-blob byte ceiling |
| 3 | `max_changed_files` | changed-path ceiling |
| 4 | `max_cost_microusd` | model/provider cost ceiling in millionths of USD |
| 5 | `max_cpu_seconds` | CPU-time ceiling |
| 6 | `max_deliveries` | delivery-attempt ceiling for one effect |
| 7 | `max_deployments` | deployment-effect ceiling |
| 8 | `max_local_commits` | local-commit effect ceiling |
| 9 | `max_memory_bytes` | memory ceiling |
| 10 | `max_merges` | merge-effect ceiling |
| 11 | `max_model_input_tokens` | model-input-token ceiling |
| 12 | `max_model_output_tokens` | model-output-token ceiling |
| 13 | `max_pull_requests` | pull-request effect ceiling |
| 14 | `max_pushes` | push-effect ceiling |
| 15 | `max_wall_seconds` | wall-time ceiling |

### WorkSpecV1 fields

| Order | Field | Required | Type or finite value | Role | In identity |
| ---: | --- | --- | --- | --- | --- |
| 1 | `schema_id` | yes | `governed-execution.nwp-work-spec.v1` | identity | yes |
| 2 | `work_spec_ref` | yes | safe ref | identity | yes |
| 3 | `program_ref` | yes | safe ref | correlation | yes |
| 4 | `program_version_ref` | yes | safe ref | correlation | yes |
| 5 | `accepted_intent_revision_ref` | yes | safe ref | correlation | yes |
| 6 | `work_item_ref` | yes | safe ref | correlation | yes |
| 7 | `work_item_revision_ref` | yes | safe ref | correlation | yes |
| 8 | `repository_ref` | yes | safe ref | effect ceiling | yes |
| 9 | `base_git_object_format` | yes | `sha1` | evidence | yes |
| 10 | `base_git_oid` | yes | 40 lowercase hex | evidence | yes |
| 11 | `authorized_paths` | yes | sorted unique safe-path array | effect ceiling | yes |
| 12 | `objective` | yes | bounded private string | evidence | yes |
| 13 | `requirements` | yes | ordered non-empty private-string array | evidence | yes |
| 14 | `exclusions` | yes | ordered non-empty private-string array | effect ceiling | yes |
| 15 | `validation_requirement_ref` | yes | safe ref | safe reference | yes |
| 16 | `review_requirement_ref` | yes | safe ref | safe reference | yes |
| 17 | `privacy_classification` | yes | `private_work_spec` | privacy classification | yes |
| 18 | `work_spec_digest` | yes | SHA-256 | evidence | no |

There are no optional WorkSpecV1 fields.

### AttemptFenceV1 fields

| Order | Field | Required | Type or finite value | Role | In identity |
| ---: | --- | --- | --- | --- | --- |
| 1 | `schema_id` | yes | `governed-execution.nwp-attempt-fence.v1` | identity | yes |
| 2 | `attempt_fence_ref` | yes | safe ref | identity | yes |
| 3 | `parent_standing_grant_ref` | yes | safe ref | authority-sensitive binding | yes |
| 4 | `parent_standing_grant_digest` | yes | SHA-256 | authority-sensitive binding | yes |
| 5 | `attempt_authorization_ref` | yes | safe ref | authority-sensitive binding | yes |
| 6 | `attempt_authorization_digest` | yes | SHA-256 | authority-sensitive binding | yes |
| 7 | `program_ref` | yes | safe ref | correlation | yes |
| 8 | `program_version_ref` | yes | safe ref | correlation | yes |
| 9 | `accepted_intent_revision_ref` | yes | safe ref | correlation | yes |
| 10 | `work_item_ref` | yes | safe ref | correlation | yes |
| 11 | `work_item_revision_ref` | yes | safe ref | correlation | yes |
| 12 | `semantic_attempt_ref` | yes | safe ref | identity | yes |
| 13 | `repository_ref` | yes | safe ref | effect ceiling | yes |
| 14 | `base_git_object_format` | yes | `sha1` | evidence | yes |
| 15 | `base_git_oid` | yes | 40 lowercase hex | evidence | yes |
| 16 | `path_ceiling` | yes | sorted unique safe-path array | effect ceiling | yes |
| 17 | `allowed_effect_classes` | yes | sorted subset of `author_candidate`, `validate_candidate`, `review_candidate`, `cancel_effect`, `local_git_commit` | effect ceiling | yes |
| 18 | `aggregate_ceilings` | yes | exact `CeilingsV1` object | effect ceiling | yes |
| 19 | `expires_at` | yes | whole-second UTC | authority-sensitive binding | yes |
| 20 | `global_stop_ref` | yes | safe ref | authority-sensitive binding | yes |
| 21 | `global_stop_version` | yes | non-negative integer | authority-sensitive binding | yes |
| 22 | `attempt_fence_digest` | yes | SHA-256 | evidence | no |

There are no optional AttemptFenceV1 fields.

### EffectFenceV1 fields

| Order | Field | Required | Type or finite value | Role | In identity |
| ---: | --- | --- | --- | --- | --- |
| 1 | `schema_id` | yes | `governed-execution.nwp-effect-fence.v1` | identity | yes |
| 2 | `effect_fence_ref` | yes | safe ref | identity | yes |
| 3 | `parent_standing_grant_ref` | yes | safe ref | authority-sensitive binding | yes |
| 4 | `parent_standing_grant_digest` | yes | SHA-256 | authority-sensitive binding | yes |
| 5 | `effect_authorization_ref` | yes | safe ref | authority-sensitive binding | yes |
| 6 | `effect_authorization_digest` | yes | SHA-256 | authority-sensitive binding | yes |
| 7 | `attempt_fence_ref` | yes | safe ref | authority-sensitive binding | yes |
| 8 | `attempt_fence_digest` | yes | SHA-256 | authority-sensitive binding | yes |
| 9 | `program_ref` | yes | safe ref | correlation | yes |
| 10 | `program_version_ref` | yes | safe ref | correlation | yes |
| 11 | `accepted_intent_revision_ref` | yes | safe ref | correlation | yes |
| 12 | `work_item_ref` | yes | safe ref | correlation | yes |
| 13 | `work_item_revision_ref` | yes | safe ref | correlation | yes |
| 14 | `semantic_attempt_ref` | yes | safe ref | correlation | yes |
| 15 | `effect_intent_ref` | yes | safe ref | identity | yes |
| 16 | `effect_class` | yes | `author_candidate`, `validate_candidate`, `review_candidate`, `cancel_effect`, or `local_git_commit` | effect ceiling | yes |
| 17 | `command_ref` | yes | safe ref | correlation | yes |
| 18 | `command_digest` | yes | SHA-256 | authority-sensitive binding | yes |
| 19 | `candidate_ref` | yes | safe ref | correlation | yes |
| 20 | `repository_ref` | yes | safe ref | effect ceiling | yes |
| 21 | `base_git_object_format` | yes | `sha1` | evidence | yes |
| 22 | `base_git_oid` | yes | 40 lowercase hex | evidence | yes |
| 23 | `path_ceiling` | yes | sorted unique safe-path array | effect ceiling | yes |
| 24 | `effect_ceilings` | yes | exact `CeilingsV1` object | effect ceiling | yes |
| 25 | `expires_at` | yes | whole-second UTC | authority-sensitive binding | yes |
| 26 | `global_stop_ref` | yes | safe ref | authority-sensitive binding | yes |
| 27 | `global_stop_version` | yes | non-negative integer | authority-sensitive binding | yes |
| 28 | `portable_capsule_digest` | yes | SHA-256 or JSON `null` | authority-sensitive binding | yes |
| 29 | `cancellation_target_effect_intent_ref` | yes | safe ref or JSON `null` | authority-sensitive binding | yes |
| 30 | `cancellation_target_effect_fence_ref` | yes | safe ref or JSON `null` | authority-sensitive binding | yes |
| 31 | `cancellation_target_effect_fence_digest` | yes | SHA-256 or JSON `null` | authority-sensitive binding | yes |
| 32 | `effect_fence_digest` | yes | SHA-256 | evidence | no |

There are exactly 32 required and no optional EffectFenceV1 fields. Its
identity payload has exactly 31 fields and excludes only
`effect_fence_digest`. The three cancellation-target fields are required and
nullable; they are all JSON `null` for `author_candidate`,
`validate_candidate`, `review_candidate`, and `local_git_commit`, and are all
non-null for `cancel_effect`. `portable_capsule_digest` is null only for an
effect such as candidate authoring that precedes sealing; validation, review,
and Git effects require the exact sealed digest. Cancellation capsule binding
is determined by the immutable target rules in C2A-PROTO-005.

### WorkerCommandV1 fields

| Order | Field | Required | Type or finite value | Role | In identity |
| ---: | --- | --- | --- | --- | --- |
| 1 | `schema_id` | yes | `governed-execution.nwp-worker-command.v1` | identity | yes |
| 2 | `command_ref` | yes | safe ref | identity | yes |
| 3 | `program_ref` | yes | safe ref | correlation | yes |
| 4 | `program_version_ref` | yes | safe ref | correlation | yes |
| 5 | `accepted_intent_revision_ref` | yes | safe ref | correlation | yes |
| 6 | `work_item_ref` | yes | safe ref | correlation | yes |
| 7 | `work_item_revision_ref` | yes | safe ref | correlation | yes |
| 8 | `semantic_attempt_ref` | yes | safe ref | correlation | yes |
| 9 | `effect_intent_ref` | yes | safe ref | correlation | yes |
| 10 | `effect_class` | yes | `author_candidate` | effect ceiling | yes |
| 11 | `candidate_ref` | yes | safe ref | identity | yes |
| 12 | `repository_ref` | yes | safe ref | effect ceiling | yes |
| 13 | `base_git_object_format` | yes | `sha1` | evidence | yes |
| 14 | `base_git_oid` | yes | 40 lowercase hex | evidence | yes |
| 15 | `path_ceiling` | yes | sorted unique safe-path array | effect ceiling | yes |
| 16 | `work_spec_ref` | yes | safe ref | safe reference | yes |
| 17 | `work_spec_digest` | yes | SHA-256 | evidence | yes |
| 18 | `standing_grant_ref` | yes | safe ref | authority-sensitive binding | yes |
| 19 | `standing_grant_digest` | yes | SHA-256 | authority-sensitive binding | yes |
| 20 | `attempt_authorization_ref` | yes | safe ref | authority-sensitive binding | yes |
| 21 | `attempt_authorization_digest` | yes | SHA-256 | authority-sensitive binding | yes |
| 22 | `effect_authorization_ref` | yes | safe ref | authority-sensitive binding | yes |
| 23 | `effect_authorization_digest` | yes | SHA-256 | authority-sensitive binding | yes |
| 24 | `attempt_fence_ref` | yes | safe ref | authority-sensitive binding | yes |
| 25 | `attempt_fence_digest` | yes | SHA-256 | authority-sensitive binding | yes |
| 26 | `effect_fence_ref` | yes | safe ref | authority-sensitive binding | yes |
| 27 | `effect_fence_digest` | yes | SHA-256 | authority-sensitive binding | no |
| 28 | `global_stop_ref` | yes | safe ref | authority-sensitive binding | yes |
| 29 | `global_stop_version` | yes | non-negative integer | authority-sensitive binding | yes |
| 30 | `validation_requirement_ref` | yes | safe ref | safe reference | yes |
| 31 | `validation_requirement_digest` | yes | SHA-256 | evidence | yes |
| 32 | `review_requirement_ref` | yes | safe ref | safe reference | yes |
| 33 | `review_requirement_digest` | yes | SHA-256 | evidence | yes |
| 34 | `capsule_schema_id` | yes | `governed-execution.nwp-candidate-capsule-manifest.v1` | correlation | yes |
| 35 | `capsule_profile_ref` | yes | safe ref | safe reference | yes |
| 36 | `effect_ceilings` | yes | exact `CeilingsV1` object | effect ceiling | yes |
| 37 | `privacy_classification` | yes | `private_source_change` | privacy classification | yes |
| 38 | `redaction_profile_ref` | yes | safe ref | privacy classification | yes |
| 39 | `command_digest` | yes | SHA-256 | evidence | no |

There are no optional WorkerCommandV1 fields. `effect_fence_digest` is the
required postcomputed coherence binding described above and is excluded only
from command identity to prevent a recursive digest graph.

### DeliveryEnvelopeV1 fields

| Order | Field | Required | Type or finite value | Role | In identity |
| ---: | --- | --- | --- | --- | --- |
| 1 | `schema_id` | yes | `governed-execution.nwp-delivery-envelope.v1` | identity | yes |
| 2 | `delivery_attempt_ref` | yes | safe ref | identity | yes |
| 3 | `program_ref` | yes | safe ref | correlation | yes |
| 4 | `program_version_ref` | yes | safe ref | correlation | yes |
| 5 | `command_ref` | yes | safe ref | originating author-command lineage | yes |
| 6 | `command_digest` | yes | SHA-256 | originating author-command lineage | yes |
| 7 | `semantic_attempt_ref` | yes | safe ref | originating semantic attempt | yes |
| 8 | `effect_intent_ref` | yes | safe ref | current effect intent | yes |
| 9 | `attempt_fence_ref` | yes | safe ref | originating attempt-fence binding | yes |
| 10 | `attempt_fence_digest` | yes | SHA-256 | originating attempt-fence binding | yes |
| 11 | `effect_fence_ref` | yes | safe ref | current effect-fence binding | yes |
| 12 | `effect_fence_digest` | yes | SHA-256 | current effect-fence binding | yes |
| 13 | `adapter_kind` | yes | `direct_local_bootstrap` or `execution_substrate` | correlation | yes |
| 14 | `adapter_safe_correlation_ref` | yes | safe ref | correlation | yes |
| 15 | `delivery_envelope_digest` | yes | SHA-256 | evidence | no |

There are exactly fifteen required and no optional DeliveryEnvelopeV1 fields.
Its identity payload has exactly fourteen fields and excludes only
`delivery_envelope_digest`.

### WorkerObservationV1 fields

| Order | Field | Required | Type or finite value | Role | In identity |
| ---: | --- | --- | --- | --- | --- |
| 1 | `schema_id` | yes | `governed-execution.nwp-worker-observation.v1` | identity | yes |
| 2 | `observation_ref` | yes | safe ref | identity | yes |
| 3 | `source_kind` | yes | source-kind matrix value | evidence | yes |
| 4 | `source_ref` | yes | safe ref | safe reference | yes |
| 5 | `source_invocation_ref` | yes | safe ref | correlation | yes |
| 6 | `delivery_attempt_ref` | yes | safe ref | correlation | yes |
| 7 | `program_ref` | yes | safe ref | correlation | yes |
| 8 | `program_version_ref` | yes | safe ref | correlation | yes |
| 9 | `accepted_intent_revision_ref` | yes | safe ref | correlation | yes |
| 10 | `work_item_ref` | yes | safe ref | correlation | yes |
| 11 | `work_item_revision_ref` | yes | safe ref | correlation | yes |
| 12 | `semantic_attempt_ref` | yes | safe ref | correlation | yes |
| 13 | `effect_intent_ref` | yes | safe ref | correlation | yes |
| 14 | `command_ref` | yes | safe ref | correlation | yes |
| 15 | `command_digest` | yes | SHA-256 | evidence | yes |
| 16 | `attempt_fence_ref` | yes | safe ref | authority-sensitive binding | yes |
| 17 | `attempt_fence_digest` | yes | SHA-256 | authority-sensitive binding | yes |
| 18 | `effect_fence_ref` | yes | safe ref | authority-sensitive binding | yes |
| 19 | `effect_fence_digest` | yes | SHA-256 | authority-sensitive binding | yes |
| 20 | `observation_kind` | yes | source/observation matrix value | evidence | yes |
| 21 | `outcome` | yes | source/observation matrix value | evidence | yes |
| 22 | `reason_code` | yes | bounded finite reason code | evidence | yes |
| 23 | `evidence_refs` | yes | sorted unique safe-ref array | evidence | yes |
| 24 | `observed_at` | yes | whole-second UTC source timestamp | evidence | yes |
| 25 | `candidate_ref` | conditional | safe ref | correlation | yes when present |
| 26 | `capsule_manifest_ref` | conditional | safe ref | safe reference | yes when present |
| 27 | `portable_capsule_digest` | conditional | SHA-256 | evidence | yes when present |
| 28 | `process_exit_code` | conditional | integer from -255 through 255, boolean rejected | evidence | yes when present |
| 29 | `observation_digest` | yes | SHA-256 | evidence | no |

The exact optional-field inventory is `candidate_ref`, `capsule_manifest_ref`,
`portable_capsule_digest`, and `process_exit_code`; the source-kind matrix in
C2A-PROTO-006 makes each required or prohibited for every observation kind.

### CandidateCapsuleManifestV1 fields

| Order | Field | Required | Type or finite value | Role | In identity |
| ---: | --- | --- | --- | --- | --- |
| 1 | `schema_id` | yes | `governed-execution.nwp-candidate-capsule-manifest.v1` | identity | yes |
| 2 | `canonicalization_profile` | yes | `canonical-json.sorted-keys.utf8.v1` | evidence | yes |
| 3 | `digest_domain` | yes | manifest digest domain | evidence | yes |
| 4 | `candidate_ref` | yes | safe ref | identity | yes |
| 5 | `capsule_manifest_ref` | yes | safe ref | identity | yes |
| 6 | `program_ref` | yes | safe ref | correlation | yes |
| 7 | `program_version_ref` | yes | safe ref | correlation | yes |
| 8 | `accepted_intent_revision_ref` | yes | safe ref | correlation | yes |
| 9 | `work_item_ref` | yes | safe ref | correlation | yes |
| 10 | `work_item_revision_ref` | yes | safe ref | correlation | yes |
| 11 | `semantic_attempt_ref` | yes | safe ref | correlation | yes |
| 12 | `effect_intent_ref` | yes | safe ref | correlation | yes |
| 13 | `command_ref` | yes | safe ref | correlation | yes |
| 14 | `command_digest` | yes | SHA-256 | evidence | yes |
| 15 | `attempt_fence_ref` | yes | safe ref | authority-sensitive binding | yes |
| 16 | `attempt_fence_digest` | yes | SHA-256 | authority-sensitive binding | yes |
| 17 | `effect_fence_ref` | yes | safe ref | authority-sensitive binding | yes |
| 18 | `effect_fence_digest` | yes | SHA-256 | authority-sensitive binding | yes |
| 19 | `repository_ref` | yes | safe ref | effect ceiling | yes |
| 20 | `base_git_object_format` | yes | `sha1` | evidence | yes |
| 21 | `base_git_oid` | yes | 40 lowercase hex | evidence | yes |
| 22 | `authorized_path_scope_digest` | yes | domain-separated SHA-256 | effect ceiling | yes |
| 23 | `entries` | yes | sorted non-empty `CapsuleEntryV1` array | evidence | yes |
| 24 | `portable_capsule_digest` | yes | SHA-256 | evidence | no |

There are no optional CandidateCapsuleManifestV1 fields.

### CapsuleEntryV1 object

Each entry has exactly these required fields and entries are sorted by `path`:

| Order | Field | Type or finite value |
| ---: | --- | --- |
| 1 | `path` | first-slice authorized safe relative path |
| 2 | `operation` | `replace_regular_file` |
| 3 | `mode` | `100644` or `100755` |
| 4 | `before_blob_sha256` | SHA-256 |
| 5 | `before_byte_length` | non-negative integer |
| 6 | `after_blob_sha256` | SHA-256 |
| 7 | `after_byte_length` | non-negative integer |

### Normative golden vectors

Each JSON block below is the exact canonical identity byte sequence, represented
as one ASCII/UTF-8 line without a trailing LF. The reported byte length excludes
Markdown fencing and excludes a trailing LF. Each SHA-256 is the
domain-separated record digest, not a raw hash of the JSON alone.

#### Golden vector — WorkSpecV1

- Schema ID: `governed-execution.nwp-work-spec.v1`
- Digest domain: `governed-execution.nwp-work-spec.v1.identity`
- Canonical byte length: `1158`
- Domain-separated SHA-256: `5ae0add98fb3b6a233b778fe165dfa7ef8d1f3c43e824dddbdb6827958360ade`
- Excluded full-record field: `work_spec_digest=5ae0add98fb3b6a233b778fe165dfa7ef8d1f3c43e824dddbdb6827958360ade`

```json
{"accepted_intent_revision_ref":"intent-revision.0001","authorized_paths":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","exclusions":["Do not push, create a pull request, merge, or deploy.","Do not modify Execution Substrate runtime source."],"objective":"Document the bounded direct-local bootstrap proof while preserving Execution Substrate migration gates.","privacy_classification":"private_work_spec","program_ref":"program.es-docs","program_version_ref":"program-version.0001","repository_ref":"repository.execution-substrate","requirements":["Modify only the three authorized repository-relative paths.","Preserve Execution Substrate reliable-submit ownership and current P0.","Produce no runtime, schema, or service change."],"review_requirement_ref":"review.es-docs.0001","schema_id":"governed-execution.nwp-work-spec.v1","validation_requirement_ref":"validation.es-docs.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001","work_spec_ref":"work-spec.es-docs.0001"}
```

#### Golden vector — AttemptFenceV1

- Schema ID: `governed-execution.nwp-attempt-fence.v1`
- Digest domain: `governed-execution.nwp-attempt-fence.v1.identity`
- Canonical byte length: `1525`
- Domain-separated SHA-256: `7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e`
- Excluded full-record field: `attempt_fence_digest=7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e`

```json
{"accepted_intent_revision_ref":"intent-revision.0001","aggregate_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":10000000,"max_cpu_seconds":3600,"max_deliveries":2,"max_deployments":0,"max_local_commits":1,"max_memory_bytes":4294967296,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":3600},"allowed_effect_classes":["author_candidate","cancel_effect","local_git_commit","review_candidate","validate_candidate"],"attempt_authorization_digest":"2222222222222222222222222222222222222222222222222222222222222222","attempt_authorization_ref":"attempt-authorization.0001","attempt_fence_ref":"attempt-fence.0001","base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","expires_at":"2030-01-01T00:00:00Z","global_stop_ref":"global-stop.current","global_stop_version":7,"parent_standing_grant_digest":"1111111111111111111111111111111111111111111111111111111111111111","parent_standing_grant_ref":"standing-grant.0001","path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"program_ref":"program.es-docs","program_version_ref":"program-version.0001","repository_ref":"repository.execution-substrate","schema_id":"governed-execution.nwp-attempt-fence.v1","semantic_attempt_ref":"semantic-attempt.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001"}
```

#### Golden vector — EffectFenceV1

- Schema ID: `governed-execution.nwp-effect-fence.v1`
- Digest domain: `governed-execution.nwp-effect-fence.v1.identity`
- Canonical byte length: `1928`
- Domain-separated SHA-256: `71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3`
- Excluded full-record field: `effect_fence_digest=71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3`

```json
{"accepted_intent_revision_ref":"intent-revision.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","cancellation_target_effect_fence_digest":null,"cancellation_target_effect_fence_ref":null,"cancellation_target_effect_intent_ref":null,"candidate_ref":"candidate.0001","command_digest":"6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927","command_ref":"worker-command.0001","effect_authorization_digest":"3333333333333333333333333333333333333333333333333333333333333333","effect_authorization_ref":"effect-authorization.0001","effect_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":10000000,"max_cpu_seconds":3600,"max_deliveries":2,"max_deployments":0,"max_local_commits":0,"max_memory_bytes":4294967296,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":3600},"effect_class":"author_candidate","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","expires_at":"2030-01-01T00:00:00Z","global_stop_ref":"global-stop.current","global_stop_version":7,"parent_standing_grant_digest":"1111111111111111111111111111111111111111111111111111111111111111","parent_standing_grant_ref":"standing-grant.0001","path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"portable_capsule_digest":null,"program_ref":"program.es-docs","program_version_ref":"program-version.0001","repository_ref":"repository.execution-substrate","schema_id":"governed-execution.nwp-effect-fence.v1","semantic_attempt_ref":"semantic-attempt.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001"}
```

#### Golden vector — WorkerCommandV1

- Schema ID: `governed-execution.nwp-worker-command.v1`
- Digest domain: `governed-execution.nwp-worker-command.v1.identity`
- Canonical byte length: `2444`
- Domain-separated SHA-256: `6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927`
- Excluded full-record fields: `effect_fence_digest=71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3`, `command_digest=6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927`

```json
{"accepted_intent_revision_ref":"intent-revision.0001","attempt_authorization_digest":"2222222222222222222222222222222222222222222222222222222222222222","attempt_authorization_ref":"attempt-authorization.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","candidate_ref":"candidate.0001","capsule_profile_ref":"capsule-profile.regular-replace-v1","capsule_schema_id":"governed-execution.nwp-candidate-capsule-manifest.v1","command_ref":"worker-command.0001","effect_authorization_digest":"3333333333333333333333333333333333333333333333333333333333333333","effect_authorization_ref":"effect-authorization.0001","effect_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":10000000,"max_cpu_seconds":3600,"max_deliveries":2,"max_deployments":0,"max_local_commits":0,"max_memory_bytes":4294967296,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":3600},"effect_class":"author_candidate","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","global_stop_ref":"global-stop.current","global_stop_version":7,"path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"privacy_classification":"private_source_change","program_ref":"program.es-docs","program_version_ref":"program-version.0001","redaction_profile_ref":"redaction.source-private-v1","repository_ref":"repository.execution-substrate","review_requirement_digest":"5555555555555555555555555555555555555555555555555555555555555555","review_requirement_ref":"review.es-docs.0001","schema_id":"governed-execution.nwp-worker-command.v1","semantic_attempt_ref":"semantic-attempt.0001","standing_grant_digest":"1111111111111111111111111111111111111111111111111111111111111111","standing_grant_ref":"standing-grant.0001","validation_requirement_digest":"4444444444444444444444444444444444444444444444444444444444444444","validation_requirement_ref":"validation.es-docs.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001","work_spec_digest":"5ae0add98fb3b6a233b778fe165dfa7ef8d1f3c43e824dddbdb6827958360ade","work_spec_ref":"work-spec.es-docs.0001"}
```

#### Golden vector — DeliveryEnvelopeV1

- Schema ID: `governed-execution.nwp-delivery-envelope.v1`
- Digest domain: `governed-execution.nwp-delivery-envelope.v1.identity`
- Canonical byte length: `755`
- Domain-separated SHA-256: `83e68b50759dc21746ef7b521edb8f7b61cf5446d819c8c7aa47bee048841f0e`
- Excluded full-record field: `delivery_envelope_digest=83e68b50759dc21746ef7b521edb8f7b61cf5446d819c8c7aa47bee048841f0e`

```json
{"adapter_kind":"direct_local_bootstrap","adapter_safe_correlation_ref":"adapter-correlation.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","command_digest":"6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927","command_ref":"worker-command.0001","delivery_attempt_ref":"delivery-attempt.0001","effect_fence_digest":"71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","program_ref":"program.es-docs","program_version_ref":"program-version.0001","schema_id":"governed-execution.nwp-delivery-envelope.v1","semantic_attempt_ref":"semantic-attempt.0001"}
```

#### Golden vector — WorkerObservationV1

- Schema ID: `governed-execution.nwp-worker-observation.v1`
- Digest domain: `governed-execution.nwp-worker-observation.v1.identity`
- Canonical byte length: `1324`
- Domain-separated SHA-256: `b605b2779fa5b46ebff2d23d7026c643debde509c015e840608b0991f1c52a6f`
- Excluded full-record field: `observation_digest=b605b2779fa5b46ebff2d23d7026c643debde509c015e840608b0991f1c52a6f`

```json
{"accepted_intent_revision_ref":"intent-revision.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","candidate_ref":"candidate.0001","capsule_manifest_ref":"capsule-manifest.0001","command_digest":"6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927","command_ref":"worker-command.0001","delivery_attempt_ref":"delivery-attempt.0001","effect_fence_digest":"71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","evidence_refs":["evidence.capsule-seal.0001"],"observation_kind":"capsule_sealed","observation_ref":"observation.capsule-sealed.0001","observed_at":"2026-08-08T18:00:00Z","outcome":"sealed","portable_capsule_digest":"b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c","program_ref":"program.es-docs","program_version_ref":"program-version.0001","reason_code":"reason.none","schema_id":"governed-execution.nwp-worker-observation.v1","semantic_attempt_ref":"semantic-attempt.0001","source_invocation_ref":"source-invocation.capsule-builder.0001","source_kind":"capsule_builder","source_ref":"capsule-builder.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001"}
```

#### Golden vector — CandidateCapsuleManifestV1

- Schema ID: `governed-execution.nwp-candidate-capsule-manifest.v1`
- Digest domain: `governed-execution.nwp-candidate-capsule-manifest.v1.identity`
- Canonical byte length: `2178`
- Domain-separated SHA-256: `b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c`
- Excluded full-record field: `portable_capsule_digest=b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c`

```json
{"accepted_intent_revision_ref":"intent-revision.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","authorized_path_scope_digest":"881d8190e95accffbce9d463a68910703595e5106ce81ba00a8433404b6c8116","base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","candidate_ref":"candidate.0001","canonicalization_profile":"canonical-json.sorted-keys.utf8.v1","capsule_manifest_ref":"capsule-manifest.0001","command_digest":"6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927","command_ref":"worker-command.0001","digest_domain":"governed-execution.nwp-candidate-capsule-manifest.v1.identity","effect_fence_digest":"71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","entries":[{"after_blob_sha256":"7c1525eca0dfcccb6dcda32fe7f7f58281aa82be220018b1f69f4b529503ea8a","after_byte_length":52,"before_blob_sha256":"1ac70a99e7e54c57641ba8c0cb1e49ae7d0e6e5a7b1acaa0443e5afc1782f73a","before_byte_length":53,"mode":"100644","operation":"replace_regular_file","path":".docs/system_overview/hybrid_integration_architecture_adr.md"},{"after_blob_sha256":"3b80b40624b6a3834873b32839e8e7e73644def7437389a5eaea12abe480f180","after_byte_length":45,"before_blob_sha256":"d0cc82b8b8733e1b4ee2aba05aad19d474ed16e746bcac709b083d5ce2d848d9","before_byte_length":46,"mode":"100644","operation":"replace_regular_file","path":"PLANS.md"},{"after_blob_sha256":"267a3924b2a2ce1260c9d2532bf75db970eda7c76c40042d192e6cdece8202c2","after_byte_length":53,"before_blob_sha256":"47fc7108400e128ad4deade38d14c9c410b3f4dd23d3e022b008ac279d96ef90","before_byte_length":54,"mode":"100644","operation":"replace_regular_file","path":"docs_contract_test.go"}],"program_ref":"program.es-docs","program_version_ref":"program-version.0001","repository_ref":"repository.execution-substrate","schema_id":"governed-execution.nwp-candidate-capsule-manifest.v1","semantic_attempt_ref":"semantic-attempt.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001"}
```

## C2A-PROTO-004 — Private Work Specification, Worker Command, And Delivery Envelope

Classification: FUTURE IMPLEMENTATION DETAIL

Required before: any source

`WorkSpecV1` is the private, closed-world desired-work attachment. Its stable
reference and digest bind the accepted-intent revision, work-item revision,
exact bounded objective, ordered requirements, ordered exclusions, validation
and review requirements, ES repository identity, base OID, and exactly three
authorized paths. It is not chat history or a raw model prompt. It must not be
stored in Coordinator SQLite or exposed in public reports or logs.

`WorkerCommandV1` is only the originating candidate-authoring semantic command.
Its sole effect class is `author_candidate`; it is not generalized into a
validation, review, cancellation, or Git command. It binds the WorkSpec
reference and digest and all authority, fence, global-stop,
repository/base/path, capsule, resource, cost, privacy, and redaction fields in
C2A-PROTO-003. Its preassigned `candidate_ref` identifies the candidate lineage
before bytes exist. The first authoring command has
`max_local_commits`, `max_pushes`, `max_pull_requests`, `max_merges`, and
`max_deployments` equal to zero. It therefore authorizes no Git or publication
effect even if every structural check succeeds.

Command identity excludes delivery identity, adapter route, source invocation,
PID, absolute path, receive timestamp, retry count, transport framing,
credentials, endpoint, raw prompt, transcript, JSONL, and generic metadata.
The complete record remains closed-world; exclusion from identity does not
permit those fields in the command.

Replay is exact:

- the same `command_ref`, `command_digest`, and postcomputed
  `effect_fence_digest` is exact replay;
- the same `command_ref` with any different digest is conflict; and
- redelivery creates a new delivery identity under the exact delta below.

`DeliveryEnvelopeV1` is the only route-specific wrapper and represents the
**current effect delivery**. Its current effect class is exactly one of
`author_candidate`, `validate_candidate`, `review_candidate`, or
`cancel_effect`, as established by its current `effect_intent_ref` and current
`EffectFenceV1`; it never carries `local_git_commit`. The separately governed
Git effect remains under C2A-PROTO-010.

For every delivery, `delivery_attempt_ref` is current delivery identity;
`semantic_attempt_ref` is the originating semantic attempt;
`effect_intent_ref` is current effect intent; `attempt_fence_ref` and digest
bind the originating attempt fence; `effect_fence_ref` and digest bind the
current effect fence; and `command_ref` and digest bind the originating
author-candidate command lineage. For authoring, that command is also the
command being delivered. For validation, review, and cancellation, the current
action is selected by the current effect intent and fence while the command
fields remain provenance lineage.

`WorkerObservationV1` uses the same distinction: its delivery and source
invocation are current; its effect intent and effect fence are current; and its
command reference and digest retain the originating author-command lineage.
The v1 field names are unchanged.

### Current-effect/originating-author relation vectors

All four vectors use semantic attempt `semantic-attempt.0001`, originating
command `worker-command.0001`, and originating command digest
`6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927`.
Every other literal shown is vector-specific. JSON `null` in the three target
columns is an exact serialized value, not absence.

| Vector | Current effect class | Current effect intent | Current effect fence ref | Current effect-fence digest | Capsule binding | Cancellation target effect intent | Cancellation target effect fence ref | Cancellation target effect-fence digest | Delivery attempt | Adapter-safe correlation | Source invocation | Observation ref |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| author | `author_candidate` | `effect-intent.author.0001` | `effect-fence.0001` | `71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3` | JSON `null` before sealing | JSON `null` | JSON `null` | JSON `null` | `delivery-attempt.author.0001` | `adapter-correlation.author.0001` | `source-invocation.capsule-builder.0001` | `observation.capsule-sealed.0001` |
| validation | `validate_candidate` | `effect-intent.validate.0001` | `effect-fence.validate.0001` | `d0867a8d6d6f89fcd8d7efe1a150f6eb904f0dd8a918065de0224db0cb9a9531` | `b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c` | JSON `null` | JSON `null` | JSON `null` | `delivery-attempt.validation.0001` | `adapter-correlation.validation.0001` | `source-invocation.validator.0001` | `validation-observation.0001` |
| review | `review_candidate` | `effect-intent.review.0001` | `effect-fence.review.0001` | `e615b172eeddca9b69fd6d956b535e7ca60eb36f51e73038586a9ce67316a2bc` | `b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c` | JSON `null` | JSON `null` | JSON `null` | `delivery-attempt.review.0001` | `adapter-correlation.review.0001` | `source-invocation.reviewer.0001` | `independent-review.0001` |
| cancellation | `cancel_effect` | `effect-intent.cancel.0001` | `effect-fence.cancel.0001` | `ccaf53c44a06410e602c9f39ddc1677e734c0ba6f92c783752b28d1f7e5ff463` | JSON `null`; targets the non-capsule-consuming author effect | `effect-intent.author.0001` | `effect-fence.0001` | `71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3` | `delivery-attempt.cancellation.0001` | `adapter-correlation.cancellation.0001` | `source-invocation.cancel.0001` | `observation.cancellation.0001` |

Validation and review bind the exact sealed capsule digest. Cancellation may
have a null capsule binding only when the targeted effect does not consume a
sealed capsule; cancellation of validation, review, or another
capsule-consuming effect binds that exact digest.

### Capsule-consuming cancellation relation vector

The separate positive control below is not a fifth principal relation family.
It proves that cancellation of an exact capsule-consuming validation effect is
representable without changing DeliveryEnvelopeV1 or WorkerObservationV1.

| Current effect intent | Current effect fence ref | Current effect-fence digest | Target effect intent | Target effect fence ref | Target effect-fence digest | Capsule binding |
| --- | --- | --- | --- | --- | --- | --- |
| `effect-intent.cancel-validation.0001` | `effect-fence.cancel-validation.0001` | `ae4de68f737afa1e5f22b72384a188abad36d3f9a4ae5e28e835e7644dc0b66b` | `effect-intent.validate.0001` | `effect-fence.validate.0001` | `d0867a8d6d6f89fcd8d7efe1a150f6eb904f0dd8a918065de0224db0cb9a9531` | `b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c` |

### Exact redelivery delta

A redelivery comparison first requires both the original and candidate
DeliveryEnvelopeV1 records to pass, in order: exact closed keyset, exact schema
ID, exact scalar types, exact safe-reference grammar, exact digest grammar,
exact finite adapter kind, exact self-digest, and exact current-effect,
originating-command, AttemptFence, and EffectFence relations. Only after both
complete validations succeed may the exact delta be compared.

A redelivery of one current effect preserves an exact keyset and may change
only these identity-payload values:

1. `delivery_attempt_ref`
2. `adapter_safe_correlation_ref`

Every other identity-payload key and value is byte-semantically identical,
including schema, program, program version, semantic attempt, current effect
intent, originating command, both originating attempt-fence fields, both
current effect-fence fields, and `adapter_kind`. The excluded derived
`delivery_envelope_digest` necessarily changes after either permitted identity
change and must equal the recomputed digest. A missing key, additional key, or
any other changed value is not redelivery. A route change between
`direct_local_bootstrap` and `execution_substrate` is not redelivery; it
requires a separately selected effect intent, effect fence, and delivery.

Direct-local and ES may carry different selected effects, but neither may
translate or change the semantic author command. No structurally valid
WorkSpec, command, or delivery envelope is executable authorization. No
non-authoring source implementation, framing, launch, or credential mechanism
is authorized here.

## C2A-PROTO-005 — Standing-Authority Bindings, Attempt And Effect Fences, Global Stop, And Cancellation

Classification: ACCEPTED STRATEGIC TARGET

Required before: any source

`AttemptFenceV1` is a target-only subordinate attempt binding. It binds the
parent standing grant and attempt authorization; program, version, accepted
intent, work item, revision, and semantic attempt; repository, object format,
base, aggregate path and effect ceilings; expiry; and the coding global-stop
reference and version.

`EffectFenceV1` is a separate, narrower binding for one effect intent and
effect class. It additionally binds the command digest, preassigned candidate,
narrower path and effect ceilings, and—when validation, review, Git, or a
cancellation target consumes a sealed candidate—the exact portable capsule
digest. A null capsule digest is permitted before sealing for candidate
authoring and for cancellation only when the targeted effect does not consume
a sealed capsule.

The author `EffectFenceV1` is exactly post-bound to the complete originating
`WorkerCommandV1`, not merely to a structurally valid sibling fence under the
same AttemptFence. The actual author fence must have the exact ref and digest
stored by the complete command; the fence must bind that command's independently
recomputed ref and digest; and both stored digests must equal their independent
domain-separated recomputations. Program/version, accepted intent, work and
revision, semantic attempt, author effect intent and class, candidate,
repository/base/path, parent grant, attempt and effect authorizations,
AttemptFence, global stop, and effect ceilings agree exactly wherever mapped.
The author fence has null capsule and cancellation-target fields. Validation,
review, cancellation, Git, delivery, observation, and capsule relations must
receive and validate this actual post-bound author fence; substituting a
different resealed sibling is invalid even when all other attempt-level fields
remain coherent.

Every EffectFence must name an `effect_class` that occurs exactly once in the
referenced AttemptFence's sorted `allowed_effect_classes`. The canonical
AttemptFence permits exactly `author_candidate`, `cancel_effect`,
`local_git_commit`, `review_candidate`, and `validate_candidate`; omission of
`cancel_effect` makes the canonical cancellation relation invalid.

The cancellation-target relation is closed and immutable:

- `author_candidate`, `validate_candidate`, `review_candidate`, and
  `local_git_commit` require all three cancellation-target fields to be JSON
  `null`;
- `cancel_effect` requires all three fields to be non-null and to identify one
  exact already-existing target EffectFence;
- the target is not the cancellation fence itself and has class
  `author_candidate`, `validate_candidate`, or `review_candidate`;
- target and cancellation agree exactly on program and program version,
  accepted-intent and work-item revisions, semantic attempt, repository, Git
  object format and base OID, AttemptFence ref and digest, candidate, and
  originating author-command ref and digest; and
- the cancellation digest includes all three target fields. Delivery and
  observation records bind that target transitively through the exact current
  cancellation EffectFence ref and digest and do not duplicate target fields.

`local_git_commit` is not a DeliveryEnvelopeV1 or WorkerObservationV1
cancellation target. Git cancellation or interruption remains deferred under
C2A-PROTO-010. A cancellation targeting `author_candidate` with a null target
capsule must itself have a null capsule. A cancellation targeting
`validate_candidate` or `review_candidate` requires the target's non-null
portable capsule digest and must equal it exactly. Wrong sibling, mixed
intent/ref/digest, self, cross-attempt, cross-program, cross-revision,
cross-repository, cross-base, null capsule-consuming, and unrelated-capsule
relations are invalid.

The following non-authority rules are unconditional:

- schema validity is not authorization;
- digest validity is not authorization; and
- reference possession is not authorization.

A future verifier must validate the complete grant, subordinate authorization,
fence, expiry and revocation, repository, base, path, and current-global-stop
relation before launch or effect. The Coordinator may derive only narrower
subordinate records; it may not exceed, extend, renew, reinterpret, or outlive
the parent standing authority.

A post-launch stop creates a separate cancellation intent. Cancellation intent,
termination request, termination acknowledgement, signal delivery, process
exit, semantic abandonment, and semantic cancellation are distinct facts.
Process exit proves neither semantic cancellation nor semantic completion and
does not prove that no candidate capsule exists.

## C2A-PROTO-006 — Finite Source Observations And Coordinator Ingest Dispositions

Classification: FUTURE IMPLEMENTATION DETAIL

Required before: any source

The exact first-slice `source_kind` inventory is:

1. `direct_local_adapter`
2. `es_adapter`
3. `worker`
4. `capsule_builder`
5. `validator`
6. `independent_reviewer`
7. `workspace_custodian`
8. `capsule_store`

The **underlying fact owner** owns the external or source-native fact. The
**canonical observation author** constructs and authors
`WorkerObservationV1`. The **adapter/carrier** transports the command,
envelope, observation, or opaque result. The **Coordinator recorder** records
the safe observation and ingest disposition through a future guarded writer
boundary. Carrying or recording a fact transfers neither authorship nor
authority.

### Observation fact-owner and authorship matrix

| Observation family | Underlying fact owner | Canonical observation author | Permitted carrier |
| --- | --- | --- | --- |
| delivery acknowledged/rejected/unknown | direct-local delivery supervisor or ES submit/recovery owner | `direct_local_adapter` or `es_adapter` | the selected route only |
| worker started/completed and candidate captured | worker process | `worker` | direct-local or ES route |
| capsule sealed/seal failed | capsule builder | `capsule_builder` | direct-local or ES route |
| validation completed | validator/test runtime | `validator` | direct-local or ES route |
| independent review completed | independent reviewer | `independent_reviewer` | direct-local or ES route |
| cancellation acknowledged/rejected | direct-local supervisor or ES cancellation/lifecycle owner | `direct_local_adapter` or `es_adapter` | selected route |
| process exit/deadline | OS/supervisor for direct-local or ES lifecycle owner | `direct_local_adapter` or `es_adapter` | selected route |
| workspace teardown | workspace custodian | `workspace_custodian` | selected route |
| capsule retrieval | capsule store | `capsule_store` | selected route |

`source_kind` is the canonical observation-author kind, and `source_ref` is
that author's stable safe record reference. The existing v1 `evidence_refs`
field has the `safe_evidence_refs` role and may safely bind the underlying fact
owner's native record. Carrier identity is route or transport metadata outside
the semantic observation identity. ES remains the fact owner for ES
admission/runtime/lifecycle facts even when `es_adapter` authors the canonical
Coordinator observation. A direct-local adapter does not become the OS-process
fact owner merely because it authors an observation. Coordinator does not
become the fact owner merely because it records the observation.

Route pairing is exact for every adapter-authored delivery, cancellation,
process, or deadline observation. `direct_local_bootstrap` requires
`source_kind=direct_local_adapter` and the source-native fact remains owned by
the direct-local supervisor or OS/process source. `execution_substrate`
requires `source_kind=es_adapter` and the source-native fact remains owned by
the ES submit, recovery, or lifecycle owner. This applies to
`delivery_acknowledged`, `delivery_rejected`, `delivery_outcome_unknown`,
`cancellation_acknowledged`, `cancellation_rejected`, `process_exited`, and
`deadline_elapsed`. Every cross-pair is invalid. The selected adapter carries
the canonical observation and Coordinator records it; carriage and recording
transfer neither fact ownership nor canonical authorship. In particular,
`delivery_acknowledged` remains transport evidence and is not semantic
acceptance.

The source/observation-kind matrix is closed. A slash-separated source cell is
an exact finite alternative set. `none` means all four conditional fields are
prohibited. `candidate` means only `candidate_ref` is required. `capsule` means
`candidate_ref`, `capsule_manifest_ref`, and `portable_capsule_digest` are
required. `exit` means only `process_exit_code` is required.

### Source/observation-kind matrix

| Order | Observation kind | Permitted source kind | Finite outcome | Conditional fields |
| ---: | --- | --- | --- | --- |
| 1 | `delivery_acknowledged` | `direct_local_adapter` / `es_adapter` | `acknowledged` | none |
| 2 | `delivery_rejected` | `direct_local_adapter` / `es_adapter` | `rejected` | none |
| 3 | `worker_started` | `worker` | `started` | none |
| 4 | `worker_completed` | `worker` | `completed` | none |
| 5 | `candidate_captured` | `worker` | `captured` | candidate |
| 6 | `capsule_sealed` | `capsule_builder` | `sealed` | capsule |
| 7 | `capsule_seal_failed` | `capsule_builder` | `failed` | candidate |
| 8 | `validation_completed` | `validator` | `passed` / `failed` / `inconclusive` / `not_run` | capsule |
| 9 | `independent_review_completed` | `independent_reviewer` | `passed` / `failed` / `inconclusive` | capsule |
| 10 | `cancellation_acknowledged` | `direct_local_adapter` / `es_adapter` | `acknowledged` | none |
| 11 | `cancellation_rejected` | `direct_local_adapter` / `es_adapter` | `rejected` | none |
| 12 | `process_exited` | `direct_local_adapter` / `es_adapter` | `exited` | exit |
| 13 | `deadline_elapsed` | `direct_local_adapter` / `es_adapter` | `elapsed` | none |
| 14 | `delivery_outcome_unknown` | `direct_local_adapter` / `es_adapter` | `unknown` | none |
| 15 | `workspace_teardown_succeeded` | `workspace_custodian` | `succeeded` | capsule |
| 16 | `workspace_teardown_failed` | `workspace_custodian` | `failed` | capsule |
| 17 | `capsule_retrieval_succeeded` | `capsule_store` | `succeeded` | capsule |
| 18 | `capsule_retrieval_failed` | `capsule_store` | `failed` | capsule |

### Observation current-effect relation matrix

| Observation kind | Permitted current `EffectFenceV1.effect_class` |
| --- | --- |
| `delivery_acknowledged` | `author_candidate`, `validate_candidate`, `review_candidate`, or `cancel_effect` |
| `delivery_rejected` | `author_candidate`, `validate_candidate`, `review_candidate`, or `cancel_effect` |
| `worker_started` | `author_candidate` only |
| `worker_completed` | `author_candidate` only |
| `candidate_captured` | `author_candidate` only |
| `capsule_sealed` | `author_candidate` only |
| `capsule_seal_failed` | `author_candidate` only |
| `validation_completed` | `validate_candidate` only |
| `independent_review_completed` | `review_candidate` only |
| `cancellation_acknowledged` | `cancel_effect` only |
| `cancellation_rejected` | `cancel_effect` only |
| `process_exited` | `author_candidate`, `validate_candidate`, `review_candidate`, or `cancel_effect` |
| `deadline_elapsed` | `author_candidate`, `validate_candidate`, `review_candidate`, or `cancel_effect` |
| `delivery_outcome_unknown` | `author_candidate`, `validate_candidate`, `review_candidate`, or `cancel_effect` |
| `workspace_teardown_succeeded` | `author_candidate` or `cancel_effect` |
| `workspace_teardown_failed` | `author_candidate` or `cancel_effect` |
| `capsule_retrieval_succeeded` | `validate_candidate` or `review_candidate` |
| `capsule_retrieval_failed` | `validate_candidate` or `review_candidate` |

Each observation binds the exact program/version, work/revision, semantic
attempt, current effect intent, originating command lineage, current delivery,
originating attempt fence, and current effect fence. Every reference is an
exact bounded string; objects, arrays, booleans, and integers are invalid in a
reference field. Every digest is exactly 64 lowercase hexadecimal characters.
`process_exit_code` is an exact integer from -255 through 255 and rejects a
boolean. `observed_at` is the bounded whole-second source timestamp and is
evidence without ordering or acceptance authority. `reason_code` is a bounded
finite token; `provably_not_accepted` is reserved for the exact
unknown-outcome/redelivery proof in C2A-PROTO-007. Evidence references are
sorted, unique safe refs. The finite payload is only the matrix outcome,
bounded reason code, bounded safe evidence references, and matrix-authorized
conditional fields. Unknown fields fail validation.

The live finite relation is compositional: closed WorkerObservationV1
structure, complete DeliveryEnvelopeV1 validation, the actual current
EffectFenceV1, the actual AttemptFenceV1, the originating WorkerCommandV1,
route/source pairing, observation-kind/effect-class pairing, and—whenever
capsule fields apply—the exact validated CandidateCapsuleManifestV1 must all
pass. Across those records, program, version, accepted intent, work item and
revision, semantic attempt, current effect intent, command ref and digest,
delivery attempt, both fence refs and digests, candidate ref, capsule manifest
ref, and portable capsule digest must agree wherever the field applies.

`capsule_sealed`, `validation_completed`,
`independent_review_completed`, `capsule_retrieval_succeeded`, and
`capsule_retrieval_failed` require the exact candidate, manifest ref, and
portable digest of the validated capsule. The other matrix rows whose
conditional form is `capsule` obey the same exact capsule binding.
`capsule_seal_failed` requires the exact candidate and may not fabricate a
manifest ref or portable digest. Validation and review require a non-null
current EffectFence capsule digest equal to the observation and validated
manifest. A capsule from another attempt, current effect, or originating
author-command lineage is invalid. Cancellation observations require the
current `cancel_effect` fence and its immutable target relation to validate;
they carry no duplicate target fields.

Conditional fields are exact. `candidate_captured` and
`capsule_seal_failed` require only `candidate_ref`. `capsule_sealed`,
`validation_completed`, `independent_review_completed`, both workspace
teardown kinds, and both capsule retrieval kinds require `candidate_ref`,
`capsule_manifest_ref`, and `portable_capsule_digest`. `process_exited`
requires only `process_exit_code`. All remaining kinds prohibit all four
conditional fields.

An observation may not contain or author acceptance, a Coordinator semantic
rejection, repair, replan, retry authorization, program completion,
publication, or desired state. Recording an observation does not convert it
into a Coordinator decision.

## C2A-PROTO-007 — Replay, Duplicate, Late, Stale, Ambiguous, And Unknown-Outcome Semantics

Classification: FUTURE IMPLEMENTATION DETAIL

Required before: any source

Source observation and Coordinator ingest treatment are distinct. Before any
disposition is assigned, schema, canonical digest, exact field types, finite
enums, source-kind/observation-kind/outcome relation, current-effect relation,
and conditional fields must all pass. A malformed record receives no ingest
disposition.

For a valid observation, the exact first-slice disposition matrix is evaluated
top to bottom:

### Ingest-disposition precedence matrix

| Order | Ingest disposition | Exact condition | Progression consequence |
| ---: | --- | --- | --- |
| 1 | `duplicate_exact` | same `observation_ref` already exists with the same `observation_digest` | no second fact or progression action |
| 2 | `conflict_quarantined` | same `observation_ref` already exists with a different digest | quarantine both identity claims; no progression |
| 3 | `ambiguous_quarantined` | no prior ref exists, but there is no unique immutable attempt/effect/command/delivery/fence/source binding, the binding is contradictory, or source-owner evidence cannot distinguish late from stale | quarantine; no progression or blind retry |
| 4 | `stale_retained` | no prior ref exists and source-owner evidence proves the fact was authored after its bound program/work/authority/fence became stale, expired, or revoked | retain as evidence; cannot advance progression |
| 5 | `late_retained` | no prior ref exists, exact historical binding is known, the fact was authored while that binding was valid, and ingestion occurs after the effect became terminal or superseded | retain against the original effect; never apply to a newer attempt |
| 6 | `recorded` | no prior ref exists and the exact binding is current with no earlier condition | retain as evidence; evaluate separately |

Local receipt time or an unauthoritative source timestamp cannot decide late
versus stale. Late and stale evidence retain original identity and attribution;
they are never rewritten onto a newer program version, work revision, semantic
attempt, effect intent, delivery, or fence. No disposition creates semantic
acceptance, repair, replan, retry authorization, program completion, or
publication.

An unknown delivery outcome is an observation, not a disposition, and generic
reconciliation is insufficient for redelivery. After
`delivery_outcome_unknown`, redelivery remains blocked unless all five
conditions hold:

1. a valid original `delivery_outcome_unknown` observation is bound to the
   exact affected delivery and complete semantic graph;
2. the underlying delivery fact owner provides source-native proof of rejection
   and non-acceptance, and the canonical rejection observation safely
   references that exact owner-evidence ref;
3. the selected route's canonical observation author constructs a valid exact
   `delivery_rejected` WorkerObservationV1 whose reason code is exactly
   `provably_not_accepted`, whose route/source pair is exact, and whose
   delivery, effect, command, fences, program, and version equal the unknown
   observation and actual relation records;
4. Coordinator separately records a closed redelivery decision relation bound
   to that same graph and exact owner-evidence ref; and
5. the parent and subordinate authority relation remains valid, unexpired, and
   unrevoked under the current applicable coding global-stop ref and version.

The test-only Coordinator decision relation is closed and binds only its safe
decision ref, `redeliver` kind, program/version, semantic attempt, effect,
delivery, command ref/digest, both fence refs/digests, owner-evidence ref,
coding global-stop ref/version, and a valid-current authority evaluation. It is
target-contract evidence, not an eighth semantic schema, durable state,
executable authorization, or a runtime decision engine. Detached booleans,
generic reconciled flags, bare reason strings, or any observation, proof,
decision, authority evaluation, or global-stop claim without the other actual
records fail closed.

Before the five-condition decision is eligible, the rejection observation is
evaluated against the already recorded unknown observation through the same
ingest-precedence matrix above. Same ref and same digest is
`duplicate_exact`; same ref and different digest is `conflict_quarantined`;
unbound or contradictory is `ambiguous_quarantined`; stale is
`stale_retained`; and late is `late_retained`. None is redelivery evidence.
Only a distinct, independently valid, exactly bound, current rejection whose
disposition is `recorded` may contribute to the five conditions. This is a
pure test-only relation and does not implement durable ingest. Its closed
source-owner lifecycle relation binds the delivery attempt, effect-fence ref
and digest, and owner-evidence ref and distinguishes only `current`, `stale`,
or `late`; observation timestamps alone do not make that classification.

For a non-cancellation current effect, the unknown-outcome relation requires
the cancellation target argument to be omitted. For `cancel_effect`, it
requires the actual exact target EffectFence record and carries that same
record through validation of the current effect fence, delivery, both source
observations, Coordinator decision relation, and authority/global-stop
relation. The current fence's immutable target intent ref, fence ref, and fence
digest must equal the supplied target. Author targets consume no capsule;
validation or review targets require the exact sealed portable-capsule digest.
The canonical author-effect, cancellation-to-author, and
cancellation-to-validation graphs are positive controls. Missing, explicit
null, malformed, sibling, cross-attempt, wrong-capsule, wrong-route, and
conflicting-observation variants fail closed without adding an eighth schema.

The source observation is evidence, not the Coordinator decision. C2A creates
no universal retry or event grammar.

## C2A-PROTO-008 — Candidate Capsule Manifest, Portable Digest, Custody, And Retrieval

Classification: FUTURE IMPLEMENTATION DETAIL

Required before: any source

The selected portable capsule identity is a canonical manifest plus immutable
blobs. Git tree or object representation, tar identity, compressed archive
identity, local directory identity, and absolute path are not its canonical
identity. The full manifest has the exact fields in C2A-PROTO-003; the portable
digest is excluded from its own canonical identity payload.

The canonically sorted authorized path set is exactly:

1. `.docs/system_overview/hybrid_integration_architecture_adr.md`
2. `PLANS.md`
3. `docs_contract_test.go`

Every entry is a repository-relative POSIX path with operation
`replace_regular_file`, mode `100644` or `100755`, and exact before/after blob
SHA-256 and byte lengths. The first slice permits replacement of regular files
only. It fails closed on add, delete, rename, symlink, submodule, directory
entry, device, socket, FIFO, hardlink, unsupported mode, absolute path,
traversal, empty segment, dot segment, URI-like path, backslash, NUL, duplicate
path, case-equivalent path, normalization-equivalent path, or a fourth ES path.

Manifest validity requires the declared digest and length of every before and
after blob to equal the immutable bytes, the independently recomputed
authorized-path-scope digest to equal the exact three sorted paths, and the
portable digest to equal the complete canonical manifest. These checks are
cross-record, not merely shape checks. The manifest must have exact
`schema_id=governed-execution.nwp-candidate-capsule-manifest.v1`,
`canonicalization_profile=canonical-json.sorted-keys.utf8.v1`, and
`digest_domain=governed-execution.nwp-candidate-capsule-manifest.v1.identity`.
Its AttemptFence ref and digest must bind the actual structurally validated
AttemptFence; a coherently resealed graph cannot substitute a false root. The
manifest, originating author
command, author effect fence, and sealed observation must agree exactly on:

### Capsule cross-record binding matrix

| Order | Cross-record binding |
| ---: | --- |
| 1 | `program_ref` |
| 2 | `program_version_ref` |
| 3 | `accepted_intent_revision_ref` |
| 4 | `work_item_revision_ref` |
| 5 | `semantic_attempt_ref` |
| 6 | author `effect_intent_ref` |
| 7 | originating `command_ref` |
| 8 | originating `command_digest` |
| 9 | `candidate_ref` |
| 10 | `attempt_fence_ref` and `attempt_fence_digest` |
| 11 | author `effect_fence_ref` and `effect_fence_digest` |
| 12 | `repository_ref` |
| 13 | `base_git_object_format` and `base_git_oid` |
| 14 | `authorized_path_scope_digest` |
| 15 | `capsule_manifest_ref` and `portable_capsule_digest` |

The normative manifest vector uses deterministic synthetic test-fixture blob
identities. It is not a real Execution Substrate candidate, creates no file,
and authorizes no capsule builder or store.

Roles are exact:

### Capsule custody-role matrix

| Role | Capsule responsibility |
| --- | --- |
| worker | candidate-byte source |
| capsule builder | canonical sealer |
| private immutable worker-side store | physical custodian |
| Coordinator | safe refs, digests, ingest dispositions, and decisions only |
| reviewer | read-only attempt-bound and capsule-bound retrieval |
| later ES | opaque carrier or custodian under an ES-owned contract |
| Git | object and ref truth only after a separately selected Git effect |

Retrieval authority is separate from a safe reference. It is read-only,
attempt-bound, capsule-bound, audience-bound, non-enumerating, non-mutating,
and no longer-lived than its parent authority. Physical store path, encryption,
quota, retention duration, garbage collection, and ES carriage remain deferred.
A capsule digest is not a path, credential, authority proof, acceptance
decision, or Git identity. The following owner-local rules are independently
mandatory within C2A-PROTO-008:

- `capsule_manifest_ref` is not retrieval authority.
- `portable_capsule_digest` is not retrieval authority.
- Safe-reference possession is not retrieval authority.
- Digest possession is not authorization.

The following fenced inventory names the exact ordinary affirmative
contradictions. The fenced occurrences are non-normative examples; an ordinary
occurrence of any listed sentence inside this clause invalidates the contract:

```text
`capsule_manifest_ref` is retrieval authority.
`portable_capsule_digest` is retrieval authority.
Safe-reference possession is retrieval authority.
Digest possession is authorization.
```

Therefore the portable capsule digest does not authorize retrieval, possession
of `capsule_manifest_ref` is not sufficient retrieval authority, a safe capsule
reference is not a bearer retrieval credential, and reviewers may not
enumerate capsules using a digest. Removal, affirmative inversion, or movement
of any of these rules outside C2A-PROTO-008 invalidates the contract.

## C2A-PROTO-009 — Validation, Independent Review, Model Proposal, And Coordinator Decision

Classification: ACCEPTED STRATEGIC TARGET

Required before: any source

The decision roles remain separate:

### Decision-role matrix

| Stage | Authority posture |
| --- | --- |
| worker self-report | evidence only |
| structural validation | source-owned validation observation |
| repository test execution | source-owned validation observation |
| independent review | separate reviewer observation or proposal bound to the exact capsule |
| model review | non-authoritative proposal |
| Coordinator | sole durable semantic decision writer under valid authority |

The closed validation or review observation contains only the existing exact
`WorkerObservationV1` fields: finite observation kind and outcome, bounded
reason code, safe `evidence_refs`, exact candidate/capsule refs and digest, and
the common immutable bindings. It has no direct requirement-profile,
tool-version, raw-tool-output, detailed-count, unrestricted-validation-record,
or review-narrative field. Detailed requirement, tool, profile, count, and
private-output material remains behind a bounded safe evidence reference under
a future owner contract. No raw validation or review output enters Coordinator
SQLite or a public report.

Successful validation does not create acceptance. `inconclusive` or `not_run`
does not satisfy required validation. A byte-changing repair normally creates
a new semantic attempt and candidate. Replan changes the governing program or
work revision, and stale proposals cannot advance that revision.

## C2A-PROTO-010 — Separate First-Slice Git Effect

Classification: ACCEPTED STRATEGIC TARGET

Required before: any source

The first-slice Git effect is semantic target only. It has its own
`git_effect_intent_ref`, authorization, and effect fence and binds the accepted
Coordinator decision, semantic attempt, candidate, capsule manifest, portable
capsule digest, ES repository identity, exact base OID, exact three-path
ceiling, designated local feature ref, expected current ref and base, and one
intended commit content or tree. Its hard ceilings are exactly one local commit
and zero pushes, pull requests, merges, and deployments.

Immediately before the effect, a future handler must revalidate authority,
global stop, repository identity, base, capsule integrity,
candidate/workspace equality, path ceiling, and effect ceiling. It must block
on stale base, unexpected ref, unexpected tree, dirty unrelated content,
capsule mismatch, candidate mismatch, missing acceptance, missing fence, or
ambiguous authority.

### Git-effect prohibition matrix

Each row is an independent hard prohibition within this clause.

| Order | Prohibited effect | Exact posture |
| ---: | --- | --- |
| 1 | automatic rebase | prohibited |
| 2 | automatic merge | prohibited |
| 3 | automatic amend | prohibited |
| 4 | path or effect widening | prohibited |
| 5 | push | prohibited |
| 6 | remote-ref mutation | prohibited |
| 7 | pull-request creation | prohibited |
| 8 | deployment | prohibited |
| 9 | hooks-based extra effect | prohibited |
| 10 | hidden second commit | prohibited |
| 11 | blind second commit after unknown outcome | prohibited |

### Git-effect mandatory bindings and reconciliation

| Requirement | Exact posture |
| --- | --- |
| local feature-branch commit ceiling | exactly one |
| effect binding | exact accepted decision, semantic attempt, candidate, capsule manifest, portable capsule digest, repository, base, path ceiling, designated local ref, expected current ref, and intended tree |
| immediate pre-effect check | revalidate authority, global stop, repository, base, capsule integrity, candidate/workspace equality, path ceiling, and effect ceiling |
| unknown-outcome treatment | reconcile from Git object and ref truth before any further effect |
| commit observation | Git evidence only; not semantic completion |

Commands, branch naming, commit-message format, signing, author and committer
identity, and credentials remain deferred.

## C2A-PROTO-011 — Direct-Local And ES Semantic Conformance

Classification: ACCEPTED STRATEGIC TARGET

Required before: any source

Direct-local bootstrap and the later ES route must eventually share exactly:

1. schema IDs;
2. canonical bytes;
3. golden digests;
4. semantic command;
5. delivery semantics;
6. observation semantics;
7. attempt and effect fences;
8. capsule model;
9. safe-reference model;
10. exact replay and conflict behavior;
11. source attribution;
12. late, stale, and ambiguous handling;
13. cancellation and reconciliation semantics;
14. privacy and error mapping; and
15. the same worker artifact and version.

Only transport wrapping may differ. No route may translate semantic identities
into a route-specific dialect. ES owns admission, reliable submit,
response-loss recovery, runtime lifecycle, cancellation correlation, retained
results, and ES-side ambiguity resolution. The Coordinator must not implement
an ES recovery workaround, Nomad scraper, parallel lifecycle store, or ES
reprioritization. Bridge and Bridge Core are not part of conformance.
Bridge Core remains unused.

## C2A-PROTO-012 — Process, Release, Terminal Receipt, And Credential Gates

Classification: FUTURE IMPLEMENTATION DETAIL

Required before: external process launch

The selected first-topology direction is one one-shot subprocess, one semantic
command on standard input, one bounded protocol-only result on standard output,
no listener, and no daemon. A per-child anonymous result file descriptor or
socketpair is a permitted pre-launch fallback only if standard-output purity or
cancellation requires it. A named Unix-domain listener and filesystem mailbox
control transport are rejected for the first slice.

This is a target direction and launch gate, not current implementation. Exact
framing, executable identity, artifact versioning, packaging, release and
rollback, containment, terminal receipt, size limits, exit and error precedence,
and credential delivery must be separately frozen before any external process
launch.

A durable effect intent must precede every external process I/O attempt.

Credentials are out-of-band, role-separated, least privilege, and absent from
DTOs, argv, logs, reports, capsules, and inherited unrelated descriptors. No
worker-side component receives Coordinator durable-write authority.

## C2A-PROTO-013 — Privacy, Redaction, And Artifact Placement

Classification: ACCEPTED STRATEGIC TARGET

Required before: any source

The placement grammar is closed-world. Material classes not listed in a
location's permitted cell are prohibited at that location. This includes, at
minimum, the exact rejected sentinel classes `trust_material`,
`capsule_bytes`, `private_work_spec`, `unrestricted_diff`,
`database_material`, `token`, `raw_chat_history`, `raw_prompt`, `transcript`,
`codex_jsonl`, `credential`, `private_endpoint`, `absolute_path`, `raw_log`,
and `workspace_bytes`. A more specific permitted class does not admit its
generic rejected sentinel; for example, `immutable_capsule_blob` does not admit
arbitrary `capsule_bytes`.

### Placement matrix

| Location | Permitted material | Prohibited material | Authority posture |
| --- | --- | --- | --- |
| Coordinator SQLite | `safe_id`, `safe_ref`, `digest`, `binding`, `ceiling`, `status`, `reason_code`, `coordinator_decision`, `ingest_disposition` | every unlisted material class (closed-world) | future guarded durable progression only |
| private WorkSpec material | `private_objective`, `private_requirement`, `private_exclusion`, `safe_binding` | every unlisted material class (closed-world) | private desired-work attachment; not durable program truth |
| worker workspace | `checked_out_base_bytes`, `authorized_candidate_bytes` | every unlisted material class (closed-world) | mutable execution material only |
| capsule store | `authorized_changed_file_blob`, `canonical_capsule_manifest`, `immutable_capsule_blob` | every unlisted material class (closed-world) | private physical custody only |
| validation/review observations | `bounded_status`, `bounded_reason_code`, `safe_evidence_ref`, `candidate_ref`, `capsule_manifest_ref`, `portable_capsule_digest` | every unlisted material class (closed-world) | source evidence or proposal only |
| model proposals | `safe_ref`, `bounded_proposal_status`, `bounded_reason_code`, `capsule_binding` | every unlisted material class (closed-world) | non-authoritative proposal only |
| public reports | `safe_id`, `safe_ref`, `digest`, `status`, `reason_code` | every unlisted material class (closed-world) | projection only |
| logs | `bounded_reason_code`, `redacted_safe_correlation` | every unlisted material class (closed-world) | non-authoritative diagnostics only |
| Git | `accepted_authorized_changed_file_bytes`, `git_object`, `designated_local_ref` | every unlisted material class (closed-world) | object and ref truth only |
| later ES retained result | `bounded_lifecycle_envelope`, `bounded_result_envelope`, `opaque_safe_capsule_ref` | every unlisted material class (closed-world) | ES runtime truth; not Coordinator semantic truth |

Redaction happens before an observation, proposal, diagnostic, or projection
crosses its boundary. A safe ref or digest does not grant retrieval authority.

## C2A-PROTO-014 — Mechanical Direct-Local Bootstrap Stop Conditions

Classification: ACCEPTED STRATEGIC TARGET

Required before: any source

The direct-local first slice must stop on each condition independently and in
this exact order:

1. Missing or invalid standing grant, subordinate authorization, attempt fence,
   effect fence, or current global-stop binding.
2. Expired, revoked, stale, ambiguous, widened, or mismatched authority.
3. Repository identity, base OID, Git object format, or path ceiling mismatch.
4. A second repository.
5. A second active invocation.
6. A Bridge, connector, CP, IM, MA, Host Lens, Symphony, or Bridge Core trigger
   or dependency.
7. Direct Coordinator SQLite access by worker, adapter, supervisor, reviewer,
   model adapter, capsule component, or Git component.
8. Worker/adapter creation of semantic attempts, acceptance, repair, replan, or
   publication decisions.
9. Any push, remote-ref mutation, PR, merge, deployment, or
   production-autonomy claim.
10. Command/delivery/observation/fence/capsule contract-version divergence
    between direct-local and the future ES route.
11. Candidate authorship, capsule sealing, custody, safe-reference, or retrieval
    ambiguity.
12. Unknown process or delivery outcome without authoritative reconciliation.
13. Blind redelivery after an unknown outcome.
14. Stale validation, review, model, decision, or Git-effect binding.
15. Expansion beyond the first accepted slice without a Coordinator-owned
    durable one-shot latch and a separately accepted migration review.

Marker files, reports, adapter memory, chat state, Bridge ledgers, and capsule
records are not sufficient to satisfy the expansion latch.

## C2A-PROTO-015 — Tranche Gates, No-Schema Posture, And Deferred Mechanics

Classification: FUTURE IMPLEMENTATION DETAIL

Required before: durable schema change

C2A1 is current only for pure internal semantic values and the six named pure
coherence validators. C2A1 adds no SQLite table or column, durable C2A state,
migration, package export, dependency, script, entry point, worker, adapter,
supervisor, process, filesystem store, Git handler, network client, model
client, Bridge or ES integration, scheduler, queue, service, API, IPC,
reconciler, or autonomous loop. When C2A was frozen, physical application
generation 1 and terminal migration `0001_initial` were the current baseline.
That schema-0001 statement is historical only. The current repository is at
physical application generation 2 with terminal migration
`0002_development_program_and_effect_state`, implemented by C2B2 Slice 1.
Current B4c behavior remains unchanged.

C2A1 implements the exact bounded source contract in
`.docs/c2a1-pure-semantic-values.md`; it may not launch a process or implement
durable mutation. The historical C2A freeze required separate later acceptance
for durable schema design and forward migration. C2B2 Slice 1 subsequently
implemented migration 0002 under its own physical-schema authority. C2A did not
create or own migration 0002. C2A assigns no migration number and authorizes no
schema work. Its semantic fields, values, identities, relations, and pure-value
source do not themselves create durable C2A tables or durable C2A runtime rows.
The generation-2 physical schema is a C2B2 Slice-1 implementation fact, distinct
from C2A/C2A1 semantic authority.

Migration 0003 remains absent. C2B2 Slice 2 provides pure private row/value
reconstruction over the unchanged C2A1 values. C2B2 private readers are
implemented; VS1B consumes unchanged C2A/C2B2 semantics for private
route-neutral genesis, and C2B3D consumes unchanged authoring, effect,
delivery, and redelivery relations for private author-effect persistence and
verification. C2A itself remains unchanged and confers no durable or
executable authority. Worker, process, or model execution, Git effects,
direct-local execution, ES routing, Bridge integration, publication, service,
API, and IPC also remain absent.

Still deferred are raw JSON decoding and full-record wire encoding, executable
authorization verification, revocation source and freshness, observation
ingest, unknown-outcome decisions, process framing, executable and artifact
identity, packaging and release, terminal receipt, containment, credential
handoff, physical capsule storage and retrieval, validation and review
execution, model invocation, Git commands and credentials, direct-local
bootstrap, ES routing, reconciliation, later schema persistence or migration,
service, API, IPC, scheduler, queue, and autonomous-loop mechanics. Pure canonical
identity-byte construction and the six named coherence validators are current
C2A1 behavior rather than deferred runtime mechanics.

### Direct pytest contract oracle

This C2A document is the semantic authority. Documentation-contract tests own
independently authored expected schema and vector constants and compare them
directly with bounded document parsing, canonical encoding, digest, strict
schema-validation, and strict relation-validation results. Core validators
consume the actual caller-supplied related records and never choose a canonical
fixture. Explicitly named test convenience wrappers may substitute canonical
fixtures only for the exact private omission sentinel.

Pytest parameter rows and deterministic fixtures are test inputs, not semantic
authority. Direct pytest collection and assertion outcomes are execution
evidence. An independent audit constructs and mutates semantic inputs directly
and does not accept an implementation-authored case inventory, dispatch claim,
trace claim, or aggregate test-artifact digest as proof.

Logical case IDs are not compatibility contracts. Pytest node IDs, node order,
node count, node bytes, AST shape, and their hashes are not compatibility
contracts. Operation, fixture, helper, binding, and trace registries are
retired, as are the custom mutation dispatcher, global recorder,
execution-token machinery, canonical executed-ledger records, fixed case and
node inventories, and aggregate acceptance hashes. They are not replaced by a
smaller manifest, generic semantic runner, or another attestation layer.

The seven frozen schema vectors and five frozen relation vectors remain the
byte-semantic contract authorities. No parser output, fixture, parameter row,
collected node, assertion report, audit record, or other test artifact becomes
durable program truth, runtime truth, semantic acceptance, or executable
authority.

Implementation and accepting audit must remain different roles. This
implementation may become ready for an independent audit; it cannot claim to
have performed or accepted that audit.

<!-- COGNITIVE_PROPOSAL_SELECTION_CROSS_REFERENCE_BEGIN -->
## Cognitive proposal and selection candidate

Section 41 of `.docs/c2b-durable-development-state.md` is the sole detailed semantic owner
for this bounded freeze. C2B3D remains current and unchanged. Section 41 is an
uncommitted contract candidate pending independent audit. Migration 0003 and all source/runtime remain absent.
The first later source tranche ends at typed pre-execution proposal admission plus Coordinator selection or non-selection;
it performs no model invocation or dispatch. In particular, model invocation, dispatch, worker contact, post-execution review, semantic decision, Git, and publication remain blocked.
The full remote-worker phase is not reduced to that first source tranche.

The finite candidate placement amendment, with its exact closed inventory owned
only by Section 41, permits Coordinator SQLite to hold model-contract and
redacted-configuration refs/digests; source-invocation, context, proposal,
private-artifact, and safe-projection schema IDs/refs/digests; bounded counts;
closed phase, recommendation, status, and reason codes; closed role-specific
evidence bindings; and Coordinator disposition, current-selection, graph,
receipt, and safe-result facts. It changes no established C2A schema, golden
vector, field order, or digest identity.

Raw prompts, hidden reasoning, provider sessions or history, raw request or
response payloads, arbitrary model text, private WorkSpec content, private plan
text, credentials, headers, endpoints, account or organization IDs, bearer
material, database material, and unrestricted logs remain prohibited in SQLite
and reports. The normalized typed private artifact remains outside SQLite under
separately governed custody, and its safe ref or digest grants no retrieval
authority.
<!-- COGNITIVE_PROPOSAL_SELECTION_CROSS_REFERENCE_END -->
