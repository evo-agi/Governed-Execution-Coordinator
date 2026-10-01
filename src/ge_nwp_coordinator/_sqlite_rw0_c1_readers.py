"""Guarded private RW0-C1 readers over one mutation read capability."""

from __future__ import annotations

from dataclasses import dataclass
import datetime
import hashlib
import json
import re
import typing

from . import _worker_execution_semantic_values as _worker_values
from ._rw0_c1_row_values import RW0C1RowValue, rw0_c1_row_value_from_tuple
from ._sqlite_rw0_c1_reader_contracts import (
    AUTHORITY_EFFECT_CLASSES,
    AUTHORITY_EFFECT_CLASSES_BY_DIGEST,
    C2A_EVIDENCE_REFS,
    C2A_EVIDENCE_REFS_BY_DIGEST,
    EVIDENCE_BY_KIND_DIGEST,
    EVIDENCE_BY_KIND_REF,
    MEMBERSHIP_BY_DIGEST,
    MEMBERSHIP_BY_PHASE_KIND_DIGEST,
    MEMBERSHIP_BY_PHASE_KIND_REF,
    MEMBERSHIP_BY_REF,
    MEMBERSHIP_PAGE,
    OPERANDS_FOR_RELATION,
    PHASE_BY_DIGEST,
    PHASE_BY_K8,
    PHASE_BY_PAIR,
    PHASE_BY_REF,
    RECEIPT_BY_MUTATION_REF,
    RELATION_BY_DIGEST,
    RELATION_BY_REF,
    RELATIONS_FOR_MEMBERSHIP,
    RELATIONS_FOR_PHASE,
    SECTION41_POST_EXECUTION_EVIDENCE_FAMILY,
    TYPED_VALUE_BY_KIND_REF,
    TYPED_VALUE_BY_KIND_DIGEST,
    OWNER_DEVELOPMENT_SELECT_BY_ROLE,
    RW0C1SelectSpecification,
)
from .sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from .sqlite_transition_select_support import _execute_select_fetch_bounded


__all__: tuple[str, ...] = ()


