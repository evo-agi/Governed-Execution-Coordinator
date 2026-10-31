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
generation 2, now contains exactly four production SQL migration resources in
the complete catalog
`[0001_initial, 0002_development_program_and_effect_state, 0003_cognitive_proposal_and_selection_state, 0004_rw0_c1_durable_evidence]`,
and terminates at `0004_rw0_c1_durable_evidence`. The current production SQL
resource count is `4`. Migration 0002 is an unchanged historical prefix. C2B2
did not implement or acquire ownership of migration 0003, migration 0004, the
Section 41 runtime, or RW0-C1. Migration 0002's complete literal UTF-8 SQL resource is
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
initialization applies the complete catalog `[0001, 0002, 0003, 0004]` in one
`BEGIN IMMEDIATE` transaction with one planned timestamp and one commit attempt.
Current explicit migration applies `[0002, 0003, 0004]` from exact 0001,
`[0003, 0004]` from exact 0002, or `[0004]` from exact 0003 in one
administrative transaction. Ordinary product or writer open never migrates:
exact 0001, exact 0002, and exact 0003 are public `UNKNOWN` until explicit
migration, while only exact generation-2 tip 0004 is managed current state.

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
migration 0004. The retained tests-only writer session is generation 2, and
legacy fixture seeding leaves all nineteen C2B tables and all nine cognitive
proposal-selection tables and all twenty-three RW0-C1 tables empty. The fixture imports no C2B or cognitive
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

<!-- RW0_C1_CURRENT_STATUS_BEGIN -->
**Current catalog after RW0-C1.**

The current generation-2 catalog is
`[0001_initial, 0002_development_program_and_effect_state, 0003_cognitive_proposal_and_selection_state, 0004_rw0_c1_durable_evidence]`,
the short sequence is `[0001, 0002, 0003, 0004]`, and the terminal migration is
`0004_rw0_c1_durable_evidence`. The current production SQL resource count is
`4`. Migration 0002 remains an unchanged historical prefix; C2B2 did not
implement or acquire ownership of migration 0003 or migration 0004.
<!-- RW0_C1_CURRENT_STATUS_END -->

<!-- SECTION41_0005_CURRENT_CATALOG_SUCCESSOR_BEGIN -->
### Current catalog after native Section 41 post-execution admission

The complete current generation-2 catalog is
`[0001_initial, 0002_development_program_and_effect_state, 0003_cognitive_proposal_and_selection_state, 0004_rw0_c1_durable_evidence, 0005_section41_post_execution_proposal_family]`.
Its short sequence is `[0001, 0002, 0003, 0004, 0005]`, and the current
production SQL resource count is `5`. The terminal migration is
`0005_section41_post_execution_proposal_family`, adding two immutable STRICT
tables, four guards, no explicit index and no seed. Earlier statements in
this document that call 0004 the current tip describe the prior C1 tranche.
Migration 0002 remains an unchanged historical prefix and its literal oracle
above remains frozen. C2B2 did not implement or acquire ownership of
migration 0003, 0004 or 0005; Section 41 owns 0005 through
`.docs/section41-post-execution-proposal-family.md`.
<!-- SECTION41_0005_CURRENT_CATALOG_SUCCESSOR_END -->

<!-- RW0_C2_0007_CURRENT_CATALOG_SUCCESSOR_BEGIN -->
### Current workspace catalog after the RW0-C2 P0/P1 physical candidate

The complete current generation-2 workspace catalog is
`[0001_initial, 0002_development_program_and_effect_state, 0003_cognitive_proposal_and_selection_state, 0004_rw0_c1_durable_evidence, 0005_section41_post_execution_proposal_family, 0006_rw0_c2_scope_admission, 0007_rw0_c2_progression_decision]`.
Its short sequence is `[0001, 0002, 0003, 0004, 0005, 0006, 0007]` and the
current production SQL resource count is `7`. The terminal migration is
`0007_rw0_c2_progression_decision`; the cumulative schema has 74 user tables,
134 triggers, and five explicit indexes. Migration 0006 adds the four private
program-independent P0 admission tables; migration 0007 adds the six private
P1 progression supplemental tables. Both are uncommitted artificial-offline
candidate source. The predecessor 0001–0005 migrations and their literal
oracles remain unchanged. Earlier current-tip statements in this document
describe their named historical tranches. Migration 0002 remains an unchanged
historical prefix and C2B2 acquires no P0/P1 progression authority.
<!-- RW0_C2_0007_CURRENT_CATALOG_SUCCESSOR_END -->

<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->
### RW0-C2 0007 committed-source catalog status

The preceding 0007 candidate block is preserved as an exact historical
checkpoint. Independent artifact audit accepted tree `161ed4b544baf970cc26428b9805a106ea0f3edf` and local commit
`8704e6c7988250598809f3a0daf88c3e11493488` records it; neither fact changes migration 0002's prefix ownership.
The current source catalog remains seven generation-2 resources through
`0007_rw0_c2_progression_decision`, with 74 user tables, 134 triggers, and
five explicit indexes. Migration 0006 supplies four P0-only tables; migration
0007 supplies six P1 supplemental tables. Older managed prefixes still require
explicit administrative migration. This local source status implies no live
supplier, product mutation permission, or publication.
<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->

<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_BEGIN -->
## RW0 normal terminal closure current candidate

The uncommitted `artificial_offline_normal.v1` candidate adds a separate private Coordinator terminal writer on generation-2 migration 0008. It consumes checked P0, phase, Section 41 A, C1 rank-15/V22 and P1 evidence under one fenced transaction and records only the five normal outcomes: accept, repair, replan, terminal_reject and block. The P1 decision remains prior decision history; its acceptance fact is bound only for accept and is never mutated. Cancellation, live supplier/contact, ES routing, Git effects, publication and executable permission remain outside this candidate. See `.docs/rw0-terminal-outcome-physical-closure.md`.

The current contiguous catalog ends at `0008_rw0_terminal_outcome` at application generation 2, with 78 tables, 142 triggers and five explicit indexes. Exact older prefixes require explicit administrative migration; ordinary operations do not auto-migrate.
The complete current catalog is `[0001_initial, 0002_development_program_and_effect_state, 0003_cognitive_proposal_and_selection_state, 0004_rw0_c1_durable_evidence, 0005_section41_post_execution_proposal_family, 0006_rw0_c2_scope_admission, 0007_rw0_c2_progression_decision, 0008_rw0_terminal_outcome]`; its short sequence is `[0001, 0002, 0003, 0004, 0005, 0006, 0007, 0008]`. The current production SQL resource count is `8`.
<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_END -->
