"""Direct C2A1 allowance, runtime nonimplementation, and provenance tests."""

from __future__ import annotations

import ast
from copy import deepcopy
import pytest
import tomllib

from c2a_contract_support import (
    AUTHORIZED_PATCH_PATHS,
    BOOTSTRAP_STOPS,
    CLAUSES,
    DOC,
    GOLDEN_BYTES,
    GOLDEN_META,
    ROOT,
    _BoundedMarkdown,
    _section,
)

EXPECTED_PRODUCTION_FILES = (
    "__init__.py",
    "_worker_execution_semantic_values.py",
    "backlog.py",
    "canonicalization.py",
    "global_stop.py",
    "lease.py",
    "models.py",
    "persistence_contracts.py",
    "reports.py",
    "sqlite_connection.py",
    "sqlite_errors.py",
    "sqlite_global_stop_event_contracts.py",
    "sqlite_global_stop_preflight_contracts.py",
    "sqlite_global_stop_readers.py",
    "sqlite_global_stop_write_contracts.py",
    "sqlite_location.py",
    "sqlite_migration.py",
    "sqlite_migrations/0001_initial.sql",
    "sqlite_migrations/0002_development_program_and_effect_state.sql",
    "sqlite_migrations/__init__.py",
    "sqlite_mutation_transaction_contracts.py",
    "sqlite_security.py",
    "sqlite_transition_dry_run_contracts.py",
    "sqlite_transition_event_contracts.py",
    "sqlite_transition_event_readers.py",
    "sqlite_transition_read_scope.py",
    "sqlite_transition_select_support.py",
    "sqlite_transition_transaction.py",
    "sqlite_transition_write_contracts.py",
    "sqlite_writer_session.py",
    "sqlite_writer_state.py",
    "state_authority_lock.py",
    "state_machine.py",
    "state_store.py",
)


EXPECTED_PUBLIC_EXPORTS = (
    "AuthorizationDecision",
    "CommittedGlobalStopUpdate",
    "CommittedTransition",
    "DependencyDecision",
    "FiniteBacklog",
    "GlobalStopApplyPreflightError",
    "GlobalStopApplyPreflightFailureReason",
    "GlobalStopConflict",
    "LEASE_SCHEMA_ID",
    "LeaseIdentityValidation",
    "LeaseRuntimeDecision",
    "LeaseRuntimeStatus",
    "SafeWriterMetadata",
    "StateStore",
    "StandingLease",
    "TransitionApplyPreflightError",
    "TransitionApplyPreflightFailureReason",
    "TransitionCommand",
    "TransitionContext",
    "TransitionConflict",
    "TransitionEvaluation",
    "TransitionEvent",
    "TransitionEventOutcome",
    "UnsupportedAuthorizationProvider",
    "WriterSessionError",
    "WriterSessionFailureReason",
    "WriterSession",
    "WorkItem",
    "WorkItemRecord",
    "WorkItemState",
    "derive_lease_runtime_decision",
    "evaluate_transition",
    "transition",
    "validate_standing_lease",
)


C2A_RUNTIME_IMPLEMENTATION_SENTINELS = (
    "first_slice_worker",
    "worker_supervisor",
    "process_launcher",
    "validation_executor",
    "review_executor",
    "git_effect_handler",
    "model_client",
    "queue_consumer",
    "autonomous_loop",
)


CURRENT_C2A1_CONTRADICTIONS = (
    "Coordinator currently launches the first-slice worker.",
    "Coordinator currently stores candidate capsules.",
    "Coordinator currently performs the first-slice Git effect.",
    "Coordinator currently routes the worker through ES.",
    "C2A1 values confer executable authority.",
    "C2A1 values write durable state.",
)


HISTORICAL_C2A_FREEZE_GENERATION = 1
HISTORICAL_C2A_FREEZE_MIGRATION = "0001_initial"
CURRENT_PHYSICAL_APPLICATION_GENERATION = 2
CURRENT_PHYSICAL_TERMINAL_MIGRATION = "0002_development_program_and_effect_state"
ABSENT_MIGRATION = "0003"
CURRENT_SCHEMA_STATUS_INVALID = "current_schema_status_invalid"