_SAFE_REF_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]*\Z")
_DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_SHA1_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
_RESERVED_SAFE_REF_PREFIXES = (
    "connector-",
    "tunnel-",
    "workspace-",
    "org-",
    "organization-",
    "user-",
)
_FIXED_SAFE_PATHS = (
    ".docs/system_overview/hybrid_integration_architecture_adr.md",
    "PLANS.md",
    "docs_contract_test.go",
)
_FIXED_SAFE_PATHS_JSON = (
    '[".docs/system_overview/hybrid_integration_architecture_adr.md",'
    '"PLANS.md","docs_contract_test.go"]'
)
_EFFECT_CLASSES = (
    "author_candidate",
    "cancel_effect",
    "local_git_commit",
    "review_candidate",
    "validate_candidate",
)
_CEILING_FIELDS = (
    "max_active_invocations",
    "max_candidate_bytes",
    "max_changed_files",
    "max_cost_microusd",
    "max_cpu_seconds",
    "max_deliveries",
    "max_deployments",
    "max_local_commits",
    "max_memory_bytes",
    "max_merges",
    "max_model_input_tokens",
    "max_model_output_tokens",
    "max_pull_requests",
    "max_pushes",
    "max_wall_seconds",
)
_POST_EXECUTION_EVIDENCE = (
    ("candidate_capsule", 5, 1),
    ("worker_result", 6, 1),
    ("validation_result", 7, 1),
    ("independent_review", 8, 1),
    ("standing_policy", 9, 1),
    ("risk_lane", 10, 1),
    ("authority_currentness_attestation", 11, 1),
    ("global_stop", 12, 1),
    ("effect_ceiling", 13, 1),
)


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1OwnerRowSnapshot:
    """Literal, privacy-safe snapshot of one validated immutable owner row."""

    owner_role: str
    columns: tuple[str, ...]
    values: tuple[object, ...]
    semantic_value: object | None = None
    wrapper_schema_id: str | None = None

    def __post_init__(self) -> None:
        if (
            type(self.owner_role) is not str
            or type(self.columns) is not tuple
            or type(self.values) is not tuple
            or len(self.columns) != len(self.values)
            or len(set(self.columns)) != len(self.columns)
            or any(type(column) is not str for column in self.columns)
        ):
            raise _database_integrity_failure() from None

    def value(self, column: str) -> object:
        try:
            return self.values[self.columns.index(column)]
        except (ValueError, IndexError):
            raise _database_integrity_failure() from None

    def to_mapping(self) -> dict[str, object]:
        return dict(zip(self.columns, self.values, strict=True))

    def __repr__(self) -> str:
        return "<RW0C1OwnerRowSnapshot>"


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1RelationAggregate:
    binding: RW0C1RowValue
    operands: tuple[RW0C1RowValue, ...]

    def __post_init__(self) -> None:
        if self.binding.table_name != "rw0_relation_bindings":
            raise _database_integrity_failure() from None
        expected = self.binding.value("operand_count")
        if type(expected) is not int or expected != len(self.operands) or expected > 14:
            raise _database_integrity_failure() from None
        for ordinal, operand in enumerate(self.operands):
            if (
                operand.table_name != "rw0_relation_operands"
                or operand.value("operand_ordinal") != ordinal
                or operand.value("relation_ref") != self.binding.value("relation_ref")
                or operand.value("relation_digest") != self.binding.value("relation_digest")
                or operand.value("phase_basis_ref") != self.binding.value("phase_basis_ref")
            ):
                raise _database_integrity_failure() from None

    def __repr__(self) -> str:
        return "<RW0C1RelationAggregate>"


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1RelationSetAggregate:
    relations: tuple[RW0C1RelationAggregate, ...]

    def __post_init__(self) -> None:
        if len(self.relations) > 2:
            raise _database_integrity_failure() from None
        if tuple(item.binding.value("relation_rank") for item in self.relations) != tuple(range(len(self.relations))):
            raise _database_integrity_failure() from None

    def __repr__(self) -> str:
        return "<RW0C1RelationSetAggregate>"


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1TypedEvidenceAggregate:
    registry: RW0C1RowValue
    payload: RW0C1RowValue
    children: tuple[RW0C1RowValue, ...]

    def __post_init__(self) -> None:
        kind_rank = self.registry.value("kind_rank")
        if (
            self.registry.table_name != "rw0_evidence_values"
            or type(kind_rank) is not int
            or not 1 <= kind_rank <= 15
            or self.payload.table_name != TYPED_VALUE_BY_KIND_REF[kind_rank - 1].table_name
        ):
            raise _database_integrity_failure() from None
        for column in ("kind_rank", "value_ref", "value_digest", "value_schema_id"):
            if self.registry.value(column) != self.payload.value(column):
                raise _database_integrity_failure() from None
        if kind_rank == 1:
            expected = self.payload.value("allowed_effect_class_count")
            child_table = "rw0_authority_observation_effect_classes"
        elif kind_rank == 12:
            expected = self.payload.value("evidence_ref_count")
            child_table = "rw0_c2a_worker_observation_evidence_refs"
        else:
            expected = 0
            child_table = ""
        if type(expected) is not int or expected != len(self.children):
            raise _database_integrity_failure() from None
        for ordinal, child in enumerate(self.children):
            if (
                child.table_name != child_table
                or child.value("ordinal") != ordinal
                or child.value("kind_rank") != kind_rank
                or child.value("value_ref") != self.registry.value("value_ref")
                or child.value("value_digest") != self.registry.value("value_digest")
            ):
                raise _database_integrity_failure() from None

    def __repr__(self) -> str:
        return "<RW0C1TypedEvidenceAggregate>"


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1MembershipFamily:
    phase: RW0C1RowValue
    typed_evidence: RW0C1TypedEvidenceAggregate
    membership: RW0C1RowValue
    relation_set: RW0C1RelationSetAggregate

    def __post_init__(self) -> None:
        kind_rank = self.membership.value("kind_rank")
        expected_relation_counts = (
            {0}
            if kind_rank in {5, 7}
            else ({1, 2} if kind_rank == 12 else {1})
        )
        if (
            self.phase.table_name != "rw0_phase_instances"
            or self.membership.table_name != "rw0_evidence_memberships"
            or self.phase.value("phase_basis_ref") != self.membership.value("phase_basis_ref")
            or self.phase.value("phase_basis_digest") != self.membership.value("phase_basis_digest")
            or len(self.relation_set.relations) not in expected_relation_counts
        ):
            raise _database_integrity_failure() from None
        registry = self.typed_evidence.registry
        for column in ("kind_rank", "value_ref", "value_digest", "value_schema_id"):
            if registry.value(column) != self.membership.value(column):
                raise _database_integrity_failure() from None
        for relation in self.relation_set.relations:
            binding = relation.binding
            if (
                binding.value("subject_type") != "evidence_membership"
                or binding.value("subject_membership_ref") != self.membership.value("membership_ref")
                or binding.value("subject_membership_digest") != self.membership.value("membership_digest")
            ):
                raise _database_integrity_failure() from None

    def __repr__(self) -> str:
        return "<RW0C1MembershipFamily>"


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1MembershipPage:
    entries: tuple[tuple[int, str, str], ...]
    next_cursor: tuple[int, str] | None

    def __repr__(self) -> str:
        return "<RW0C1MembershipPage>"


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1Section41PostExecutionEvidenceFamily:
    rows: tuple[RW0C1OwnerRowSnapshot, ...]

    def __post_init__(self) -> None:
        if type(self.rows) is not tuple or len(self.rows) not in {0, 9}:
            raise _database_integrity_failure() from None
        if not self.rows:
            return
        proposal_ref = self.rows[0].value("proposal_ref")
        evidence_set_ref = self.rows[0].value("evidence_set_ref")
        for row, (role, rank, required) in zip(
            self.rows, _POST_EXECUTION_EVIDENCE, strict=True
        ):
            if (
                type(row) is not RW0C1OwnerRowSnapshot
                or row.owner_role
                != "development_model_proposal_evidence_binding"
                or row.value("proposal_ref") != proposal_ref
                or row.value("proposal_phase")
                != "post_execution_semantic_review"
                or row.value("evidence_set_ref") != evidence_set_ref
                or row.value("evidence_role") != role
                or row.value("role_rank") != rank
                or row.value("ordinal") != 0
                or row.value("required_for_selection") != required
            ):
                raise _database_integrity_failure() from None

    def __repr__(self) -> str:
        return "<RW0C1Section41PostExecutionEvidenceFamily>"


