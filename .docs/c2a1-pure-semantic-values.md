# C2A1 Pure Semantic Values

Status: current bounded implementation contract

Implementation tranche: C2A1 — Pure No-I/O Semantic Values

Production module:
`src/ge_nwp_coordinator/_worker_execution_semantic_values.py`

Package-root export: none

Runtime or durable-state authorization: none

This record owns the Coordinator-local implementation boundary for the first
C2A source tranche. The authoritative C2A contract remains
`.docs/c2a-first-slice-semantic-protocol-contract.md`. C2A remains authoritative
for fields, identities, vectors, and semantic relationships. This record does
not restate or replace those field tables, digest domains, golden vectors,
relation vectors, cancellation rules, route/source rules, path scope, privacy
grammar, or Git ceiling.

## Implemented Scope

C2A1 implements pure internal values and the named pure coherence validators.
The implementation consists of exactly one standard-library-only, role-based
internal source module. C2B2 Slice-2 row reconstruction is its sole private
production consumer. The C2A1 module is not imported or re-exported by
`ge_nwp_coordinator.__init__`, and the consumer transfers no C2A semantic
ownership.

The implemented immutable values are:

| Value | Role | Exact field count |
| --- | --- | ---: |
| `CeilingsV1` | embedded closed value | 15 |
| `CapsuleEntryV1` | embedded closed value | 7 |
| `WorkSpecV1` | top-level semantic record | 18 |
| `AttemptFenceV1` | top-level semantic record | 22 |
| `EffectFenceV1` | top-level semantic record | 32 |
| `WorkerCommandV1` | top-level semantic record | 39 |
| `DeliveryEnvelopeV1` | top-level semantic record | 15 |
| `WorkerObservationV1` | top-level semantic record | 25 required plus exactly 4 conditionally present fields |
| `CandidateCapsuleManifestV1` | top-level semantic record | 24 |

The implemented pure relation functions are:

1. `validate_authoring_relation`
2. `validate_effect_relation`
3. `validate_delivery_relation`
4. `validate_redelivery_relation`
5. `validate_capsule_manifest_relation`
6. `validate_observation_relation`

These functions return `None` on success and raise the bounded
`WorkerExecutionValueError` on failure. They accept explicit actual value
objects through keyword-only parameters. They do not accept detached trust
booleans, infer records from golden fixtures, or use Python object identity as
semantic proof.

## Record-Local Validity, Graph Coherence, And Authority

Three claims remain distinct:

1. **Record-local validity** means a complete mapping has the exact closed
   field shape, exact built-in field types, valid local finite values, and the
   correct stored self-digest.
2. **Graph coherence** means the applicable named relation validator has
   compared the actual related records and all C2A-mandated duplicated and
   derived bindings.
3. **Executable authority or semantic acceptance** requires separately
   governed authority, current-state, source, durable decision, or runtime
   mechanics that C2A1 does not implement.

`from_mapping()` establishes only record-local validity. A locally valid
decoded value can remain graph-incoherent. Factory-created records that require
related records invoke their applicable pure coherence validation before they
return. No partial command, draft fence, placeholder digest, or mutable builder
escapes.

Schema validity, digest validity, object equality, reference possession, and
successful relation validation do not confer authority or acceptance.

## Exact Mapping API

`CeilingsV1` and `CapsuleEntryV1` expose:

```text
create(...)
from_mapping(payload: object)
to_mapping()
```

Every top-level value exposes:

```text
from_mapping(payload: object)
to_mapping()
identity_mapping()
canonical_identity_bytes()
computed_digest()
```

`WorkSpecV1`, `AttemptFenceV1`, `DeliveryEnvelopeV1`,
`WorkerObservationV1`, and `CandidateCapsuleManifestV1` additionally expose
their bounded `create(...)` factories. `WorkerCommandV1` has no independent
public `create()`. A new author command and its actual author EffectFence are
created only by `create_author_command_and_effect_fence(...)`.
`EffectFenceV1` has no general public `create()`. Non-author fences are created
only by `create_effect_fence(...)`.

There is no `from_dict`, `to_dict`, `from_json`, `to_json`, `serialize`,
`deserialize`, raw-byte parser, full-record encoder, framing codec, schema
registry, operation registry, dispatcher, or extension bag. Pure canonical
identity-byte construction is current; external JSON decoding and wire/runtime
encoding remain deferred.

`to_mapping()` and `identity_mapping()` return fresh built-in dictionaries and
fresh nested lists and dictionaries. They are explicit private-data accessors;
their contents are not log-safe merely because the accessors exist.

## Strict External Types And Validation Order

Every `create()` and `from_mapping()` boundary requires exact built-in types:

```text
object mapping: type(value) is dict
mapping key:    type(value) is str
array:          type(value) is list
string:         type(value) is str
integer:        type(value) is int
blob:           type(value) is bytes
```

Dict, list, string, and integer subclasses reject. Boolean is not an integer.
Tuple is not an external array. Generic mappings, bytearray, memoryview, float,
NaN, infinity, and coercible objects reject. No value is accepted through
`str(...)`, `int(...)`, truthiness, or another coercion.

Validation order is:

1. exact outer type;
2. unknown fields;
3. missing fields;
4. exact field types;
5. local field semantics;
6. stored self-digest equality; and
7. separately invoked graph coherence.

Set-like arrays must already be sorted by exact code point and unique. Ordered
arrays retain caller order and reject duplicates where C2A requires uniqueness.
Required nullable fields remain present with explicit `None`. Conditionally
inapplicable fields are absent, not `None`. Only the private `_MISSING` sentinel
means an omitted related-record argument; explicit `None`, false, zero, empty
strings, empty lists, and empty dictionaries are not omission.

## Immutable Representation

All nine values are manual classes rather than dataclasses. Each has explicit
slots, no instance dictionary, private stored fields, read-only properties,
disabled direct construction, exact-type equality, disabled hashing, constant
content-free `repr` and `str`, and blocked pickle reduction. Subclassing is
blocked. Normal assignment and deletion reject. Caller dictionaries and lists
are not retained; external arrays are stored internally as tuples and nested
objects are typed immutable values. `copy.copy()` and `copy.deepcopy()` may
return the same immutable object.

The bounded immutability claim covers the normal finite Python API. It does not
claim protection against hostile use of `object.__setattr__`.

No manifest retains caller-supplied blob bytes or blob dictionaries.

## Canonical Identity And Digests

The seven top-level values implement the exact C2A identity selections and
domain strings. Canonical identity bytes use a validated identity mapping,
object keys sorted by exact code point, compact separators, `ensure_ascii=false`,
strict UTF-8, no byte-order mark, no Unicode normalization, and no
insignificant whitespace.

Each digest is exactly:

```text
SHA-256(UTF8(digest_domain) || 0x00 || canonical_identity_bytes)
```

The implementation does not use
`src/ge_nwp_coordinator/canonicalization.py`. Encoding failures, including lone
surrogate code points, fail closed through a bounded error with no underlying
private exception context.

Self-digest exclusions remain exactly those in C2A. In particular,
`WorkerCommandV1` identity excludes both `effect_fence_digest` and
`command_digest`; all other top-level identities exclude only their named
self-digest.

## Author Command And EffectFence Post-Binding

The only new-author factory is:

```python
create_author_command_and_effect_fence(
    *,
    work_spec: WorkSpecV1,
    attempt_fence: AttemptFenceV1,
    command_ref: str,
    effect_intent_ref: str,
    effect_fence_ref: str,
    candidate_ref: str,
    effect_authorization_ref: str,
    effect_authorization_digest: str,
    expires_at: str,
    validation_requirement_digest: str,
    review_requirement_digest: str,
    capsule_profile_ref: str,
    redaction_profile_ref: str,
    effect_ceilings: CeilingsV1,
) -> tuple[WorkerCommandV1, EffectFenceV1]
```

It first checks WorkSpec/AttemptFence coherence, derives duplicated bindings
from the supplied values, constructs the private command identity containing
`effect_fence_ref`, computes `command_digest`, constructs and seals the actual
author fence with that command digest, completes the command with both stored
digests, validates the actual authoring relation, and returns only the two
complete values. The author fence has a null capsule binding and three null
cancellation-target fields.

## Non-Author EffectFence Factory

`create_effect_fence(...)` accepts the actual AttemptFence, originating author
command, and actual post-bound author fence. It rejects `author_candidate`.
Validation, review, and local-Git semantic fences require the exact bound
capsule manifest. Cancellation requires the actual immutable target
EffectFence. Cancellation targeting authoring has a null capsule binding;
cancellation targeting validation or review binds the exact target manifest
digest. Creating a fence neither verifies standing authority nor authorizes or
executes an effect.

The local-Git semantic ceiling remains exactly one local commit and zero pushes,
pull requests, merges, and deployments. C2A1 creates only the pure value and
coherence relation; it performs no Git operation and makes no acceptance
decision.

## Capsule Manifest And Binary Blobs

`CandidateCapsuleManifestV1.create(...)` accepts exact built-in
`before_blobs`, `after_blobs`, and `modes` dictionaries keyed by the exact C2A
three-path set. Blob values are exact bytes and may be arbitrary binary data.
UTF-8 validity and a final line feed are not required. Modes are exactly
`100644` or `100755`. Entries fix `operation=replace_regular_file`, remain in
exact path-code-point order, and contain only raw SHA-256 digests and byte
lengths. The factory computes the authorized-path-scope digest and portable
manifest digest entirely in memory and retains no blob bytes.