HISTORICALLY_QUALIFIED_SCHEMA_0001_WORDING = (
    "When the C2A contract was originally frozen, the current physical "
    "application generation was 1 and the terminal migration was `0001_initial`.",
    "That is the historical C2A freeze baseline, not the current physical "
    "repository state.",
    "When C2A was frozen, physical application generation 1 and terminal "
    "migration `0001_initial` were the current baseline.",
    "That schema-0001 statement is historical only.",
)

CURRENT_PHYSICAL_SCHEMA_WORDING = (
    "The current physical application generation is 2 and the current terminal "
    "migration is `0002_development_program_and_effect_state`.",
    "Migration `0001_initial` remains the preserved historical schema-v1 "
    "migration; migration 0002 is implemented by C2B2 Slice 1.",
    "C2A did not create or own migration 0002.",
    "The generation-2 physical schema is a C2B2 Slice-1 implementation fact.",
    "C2A/C2A1 semantic authority remains distinct from C2B2 physical-schema "
    "authority.",
)

CURRENT_SCHEMA_STATUS_CONTRADICTIONS = (
    "Current schema 0001",
    "current terminal migration 0001",
    "migration 0002 remains unimplemented",
    "migrations 0002 and 0003 remain unimplemented",
    "C2A owns migration 0002",
    "C2A owns current durable C2B rows",
    "migration 0003 is current",
    "current physical generation remains 1",
)

CURRENT_ABSENCE_WORDING = (
    "Migration 0003 remains absent.",
    "C2B2 pure row/value source, C2B2 private readers, C2B mutation, replay, "
    "and recovery, and C2B3 behavior remain absent; C2B3 has not started.",
    "Worker, process, or model execution, Git effects, direct-local execution, "
    "ES routing, Bridge integration, publication, service, API, and IPC also "
    "remain absent.",
)

AGENTS_CURRENT_SCHEMA_WORDING = (
    "C2B2 Slice 1 now implements the generation-2 physical schema, and "
    "`0002_development_program_and_effect_state` is the implemented current "
    "physical terminal migration.",
    "Migration 0003 remains unimplemented and deferred.",
    "C2B2 pure row/value source and private readers, C2B mutation, replay, and "
    "recovery, observation ingest, decisions, latch behavior, authority "
    "verification, worker/process execution, Git effects, direct-local "
    "behavior, and ES routing remain unimplemented.",
    "C2B3 has not started.",
)


def _current_c2a_posture_validation(text: str) -> tuple[bool, str | None]:
    parsed = _BoundedMarkdown(text)
    status = parsed.section(f"{CLAUSES[0][0]} — {CLAUSES[0][1]}", 2)
    tranche = parsed.section(f"{CLAUSES[14][0]} — {CLAUSES[14][1]}", 2)
    scoped = "\n".join(
        parsed.outside_text(*parsed.span(f"{identifier} — {title}", 2)[:2])
        for identifier, title, _, _ in CLAUSES
    )
    normalized = " ".join(text.split())
    current_schema_status_invalid = any(
        contradiction.casefold() in normalized.casefold()
        for contradiction in CURRENT_SCHEMA_STATUS_CONTRADICTIONS
    )
    diagnostic = (
        CURRENT_SCHEMA_STATUS_INVALID if current_schema_status_invalid else None
    )
    valid = (
        "C2A1 implements one internal pure no-I/O semantic-value source module"
        in " ".join(status.split())
        and "C2A1 is current only for pure internal semantic values" in tranche
        and all(contradiction not in scoped for contradiction in CURRENT_C2A1_CONTRADICTIONS)
        and all(wording in normalized for wording in HISTORICALLY_QUALIFIED_SCHEMA_0001_WORDING)
        and all(wording in normalized for wording in CURRENT_PHYSICAL_SCHEMA_WORDING)
        and all(wording in normalized for wording in CURRENT_ABSENCE_WORDING)
        and not current_schema_status_invalid
    )
    return valid, diagnostic


def _current_c2a_posture_valid(text: str) -> bool:
    valid, _diagnostic = _current_c2a_posture_validation(text)
    return valid