def _safe_ref(value: object) -> str:
    if (
        type(value) is not str
        or not 1 <= len(value) <= 96
        or _SAFE_REF_PATTERN.fullmatch(value) is None
        or value.lower().startswith(_RESERVED_SAFE_REF_PREFIXES)
    ):
        raise _database_integrity_failure() from None
    return value


def _digest(value: object) -> str:
    if type(value) is not str or _DIGEST_PATTERN.fullmatch(value) is None:
        raise _database_integrity_failure() from None
    return value


def _timestamp(value: object) -> str:
    try:
        if (
            type(value) is not str
            or len(value) != 20
            or value[4] != "-"
            or value[7] != "-"
            or value[10] != "T"
            or value[13] != ":"
            or value[16] != ":"
            or value[19] != "Z"
            or not (
                value[0:4]
                + value[5:7]
                + value[8:10]
                + value[11:13]
                + value[14:16]
                + value[17:19]
            ).isdigit()
        ):
            raise ValueError
        parsed = datetime.datetime(
            int(value[0:4]),
            int(value[5:7]),
            int(value[8:10]),
            int(value[11:13]),
            int(value[14:16]),
            int(value[17:19]),
            tzinfo=datetime.timezone.utc,
        )
        rendered = (
            f"{parsed.year:04d}-{parsed.month:02d}-{parsed.day:02d}T"
            f"{parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d}Z"
        )
        if rendered != value:
            raise ValueError
    except (TypeError, ValueError, OverflowError):
        raise _database_integrity_failure() from None
    return value


def _canonical_digest(domain: str, value: object) -> str:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8", errors="strict")
    except (TypeError, ValueError, UnicodeError):
        raise _database_integrity_failure() from None
    return hashlib.sha256(domain.encode("utf-8") + b"\x00" + encoded).hexdigest()


def _kind_rank(value: object) -> int:
    if type(value) is not int or not 1 <= value <= 15:
        raise _database_integrity_failure() from None
    return value


def _optional_row(
    capability: object,
    specification: RW0C1SelectSpecification,
    parameters: tuple[object, ...],
) -> RW0C1RowValue | None:
    rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=specification.sql,
        parameters=parameters,
        limit=specification.fetch_limit,
    )
    if len(rows) == 0:
        return None
    if len(rows) != 1:
        raise _database_integrity_failure() from None
    try:
        return rw0_c1_row_value_from_tuple(specification.table_name, rows[0])
    except Exception:
        raise _database_integrity_failure() from None


def _aggregate_rows(
    capability: object,
    specification: RW0C1SelectSpecification,
    parameters: tuple[object, ...],
    *,
    overflow_at: int,
) -> tuple[RW0C1RowValue, ...]:
    rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=specification.sql,
        parameters=parameters,
        limit=specification.fetch_limit,
    )
    if len(rows) >= overflow_at:
        raise _database_integrity_failure() from None
    result: list[RW0C1RowValue] = []
    try:
        for row in rows:
            result.append(rw0_c1_row_value_from_tuple(specification.table_name, row))
    except Exception:
        raise _database_integrity_failure() from None
    return tuple(result)


def _read_receipt(capability: object, mutation_ref: object) -> RW0C1RowValue | None:
    return _optional_row(capability, RECEIPT_BY_MUTATION_REF, (_safe_ref(mutation_ref),))


def _read_phase_by_ref(capability: object, phase_basis_ref: object) -> RW0C1RowValue | None:
    return _optional_row(capability, PHASE_BY_REF, (_safe_ref(phase_basis_ref),))


def _read_phase_by_pair(
    capability: object, phase_basis_ref: object, phase_basis_digest: object,
) -> RW0C1RowValue | None:
    return _optional_row(
        capability, PHASE_BY_PAIR, (_safe_ref(phase_basis_ref), _digest(phase_basis_digest))
    )


def _read_phase_by_digest(capability: object, phase_basis_digest: object) -> RW0C1RowValue | None:
    return _optional_row(capability, PHASE_BY_DIGEST, (_digest(phase_basis_digest),))


def _read_phase_by_k8(capability: object, k8: tuple[object, ...]) -> RW0C1RowValue | None:
    if type(k8) is not tuple or len(k8) != 8:
        raise _database_integrity_failure() from None
    return _optional_row(capability, PHASE_BY_K8, tuple(_safe_ref(value) for value in k8))


def _read_registry_by_kind_ref(
    capability: object, kind_rank: object, value_ref: object,
) -> RW0C1RowValue | None:
    return _optional_row(
        capability, EVIDENCE_BY_KIND_REF, (_kind_rank(kind_rank), _safe_ref(value_ref))
    )


