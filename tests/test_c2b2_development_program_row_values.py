from __future__ import annotations

import hashlib
import json

import pytest

from ge_nwp_coordinator import _development_program_row_values as rows
from ge_nwp_coordinator._worker_execution_semantic_values import WorkSpecV1
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError


TIMESTAMP = "2026-08-15T12:34:56Z"
SHA = "1" * 64
OID = "2" * 40
PATHS = (
    ".docs/system_overview/hybrid_integration_architecture_adr.md",
    "PLANS.md",
    "docs_contract_test.go",
)
PATHS_JSON = '[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"]'
WORK_SPEC_BINDING_SAFE_PROJECTION_DIGEST_COLUMN = "safe_projection_digest"
WORK_SPEC_BINDING_SAFE_PROJECTION_DIGEST_INDEX = 15
WORK_SPEC_BINDING_SAFE_PROJECTION_DIGEST_REQUIRED = True
WORK_SPEC_BINDING_SAFE_PROJECTION_DIGEST_SQL_NULLABILITY = "NOT NULL"

PROGRAM_SCHEMA_DOMAIN_LEDGER = (
    ("_DEVELOPMENT_PROGRAM_HEAD_SCHEMA", "governed-execution.nwp-development-program-head.v1", "_DEVELOPMENT_PROGRAM_HEAD_DOMAIN", "governed-execution.nwp-development-program-head.v1.identity"),
    ("_DEVELOPMENT_PROGRAM_VERSION_SCHEMA", "governed-execution.nwp-development-program-version.v1", "_DEVELOPMENT_PROGRAM_VERSION_DOMAIN", "governed-execution.nwp-development-program-version.v1.identity"),
    ("_DEVELOPMENT_ACCEPTED_INTENT_REVISION_SCHEMA", "governed-execution.nwp-development-accepted-intent-revision.v1", "_DEVELOPMENT_ACCEPTED_INTENT_REVISION_DOMAIN", "governed-execution.nwp-development-accepted-intent-revision.v1.identity"),
    ("_DEVELOPMENT_WORK_ITEM_HEAD_SCHEMA", "governed-execution.nwp-development-work-item-head.v1", "_DEVELOPMENT_WORK_ITEM_HEAD_DOMAIN", "governed-execution.nwp-development-work-item-head.v1.identity"),
    ("_DEVELOPMENT_WORK_ITEM_REVISION_SCHEMA", "governed-execution.nwp-development-work-item-revision.v1", "_DEVELOPMENT_WORK_ITEM_REVISION_DOMAIN", "governed-execution.nwp-development-work-item-revision.v1.identity"),
    ("_DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_SCHEMA", "governed-execution.nwp-development-program-version-work-item.v1", "_DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_DOMAIN", "governed-execution.nwp-development-program-version-work-item.v1.identity"),
    ("_DEVELOPMENT_REVISION_EDGE_SCHEMA", "governed-execution.nwp-development-revision-edge.v1", "_DEVELOPMENT_REVISION_EDGE_DOMAIN", "governed-execution.nwp-development-revision-edge.v1.identity"),
    ("_DEVELOPMENT_WORK_SPEC_BINDING_SCHEMA", "governed-execution.nwp-development-work-spec-binding.v1", "_DEVELOPMENT_WORK_SPEC_BINDING_DOMAIN", "governed-execution.nwp-development-work-spec-binding.v1.identity"),
    ("_DEVELOPMENT_SEMANTIC_ATTEMPT_SCHEMA", "governed-execution.nwp-development-semantic-attempt.v1", "_DEVELOPMENT_SEMANTIC_ATTEMPT_DOMAIN", "governed-execution.nwp-development-semantic-attempt.v1.identity"),
)

PROGRAM_VOCABULARIES = {
    "_PROGRAM_STATES": ("active", "accepted", "terminal_rejected", "blocked"),
    "_PROGRAM_VERSION_KINDS": ("initial", "accepted", "repair", "replan", "terminal_rejected", "blocked"),
    "_WORK_STATES": ("planned", "active", "accepted", "repair_required", "terminal_rejected", "blocked"),
    "_WORK_ITEM_REVISION_KINDS": ("initial", "replan"),
    "_REVISION_EDGE_KINDS": ("accepted_intent_supersedes", "work_item_supersedes", "work_item_split", "work_item_merge"),
    "_ATTEMPT_PHASES": ("established",),
}