`validate_capsule_manifest_relation(...)` compares the actual manifest,
originating author records, exact path scope, and actual caller-supplied before
and after bytes. A changed byte, wrong length, wrong digest, missing key, extra
key, unrelated graph, or sibling record fails closed.

This is pure identity and coherence computation. It is not capsule sealing,
storage, retrieval, custody, or retrieval authority.

## Pure Relation Coverage

`validate_authoring_relation(...)` checks the actual WorkSpec, AttemptFence,
originating author command, and actual post-bound author fence, including all
duplicated program, revision, grant, authorization, repository, base, path,
ceiling, expiry, and global-stop relations.

`validate_effect_relation(...)` checks the current EffectFence against the
actual AttemptFence and originating author lineage, the effect-class ceiling,
narrower numeric ceilings, expiry bound, capsule binding, immutable
cancellation-target tuple, and capsule-consuming cancellation rule.

`validate_delivery_relation(...)` checks a complete DeliveryEnvelope against
the originating command, AttemptFence, actual author fence, current fence,
current-effect binding, and finite route value. Local-Git effects are not
deliverable through this first-slice envelope.

`validate_redelivery_relation(...)` first validates both complete delivery
graphs and then requires the exact redelivery delta: both
`delivery_attempt_ref` and `adapter_safe_correlation_ref` change, the excluded
self-digest is recomputed, and every other identity value remains equal. It
does not decide whether redelivery is authorized.

`validate_capsule_manifest_relation(...)` checks the actual manifest graph,
three-path scope, caller bytes, entry lengths and hashes, path-scope digest, and
portable digest.

`validate_observation_relation(...)` checks the complete observation,
delivery, current fence, originating command, AttemptFence, actual author
fence, finite kind/outcome/conditional form, direct-local or ES route/source
pair, conditional capsule relation and actual bytes where applicable,
cancellation target where applicable, and self-digest.

These validators do not verify standing grants, revocation, external-clock
freshness, ES admission, runtime lifecycle, or Coordinator durable state.

## Error And Privacy Boundary

`WorkerExecutionValueError` has exactly these stable reasons:

```text
unknown_field
missing_field
invalid_field_type
invalid_field_value
digest_mismatch
relation_mismatch
```

It carries only `reason` and `field_path`. Its message is exactly
`<reason>:<field_path>`. Field paths use a fixed schema-owned vocabulary and do
not interpolate supplied keys or values. Errors retain no raw mapping, blob,
private WorkSpec text, absolute path, endpoint, credential, prompt, transcript,
JSONL, or underlying exception text. The module adds no logging and no generic
redaction or sanitization framework.

All value representations are constant and content-free, for example
`<WorkSpecV1>` and `<AttemptFenceV1>`.

## No-I/O And Non-Authority Boundary

The source module imports only `datetime`, `hashlib`, `json`, `re`, `typing`,
and future annotations. It imports no Coordinator module, test support, Bridge,
or Execution Substrate code. It performs no filesystem, working-directory,
environment, clock acquisition, randomness, network, process, Git, or SQLite
operation. It has no hidden cache, mutable registry, logging, package entry
point, runtime caller, reader authority, or durable mutation. Its sole private
production consumer is C2B2 Slice-2 pure row reconstruction.

C2A1 does not implement executable authorization, durable state, ingest,
unknown-outcome decisions, process execution, capsule custody, Git effects, or
ES routing.

It also does not implement a worker, supervisor, process launcher, adapter,
service, API, IPC, scheduler, queue, autonomous loop, capsule store, validation
or review executor, model client, Git handler, standing-authority verifier,
observation recorder, reconciliation engine, direct-local bootstrap, or ES
submission path.

## Test And Provenance Posture

Four direct source-test modules cover values, independently literal vectors,
actual-record relations, and the finite source boundary. Existing C2A document
oracles remain evidence for the authoritative C2A contract. Tests do not become
semantic authority, runtime truth, executable permission, durable program
truth, or independent acceptance.

The C2A1 implementation role may make this tranche ready for a fresh
independent audit. It cannot perform or claim that accepting audit itself.

## Deferred Mechanics

Still deferred are raw JSON decoding, full-record wire encoding, duplicate-key
wire parsing, framing, authority issuance or verification, expiry/revocation
lookup, freshness acquisition, durable C2A state, observation ingest and
disposition, the five-condition unknown-outcome decision, retry/redelivery
authorization, reconciliation, worker launch, capsule storage/retrieval,
validation/review execution, model invocation, Git execution, direct-local
adapter behavior, ES routing, packaging/release, service/API/IPC, scheduler,
queue, and autonomous-loop mechanics.