def _bootstrap_contract_valid(items: tuple[str, ...]) -> bool:
    return items == BOOTSTRAP_STOPS


EXACT_HISTORICAL_BASELINES = {
    "Coordinator": {
        "branch": "trunk_dev",
        "head": "e5d7e48fdf72442b0acda75cf6f56cf519c39020",
        "tree": "ba4ed0903f9eebca241d7844b2eea39abeebf770",
        "upstream": "origin/trunk_dev",
        "divergence": "0/0",
    },
    "Bridge": {
        "branch": "trunk_dev",
        "head": "ca558d7a4178822b7ead25787ceb9465cb10f9c1",
        "tree": "518a9544f38aeb615633001c166fb6ba2d98d636",
        "upstream": "origin/trunk_dev",
        "divergence": "0/0",
    },
    "Execution Substrate": {
        "branch": "trunk_dev",
        "head": "4f797fb63d3c5b95275b1455af36ebc9b695f773",
        "tree": "6ae5fdfdf066fcf1d870b204d744612217a298cf",
        "upstream": "origin/trunk_dev",
        "divergence": "0/0",
    },
}


EXACT_GOLDEN_DIGESTS = {
    "WorkSpecV1": "5ae0add98fb3b6a233b778fe165dfa7ef8d1f3c43e824dddbdb6827958360ade",
    "AttemptFenceV1": "7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e",
    "EffectFenceV1": "71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3",
    "WorkerCommandV1": "6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927",
    "DeliveryEnvelopeV1": "83e68b50759dc21746ef7b521edb8f7b61cf5446d819c8c7aa47bee048841f0e",
    "WorkerObservationV1": "b605b2779fa5b46ebff2d23d7026c643debde509c015e840608b0991f1c52a6f",
    "CandidateCapsuleManifestV1": "b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c",
}


PROVENANCE_CONTROL = {
    "changed_paths": AUTHORIZED_PATCH_PATHS,
    "repositories": deepcopy(EXACT_HISTORICAL_BASELINES),
    "goldens": {
        model: {"canonical_bytes": GOLDEN_BYTES[model], "domain_digest": EXACT_GOLDEN_DIGESTS[model]}
        for model in GOLDEN_BYTES
    },
    "implementation_role": "parent implementation role",
    "accepting_audit_role": "independent accepting auditor",
}


def _provenance_contract_valid(record: dict[str, object]) -> bool:
    if set(record) != {"changed_paths", "repositories", "goldens", "implementation_role", "accepting_audit_role"}:
        return False
    if record.get("changed_paths") != AUTHORIZED_PATCH_PATHS or record.get("repositories") != EXACT_HISTORICAL_BASELINES:
        return False
    if record.get("implementation_role") != "parent implementation role" or record.get("accepting_audit_role") != "independent accepting auditor":
        return False
    goldens = record.get("goldens")
    if not isinstance(goldens, dict) or set(goldens) != set(GOLDEN_BYTES):
        return False
    return all(
        record_for_model == {"canonical_bytes": GOLDEN_BYTES[model], "domain_digest": EXACT_GOLDEN_DIGESTS[model]}
        for model, record_for_model in goldens.items()
    )


def test_c2a_schema_0001_wording_is_historical_and_generation_2_is_current() -> None:
    assert HISTORICAL_C2A_FREEZE_GENERATION == 1
    assert HISTORICAL_C2A_FREEZE_MIGRATION == "0001_initial"
    assert CURRENT_PHYSICAL_APPLICATION_GENERATION == 2
    assert CURRENT_PHYSICAL_TERMINAL_MIGRATION == (
        "0002_development_program_and_effect_state"
    )
    assert ABSENT_MIGRATION == "0003"
    assert CURRENT_SCHEMA_STATUS_INVALID == "current_schema_status_invalid"
    assert CURRENT_SCHEMA_STATUS_CONTRADICTIONS == (
        "Current schema 0001",
        "current terminal migration 0001",
        "migration 0002 remains unimplemented",
        "migrations 0002 and 0003 remain unimplemented",
        "C2A owns migration 0002",
        "C2A owns current durable C2B rows",
        "migration 0003 is current",
        "current physical generation remains 1",
    )

    normalized = " ".join(DOC.split())
    for wording in HISTORICALLY_QUALIFIED_SCHEMA_0001_WORDING:
        assert wording in normalized
    for wording in CURRENT_PHYSICAL_SCHEMA_WORDING:
        assert wording in normalized
    assert _current_c2a_posture_validation(DOC) == (True, None)
    assert _current_c2a_posture_valid(DOC)