def _read_registry_by_kind_digest(
    capability: object, kind_rank: object, value_digest: object,
) -> RW0C1RowValue | None:
    return _optional_row(
        capability, EVIDENCE_BY_KIND_DIGEST, (_kind_rank(kind_rank), _digest(value_digest))
    )


def _read_membership_by_ref(capability: object, membership_ref: object) -> RW0C1RowValue | None:
    return _optional_row(capability, MEMBERSHIP_BY_REF, (_safe_ref(membership_ref),))


def _read_membership_by_digest(capability: object, membership_digest: object) -> RW0C1RowValue | None:
    return _optional_row(capability, MEMBERSHIP_BY_DIGEST, (_digest(membership_digest),))


def _read_membership_by_phase_kind_ref(
    capability: object, phase_basis_ref: object, kind_rank: object, value_ref: object,
) -> RW0C1RowValue | None:
    return _optional_row(
        capability,
        MEMBERSHIP_BY_PHASE_KIND_REF,
        (_safe_ref(phase_basis_ref), _kind_rank(kind_rank), _safe_ref(value_ref)),
    )


def _read_membership_by_phase_kind_digest(
    capability: object, phase_basis_ref: object, kind_rank: object, value_digest: object,
) -> RW0C1RowValue | None:
    return _optional_row(
        capability,
        MEMBERSHIP_BY_PHASE_KIND_DIGEST,
        (_safe_ref(phase_basis_ref), _kind_rank(kind_rank), _digest(value_digest)),
    )


def _read_relation_by_ref(capability: object, relation_ref: object) -> RW0C1RowValue | None:
    return _optional_row(capability, RELATION_BY_REF, (_safe_ref(relation_ref),))


def _read_relation_by_digest(capability: object, relation_digest: object) -> RW0C1RowValue | None:
    return _optional_row(capability, RELATION_BY_DIGEST, (_digest(relation_digest),))


def _read_relation_set(
    capability: object,
    *,
    phase_basis_ref: object,
    membership_ref: object | None,
) -> RW0C1RelationSetAggregate:
    phase_ref = _safe_ref(phase_basis_ref)
    if membership_ref is None:
        specification = RELATIONS_FOR_PHASE
        parameters = (phase_ref,)
    else:
        specification = RELATIONS_FOR_MEMBERSHIP
        parameters = (phase_ref, _safe_ref(membership_ref))
    bindings = _aggregate_rows(
        capability, specification, parameters, overflow_at=3
    )
    relations: list[RW0C1RelationAggregate] = []
    for binding in bindings:
        operands = _aggregate_rows(
            capability,
            OPERANDS_FOR_RELATION,
            (binding.value("relation_ref"),),
            overflow_at=15,
        )
        relations.append(RW0C1RelationAggregate(binding, operands))
    return RW0C1RelationSetAggregate(tuple(relations))


def _read_relation_operands(
    capability: object,
    *,
    relation_ref: object,
) -> tuple[RW0C1RowValue, ...]:
    """Read one derived relation's bounded operand family without its parent.

    Recovery uses this independent lookup when proving complete absence.  It
    deliberately does not infer operand absence from a missing relation row,
    because damaged SQLite state may contain an orphan created outside the
    guarded Coordinator writer path.
    """

    return _aggregate_rows(
        capability,
        OPERANDS_FOR_RELATION,
        (_safe_ref(relation_ref),),
        overflow_at=15,
    )


def _read_typed_payload_by_kind_ref(
    capability: object,
    *,
    kind_rank: object,
    value_ref: object,
) -> RW0C1RowValue | None:
    rank = _kind_rank(kind_rank)
    return _optional_row(
        capability,
        TYPED_VALUE_BY_KIND_REF[rank - 1],
        (rank, _safe_ref(value_ref)),
    )


def _read_typed_payload_by_kind_digest(
    capability: object,
    *,
    kind_rank: object,
    value_digest: object,
) -> RW0C1RowValue | None:
    rank = _kind_rank(kind_rank)
    return _optional_row(
        capability,
        TYPED_VALUE_BY_KIND_DIGEST[rank - 1],
        (rank, _digest(value_digest)),
    )


def _read_typed_children_by_ref(
    capability: object,
    *,
    kind_rank: object,
    value_ref: object,
) -> tuple[RW0C1RowValue, ...]:
    rank = _kind_rank(kind_rank)
    ref = _safe_ref(value_ref)
    if rank == 1:
        return _aggregate_rows(
            capability,
            AUTHORITY_EFFECT_CLASSES,
            (ref,),
            overflow_at=16,
        )
    if rank == 12:
        return _aggregate_rows(
            capability,
            C2A_EVIDENCE_REFS,
            (ref,),
            overflow_at=258,
        )
    return ()


