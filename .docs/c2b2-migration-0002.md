# C2B2 Migration 0002

Status: `CURRENT IMPLEMENTED CONTRACT` for C2B2 Slice 1 physical schema
representability and migration administration only.

This document is implementation/status evidence. The semantic owner remains
`.docs/c2b-durable-development-state.md`; cumulative packaged SQL remains the
only expected-schema authority. This document is not a second semantic
authority, a cumulative schema snapshot, or a new durable tranche identity.

## Implemented Boundary

The current application generation is 2 and the terminal catalog entry is
`0002_development_program_and_effect_state`. Its complete literal UTF-8 SQL
resource is
`src/ge_nwp_coordinator/sqlite_migrations/0002_development_program_and_effect_state.sql`:

```text
size: 154434 bytes
SHA-256: 5859f49994b1467db71911fb60db4f1cfc562af7517dc6e4d81b5b29ca44d56c
compatibility: [2,2]
destructive: false
```

Migration 0002 adds exactly nineteen STRICT tables, thirty immutable-table
UPDATE/DELETE guards, and one partial unique application index. It creates no
view and seeds no C2B row. Migration `0001_initial` bytes, checksum,
compatibility, history meaning, and schema-v1 fixture remain unchanged.

SQLite 3.37.0 or newer is required whenever a selected suffix or expected
schema prefix includes migration 0002. An older or malformed runtime fails as
`sqlite_posture_unavailable` before state-root creation, common-lock
acquisition, writable open, transaction start, or target mutation.

Fresh initialization selects `[0001, 0002]` and applies both resources and
both migration-history rows in one `BEGIN IMMEDIATE` transaction with one
planned timestamp and one commit attempt. Explicit migration from an exact
supported 0001 prefix selects only `[0002]` and uses one administrative
transaction. Ordinary product or writer open never migrates: exact 0001 is
public `UNKNOWN` until explicit migration, while exact generation-2 tip 0002 is
managed current state.

Migration completion performs sequence-scoped zero-seed verification. After
0001 on a fresh installation it verifies the original nine ordinary bootstrap
tables and the canonical clear global-stop singleton. After 0002 on either a
fresh installation or exact upgrade it verifies all nineteen C2B tables are
empty. C2B emptiness is not an ordinary exact-current invariant because a later
authorized mutation tranche may populate those tables.

Expected live schema remains derived by applying cumulative packaged SQL
through the selected terminal in an isolated database. History is installed
migration evidence, and the independently observed live schema must equal that
cumulative manifest. No schema-v2 snapshot, manifest cache, or second schema
authority exists.

## Historical Fixture Compatibility

The shared tests-only B3/B4 coherent fixture preserves its historical
schema-0001 coding-work graph, transition, fencing, replay, and global-stop
meanings. Its temporary physical database is now exact generation 2 / terminal
migration 0002. The retained tests-only writer session is generation 2, and
legacy fixture seeding leaves all nineteen C2B tables empty. The fixture imports
no C2B row/value adapter, invokes no C2B private reader, and invokes no C2B
mutation API.

## Slice-2 Cross-Reference

C2B2 Slice 2 now implements the pure private row/value source recorded in
`.docs/c2b2-pure-durable-row-values.md`. It does not change migration 0002, the
generation-2 physical schema, migration history, catalog, schema manifest, or
any Slice-1 behavior. C2B2 Slice 3 now implements the private readers recorded
in `.docs/c2b2-private-readers.md`; it likewise makes no schema or migration
change. The later VS1B tranche uses this unchanged schema for one private
route-neutral program-genesis mutation, exact replay, and readback-only recovery.

## Explicit Nonimplementation

C2B2 Slice 1 adds no pure C2B row/value source and no private nominal reader.
Slice 1 itself adds no program-initialization, author-effect, bound-effect,
decision, receipt, observation-ingest, or other C2B mutation. The later VS1B
source implements only route-neutral program genesis and its exact family
replay/readback recovery without changing this migration. Author/bound effects,
observation ingest, and all later families remain absent.

The slice adds no public DTO, package-root export, `StateStore` method,
`WriterSession` method, API, CLI, service, IPC surface, dependency, second
database, writer, lock, capability, mutation slot, or transaction controller.
It creates no worker/process/model execution, capsule custody, Git effect,
direct-local route, Execution Substrate route, Bridge behavior, scheduler,
queue, reconciler, publication, deployment, or autonomous loop.