def test_generation_2_physical_schema_does_not_widen_c2a_or_c2b_runtime() -> None:
    nonimplementation = " ".join(
        _section(DOC, f"{CLAUSES[14][0]} — {CLAUSES[14][1]}", 2).split()
    )
    for wording in CURRENT_ABSENCE_WORDING:
        assert wording in nonimplementation
    assert (
        "C2A semantic fields, values, identities, relations, and pure-value "
        "source do not themselves create durable C2A tables or durable C2A "
        "runtime rows."
    ) in " ".join(DOC.split())


@pytest.mark.parametrize(
    "historical_wording",
    HISTORICALLY_QUALIFIED_SCHEMA_0001_WORDING,
)
def test_each_schema_0001_statement_is_explicitly_historical(
    historical_wording: str,
) -> None:
    assert historical_wording in " ".join(DOC.split())
    assert _current_c2a_posture_valid(DOC)


@pytest.mark.parametrize(
    "contradiction",
    (
        "Current schema 0001",
        "current terminal migration 0001",
        "migration 0002 remains unimplemented",
        "migrations 0002 and 0003 remain unimplemented",
        "C2A owns migration 0002",
        "C2A owns current durable C2B rows",
        "migration 0003 is current",
        "current physical generation remains 1",
    ),
    ids=(
        "unqualified-current-schema-0001",
        "current-terminal-0001",
        "migration-0002-unimplemented",
        "migrations-0002-0003-unimplemented",
        "c2a-owns-migration-0002",
        "c2a-owns-durable-c2b-rows",
        "migration-0003-current",
        "physical-generation-1-current",
    ),
)
def test_current_schema_status_contradictions_fail_closed(
    contradiction: str,
) -> None:
    assert _current_c2a_posture_validation(DOC) == (True, None)
    next_clause = f"## {CLAUSES[1][0]} — {CLAUSES[1][1]}"
    changed = DOC.replace(next_clause, contradiction + "\n\n" + next_clause, 1)
    valid, diagnostic = _current_c2a_posture_validation(changed)
    assert valid is False
    assert diagnostic == "current_schema_status_invalid"
    assert not _current_c2a_posture_valid(changed)


@pytest.mark.parametrize(
    "accepted_statement",
    (
        "Historically, C2A froze physical application generation 1 and terminal "
        "migration `0001_initial`; this is not the current physical repository state.",
        "The current physical application generation is 2.",
        "The current terminal migration is "
        "`0002_development_program_and_effect_state`.",
        "Migration 0003 remains absent and deferred.",
        "C2A does not own migration 0002.",
        "C2A does not own durable C2B rows.",
    ),
    ids=(
        "historical-generation-1-migration-0001",
        "current-generation-2",
        "current-migration-0002",
        "migration-0003-absent",
        "c2a-does-not-own-migration-0002",
        "c2a-does-not-own-durable-c2b-rows",
    ),
)
def test_current_schema_status_positive_controls_remain_accepted(
    accepted_statement: str,
) -> None:
    next_clause = f"## {CLAUSES[1][0]} — {CLAUSES[1][1]}"
    changed = DOC.replace(next_clause, accepted_statement + "\n\n" + next_clause, 1)
    assert _current_c2a_posture_validation(changed) == (True, None)
    assert _current_c2a_posture_valid(changed)


def test_agents_current_schema_status_is_consistent_with_c2a_history() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    normalized = " ".join(agents.split())
    for wording in AGENTS_CURRENT_SCHEMA_WORDING:
        assert wording in normalized
    for contradiction in CURRENT_SCHEMA_STATUS_CONTRADICTIONS:
        assert contradiction.casefold() not in normalized.casefold()