def _read_typed_children_by_digest(
    capability: object,
    *,
    kind_rank: object,
    value_digest: object,
) -> tuple[RW0C1RowValue, ...]:
    rank = _kind_rank(kind_rank)
    digest = _digest(value_digest)
    if rank == 1:
        return _aggregate_rows(
            capability,
            AUTHORITY_EFFECT_CLASSES_BY_DIGEST,
            (digest,),
            overflow_at=16,
        )
    if rank == 12:
        return _aggregate_rows(
            capability,
            C2A_EVIDENCE_REFS_BY_DIGEST,
            (digest,),
            overflow_at=258,
        )
    return ()


def _read_typed_evidence(
    capability: object,
    *,
    kind_rank: object,
    value_ref: object,
) -> RW0C1TypedEvidenceAggregate | None:
    rank = _kind_rank(kind_rank)
    ref = _safe_ref(value_ref)
    registry = _read_registry_by_kind_ref(capability, rank, ref)
    payload = _read_typed_payload_by_kind_ref(
        capability,
        kind_rank=rank,
        value_ref=ref,
    )
    if registry is None and payload is None:
        return None
    if registry is None or payload is None:
        raise _database_integrity_failure() from None
    children = _read_typed_children_by_ref(
        capability,
        kind_rank=rank,
        value_ref=ref,
    )
    return RW0C1TypedEvidenceAggregate(registry, payload, children)


def _read_membership_family(
    capability: object,
    *,
    phase_basis_ref: object,
    membership_ref: object,
) -> RW0C1MembershipFamily | None:
    phase_ref = _safe_ref(phase_basis_ref)
    phase = _read_phase_by_ref(capability, phase_ref)
    membership = _read_membership_by_ref(capability, membership_ref)
    if membership is None:
        return None
    if membership.value("phase_basis_ref") != phase_ref:
        return None
    if phase is None:
        raise _database_integrity_failure() from None
    typed = _read_typed_evidence(
        capability,
        kind_rank=membership.value("kind_rank"),
        value_ref=membership.value("value_ref"),
    )
    if typed is None:
        raise _database_integrity_failure() from None
    relation_set = _read_relation_set(
        capability,
        phase_basis_ref=phase_ref,
        membership_ref=membership_ref,
    )
    return RW0C1MembershipFamily(phase, typed, membership, relation_set)


def _read_membership_page(
    capability: object,
    *,
    phase_basis_ref: object,
    after_kind_rank: object,
    after_membership_ref: object,
    maximum: object,
) -> RW0C1MembershipPage:
    phase_ref = _safe_ref(phase_basis_ref)
    if type(after_kind_rank) is not int or not 0 <= after_kind_rank <= 15:
        raise _database_integrity_failure() from None
    after_ref = _safe_ref(after_membership_ref)
    if type(maximum) is not int or not 1 <= maximum <= 256:
        raise _database_integrity_failure() from None
    rows = _aggregate_rows(
        capability,
        MEMBERSHIP_PAGE,
        (phase_ref, after_kind_rank, after_kind_rank, after_ref),
        overflow_at=258,
    )
    visible = rows[:maximum]
    entries = tuple(
        (
            typing.cast(int, row.value("kind_rank")),
            typing.cast(str, row.value("membership_ref")),
            typing.cast(str, row.value("membership_digest")),
        )
        for row in visible
    )
    next_cursor = None
    if len(rows) > maximum and visible:
        last = visible[-1]
        next_cursor = (
            typing.cast(int, last.value("kind_rank")),
            typing.cast(str, last.value("membership_ref")),
        )
    return RW0C1MembershipPage(entries, next_cursor)


def _literal_mapping(
    columns: tuple[str, ...], row: object,
) -> tuple[tuple[object, ...], dict[str, object]]:
    if type(row) is not tuple or len(row) != len(columns):
        raise _database_integrity_failure() from None
    values = typing.cast(tuple[object, ...], row)
    if any(type(value) not in {str, int, type(None)} for value in values):
        raise _database_integrity_failure() from None
    return values, dict(zip(columns, values, strict=True))


def _fixed_paths(value: object) -> tuple[str, ...]:
    if value != _FIXED_SAFE_PATHS_JSON or type(value) is not str:
        raise _database_integrity_failure() from None
    return _FIXED_SAFE_PATHS


def _effect_classes_from_mask(value: object) -> tuple[str, ...]:
    if type(value) is not int or not 1 <= value <= 31:
        raise _database_integrity_failure() from None
    return tuple(
        effect_class
        for bit, effect_class in enumerate(_EFFECT_CLASSES)
        if value & (1 << bit)
    )


def _ceilings(mapping: dict[str, object], prefix: str) -> dict[str, object]:
    result = {name: mapping[prefix + name] for name in _CEILING_FIELDS}
    if any(
        type(value) is not int or not 0 <= value <= 9_223_372_036_854_775_807
        for value in result.values()
    ):
        raise _database_integrity_failure() from None
    return result


