# C2B2 Migration 0002

Status: `CURRENT IMPLEMENTED CONTRACT` for C2B2 Slice 1 physical schema
representability and migration administration only. This document preserves
the status at that tranche's completion and separately records the current
repository status after Section 42.

This document is implementation/status evidence. The semantic owner remains
`.docs/c2b-durable-development-state.md`; cumulative packaged SQL remains the
only expected-schema authority. This document is not a second semantic
authority, a cumulative schema snapshot, or a new durable tranche identity.

## Implemented Boundary

At C2B2 Slice 1 tranche completion, application generation 2 terminated at
`0002_development_program_and_effect_state` and the package contained exactly
two production SQL migration resources. That is historical tranche status, not
the current repository tip. The current repository remains at application
generation 2, now contains exactly three production SQL migration resources in
the complete catalog
`[0001_initial, 0002_development_program_and_effect_state, 0003_cognitive_proposal_and_selection_state]`,
and terminates at `0003_cognitive_proposal_and_selection_state`. The current
production SQL resource count is `3`. Migration 0002 is an unchanged historical
prefix. C2B2 did not implement or acquire ownership of migration 0003 or the
Section 41 runtime. Migration 0002's complete literal UTF-8 SQL resource is
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

At Slice 1 tranche completion, fresh initialization selected `[0001, 0002]`
and explicit migration from an exact supported 0001 prefix selected `[0002]`.
Those are explicitly historical tranche paths. Current generation-2 fresh
initialization applies the complete catalog `[0001, 0002, 0003]` in one
`BEGIN IMMEDIATE` transaction with one planned timestamp and one commit attempt.
Current explicit migration applies `[0002, 0003]` from exact 0001 or `[0003]`
from exact 0002 in one administrative transaction. Ordinary product or writer
open never migrates: exact 0001 and exact 0002 are public `UNKNOWN` until
explicit migration, while only exact generation-2 tip 0003 is managed current
state.

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
migration 0003. The retained tests-only writer session is generation 2, and
legacy fixture seeding leaves all nineteen C2B tables and all nine cognitive
proposal-selection tables empty. The fixture imports no C2B or cognitive
row/value adapter, invokes no C2B private reader, and invokes no C2B mutation
API.

## Slice-2 Cross-Reference

C2B2 Slice 2 now implements the pure private row/value source recorded in
`.docs/c2b2-pure-durable-row-values.md`. It did not change migration 0002,
migration history, or any Slice-1 behavior when that tranche closed. C2B2 Slice
3 likewise introduced no schema or migration. Later migration 0003 does not
belong to either C2B2 slice and does not reinterpret the migration-0002 core.
VS1B uses that unchanged core for one private route-neutral program-genesis
mutation, exact replay, and readback-only recovery. C2B3D uses the same core for
one private ten-row/nine-graph-entry author-effect establishment family, exact
replay, and readback-only recovery. Section 41 separately owns the later private
pre-execution selection family carried by migration 0003.

## Explicit Nonimplementation

C2B2 Slice 1 adds no pure C2B row/value source and no private nominal reader.
Slice 1 itself adds no program-initialization, author-effect, bound-effect,
decision, receipt, observation-ingest, or other C2B mutation. VS1B implements
route-neutral program genesis and its exact family replay/readback recovery
without changing this migration. C2B3D implements the private author-effect
establishment family without changing it. Bound effects, observation ingest,
and all later families remain absent.

The slice adds no public DTO, package-root export, `StateStore` method,
`WriterSession` method, API, CLI, service, IPC surface, dependency, second
database, writer, lock, capability, mutation slot, or transaction controller.
It creates no worker/process/model execution, capsule custody, Git effect,
direct-local route, Execution Substrate route, Bridge behavior, scheduler,
queue, reconciler, publication, deployment, or autonomous loop.