def test_worker_source_release_and_process_target_remains_nonimplemented() -> None:
    status = " ".join(_section(DOC, f"{CLAUSES[0][0]} — {CLAUSES[0][1]}", 2).split())
    assert "initial worker source and release ownership in the Coordinator repository" in status
    assert "worker execution occurs in a separate OS process" in status
    assert "This ownership and process statement is not current implementation." in status


def test_exact_c2a1_source_allowance_and_runtime_nonimplementation() -> None:
    package_dir = ROOT / "src/ge_nwp_coordinator"
    production_files = tuple(
        sorted(path.relative_to(package_dir).as_posix() for path in package_dir.rglob("*") if path.is_file() and path.suffix in {".py", ".sql"})
    )
    assert production_files == tuple(sorted(EXPECTED_PRODUCTION_FILES))

    schema_paths = tuple(sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "schemas").rglob("*") if path.is_file()))
    assert schema_paths == ("schemas/sqlite/coordinator-state-v1.sql",)
    migration_paths = tuple(sorted(path.relative_to(package_dir).as_posix() for path in (package_dir / "sqlite_migrations").rglob("*") if path.is_file()))
    assert migration_paths == (
        "sqlite_migrations/0001_initial.sql",
        "sqlite_migrations/0002_development_program_and_effect_state.sql",
        "sqlite_migrations/__init__.py",
    )

    semantic_path = package_dir / "_worker_execution_semantic_values.py"
    source_paths = tuple(path for path in package_dir.rglob("*.py") if path.is_file())
    nonsemantic_source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in source_paths
        if path != semantic_path
    )
    semantic_source = semantic_path.read_text(encoding="utf-8")
    schema_text = (ROOT / "schemas/sqlite/coordinator-state-v1.sql").read_text(encoding="utf-8") + (package_dir / "sqlite_migrations/0001_initial.sql").read_text(encoding="utf-8")
    for schema_id in EXACT_GOLDEN_DIGESTS:
        assert GOLDEN_META[schema_id][0] in semantic_source
        assert GOLDEN_META[schema_id][0] not in nonsemantic_source_text
        assert GOLDEN_META[schema_id][0] not in schema_text
    for sentinel in C2A_RUNTIME_IMPLEMENTATION_SENTINELS:
        assert sentinel not in semantic_source

    semantic_tree = ast.parse(semantic_source)
    semantic_classes = {
        node.name for node in semantic_tree.body if isinstance(node, ast.ClassDef)
    }
    semantic_functions = {
        node.name for node in semantic_tree.body if isinstance(node, ast.FunctionDef)
    }
    assert {
        "CeilingsV1",
        "CapsuleEntryV1",
        "WorkSpecV1",
        "AttemptFenceV1",
        "EffectFenceV1",
        "WorkerCommandV1",
        "DeliveryEnvelopeV1",
        "WorkerObservationV1",
        "CandidateCapsuleManifestV1",
        "WorkerExecutionValueError",
    } <= semantic_classes
    assert {
        "create_author_command_and_effect_fence",
        "create_effect_fence",
        "validate_authoring_relation",
        "validate_effect_relation",
        "validate_delivery_relation",
        "validate_redelivery_relation",
        "validate_capsule_manifest_relation",
        "validate_observation_relation",
    } <= semantic_functions

    package_root = (package_dir / "__init__.py").read_text(encoding="utf-8")
    module = ast.parse(package_root)
    export_assignments = [node for node in module.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets)]
    assert len(export_assignments) == 1
    exports = tuple(ast.literal_eval(export_assignments[0].value))
    assert exports == EXPECTED_PUBLIC_EXPORTS
    for model in GOLDEN_META:
        assert model not in exports

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["dependencies"] == []
    assert "scripts" not in pyproject["project"]
    assert "entry-points" not in pyproject["project"]

    nonimplementation = " ".join(_section(DOC, f"{CLAUSES[14][0]} — {CLAUSES[14][1]}", 2).split())
    for phrase in (
        "C2A1 is current only for pure internal semantic values and the six named pure coherence validators.",
        "C2A1 adds no SQLite table or column, durable C2A state, migration, package export, dependency, script, entry point, worker, adapter, supervisor, process, filesystem store, Git handler, network client, model client, Bridge or ES integration, scheduler, queue, service, API, IPC, reconciler, or autonomous loop",
        "C2A did not create or own migration 0002",
        "Migration 0003 remains absent.",
        "C2A assigns no migration number and authorizes no schema work.",
    ):
        assert phrase in nonimplementation