def _work_spec_owner_snapshot(
    columns: tuple[str, ...], values: tuple[object, ...], mapping: dict[str, object],
) -> RW0C1OwnerRowSnapshot:
    if (
        mapping["schema_id"]
        != "governed-execution.nwp-development-work-spec-binding.v1"
        or mapping["base_git_object_format"] != "sha1"
        or type(mapping["base_git_oid"]) is not str
        or _SHA1_PATTERN.fullmatch(mapping["base_git_oid"]) is None
        or mapping["privacy_classification"] != "private_work_spec"
    ):
        raise _database_integrity_failure() from None
    for name in (
        "work_spec_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "repository_ref",
        "validation_requirement_ref",
        "review_requirement_ref",
    ):
        _safe_ref(mapping[name])
    for name in (
        "work_spec_digest",
        "safe_projection_digest",
        "work_spec_binding_digest",
    ):
        _digest(mapping[name])
    paths = _fixed_paths(mapping["authorized_paths_json"])
    _timestamp(mapping["recorded_at"])
    projection_schema = (
        "governed-execution.nwp-development-work-spec-safe-projection.v1"
    )
    projection_identity = {
        "schema_id": projection_schema,
        "work_spec_ref": mapping["work_spec_ref"],
        "program_ref": mapping["program_ref"],
        "program_version_ref": mapping["program_version_ref"],
        "accepted_intent_revision_ref": mapping["accepted_intent_revision_ref"],
        "work_item_ref": mapping["work_item_ref"],
        "work_item_revision_ref": mapping["work_item_revision_ref"],
        "repository_ref": mapping["repository_ref"],
        "base_git_object_format": mapping["base_git_object_format"],
        "base_git_oid": mapping["base_git_oid"],
        "authorized_paths": paths,
        "validation_requirement_ref": mapping["validation_requirement_ref"],
        "review_requirement_ref": mapping["review_requirement_ref"],
        "privacy_classification": mapping["privacy_classification"],
        "work_spec_digest": mapping["work_spec_digest"],
    }
    if mapping["safe_projection_digest"] != _canonical_digest(
        projection_schema + ".identity", projection_identity
    ):
        raise _database_integrity_failure() from None
    identity = {
        name: mapping[name]
        for name in columns
        if name != "work_spec_binding_digest"
    }
    if mapping["work_spec_binding_digest"] != _canonical_digest(
        typing.cast(str, mapping["schema_id"]) + ".identity", identity
    ):
        raise _database_integrity_failure() from None
    return RW0C1OwnerRowSnapshot(
        "development_work_spec_binding", columns, values
    )


def _attempt_fence_owner_snapshot(
    columns: tuple[str, ...], values: tuple[object, ...], mapping: dict[str, object],
) -> RW0C1OwnerRowSnapshot:
    semantic = _worker_values.AttemptFenceV1.from_mapping(
        {
            "schema_id": mapping["schema_id"],
            "attempt_fence_ref": mapping["attempt_fence_ref"],
            "parent_standing_grant_ref": mapping["parent_standing_grant_ref"],
            "parent_standing_grant_digest": mapping["parent_standing_grant_digest"],
            "attempt_authorization_ref": mapping["attempt_authorization_ref"],
            "attempt_authorization_digest": mapping["attempt_authorization_digest"],
            "program_ref": mapping["program_ref"],
            "program_version_ref": mapping["program_version_ref"],
            "accepted_intent_revision_ref": mapping["accepted_intent_revision_ref"],
            "work_item_ref": mapping["work_item_ref"],
            "work_item_revision_ref": mapping["work_item_revision_ref"],
            "semantic_attempt_ref": mapping["semantic_attempt_ref"],
            "repository_ref": mapping["repository_ref"],
            "base_git_object_format": mapping["base_git_object_format"],
            "base_git_oid": mapping["base_git_oid"],
            "path_ceiling": list(_fixed_paths(mapping["path_ceiling_json"])),
            "allowed_effect_classes": list(
                _effect_classes_from_mask(mapping["allowed_effect_class_mask"])
            ),
            "aggregate_ceilings": _ceilings(mapping, "aggregate_"),
            "expires_at": mapping["expires_at"],
            "global_stop_ref": mapping["global_stop_ref"],
            "global_stop_version": mapping["global_stop_version"],
            "attempt_fence_digest": mapping["attempt_fence_digest"],
        }
    )
    _timestamp(mapping["recorded_at"])
    return RW0C1OwnerRowSnapshot(
        "development_attempt_fence", columns, values, semantic
    )