class _StringSubclass(str):
    pass


def _digest(domain: str, identity: dict[str, object]) -> str:
    payload = json.dumps(
        identity,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8", errors="strict")
    return hashlib.sha256(domain.encode("utf-8") + b"\0" + payload).hexdigest()


EXPECTED_COLUMNS = {
    "_DEVELOPMENT_PROGRAM_HEAD_COLUMNS": (
        "schema_id", "program_ref", "current_program_version_ref",
        "current_program_version_number", "head_revision", "program_state",
        "updated_at", "head_digest",
    ),
    "_DEVELOPMENT_PROGRAM_VERSION_COLUMNS": (
        "schema_id", "program_version_ref", "program_ref", "program_version_number",
        "program_version_kind", "creating_decision_ref", "accepted_intent_revision_ref",
        "created_at", "program_version_digest",
    ),
    "_DEVELOPMENT_ACCEPTED_INTENT_REVISION_COLUMNS": (
        "schema_id", "accepted_intent_revision_ref", "program_ref",
        "accepted_intent_revision_number", "prior_accepted_intent_revision_ref",
        "source_intent_ref", "source_intent_digest", "safe_projection_digest",
        "created_at", "accepted_intent_revision_digest",
    ),
    "_DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS": (
        "schema_id", "work_item_ref", "program_ref", "current_work_item_revision_ref",
        "current_work_item_revision_number", "head_revision", "work_state",
        "updated_at", "head_digest",
    ),
    "_DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS": (
        "schema_id", "work_item_revision_ref", "program_ref", "work_item_ref",
        "work_item_revision_number", "work_item_revision_kind",
        "prior_work_item_revision_ref", "accepted_intent_revision_ref", "created_at",
        "work_item_revision_digest",
    ),
    "_DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_COLUMNS": (
        "schema_id", "program_ref", "program_version_ref", "work_item_ref",
        "work_item_revision_ref", "membership_ordinal", "created_at",
        "membership_digest",
    ),
    "_DEVELOPMENT_REVISION_EDGE_COLUMNS": (
        "schema_id", "revision_edge_ref", "relation_key_digest", "program_ref",
        "revision_edge_kind", "from_accepted_intent_revision_ref",
        "to_accepted_intent_revision_ref", "from_work_item_revision_ref",
        "to_work_item_revision_ref", "created_at", "revision_edge_digest",
    ),
    "_DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS": (
        "schema_id", "work_spec_ref", "program_ref", "program_version_ref",
        "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref",
        "repository_ref", "base_git_object_format", "base_git_oid",
        "authorized_paths_json", "validation_requirement_ref", "review_requirement_ref",
        "privacy_classification", "work_spec_digest", "safe_projection_digest",
        "recorded_at", "work_spec_binding_digest",
    ),
    "_DEVELOPMENT_SEMANTIC_ATTEMPT_COLUMNS": (
        "schema_id", "semantic_attempt_ref", "program_ref", "program_version_ref",
        "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref",
        "attempt_number", "candidate_ref", "attempt_phase", "selection_decision_ref",
        "created_at", "semantic_attempt_digest",
    ),
}


def test_program_owner_column_tuples_are_independent_literals() -> None:
    assert {name: getattr(rows, name) for name in EXPECTED_COLUMNS} == EXPECTED_COLUMNS
    assert sum(len(columns) for columns in EXPECTED_COLUMNS.values()) == 96


def test_program_schema_domain_and_vocabulary_ledgers_are_independent_literals() -> None:
    for schema_name, schema, domain_name, domain in PROGRAM_SCHEMA_DOMAIN_LEDGER:
        assert getattr(rows, schema_name) == schema
        assert getattr(rows, domain_name) == domain
    assert {name: getattr(rows, name) for name in PROGRAM_VOCABULARIES} == PROGRAM_VOCABULARIES
    assert rows._DEVELOPMENT_WORK_SPEC_SAFE_PROJECTION_SCHEMA == "governed-execution.nwp-development-work-spec-safe-projection.v1"
    assert rows._DEVELOPMENT_WORK_SPEC_SAFE_PROJECTION_DOMAIN == "governed-execution.nwp-development-work-spec-safe-projection.v1.identity"


@pytest.mark.parametrize(
    ("factory", "columns", "domain", "digest_name", "identity"),
    (
        (
            rows.development_program_head_row_value_from_row_tuple,
            EXPECTED_COLUMNS["_DEVELOPMENT_PROGRAM_HEAD_COLUMNS"],
            "governed-execution.nwp-development-program-head.v1.identity",
            "head_digest",
            {"schema_id":"governed-execution.nwp-development-program-head.v1","program_ref":"program-1","current_program_version_ref":"version-1","current_program_version_number":1,"head_revision":0,"program_state":"active","updated_at":TIMESTAMP},
        ),
        (
            rows.development_program_version_row_value_from_row_tuple,
            EXPECTED_COLUMNS["_DEVELOPMENT_PROGRAM_VERSION_COLUMNS"],
            "governed-execution.nwp-development-program-version.v1.identity",
            "program_version_digest",
            {"schema_id":"governed-execution.nwp-development-program-version.v1","program_version_ref":"version-1","program_ref":"program-1","program_version_number":1,"program_version_kind":"initial","creating_decision_ref":"decision-1","accepted_intent_revision_ref":"intent-1","created_at":TIMESTAMP},
        ),
        (
            rows.development_accepted_intent_revision_row_value_from_row_tuple,
            EXPECTED_COLUMNS["_DEVELOPMENT_ACCEPTED_INTENT_REVISION_COLUMNS"],
            "governed-execution.nwp-development-accepted-intent-revision.v1.identity",
            "accepted_intent_revision_digest",
            {"schema_id":"governed-execution.nwp-development-accepted-intent-revision.v1","accepted_intent_revision_ref":"intent-1","program_ref":"program-1","accepted_intent_revision_number":1,"prior_accepted_intent_revision_ref":None,"source_intent_ref":"source-1","source_intent_digest":SHA,"safe_projection_digest":"2"*64,"created_at":TIMESTAMP},
        ),
        (
            rows.development_work_item_head_row_value_from_row_tuple,
            EXPECTED_COLUMNS["_DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS"],
            "governed-execution.nwp-development-work-item-head.v1.identity",
            "head_digest",
            {"schema_id":"governed-execution.nwp-development-work-item-head.v1","work_item_ref":"work-1","program_ref":"program-1","current_work_item_revision_ref":"work-revision-1","current_work_item_revision_number":1,"head_revision":0,"work_state":"planned","updated_at":TIMESTAMP},
        ),
        (
            rows.development_work_item_revision_row_value_from_row_tuple,
            EXPECTED_COLUMNS["_DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS"],
            "governed-execution.nwp-development-work-item-revision.v1.identity",
            "work_item_revision_digest",
            {"schema_id":"governed-execution.nwp-development-work-item-revision.v1","work_item_revision_ref":"work-revision-1","program_ref":"program-1","work_item_ref":"work-1","work_item_revision_number":1,"work_item_revision_kind":"initial","prior_work_item_revision_ref":None,"accepted_intent_revision_ref":"intent-1","created_at":TIMESTAMP},
        ),
        (
            rows.development_program_version_work_item_row_value_from_row_tuple,
            EXPECTED_COLUMNS["_DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_COLUMNS"],
            "governed-execution.nwp-development-program-version-work-item.v1.identity",
            "membership_digest",
            {"schema_id":"governed-execution.nwp-development-program-version-work-item.v1","program_ref":"program-1","program_version_ref":"version-1","work_item_ref":"work-1","work_item_revision_ref":"work-revision-1","membership_ordinal":0,"created_at":TIMESTAMP},
        ),
        (
            rows.development_revision_edge_row_value_from_row_tuple,
            EXPECTED_COLUMNS["_DEVELOPMENT_REVISION_EDGE_COLUMNS"],
            "governed-execution.nwp-development-revision-edge.v1.identity",
            "revision_edge_digest",
            {"schema_id":"governed-execution.nwp-development-revision-edge.v1","revision_edge_ref":"edge-1","relation_key_digest":"3"*64,"program_ref":"program-1","revision_edge_kind":"accepted_intent_supersedes","from_accepted_intent_revision_ref":"intent-1","to_accepted_intent_revision_ref":"intent-2","from_work_item_revision_ref":None,"to_work_item_revision_ref":None,"created_at":TIMESTAMP},
        ),
        (
            rows.development_semantic_attempt_row_value_from_row_tuple,
            EXPECTED_COLUMNS["_DEVELOPMENT_SEMANTIC_ATTEMPT_COLUMNS"],
            "governed-execution.nwp-development-semantic-attempt.v1.identity",
            "semantic_attempt_digest",
            {"schema_id":"governed-execution.nwp-development-semantic-attempt.v1","semantic_attempt_ref":"attempt-1","program_ref":"program-1","program_version_ref":"version-1","accepted_intent_revision_ref":"intent-1","work_item_ref":"work-1","work_item_revision_ref":"work-revision-1","attempt_number":1,"candidate_ref":"candidate-1","attempt_phase":"established","selection_decision_ref":"decision-1","created_at":TIMESTAMP},
        ),
    ),
)
def test_eight_program_rows_verify_literal_golden_vectors(
    factory: object,
    columns: tuple[str, ...],
    domain: str,
    digest_name: str,
    identity: dict[str, object],
) -> None:
    digest = _digest(domain, identity)
    physical = dict(identity)
    physical[digest_name] = digest
    value = factory(tuple(physical[column] for column in columns))
    assert value.identity_mapping() == identity
    assert value.computed_digest() == digest
    assert getattr(value, digest_name) == digest


def _work_spec() -> WorkSpecV1:
    return WorkSpecV1.create(
        work_spec_ref="work-spec-1",
        program_ref="program-1",
        program_version_ref="version-1",
        accepted_intent_revision_ref="intent-1",
        work_item_ref="work-1",
        work_item_revision_ref="work-revision-1",
        repository_ref="repository-1",
        base_git_oid=OID,
        authorized_paths=list(PATHS),
        objective="PRIVATE OBJECTIVE SENTINEL",
        requirements=["PRIVATE REQUIREMENT SENTINEL"],
        exclusions=["PRIVATE EXCLUSION SENTINEL"],
        validation_requirement_ref="validation-1",
        review_requirement_ref="review-1",
    )


def _work_spec_binding_row() -> tuple[object, ...]:
    work_spec = _work_spec()
    projection_identity = {
        "schema_id":"governed-execution.nwp-development-work-spec-safe-projection.v1",
        "work_spec_ref":"work-spec-1","program_ref":"program-1",
        "program_version_ref":"version-1","accepted_intent_revision_ref":"intent-1",
        "work_item_ref":"work-1","work_item_revision_ref":"work-revision-1",
        "repository_ref":"repository-1","base_git_object_format":"sha1",
        "base_git_oid":OID,"authorized_paths":PATHS,
        "validation_requirement_ref":"validation-1","review_requirement_ref":"review-1",
        "privacy_classification":"private_work_spec","work_spec_digest":work_spec.work_spec_digest,
    }
    safe_digest = _digest(
        "governed-execution.nwp-development-work-spec-safe-projection.v1.identity",
        projection_identity,
    )
    binding_identity = {
        "schema_id":"governed-execution.nwp-development-work-spec-binding.v1",
        "work_spec_ref":"work-spec-1","program_ref":"program-1",
        "program_version_ref":"version-1","accepted_intent_revision_ref":"intent-1",
        "work_item_ref":"work-1","work_item_revision_ref":"work-revision-1",
        "repository_ref":"repository-1","base_git_object_format":"sha1",
        "base_git_oid":OID,"authorized_paths_json":PATHS_JSON,
        "validation_requirement_ref":"validation-1","review_requirement_ref":"review-1",
        "privacy_classification":"private_work_spec","work_spec_digest":work_spec.work_spec_digest,
        "safe_projection_digest":safe_digest,"recorded_at":TIMESTAMP,
    }
    physical = dict(binding_identity)
    physical["work_spec_binding_digest"] = _digest(
        "governed-execution.nwp-development-work-spec-binding.v1.identity",
        binding_identity,
    )
    return tuple(
        physical[column]
        for column in EXPECTED_COLUMNS["_DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS"]
    )


def _binding_identity_from_physical_row(
    row: tuple[object, ...],
) -> dict[str, object]:
    identity_columns = EXPECTED_COLUMNS["_DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS"][:-1]
    return dict(zip(identity_columns, row[:-1], strict=True))


def _assert_exact_work_spec_binding_integrity_error(
    row: tuple[object, ...],
) -> None:
    with pytest.raises(SQLiteMutationStoreError) as caught:
        rows.development_work_spec_binding_row_value_from_row_tuple(row)
    error = caught.value
    assert type(error) is SQLiteMutationStoreError
    assert error.args == ("database_integrity_failure",)
    assert str(error) == "database_integrity_failure"
    assert repr(error) == "SQLiteMutationStoreError('database_integrity_failure')"
    assert error.internal_detail is None
    assert error.__cause__ is None
    assert error.__context__ is None
    assert getattr(error, "__notes__", None) is None
    current = error.__traceback__
    while current is not None:
        frame = current.tb_frame
        if frame.f_code.co_filename.rsplit("/", 1)[-1] == (
            "_development_program_row_values.py"
        ):
            assert all(value is not row for value in frame.f_locals.values())
            assert not any(isinstance(value, dict) for value in frame.f_locals.values())
            assert "PRIVATE" not in repr(frame.f_locals)
        current = current.tb_next


def test_work_spec_safe_projection_and_outer_binding_have_distinct_identities() -> None:
    work_spec = _work_spec()
    projection = rows.development_work_spec_safe_projection_from_work_spec(work_spec=work_spec)
    projection_identity = {
        "schema_id":"governed-execution.nwp-development-work-spec-safe-projection.v1",
        "work_spec_ref":"work-spec-1","program_ref":"program-1",
        "program_version_ref":"version-1","accepted_intent_revision_ref":"intent-1",
        "work_item_ref":"work-1","work_item_revision_ref":"work-revision-1",
        "repository_ref":"repository-1","base_git_object_format":"sha1",
        "base_git_oid":OID,"authorized_paths":PATHS,
        "validation_requirement_ref":"validation-1","review_requirement_ref":"review-1",
        "privacy_classification":"private_work_spec","work_spec_digest":work_spec.work_spec_digest,
    }
    expected_projection_digest = _digest(
        "governed-execution.nwp-development-work-spec-safe-projection.v1.identity",
        projection_identity,
    )
    assert projection.identity_mapping() == projection_identity
    assert projection.safe_projection_digest == expected_projection_digest
    assert "PRIVATE" not in repr(projection)
    assert "PRIVATE" not in repr(projection._values)
    assert all(value is not work_spec for value in projection._values)

    binding_identity = {
        "schema_id":"governed-execution.nwp-development-work-spec-binding.v1",
        "work_spec_ref":"work-spec-1","program_ref":"program-1",
        "program_version_ref":"version-1","accepted_intent_revision_ref":"intent-1",
        "work_item_ref":"work-1","work_item_revision_ref":"work-revision-1",
        "repository_ref":"repository-1","base_git_object_format":"sha1",
        "base_git_oid":OID,"authorized_paths_json":PATHS_JSON,
        "validation_requirement_ref":"validation-1","review_requirement_ref":"review-1",
        "privacy_classification":"private_work_spec","work_spec_digest":work_spec.work_spec_digest,
        "safe_projection_digest":expected_projection_digest,"recorded_at":TIMESTAMP,
    }
    outer_digest = _digest(
        "governed-execution.nwp-development-work-spec-binding.v1.identity",
        binding_identity,
    )
    physical = dict(binding_identity)
    physical["work_spec_binding_digest"] = outer_digest
    binding = rows.development_work_spec_binding_row_value_from_row_tuple(
        tuple(physical[column] for column in EXPECTED_COLUMNS["_DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS"])
    )
    assert binding.safe_projection == projection
    assert binding.identity_mapping() == binding_identity
    assert binding.computed_digest() == outer_digest


def test_work_spec_binding_valid_persisted_component_and_outer_control() -> None:
    row = _work_spec_binding_row()
    assert EXPECTED_COLUMNS["_DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS"][15] == (
        WORK_SPEC_BINDING_SAFE_PROJECTION_DIGEST_COLUMN
    )
    assert WORK_SPEC_BINDING_SAFE_PROJECTION_DIGEST_INDEX == 15
    assert WORK_SPEC_BINDING_SAFE_PROJECTION_DIGEST_REQUIRED is True
    assert WORK_SPEC_BINDING_SAFE_PROJECTION_DIGEST_SQL_NULLABILITY == "NOT NULL"
    value = rows.development_work_spec_binding_row_value_from_row_tuple(row)
    assert value.safe_projection.safe_projection_digest == row[15]
    assert value.work_spec_binding_digest == row[17]


def test_tn_09_missing_persisted_safe_projection_digest_cannot_be_synthesized() -> None:
    valid_row = _work_spec_binding_row()
    expected_component_digest = valid_row[15]
    expected_outer_digest = _digest(
        "governed-execution.nwp-development-work-spec-binding.v1.identity",
        _binding_identity_from_physical_row(valid_row),
    )
    assert valid_row[17] == expected_outer_digest
    assert type(expected_component_digest) is str
    malformed = list(valid_row)
    malformed[WORK_SPEC_BINDING_SAFE_PROJECTION_DIGEST_INDEX] = None
    malformed[17] = expected_outer_digest
    _assert_exact_work_spec_binding_integrity_error(tuple(malformed))


def test_work_spec_binding_rejects_wrong_component_with_consistent_outer_digest() -> None:
    valid_row = _work_spec_binding_row()
    incorrect_component_digest = "0" * 64
    assert incorrect_component_digest != valid_row[15]
    malformed = list(valid_row)
    malformed[WORK_SPEC_BINDING_SAFE_PROJECTION_DIGEST_INDEX] = (
        incorrect_component_digest
    )
    malformed_tuple = tuple(malformed)
    malformed[17] = _digest(
        "governed-execution.nwp-development-work-spec-binding.v1.identity",
        _binding_identity_from_physical_row(malformed_tuple),
    )
    _assert_exact_work_spec_binding_integrity_error(tuple(malformed))


def test_work_spec_binding_rejects_wrong_outer_with_correct_component_digest() -> None:
    valid_row = _work_spec_binding_row()
    malformed = list(valid_row)
    assert type(malformed[WORK_SPEC_BINDING_SAFE_PROJECTION_DIGEST_INDEX]) is str
    malformed[17] = "0" * 64
    assert malformed[17] != valid_row[17]
    _assert_exact_work_spec_binding_integrity_error(tuple(malformed))


@pytest.mark.parametrize(
    ("index", "replacement"),
    (
        (0, "governed-execution.nwp-development-program-head.v2"),
        (1, _StringSubclass("program-1")),
        (1, "workspace-secret"),
        (6, _StringSubclass(TIMESTAMP)),
        (6, "2026-08-15T12:34:56.1Z"),
        (6, "2026-08-15T12:34:56+00:00"),
        (7, "A" * 64),
        (7, "a" * 63),
        (7, "0" * 64),
    ),
)
def test_program_head_scalar_schema_timestamp_and_digest_counterfactuals(
    index: int,
    replacement: object,
) -> None:
    identity={"schema_id":"governed-execution.nwp-development-program-head.v1","program_ref":"program-1","current_program_version_ref":"version-1","current_program_version_number":1,"head_revision":0,"program_state":"active","updated_at":TIMESTAMP}
    row=list(tuple(identity.values())+(_digest("governed-execution.nwp-development-program-head.v1.identity",identity),))
    row[index]=replacement
    with pytest.raises(SQLiteMutationStoreError,match="^database_integrity_failure$"):
        rows.development_program_head_row_value_from_row_tuple(tuple(row))


def test_program_head_order_counterfactual_is_not_reinterpreted() -> None:
    identity={"schema_id":"governed-execution.nwp-development-program-head.v1","program_ref":"program-1","current_program_version_ref":"version-1","current_program_version_number":1,"head_revision":0,"program_state":"active","updated_at":TIMESTAMP}
    row=list(tuple(identity.values())+(_digest("governed-execution.nwp-development-program-head.v1.identity",identity),))
    row[1],row[2]=row[2],row[1]
    with pytest.raises(SQLiteMutationStoreError,match="^database_integrity_failure$"):
        rows.development_program_head_row_value_from_row_tuple(tuple(row))


@pytest.mark.parametrize(
    ("number", "prior"),
    ((1, "intent-0"), (2, None)),
)
def test_accepted_intent_prior_nullability_rejects_both_directions(
    number: int,
    prior: object,
) -> None:
    identity={"schema_id":"governed-execution.nwp-development-accepted-intent-revision.v1","accepted_intent_revision_ref":"intent-2","program_ref":"program-1","accepted_intent_revision_number":number,"prior_accepted_intent_revision_ref":prior,"source_intent_ref":"source-1","source_intent_digest":SHA,"safe_projection_digest":"2"*64,"created_at":TIMESTAMP}
    physical=dict(identity);physical["accepted_intent_revision_digest"]=_digest("governed-execution.nwp-development-accepted-intent-revision.v1.identity",identity)
    with pytest.raises(SQLiteMutationStoreError,match="^database_integrity_failure$"):
        rows.development_accepted_intent_revision_row_value_from_row_tuple(tuple(physical[column] for column in EXPECTED_COLUMNS["_DEVELOPMENT_ACCEPTED_INTENT_REVISION_COLUMNS"]))


@pytest.mark.parametrize(
    ("index", "replacement"),
    (
        (8, "sha256"),
        (9, "2" * 64),
        (9, "A" * 40),
        (10, '["PLANS.md",".docs/system_overview/hybrid_integration_architecture_adr.md","docs_contract_test.go"]'),
        (10, '[".docs/system_overview/hybrid_integration_architecture_adr.md", "PLANS.md", "docs_contract_test.go"]'),
        (15, "0" * 64),
    ),
)
def test_work_spec_binding_git_path_and_projection_counterfactuals(
    index: int,
    replacement: object,
) -> None:
    row=list(_work_spec_binding_row());row[index]=replacement
    with pytest.raises(SQLiteMutationStoreError,match="^database_integrity_failure$"):
        rows.development_work_spec_binding_row_value_from_row_tuple(tuple(row))


class _ForbiddenWorkSpecProbe:
    def __getattribute__(self, name: str) -> object:
        if name in {"objective", "requirements", "exclusions"}:
            raise AssertionError("PRIVATE_WORKSPEC_PROPERTY_WAS_ACCESSED")
        return object.__getattribute__(self, name)


def test_work_spec_projection_requires_exact_type_before_any_property_access() -> None:
    with pytest.raises(SQLiteMutationStoreError,match="^database_integrity_failure$"):
        rows.development_work_spec_safe_projection_from_work_spec(
            work_spec=_ForbiddenWorkSpecProbe()
        )


@pytest.mark.parametrize(
    "mutator",
    (
        lambda row: row[:3] + (True,) + row[4:],
        lambda row: row[:5] + ("unknown",) + row[6:],
        lambda row: row[:6] + ("2026-02-30T00:00:00Z",) + row[7:],
        lambda row: list(row),
    ),
)
def test_program_head_counterfactuals_reduce_to_safe_integrity_error(mutator: object) -> None:
    identity={"schema_id":"governed-execution.nwp-development-program-head.v1","program_ref":"program-1","current_program_version_ref":"version-1","current_program_version_number":1,"head_revision":0,"program_state":"active","updated_at":TIMESTAMP}
    row=tuple(identity[column] for column in EXPECTED_COLUMNS["_DEVELOPMENT_PROGRAM_HEAD_COLUMNS"][:-1])+(_digest("governed-execution.nwp-development-program-head.v1.identity",identity),)
    with pytest.raises(SQLiteMutationStoreError,match="^database_integrity_failure$"):
        rows.development_program_head_row_value_from_row_tuple(mutator(row))