@pytest.mark.parametrize("contradiction", CURRENT_C2A1_CONTRADICTIONS)
def test_current_c2a1_contradictions_are_rejected_in_status_scope(contradiction: str) -> None:
    assert _current_c2a_posture_valid(DOC)
    next_clause = f"## {CLAUSES[1][0]} — {CLAUSES[1][1]}"
    changed = DOC.replace(next_clause, contradiction + "\n\n" + next_clause, 1)
    assert not _current_c2a_posture_valid(changed)


@pytest.mark.parametrize("index", tuple(range(len(BOOTSTRAP_STOPS))))
def test_each_bootstrap_stop_is_independently_mandatory(index: int) -> None:
    assert _bootstrap_contract_valid(BOOTSTRAP_STOPS)
    assert "production- autonomy" not in DOC
    assert BOOTSTRAP_STOPS[8] == "Any push, remote-ref mutation, PR, merge, deployment, or production-autonomy claim."
    removed = BOOTSTRAP_STOPS[:index] + BOOTSTRAP_STOPS[index + 1 :]
    assert not _bootstrap_contract_valid(removed)
    inverted = list(BOOTSTRAP_STOPS)
    inverted[index] = "Permit: " + inverted[index]
    assert not _bootstrap_contract_valid(tuple(inverted))


def test_provenance_mutations_fail_closed() -> None:
    assert _provenance_contract_valid(PROVENANCE_CONTROL)

    changed_path = deepcopy(PROVENANCE_CONTROL)
    changed_path["changed_paths"] = AUTHORIZED_PATCH_PATHS + ("src/forbidden.py",)
    assert not _provenance_contract_valid(changed_path)

    for repository, fields in EXACT_HISTORICAL_BASELINES.items():
        missing_repository = deepcopy(PROVENANCE_CONTROL)
        missing_repository["repositories"].pop(repository)
        assert not _provenance_contract_valid(missing_repository), repository
        for field in fields:
            wrong = deepcopy(PROVENANCE_CONTROL)
            wrong["repositories"][repository][field] = "wrong-but-nonempty"
            assert not _provenance_contract_valid(wrong), (repository, field)

    abbreviated_bridge = deepcopy(PROVENANCE_CONTROL)
    abbreviated_bridge["repositories"]["Bridge"]["head"] = "ca558d"
    assert not _provenance_contract_valid(abbreviated_bridge)

    unrecorded = deepcopy(PROVENANCE_CONTROL)
    unrecorded["goldens"].pop("WorkerCommandV1")
    assert not _provenance_contract_valid(unrecorded)
    wrong_digest = deepcopy(PROVENANCE_CONTROL)
    wrong_digest["goldens"]["WorkerCommandV1"]["domain_digest"] = "0" * 64
    assert not _provenance_contract_valid(wrong_digest)
    missing_bytes = deepcopy(PROVENANCE_CONTROL)
    missing_bytes["goldens"]["WorkerCommandV1"].pop("canonical_bytes")
    assert not _provenance_contract_valid(missing_bytes)
    changed_bytes = deepcopy(PROVENANCE_CONTROL)
    changed_bytes["goldens"]["WorkerCommandV1"]["canonical_bytes"] += b" "
    assert not _provenance_contract_valid(changed_bytes)

    collapsed_roles = deepcopy(PROVENANCE_CONTROL)
    collapsed_roles["accepting_audit_role"] = collapsed_roles["implementation_role"]
    assert not _provenance_contract_valid(collapsed_roles)
    wrong_roles = deepcopy(PROVENANCE_CONTROL)
    wrong_roles["implementation_role"] = "wrong-but-nonempty"
    assert not _provenance_contract_valid(wrong_roles)