def _effect_fence_owner_snapshot(
    columns: tuple[str, ...], values: tuple[object, ...], mapping: dict[str, object],
) -> RW0C1OwnerRowSnapshot:
    semantic = _worker_values.EffectFenceV1.from_mapping(
        {
            "schema_id": mapping["schema_id"],
            "effect_fence_ref": mapping["effect_fence_ref"],
            "parent_standing_grant_ref": mapping["parent_standing_grant_ref"],
            "parent_standing_grant_digest": mapping["parent_standing_grant_digest"],
            "effect_authorization_ref": mapping["effect_authorization_ref"],
            "effect_authorization_digest": mapping["effect_authorization_digest"],
            "attempt_fence_ref": mapping["attempt_fence_ref"],
            "attempt_fence_digest": mapping["attempt_fence_digest"],
            "program_ref": mapping["program_ref"],
            "program_version_ref": mapping["program_version_ref"],
            "accepted_intent_revision_ref": mapping["accepted_intent_revision_ref"],
            "work_item_ref": mapping["work_item_ref"],
            "work_item_revision_ref": mapping["work_item_revision_ref"],
            "semantic_attempt_ref": mapping["semantic_attempt_ref"],
            "effect_intent_ref": mapping["effect_intent_ref"],
            "effect_class": mapping["effect_class"],
            "command_ref": mapping["command_ref"],
            "command_digest": mapping["command_digest"],
            "candidate_ref": mapping["candidate_ref"],
            "repository_ref": mapping["repository_ref"],
            "base_git_object_format": mapping["base_git_object_format"],
            "base_git_oid": mapping["base_git_oid"],
            "path_ceiling": list(_fixed_paths(mapping["path_ceiling_json"])),
            "effect_ceilings": _ceilings(mapping, "effect_"),
            "expires_at": mapping["expires_at"],
            "global_stop_ref": mapping["global_stop_ref"],
            "global_stop_version": mapping["global_stop_version"],
            "portable_capsule_digest": mapping["portable_capsule_digest"],
            "cancellation_target_effect_intent_ref": mapping[
                "cancellation_target_effect_intent_ref"
            ],
            "cancellation_target_effect_fence_ref": mapping[
                "cancellation_target_effect_fence_ref"
            ],
            "cancellation_target_effect_fence_digest": mapping[
                "cancellation_target_effect_fence_digest"
            ],
            "effect_fence_digest": mapping["effect_fence_digest"],
        }
    )
    _timestamp(mapping["recorded_at"])
    return RW0C1OwnerRowSnapshot(
        "development_effect_fence", columns, values, semantic
    )


def _author_command_owner_snapshot(
    columns: tuple[str, ...], values: tuple[object, ...], mapping: dict[str, object],
) -> RW0C1OwnerRowSnapshot:
    semantic = _worker_values.WorkerCommandV1.from_mapping(
        {
            "schema_id": mapping["schema_id"],
            "command_ref": mapping["command_ref"],
            "program_ref": mapping["program_ref"],
            "program_version_ref": mapping["program_version_ref"],
            "accepted_intent_revision_ref": mapping["accepted_intent_revision_ref"],
            "work_item_ref": mapping["work_item_ref"],
            "work_item_revision_ref": mapping["work_item_revision_ref"],
            "semantic_attempt_ref": mapping["semantic_attempt_ref"],
            "effect_intent_ref": mapping["effect_intent_ref"],
            "effect_class": mapping["effect_class"],
            "candidate_ref": mapping["candidate_ref"],
            "repository_ref": mapping["repository_ref"],
            "base_git_object_format": mapping["base_git_object_format"],
            "base_git_oid": mapping["base_git_oid"],
            "path_ceiling": list(_fixed_paths(mapping["path_ceiling_json"])),
            "work_spec_ref": mapping["work_spec_ref"],
            "work_spec_digest": mapping["work_spec_digest"],
            "standing_grant_ref": mapping["standing_grant_ref"],
            "standing_grant_digest": mapping["standing_grant_digest"],
            "attempt_authorization_ref": mapping["attempt_authorization_ref"],
            "attempt_authorization_digest": mapping["attempt_authorization_digest"],
            "effect_authorization_ref": mapping["effect_authorization_ref"],
            "effect_authorization_digest": mapping["effect_authorization_digest"],
            "attempt_fence_ref": mapping["attempt_fence_ref"],
            "attempt_fence_digest": mapping["attempt_fence_digest"],
            "effect_fence_ref": mapping["effect_fence_ref"],
            "effect_fence_digest": mapping["effect_fence_digest"],
            "global_stop_ref": mapping["global_stop_ref"],
            "global_stop_version": mapping["global_stop_version"],
            "validation_requirement_ref": mapping["validation_requirement_ref"],
            "validation_requirement_digest": mapping[
                "validation_requirement_digest"
            ],
            "review_requirement_ref": mapping["review_requirement_ref"],
            "review_requirement_digest": mapping["review_requirement_digest"],
            "capsule_schema_id": mapping["capsule_schema_id"],
            "capsule_profile_ref": mapping["capsule_profile_ref"],
            "effect_ceilings": _ceilings(mapping, "effect_"),
            "privacy_classification": mapping["privacy_classification"],
            "redaction_profile_ref": mapping["redaction_profile_ref"],
            "command_digest": mapping["command_digest"],
        }
    )
    _timestamp(mapping["recorded_at"])
    return RW0C1OwnerRowSnapshot(
        "development_author_command", columns, values, semantic
    )


def _delivery_attempt_owner_snapshot(
    columns: tuple[str, ...], values: tuple[object, ...], mapping: dict[str, object],
) -> RW0C1OwnerRowSnapshot:
    semantic = _worker_values.DeliveryEnvelopeV1.from_mapping(
        {
            name: mapping[name]
            for name in _worker_values.DeliveryEnvelopeV1._FIELDS
        }
    )
    kind = mapping["delivery_kind"]
    number = mapping["delivery_number"]
    predecessor = mapping["predecessor_delivery_attempt_ref"]
    if not (
        type(number) is int
        and (
            (kind == "initial" and number == 1 and predecessor is None)
            or (
                kind == "redelivery"
                and number >= 2
                and _safe_ref(predecessor) == predecessor
            )
        )
    ):
        raise _database_integrity_failure() from None
    _safe_ref(mapping["basis_decision_ref"])
    _timestamp(mapping["recorded_at"])
    _digest(mapping["delivery_attempt_digest"])
    wrapper_schema = (
        "governed-execution.nwp-development-delivery-attempt.v1"
    )
    identity = {
        "schema_id": wrapper_schema,
        "delivery_envelope_digest": semantic.delivery_envelope_digest,
        "delivery_kind": kind,
        "delivery_number": number,
        "predecessor_delivery_attempt_ref": predecessor,
        "basis_decision_ref": mapping["basis_decision_ref"],
        "recorded_at": mapping["recorded_at"],
    }
    if mapping["delivery_attempt_digest"] != _canonical_digest(
        wrapper_schema + ".identity", identity
    ):
        raise _database_integrity_failure() from None
    return RW0C1OwnerRowSnapshot(
        "development_delivery_attempt",
        columns,
        values,
        semantic,
        wrapper_schema,
    )


def _development_owner_snapshot_from_tuple(
    role: str, columns: tuple[str, ...], row: object,
) -> RW0C1OwnerRowSnapshot:
    values, mapping = _literal_mapping(columns, row)
    builders = {
        "development_work_spec_binding": _work_spec_owner_snapshot,
        "development_attempt_fence": _attempt_fence_owner_snapshot,
        "development_effect_fence": _effect_fence_owner_snapshot,
        "development_author_command": _author_command_owner_snapshot,
        "development_delivery_attempt": _delivery_attempt_owner_snapshot,
    }
    try:
        return builders[role](columns, values, mapping)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure() from None


def _section41_owner_snapshot_from_tuple(
    columns: tuple[str, ...], row: object,
) -> RW0C1OwnerRowSnapshot:
    values, mapping = _literal_mapping(columns, row)
    if (
        mapping["schema_id"]
        != "governed-execution.nwp-model-proposal-evidence-binding.v1"
        or mapping["proposal_phase"] != "post_execution_semantic_review"
        or type(mapping["evidence_role"]) is not str
        or type(mapping["role_rank"]) is not int
        or type(mapping["ordinal"]) is not int
        or mapping["ordinal"] < 0
        or mapping["required_for_selection"] not in {0, 1}
        or type(mapping["required_for_selection"]) is not int
    ):
        raise _database_integrity_failure() from None
    for name in ("proposal_ref", "evidence_set_ref", "evidence_ref"):
        _safe_ref(mapping[name])
    for name in ("evidence_digest", "evidence_binding_digest"):
        _digest(mapping[name])
    _timestamp(mapping["evidence_bound_at"])
    identity = {
        name: mapping[name]
        for name in columns
        if name != "evidence_binding_digest"
    }
    if mapping["evidence_binding_digest"] != _canonical_digest(
        typing.cast(str, mapping["schema_id"]) + ".identity", identity
    ):
        raise _database_integrity_failure() from None
    return RW0C1OwnerRowSnapshot(
        "development_model_proposal_evidence_binding", columns, values
    )


def _read_section41_post_execution_evidence_family(
    capability: object,
    *,
    proposal_ref: object,
) -> RW0C1Section41PostExecutionEvidenceFamily:
    ref = _safe_ref(proposal_ref)
    specification = SECTION41_POST_EXECUTION_EVIDENCE_FAMILY
    fetched = _execute_select_fetch_bounded(
        capability=capability,
        sql=specification.sql,
        parameters=(ref,),
        limit=specification.fetch_limit,
    )
    if len(fetched) not in {0, 9}:
        raise _database_integrity_failure() from None
    rows: list[RW0C1OwnerRowSnapshot] = []
    try:
        for raw in fetched:
            row = _section41_owner_snapshot_from_tuple(
                specification.columns, raw
            )
            if row.value("proposal_ref") != ref:
                raise ValueError("Section 41 evidence row mismatch")
            rows.append(row)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _database_integrity_failure() from None
    return RW0C1Section41PostExecutionEvidenceFamily(tuple(rows))


def _read_development_owner_row(
    capability: object,
    *,
    role: object,
    row_ref: object,
) -> object | None:
    if type(role) is not str or role not in OWNER_DEVELOPMENT_SELECT_BY_ROLE:
        raise _database_integrity_failure() from None
    specification = OWNER_DEVELOPMENT_SELECT_BY_ROLE[role]
    rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=specification.sql,
        parameters=(_safe_ref(row_ref),),
        limit=2,
    )
    if len(rows) == 0:
        return None
    if len(rows) != 1:
        raise _database_integrity_failure() from None
    try:
        return _development_owner_snapshot_from_tuple(
            role, specification.columns, rows[0]
        )
    except Exception:
        raise _database_integrity_failure() from None


def _database_integrity_failure() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)
