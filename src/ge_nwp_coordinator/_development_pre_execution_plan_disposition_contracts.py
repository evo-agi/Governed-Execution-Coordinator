"""Pure private contracts for Section 41 pre-execution plan disposition."""

from __future__ import annotations

from dataclasses import dataclass, field, make_dataclass
from enum import Enum
import typing

from . import _cognitive_proposal_row_values as _rows
from . import _cognitive_proposal_semantic_values as _semantic
from ._cognitive_proposal_value_support import (
    _CognitiveProposalContractViolation,
    _constant_repr,
    _require_canonical_string,
    _disable_pickle,
    _domain_separated_digest,
    _exact_equal,
    _require_enum,
    _require_exact_mapping,
    _require_nonnegative_integer,
    _require_optional_safe_ref,
    _require_optional_sha256,
    _require_reason_code,
    _require_safe_ref,
    _require_sha256,
    _require_sqlite_integer,
    _require_utc_second,
    _select_exact_type,
    _violate,
    _without_field,
)


__all__ = ()


_COMMAND_SCHEMA = (
    "governed-execution.nwp-record-pre-execution-plan-disposition-command.v1"
)
_COMMAND_DOMAIN = _COMMAND_SCHEMA + ".identity"
_RESULT_SCHEMA = "governed-execution.nwp-pre-execution-plan-disposition-result.v1"
_RESULT_DOMAIN = _RESULT_SCHEMA + ".identity"
_GRAPH_DOMAIN = "governed-execution.nwp-cognitive-mutation-graph.v1.identity"
_RECOVERY_PROBE_DOMAIN = (
    "governed-execution.nwp-pre-execution-plan-disposition-recovery-probe.v1.identity"
)

_K8_FIELDS = (
    "program_ref",
    "semantic_attempt_ref",
    "candidate_ref",
    "effect_intent_ref",
    "author_command_ref",
    "attempt_fence_ref",
    "effect_fence_ref",
    "delivery_attempt_ref",
)
_L34_FIELDS = (
    "program_ref",
    "program_version_ref",
    "program_version_number",
    "accepted_intent_revision_ref",
    "work_item_ref",
    "work_item_revision_ref",
    "semantic_attempt_ref",
    "semantic_attempt_digest",
    "attempt_number",
    "candidate_ref",
    "basis_decision_ref",
    "basis_decision_digest",
    "work_spec_ref",
    "work_spec_digest",
    "work_spec_safe_projection_digest",
    "effect_intent_ref",
    "effect_intent_digest",
    "author_command_ref",
    "author_command_digest",
    "standing_grant_ref",
    "standing_grant_digest",
    "attempt_authorization_ref",
    "attempt_authorization_digest",
    "effect_authorization_ref",
    "effect_authorization_digest",
    "attempt_fence_ref",
    "attempt_fence_digest",
    "effect_fence_ref",
    "effect_fence_digest",
    "delivery_attempt_ref",
    "delivery_envelope_digest",
    "delivery_attempt_digest",
    "authority_evaluation_ref",
    "authority_evaluation_digest",
)
_RECOVERY_IDENTITY_SHAPES = (
    ("development_model_source_invocations", ("source_invocation_ref",)),
    (
        "development_model_source_invocations",
        ("proposal_phase", "source_invocation_ref"),
    ),
    ("development_pre_execution_planning_contexts", ("planning_context_ref",)),
    (
        "development_pre_execution_planning_contexts",
        ("program_ref", "planning_context_ref"),
    ),
    ("development_private_proposal_artifact_bindings", ("artifact_ref",)),
    (
        "development_private_proposal_artifact_bindings",
        ("proposal_phase", "artifact_ref"),
    ),
    ("development_model_proposals", ("proposal_ref",)),
    ("development_model_proposals", ("source_invocation_ref",)),
    ("development_model_proposals", ("artifact_ref",)),
    ("development_model_proposals", ("proposal_phase", "proposal_ref")),
    ("development_pre_execution_plan_projections", ("proposal_ref",)),
    ("development_pre_execution_plan_projections", ("artifact_ref",)),
    (
        "development_model_proposal_evidence_bindings",
        ("proposal_ref", "evidence_role", "ordinal"),
    ),
    (
        "development_model_proposal_evidence_bindings",
        ("proposal_ref", "role_rank", "ordinal"),
    ),
    ("development_pre_execution_dispositions", ("disposition_ref",)),
    (
        "development_pre_execution_dispositions",
        ("program_ref", "disposition_ref"),
    ),
    ("development_pre_execution_dispositions", ("proposal_ref",)),
    (
        "development_pre_execution_dispositions",
        (*_L34_FIELDS, "resulting_selection_head_revision"),
    ),
    (
        "development_pre_execution_dispositions",
        (*_L34_FIELDS, "prior_selection_head_revision"),
    ),
    (
        "development_pre_execution_dispositions",
        (
            *_L34_FIELDS,
            "disposition_ref",
            "resulting_selection_head_revision",
            "selection_head_postimage_digest",
        ),
    ),
    (
        "development_pre_execution_dispositions",
        (
            *_L34_FIELDS,
            "disposition_ref",
            "proposal_ref",
            "disposition",
            "resulting_selection_head_revision",
            "selection_head_postimage_digest",
        ),
    ),
    (
        "development_pre_execution_dispositions",
        (
            "program_ref",
            "disposition_ref",
            "proposal_ref",
            "effect_intent_ref",
            "resulting_selection_head_revision",
            "selection_head_postimage_digest",
        ),
    ),
    ("development_pre_execution_selection_heads", _K8_FIELDS),
    ("development_pre_execution_selection_heads", _L34_FIELDS),
    ("development_pre_execution_selection_heads", ("effect_intent_ref",)),
    (
        "development_pre_execution_selection_heads",
        ("program_ref", "effect_intent_ref"),
    ),
    (
        "development_pre_execution_selection_heads",
        (
            "program_ref",
            "effect_intent_ref",
            "current_proposal_ref",
            "current_disposition_ref",
            "head_revision",
            "head_digest",
        ),
    ),
    ("development_cognitive_mutation_receipts", ("mutation_ref",)),
    (
        "development_cognitive_mutation_receipts",
        ("program_ref", "mutation_ref"),
    ),
    ("development_cognitive_mutation_receipts", ("disposition_ref",)),
)
assert len(_RECOVERY_IDENTITY_SHAPES) == 30
_RECOVERY_PROBE_IDENTITY_SHAPES = tuple(
    (
        table,
        tuple(
            name
            for name in identity
            if not (
                table == "development_pre_execution_dispositions"
                and name == "selection_head_postimage_digest"
            )
            and not (
                table == "development_pre_execution_selection_heads"
                and name == "head_digest"
            )
        ),
    )
    for table, identity in _RECOVERY_IDENTITY_SHAPES
)
assert len(_RECOVERY_PROBE_IDENTITY_SHAPES) == 30
_COMMAND_FIELDS = (
    "schema_id",
    "mutation_ref",
    "proposal_ref",
    "proposal_digest",
    "source_invocation_ref",
    "source_invocation_digest",
    "artifact_ref",
    "artifact_digest",
    "artifact_binding_digest",
    "planning_context_ref",
    "planning_context_digest",
    "safe_projection_digest",
    "evidence_set_ref",
    "evidence_set_digest",
    "preassigned_disposition_ref",
    "expected_current_selection_revision",
    "expected_current_selection_head_digest",
    "disposition",
    "disposition_reason_code",
    "supersedes_disposition_ref",
    "program_ref",
    "semantic_attempt_ref",
    "candidate_ref",
    "effect_intent_ref",
    "author_command_ref",
    "author_command_digest",
    "attempt_fence_ref",
    "attempt_fence_digest",
    "effect_fence_ref",
    "effect_fence_digest",
    "delivery_attempt_ref",
    "delivery_envelope_digest",
    "mutation_command_digest",
)
_GRAPH_ENTRY_FIELDS = (
    "role",
    "rank",
    "ordinal",
    "table",
    "locator",
    "member_digest",
)
_RESULT_FIELDS = (
    "schema_id",
    "mutation_ref",
    "command_digest",
    "proposal_ref",
    "disposition_ref",
    "disposition_digest",
    "disposition",
    "program_ref",
    "semantic_attempt_ref",
    "candidate_ref",
    "effect_intent_ref",
    "selection_head_revision",
    "selection_head_digest",
    "authority_selection_observation_ref",
    "authority_selection_observation_digest",
    "mutation_graph_digest",
    "recorded_at",
    "result_projection_digest",
)


# The contract budget is derived only from closed Section 41 ceilings.  One
# pair costs its tuple plus two scalar occurrences.  The recovery probe covers
# one 33-field command, one maximum planning-context graph, 15 evidence
# bindings, the K8 key and preimage, all 30 declared identity locators, and two
# three-coordinate locators for each evidence member.  The semantic allowance
# is the already-derived maximum complete bundle allowance, which includes the
# nested AttemptFence, EffectFence, Ceilings, and worker values.  Doubling the
# combined declared graph accounts for exact constructor revalidation without
# permitting input-shaped growth.
_MAX_CONTRACT_PAIR_RECONSTRUCTION_WORK = 3
_MAX_SELECTION_KEY_RECONSTRUCTION_WORK = (
    1 + len(_K8_FIELDS) * _MAX_CONTRACT_PAIR_RECONSTRUCTION_WORK
)
_MAX_COMMAND_RECONSTRUCTION_WORK = 1 + len(_COMMAND_FIELDS)
_MAX_PLANNING_CONTEXT_RECONSTRUCTION_WORK = (
    1 + len(_semantic._PLANNING_CONTEXT_FIELDS)
)
_MAX_EVIDENCE_BINDINGS_RECONSTRUCTION_WORK = (
    1
    + 15
    * (1 + len(_semantic._EVIDENCE_BINDING_FIELDS))
)
_MAX_PREIMAGE_RECONSTRUCTION_WORK = (
    1 + _MAX_SELECTION_KEY_RECONSTRUCTION_WORK + 3
)
_MAX_IDENTITY_LOCATORS_RECONSTRUCTION_WORK = 1 + sum(
    1
    + 1
    + 1
    + len(identity) * _MAX_CONTRACT_PAIR_RECONSTRUCTION_WORK
    for _table, identity in _RECOVERY_PROBE_IDENTITY_SHAPES
)
_MAX_EVIDENCE_MEMBER_LOCATORS_RECONSTRUCTION_WORK = (
    1
    + 15
    * (
        1
        + 2
        * (1 + 3 * _MAX_CONTRACT_PAIR_RECONSTRUCTION_WORK)
    )
)
_MAX_DECLARED_RECOVERY_PROBE_CONTRACT_WORK = sum(
    (
        1,
        _MAX_COMMAND_RECONSTRUCTION_WORK,
        _MAX_PLANNING_CONTEXT_RECONSTRUCTION_WORK,
        _MAX_EVIDENCE_BINDINGS_RECONSTRUCTION_WORK,
        _MAX_SELECTION_KEY_RECONSTRUCTION_WORK,
        _MAX_PREIMAGE_RECONSTRUCTION_WORK,
        _MAX_IDENTITY_LOCATORS_RECONSTRUCTION_WORK,
        _MAX_EVIDENCE_MEMBER_LOCATORS_RECONSTRUCTION_WORK,
        1,
    )
)
_MAX_EXACT_CONTRACT_RECONSTRUCTION_WORK = 2 * (
    _MAX_DECLARED_RECOVERY_PROBE_CONTRACT_WORK
    + _semantic._MAX_SEMANTIC_RECONSTRUCTION_WORK
)
assert _MAX_EXACT_CONTRACT_RECONSTRUCTION_WORK > (
    _MAX_DECLARED_RECOVERY_PROBE_CONTRACT_WORK
    + _semantic._MAX_SEMANTIC_RECONSTRUCTION_WORK
) > 0


class PreExecutionPlanDispositionConflictReasonV1(str, Enum):
    MUTATION_REF_REUSE_CONFLICT = "mutation_ref_reuse_conflict"
    GLOBAL_STOP_VERSION_CONFLICT = "global_stop_version_conflict"
    SELECTION_HEAD_VERSION_CONFLICT = "selection_head_version_conflict"
    PLANNING_SELECTION_NOT_PERMITTED = "planning_selection_not_permitted"
    PLANNING_RELATION_CONFLICT = "planning_relation_conflict"
    SEMANTIC_IDENTITY_CONFLICT = "semantic_identity_conflict"


class PreExecutionPlanDispositionRecoveryClassificationV1(str, Enum):
    COMMITTED_EXACT = "committed_exact"
    DEFINITELY_NOT_COMMITTED = "definitely_not_committed"
    UNRESOLVED = "unresolved"


def _to_plain(value: object) -> object:
    kind = type(value)
    if _contract_type_by_identity(kind) is not None:
        return value.to_mapping()
    if _semantic._semantic_type_by_identity(kind) is not None:
        return value.to_mapping()
    if _rows._row_registration_for_exact_type(kind) is not None:
        return value.to_mapping()
    if kind is tuple:
        return tuple(
            _to_plain(member) for member in typing.cast(tuple[object, ...], value)
        )
    if kind is str or kind is int or kind is bool or kind is type(None):
        return value
    if (
        kind is PreExecutionPlanDispositionConflictReasonV1
        or kind is PreExecutionPlanDispositionRecoveryClassificationV1
    ):
        return value.value
    _violate("invalid_field_type")


_CONTRACT_CLASSES: tuple[type[object], ...] = ()


def _contract_type_by_identity(candidate_type: object) -> type[object] | None:
    return _select_exact_type(candidate_type, _CONTRACT_CLASSES)


def _reject_concrete_subclass(cls: type[object], **kwargs: object) -> typing.NoReturn:
    raise TypeError("subclassing disabled")


class _ContractValue:
    __slots__ = ()
    __hash__ = None
    _FIELD_ORDER: tuple[str, ...] = ()

    def to_mapping(self) -> dict[str, object]:
        return {
            name: _to_plain(object.__getattribute__(self, name))
            for name in self._FIELD_ORDER
        }

    identity_mapping = to_mapping

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle

    def __init_subclass__(cls, **kwargs: object) -> None:
        if cls.__module__ != __name__:
            raise TypeError("subclassing disabled")


def _make_contract_class(
    name: str,
    field_order: tuple[str, ...],
    post_init: typing.Callable[[object], None],
) -> type[_ContractValue]:
    global _CONTRACT_CLASSES

    def __post_init__(self: object) -> None:
        post_init(self)

    result = typing.cast(
        type[_ContractValue],
        make_dataclass(
            name,
            [(field_name, object) for field_name in field_order],
            bases=(_ContractValue,),
            namespace={
                "__module__": __name__,
                "_FIELD_ORDER": field_order,
                "__post_init__": __post_init__,
                "__init_subclass__": _reject_concrete_subclass,
            },
            frozen=True,
            slots=True,
            repr=False,
        ),
    )
    _CONTRACT_CLASSES = (*_CONTRACT_CLASSES, result)
    return result


def _validate_lineage(value: object) -> None:
    for name in _L34_FIELDS:
        member = object.__getattribute__(value, name)
        if name in ("program_version_number", "attempt_number"):
            if _require_nonnegative_integer(member) == 0:
                _violate("invalid_field_value")
        elif name.endswith("_digest"):
            _require_sha256(member)
        else:
            _require_safe_ref(member)


CanonicalC2B3DLineage = _make_contract_class(
    "CanonicalC2B3DLineage", _L34_FIELDS, _validate_lineage
)


def _validate_command(value: object) -> None:
    mapping = typing.cast(_ContractValue, value).to_mapping()
    _require_enum(
        mapping["schema_id"],
        (_COMMAND_SCHEMA,),
        "cognitive_mutation_identity_invalid",
    )
    for name in _COMMAND_FIELDS[1:-1]:
        member = mapping[name]
        if name in ("expected_current_selection_revision",):
            if member is not None:
                _require_nonnegative_integer(member)
        elif name in ("expected_current_selection_head_digest",):
            _require_optional_sha256(member)
        elif name == "supersedes_disposition_ref":
            _require_optional_safe_ref(member)
        elif name.endswith("_digest"):
            _require_sha256(member)
        elif name == "disposition":
            _require_enum(
                member, ("selected_for_dispatch_gates", "deferred", "blocked")
            )
        elif name == "disposition_reason_code":
            _require_reason_code(member)
        else:
            _require_safe_ref(member)
    if mapping["preassigned_disposition_ref"] == mapping["proposal_ref"]:
        _violate("proposal_disposition_identity_collapse")
    if (mapping["expected_current_selection_revision"] is None) is not (
        mapping["expected_current_selection_head_digest"] is None
    ) or (mapping["expected_current_selection_revision"] is None) is not (
        mapping["supersedes_disposition_ref"] is None
    ):
        _violate("physical_family_receipt_binding_mismatch")
    _require_sha256(mapping["mutation_command_digest"])
    if mapping["mutation_command_digest"] != _domain_separated_digest(
        _COMMAND_DOMAIN, _without_field(mapping, "mutation_command_digest")
    ):
        _violate("cognitive_mutation_identity_invalid")


RecordPreExecutionPlanDispositionCommandV1 = _make_contract_class(
    "RecordPreExecutionPlanDispositionCommandV1", _COMMAND_FIELDS, _validate_command
)


def _validate_graph_entry(value: object) -> None:
    mapping = typing.cast(_ContractValue, value).to_mapping()
    role = _require_canonical_string(mapping["role"])
    if role not in (
        "source_invocation",
        "planning_context",
        "private_artifact_binding",
        "model_proposal",
        "pre_execution_plan_projection",
        "coordinator_disposition",
        "selection_head_postimage",
        *(
            f"evidence.{item}"
            for item in (*_semantic._EVIDENCE_ROLES, _semantic._READINESS_ROLE)
        ),
    ):
        _violate("physical_family_graph_digest_mismatch")
    _require_nonnegative_integer(mapping["rank"])
    _require_nonnegative_integer(mapping["ordinal"])
    _require_enum(mapping["table"], _rows._TABLE_ORDER)
    locator = mapping["locator"]
    if type(locator) is not tuple or not locator:
        _violate("physical_family_graph_digest_mismatch")
    for item in locator:
        if (
            type(item) is not tuple
            or len(item) != 2
            or type(item[0]) is not str
            or (
                type(item[1]) is not str
                and type(item[1]) is not int
            )
        ):
            _violate("physical_family_graph_digest_mismatch")
    _require_sha256(mapping["member_digest"])


CognitiveMutationGraphEntryV1 = _make_contract_class(
    "CognitiveMutationGraphEntryV1", _GRAPH_ENTRY_FIELDS, _validate_graph_entry
)


@dataclass(frozen=True, slots=True, repr=False)
class CognitiveMutationGraphV1(_ContractValue):
    mutation_ref: str
    command_digest: str
    entries: tuple[CognitiveMutationGraphEntryV1, ...]
    mutation_graph_digest: str

    _FIELD_ORDER = (
        "mutation_ref",
        "command_digest",
        "entries",
        "mutation_graph_digest",
    )

    __init_subclass__ = _reject_concrete_subclass

    def __post_init__(self) -> None:
        _require_safe_ref(self.mutation_ref)
        _require_sha256(self.command_digest)
        if (
            type(self.entries) is not tuple
            or not 21 <= len(self.entries) <= 22
            or any(
                type(entry) is not CognitiveMutationGraphEntryV1
                for entry in self.entries
            )
        ):
            _violate("physical_family_graph_digest_mismatch")
        checked_entries = tuple(
            typing.cast(
                CognitiveMutationGraphEntryV1,
                _reconstruct_exact_contract_value(
                    entry, CognitiveMutationGraphEntryV1
                ),
            )
            for entry in self.entries
        )
        ranks = tuple(entry.rank for entry in checked_entries)
        expected = tuple(range(22)) if len(self.entries) == 22 else (*range(19), 20, 21)
        if not _exact_equal(ranks, expected):
            _violate("physical_family_graph_digest_mismatch")
        _require_sha256(self.mutation_graph_digest)
        identity = {
            "mutation_ref": self.mutation_ref,
            "command_digest": self.command_digest,
            "entries": tuple(entry.to_mapping() for entry in checked_entries),
        }
        if self.mutation_graph_digest != _domain_separated_digest(
            _GRAPH_DOMAIN, identity
        ):
            _violate("physical_family_graph_digest_mismatch")
        object.__setattr__(self, "entries", checked_entries)

    def computed_digest(self) -> str:
        return _domain_separated_digest(
            _GRAPH_DOMAIN,
            _without_field(self.to_mapping(), "mutation_graph_digest"),
        )


def _validated_selection_key(
    value: object,
    reason: str = "physical_family_receipt_binding_mismatch",
) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple or len(value) != len(_K8_FIELDS):
        _violate(reason)
    checked: list[tuple[str, str]] = []
    for index, item in enumerate(typing.cast(tuple[object, ...], value)):
        if type(item) is not tuple or len(item) != 2:
            _violate(reason)
        name, member = typing.cast(tuple[object, object], item)
        if type(name) is not str or name != _K8_FIELDS[index]:
            _violate(reason)
        checked.append((name, _require_safe_ref(member, reason)))
    return tuple(checked)


@dataclass(frozen=True, slots=True, repr=False)
class PreExecutionSelectionHeadPreimageV1(_ContractValue):
    selection_key: tuple[tuple[str, str], ...]
    expected_current_selection_revision: int | None
    expected_current_selection_head_digest: str | None
    supersedes_disposition_ref: str | None

    _FIELD_ORDER = (
        "selection_key",
        "expected_current_selection_revision",
        "expected_current_selection_head_digest",
        "supersedes_disposition_ref",
    )

    __init_subclass__ = _reject_concrete_subclass

    def __post_init__(self) -> None:
        _validated_selection_key(self.selection_key)
        _require_optional_sha256(self.expected_current_selection_head_digest)
        _require_optional_safe_ref(self.supersedes_disposition_ref)
        if self.expected_current_selection_revision is not None:
            _require_nonnegative_integer(self.expected_current_selection_revision)
        if (self.expected_current_selection_revision is None) is not (
            self.expected_current_selection_head_digest is None
        ) or (self.expected_current_selection_revision is None) is not (
            self.supersedes_disposition_ref is None
        ):
            _violate("physical_family_receipt_binding_mismatch")


def _validate_result_projection(value: object) -> None:
    mapping = typing.cast(_ContractValue, value).to_mapping()
    _require_enum(
        mapping["schema_id"],
        (_RESULT_SCHEMA,),
        "physical_family_receipt_binding_mismatch",
    )
    for name in _RESULT_FIELDS[1:]:
        member = mapping[name]
        if name.endswith("_digest"):
            _require_sha256(member)
        elif name == "selection_head_revision":
            _require_nonnegative_integer(member)
        elif name == "disposition":
            _require_enum(
                member, ("selected_for_dispatch_gates", "deferred", "blocked")
            )
        elif name == "recorded_at":
            _require_utc_second(member)
        else:
            _require_safe_ref(member)
    if mapping["result_projection_digest"] != _domain_separated_digest(
        _RESULT_DOMAIN, _without_field(mapping, "result_projection_digest")
    ):
        _violate("physical_family_receipt_binding_mismatch")


PreExecutionPlanDispositionResultProjectionV1 = _make_contract_class(
    "PreExecutionPlanDispositionResultProjectionV1",
    _RESULT_FIELDS,
    _validate_result_projection,
)


@dataclass(frozen=True, slots=True, repr=False)
class PreExecutionPlanDispositionResultV1(_ContractValue):
    projection: PreExecutionPlanDispositionResultProjectionV1
    receipt_digest: str

    _FIELD_ORDER = ("projection", "receipt_digest")

    __init_subclass__ = _reject_concrete_subclass

    def __post_init__(self) -> None:
        projection = _reconstruct_exact_contract_value(
            self.projection, PreExecutionPlanDispositionResultProjectionV1
        )
        _require_sha256(self.receipt_digest)
        object.__setattr__(self, "projection", projection)

    def to_mapping(self) -> dict[str, object]:
        result = self.projection.to_mapping()
        result["receipt_digest"] = self.receipt_digest
        return result

    def __getattr__(self, name: str) -> object:
        if name in _RESULT_FIELDS:
            return object.__getattribute__(self.projection, name)
        raise AttributeError(name)


@dataclass(frozen=True, slots=True, repr=False)
class PreExecutionPlanDispositionConflictV1(_ContractValue):
    reason: PreExecutionPlanDispositionConflictReasonV1
    mutation_ref: str
    command_digest: str
    program_ref: str

    _FIELD_ORDER = ("reason", "mutation_ref", "command_digest", "program_ref")

    __init_subclass__ = _reject_concrete_subclass

    def __post_init__(self) -> None:
        if type(self.reason) is not PreExecutionPlanDispositionConflictReasonV1:
            _violate("invalid_field_type")
        _require_safe_ref(self.mutation_ref)
        _require_sha256(self.command_digest)
        _require_safe_ref(self.program_ref)


def _validated_recovery_identity_locators(
    value: object,
) -> tuple[tuple[str, tuple[tuple[str, object], ...]], ...]:
    if type(value) is not tuple or len(value) != 30:
        _violate("recovery_unresolved")
    checked: list[tuple[str, tuple[tuple[str, object], ...]]] = []
    for index, member in enumerate(typing.cast(tuple[object, ...], value)):
        if type(member) is not tuple or len(member) != 2:
            _violate("recovery_unresolved")
        table, raw_locator = typing.cast(tuple[object, object], member)
        expected_table, expected_fields = _RECOVERY_PROBE_IDENTITY_SHAPES[index]
        if type(table) is not str or table != expected_table:
            _violate("recovery_unresolved")
        if type(raw_locator) is not tuple or len(raw_locator) != len(expected_fields):
            _violate("recovery_unresolved")
        locator: list[tuple[str, object]] = []
        for coordinate_index, coordinate in enumerate(
            typing.cast(tuple[object, ...], raw_locator)
        ):
            if type(coordinate) is not tuple or len(coordinate) != 2:
                _violate("recovery_unresolved")
            name, coordinate_value = typing.cast(tuple[object, object], coordinate)
            if (
                type(name) is not str
                or name != expected_fields[coordinate_index]
                or (
                    type(coordinate_value) is not str
                    and type(coordinate_value) is not int
                )
            ):
                _violate("recovery_unresolved")
            if type(coordinate_value) is str:
                coordinate_value = _require_canonical_string(
                    coordinate_value, reason="recovery_unresolved"
                )
            else:
                coordinate_value = _require_sqlite_integer(
                    coordinate_value, "recovery_unresolved"
                )
            locator.append((name, coordinate_value))
        checked.append((table, tuple(locator)))
    return tuple(checked)


def _validated_evidence_member_locators(
    value: object,
) -> tuple[
    tuple[
        tuple[tuple[str, object], ...],
        tuple[tuple[str, object], ...],
    ],
    ...,
]:
    if type(value) is not tuple or len(value) not in (14, 15):
        _violate("recovery_unresolved")
    checked: list[
        tuple[
            tuple[tuple[str, object], ...],
            tuple[tuple[str, object], ...],
        ]
    ] = []
    shapes = (
        ("proposal_ref", "evidence_role", "ordinal"),
        ("proposal_ref", "role_rank", "ordinal"),
    )
    for member in typing.cast(tuple[object, ...], value):
        if type(member) is not tuple or len(member) != 2:
            _violate("recovery_unresolved")
        routes: list[tuple[tuple[str, object], ...]] = []
        for route_index, raw_locator in enumerate(
            typing.cast(tuple[object, object], member)
        ):
            if type(raw_locator) is not tuple or len(raw_locator) != 3:
                _violate("recovery_unresolved")
            locator: list[tuple[str, object]] = []
            for coordinate_index, coordinate in enumerate(
                typing.cast(tuple[object, ...], raw_locator)
            ):
                if type(coordinate) is not tuple or len(coordinate) != 2:
                    _violate("recovery_unresolved")
                name, coordinate_value = typing.cast(
                    tuple[object, object], coordinate
                )
                if (
                    type(name) is not str
                    or name != shapes[route_index][coordinate_index]
                    or (
                        type(coordinate_value) is not str
                        and type(coordinate_value) is not int
                    )
                ):
                    _violate("recovery_unresolved")
                if type(coordinate_value) is str:
                    coordinate_value = _require_canonical_string(
                        coordinate_value, reason="recovery_unresolved"
                    )
                else:
                    coordinate_value = _require_sqlite_integer(
                        coordinate_value, "recovery_unresolved"
                    )
                locator.append((name, coordinate_value))
            routes.append(tuple(locator))
        checked.append((routes[0], routes[1]))
    return tuple(checked)


def _derived_evidence_member_locators(
    bindings: tuple[_semantic.ModelProposalEvidenceBindingV1, ...],
) -> tuple[
    tuple[
        tuple[tuple[str, object], ...],
        tuple[tuple[str, object], ...],
    ],
    ...,
]:
    return tuple(
        (
            (
                ("proposal_ref", binding.proposal_ref),
                ("evidence_role", binding.evidence_role),
                ("ordinal", binding.ordinal),
            ),
            (
                ("proposal_ref", binding.proposal_ref),
                ("role_rank", binding.role_rank),
                ("ordinal", binding.ordinal),
            ),
        )
        for binding in bindings
    )


def _derived_recovery_identity_locators(
    command: RecordPreExecutionPlanDispositionCommandV1,
    context: _semantic.PreExecutionPlanningContextV1,
    bindings: tuple[_semantic.ModelProposalEvidenceBindingV1, ...],
    preimage: PreExecutionSelectionHeadPreimageV1,
) -> tuple[tuple[str, tuple[tuple[str, object], ...]], ...]:
    prior_revision = (
        -1
        if preimage.expected_current_selection_revision is None
        else preimage.expected_current_selection_revision
    )
    resulting_revision = _require_sqlite_integer(
        prior_revision + 1, "recovery_unresolved"
    )
    lineage = {
        name: object.__getattribute__(context, name) for name in _L34_FIELDS
    }
    representatives: dict[str, dict[str, object]] = {
        _rows._TABLE_ORDER[0]: {
            "source_invocation_ref": command.source_invocation_ref,
            "proposal_phase": "pre_execution_plan",
        },
        _rows._TABLE_ORDER[1]: {
            "planning_context_ref": command.planning_context_ref,
            "program_ref": command.program_ref,
        },
        _rows._TABLE_ORDER[2]: {
            "artifact_ref": command.artifact_ref,
            "proposal_phase": "pre_execution_plan",
        },
        _rows._TABLE_ORDER[3]: {
            "proposal_ref": command.proposal_ref,
            "source_invocation_ref": command.source_invocation_ref,
            "artifact_ref": command.artifact_ref,
            "proposal_phase": "pre_execution_plan",
        },
        _rows._TABLE_ORDER[4]: {
            "proposal_ref": command.proposal_ref,
            "artifact_ref": command.artifact_ref,
        },
        _rows._TABLE_ORDER[5]: bindings[0].to_mapping(),
        _rows._TABLE_ORDER[6]: {
            **lineage,
            "disposition_ref": command.preassigned_disposition_ref,
            "proposal_ref": command.proposal_ref,
            "effect_intent_ref": command.effect_intent_ref,
            "disposition": command.disposition,
            "prior_selection_head_revision": prior_revision,
            "resulting_selection_head_revision": resulting_revision,
        },
        _rows._TABLE_ORDER[7]: {
            **lineage,
            "program_ref": command.program_ref,
            "effect_intent_ref": command.effect_intent_ref,
            "current_proposal_ref": command.proposal_ref,
            "current_disposition_ref": command.preassigned_disposition_ref,
            "head_revision": resulting_revision,
        },
        _rows._TABLE_ORDER[8]: {
            "mutation_ref": command.mutation_ref,
            "program_ref": command.program_ref,
            "disposition_ref": command.preassigned_disposition_ref,
        },
    }
    result = tuple(
        (
            table,
            tuple((name, representatives[table][name]) for name in fields),
        )
        for table, fields in _RECOVERY_PROBE_IDENTITY_SHAPES
    )
    return _validated_recovery_identity_locators(result)


@dataclass(frozen=True, slots=True, repr=False)
class PreExecutionPlanDispositionRecoveryProbeV1(_ContractValue):
    command: RecordPreExecutionPlanDispositionCommandV1
    planning_context: _semantic.PreExecutionPlanningContextV1
    evidence_bindings: tuple[_semantic.ModelProposalEvidenceBindingV1, ...]
    selection_key: tuple[tuple[str, str], ...]
    expected_preimage: PreExecutionSelectionHeadPreimageV1
    identity_locators: tuple[tuple[str, tuple[tuple[str, object], ...]], ...]
    evidence_member_locators: tuple[
        tuple[
            tuple[tuple[str, object], ...],
            tuple[tuple[str, object], ...],
        ],
        ...,
    ]
    recovery_probe_digest: str

    _FIELD_ORDER = (
        "command",
        "planning_context",
        "evidence_bindings",
        "selection_key",
        "expected_preimage",
        "identity_locators",
        "evidence_member_locators",
        "recovery_probe_digest",
    )

    __init_subclass__ = _reject_concrete_subclass

    def __post_init__(self) -> None:
        budget = _contract_reconstruction_budget(None)
        with _semantic._semantic_reconstruction_budget_scope(budget):
            self._validate_and_normalize(budget)

    def _validate_and_normalize(
        self,
        budget: _semantic._SemanticReconstructionBudget,
    ) -> None:
        command = typing.cast(
            RecordPreExecutionPlanDispositionCommandV1,
            _reconstruct_exact_contract_value(
                self.command,
                RecordPreExecutionPlanDispositionCommandV1,
                budget,
            ),
        )
        context = typing.cast(
            _semantic.PreExecutionPlanningContextV1,
            _semantic._reconstruct_exact_semantic_value(
                self.planning_context,
                _semantic.PreExecutionPlanningContextV1,
                budget,
            ),
        )
        if type(self.evidence_bindings) is not tuple or len(
            self.evidence_bindings
        ) not in (14, 15):
            _violate("recovery_unresolved")
        bindings = tuple(
            typing.cast(
                _semantic.ModelProposalEvidenceBindingV1,
                _semantic._reconstruct_exact_semantic_value(
                    binding,
                    _semantic.ModelProposalEvidenceBindingV1,
                    budget,
                ),
            )
            for binding in self.evidence_bindings
        )
        preimage = typing.cast(
            PreExecutionSelectionHeadPreimageV1,
            _reconstruct_exact_contract_value(
                self.expected_preimage,
                PreExecutionSelectionHeadPreimageV1,
                budget,
            ),
        )
        command_key = tuple(
            (name, object.__getattribute__(command, name)) for name in _K8_FIELDS
        )
        selection_key = _validated_selection_key(
            self.selection_key, "recovery_unresolved"
        )
        if not _exact_equal(selection_key, command_key):
            _violate("recovery_unresolved")
        if not _exact_equal(selection_key, preimage.selection_key):
            _violate("recovery_unresolved")
        if not (
            preimage.expected_current_selection_revision
            == command.expected_current_selection_revision
            and preimage.expected_current_selection_head_digest
            == command.expected_current_selection_head_digest
            and preimage.supersedes_disposition_ref
            == command.supersedes_disposition_ref
        ):
            _violate("recovery_unresolved")
        relation_pairs = (
            (context.planning_context_ref, command.planning_context_ref),
            (context.planning_context_digest, command.planning_context_digest),
            (context.program_ref, command.program_ref),
            (context.semantic_attempt_ref, command.semantic_attempt_ref),
            (context.candidate_ref, command.candidate_ref),
            (context.effect_intent_ref, command.effect_intent_ref),
            (context.author_command_ref, command.author_command_ref),
            (context.author_command_digest, command.author_command_digest),
            (context.attempt_fence_ref, command.attempt_fence_ref),
            (context.attempt_fence_digest, command.attempt_fence_digest),
            (context.effect_fence_ref, command.effect_fence_ref),
            (context.effect_fence_digest, command.effect_fence_digest),
            (context.delivery_attempt_ref, command.delivery_attempt_ref),
            (context.delivery_envelope_digest, command.delivery_envelope_digest),
        )
        if any(not _exact_equal(left, right) for left, right in relation_pairs):
            _violate("recovery_unresolved")
        evidence_set_valid = True
        try:
            _semantic.ModelProposalEvidenceSetV1(
                evidence_set_ref=command.evidence_set_ref,
                proposal_ref=command.proposal_ref,
                proposal_phase="pre_execution_plan",
                entries=bindings,
                evidence_set_digest=command.evidence_set_digest,
            )
        except _CognitiveProposalContractViolation:
            evidence_set_valid = False
        if not evidence_set_valid:
            _violate("recovery_unresolved")
        locators = _validated_recovery_identity_locators(self.identity_locators)
        member_locators = _validated_evidence_member_locators(
            self.evidence_member_locators
        )
        expected_locators = _derived_recovery_identity_locators(
            command, context, bindings, preimage
        )
        expected_member_locators = _derived_evidence_member_locators(bindings)
        if not _exact_equal(locators, expected_locators) or not _exact_equal(
            member_locators, expected_member_locators
        ):
            _violate("recovery_unresolved")
        stored_digest = _require_sha256(
            self.recovery_probe_digest, "recovery_unresolved"
        )
        identity = {
            "command": command.to_mapping(),
            "planning_context": context.to_mapping(),
            "evidence_bindings": tuple(
                binding.to_mapping() for binding in bindings
            ),
            "selection_key": selection_key,
            "expected_preimage": preimage.to_mapping(),
            "identity_locators": locators,
            "evidence_member_locators": member_locators,
        }
        if stored_digest != _domain_separated_digest(_RECOVERY_PROBE_DOMAIN, identity):
            _violate("recovery_unresolved")
        object.__setattr__(self, "command", command)
        object.__setattr__(self, "planning_context", context)
        object.__setattr__(self, "evidence_bindings", bindings)
        object.__setattr__(self, "selection_key", selection_key)
        object.__setattr__(self, "expected_preimage", preimage)
        object.__setattr__(self, "identity_locators", locators)
        object.__setattr__(self, "evidence_member_locators", member_locators)


@dataclass(frozen=True, slots=True, repr=False)
class PreExecutionPlanDispositionRecoveryResultV1(_ContractValue):
    classification: PreExecutionPlanDispositionRecoveryClassificationV1
    observed_depth: int
    committed_result: PreExecutionPlanDispositionResultV1 | None = field(
        default=None, repr=False
    )

    _FIELD_ORDER = ("classification", "observed_depth", "committed_result")

    __init_subclass__ = _reject_concrete_subclass

    def __post_init__(self) -> None:
        if (
            type(self.classification)
            is not PreExecutionPlanDispositionRecoveryClassificationV1
        ):
            _violate("recovery_unresolved")
        _require_nonnegative_integer(self.observed_depth, "recovery_unresolved")
        if self.observed_depth > 257:
            _violate("recovery_unresolved")
        if (
            self.classification
            is PreExecutionPlanDispositionRecoveryClassificationV1.COMMITTED_EXACT
        ):
            if (
                type(self.committed_result) is not PreExecutionPlanDispositionResultV1
                or self.observed_depth > 256
            ):
                _violate("recovery_unresolved")
            checked_result = _reconstruct_exact_contract_value(
                self.committed_result, PreExecutionPlanDispositionResultV1
            )
            object.__setattr__(self, "committed_result", checked_result)
        elif self.committed_result is not None:
            _violate("recovery_unresolved")
        if (
            self.classification
            is PreExecutionPlanDispositionRecoveryClassificationV1.DEFINITELY_NOT_COMMITTED
            and self.observed_depth != 0
        ):
            _violate("recovery_unresolved")


_CONTRACT_CLASSES = (
    *_CONTRACT_CLASSES,
    CognitiveMutationGraphV1,
    PreExecutionSelectionHeadPreimageV1,
    PreExecutionPlanDispositionResultV1,
    PreExecutionPlanDispositionConflictV1,
    PreExecutionPlanDispositionRecoveryProbeV1,
    PreExecutionPlanDispositionRecoveryResultV1,
)


def _contract_reconstruction_budget(
    supplied: _semantic._SemanticReconstructionBudget | None,
) -> _semantic._SemanticReconstructionBudget:
    if supplied is not None and type(
        supplied
    ) is not _semantic._SemanticReconstructionBudget:
        _violate("recovery_unresolved")
    current = _semantic._current_semantic_reconstruction_budget()
    if supplied is None:
        if current is not None:
            return current
        return _semantic._SemanticReconstructionBudget(
            _MAX_EXACT_CONTRACT_RECONSTRUCTION_WORK,
            "recovery_unresolved",
        )
    if current is not None and current is not supplied:
        _violate("recovery_unresolved")
    return supplied


def _clone_exact_contract_member(
    value: object,
    active: set[int],
    depth: int,
    budget: _semantic._SemanticReconstructionBudget | None = None,
) -> object:
    exact_budget = _contract_reconstruction_budget(budget)
    with _semantic._semantic_reconstruction_budget_scope(exact_budget):
        return _clone_exact_contract_member_scoped(
            value,
            active,
            depth,
            exact_budget,
        )


def _clone_exact_contract_member_scoped(
    value: object,
    active: set[int],
    depth: int,
    budget: _semantic._SemanticReconstructionBudget,
) -> object:
    if depth > 128:
        _violate("recovery_unresolved")
    budget.consume()
    kind = type(value)
    if kind is str or kind is int or kind is bool or kind is type(None):
        return value
    if (
        kind is PreExecutionPlanDispositionConflictReasonV1
        or kind is PreExecutionPlanDispositionRecoveryClassificationV1
    ):
        return value
    if kind is tuple:
        identity = id(value)
        if identity in active:
            _violate("recovery_unresolved")
        sequence = typing.cast(tuple[object, ...], value)
        if len(sequence) > 64:
            _violate("recovery_unresolved")
        active.add(identity)
        try:
            return tuple(
                _clone_exact_contract_member(
                    member,
                    active,
                    depth + 1,
                    budget,
                )
                for member in sequence
            )
        finally:
            active.discard(identity)
    trusted_semantic_kind = _semantic._semantic_type_by_identity(kind)
    if trusted_semantic_kind is not None:
        return _semantic._reconstruct_exact_semantic_value(
            value,
            trusted_semantic_kind,
            budget,
        )
    trusted_kind = _contract_type_by_identity(kind)
    if trusted_kind is None:
        _violate("recovery_unresolved")
    identity = id(value)
    if identity in active:
        _violate("recovery_unresolved")
    active.add(identity)
    try:
        values: dict[str, object] = {}
        missing = False
        for name in typing.cast(type[_ContractValue], trusted_kind)._FIELD_ORDER:
            try:
                member = object.__getattribute__(value, name)
            except (KeyboardInterrupt, SystemExit, GeneratorExit):
                raise
            except Exception:
                missing = True
                break
            values[name] = _clone_exact_contract_member(
                member,
                active,
                depth + 1,
                budget,
            )
        if missing:
            _violate("recovery_unresolved")
        reconstructed: object = None
        failed = False
        try:
            reconstructed = trusted_kind(**values)
        except _CognitiveProposalContractViolation:
            raise
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            raise
        except Exception:
            failed = True
        if failed or type(reconstructed) is not trusted_kind:
            _violate("recovery_unresolved")
        return reconstructed
    finally:
        active.discard(identity)


def _reconstruct_exact_contract_value(
    value: object,
    expected: type[object],
    budget: _semantic._SemanticReconstructionBudget | None = None,
) -> _ContractValue:
    if (
        type(expected) is not type
        or _contract_type_by_identity(expected) is not expected
    ):
        _violate("recovery_unresolved")
    if type(value) is not expected:
        _violate("recovery_unresolved")
    exact_budget = _contract_reconstruction_budget(budget)
    try:
        with _semantic._semantic_reconstruction_budget_scope(exact_budget):
            reconstructed = _clone_exact_contract_member(
                value,
                set(),
                0,
                exact_budget,
            )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except _CognitiveProposalContractViolation:
        raise
    except (MemoryError, RecursionError):
        _violate("recovery_unresolved")
    if type(reconstructed) is not expected:
        _violate("recovery_unresolved")
    return typing.cast(_ContractValue, reconstructed)


def _require_exact_recovery_probe(
    value: object,
) -> PreExecutionPlanDispositionRecoveryProbeV1:
    return typing.cast(
        PreExecutionPlanDispositionRecoveryProbeV1,
        _reconstruct_exact_contract_value(
            value, PreExecutionPlanDispositionRecoveryProbeV1
        ),
    )


@dataclass(frozen=True, slots=True, repr=False)
class _PreExecutionPlanDispositionWritePlan:
    command: RecordPreExecutionPlanDispositionCommandV1
    rows: tuple[_rows.CanonicalCognitivePhysicalRow, ...]
    graph: CognitiveMutationGraphV1
    planned_result: PreExecutionPlanDispositionResultV1
    recovery_probe: PreExecutionPlanDispositionRecoveryProbeV1

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle
    __init_subclass__ = _reject_concrete_subclass

    def __post_init__(self) -> None:
        command = typing.cast(
            RecordPreExecutionPlanDispositionCommandV1,
            _reconstruct_exact_contract_value(
                self.command, RecordPreExecutionPlanDispositionCommandV1
            ),
        )
        if type(self.rows) is not tuple or len(self.rows) not in (22, 23):
            _violate("physical_family_order_mismatch")
        rows = tuple(
            _rows._require_exact_physical_row(row) for row in self.rows
        )
        graph = typing.cast(
            CognitiveMutationGraphV1,
            _reconstruct_exact_contract_value(self.graph, CognitiveMutationGraphV1),
        )
        planned_result = typing.cast(
            PreExecutionPlanDispositionResultV1,
            _reconstruct_exact_contract_value(
                self.planned_result, PreExecutionPlanDispositionResultV1
            ),
        )
        recovery_probe = _require_exact_recovery_probe(self.recovery_probe)
        object.__setattr__(self, "command", command)
        object.__setattr__(self, "rows", rows)
        object.__setattr__(self, "graph", graph)
        object.__setattr__(self, "planned_result", planned_result)
        object.__setattr__(self, "recovery_probe", recovery_probe)


def _record_command_from_ingress(
    mutation_ref: object,
    mutation_command_digest: object,
    bundle: object,
    disposition_identity: object,
) -> RecordPreExecutionPlanDispositionCommandV1:
    checked_bundle = _semantic._require_exact_pre_execution_bundle(bundle)
    _require_safe_ref(mutation_ref, "cognitive_mutation_identity_invalid")
    _require_sha256(mutation_command_digest, "cognitive_mutation_identity_invalid")
    identity = _require_exact_mapping(
        disposition_identity,
        (
            "preassigned_disposition_ref",
            "expected_current_selection_revision",
            "expected_current_selection_head_digest",
            "disposition",
            "disposition_reason_code",
            "supersedes_disposition_ref",
        ),
        "cognitive_mutation_identity_invalid",
    )
    context = checked_bundle.planning_context
    proposal = checked_bundle.model_proposal
    source = checked_bundle.source_invocation
    artifact = checked_bundle.private_artifact_binding
    fields: dict[str, object] = {
        "schema_id": _COMMAND_SCHEMA,
        "mutation_ref": mutation_ref,
        "proposal_ref": proposal.proposal_ref,
        "proposal_digest": proposal.proposal_digest,
        "source_invocation_ref": source.source_invocation_ref,
        "source_invocation_digest": source.source_invocation_digest,
        "artifact_ref": artifact.artifact_ref,
        "artifact_digest": artifact.artifact_digest,
        "artifact_binding_digest": artifact.artifact_binding_digest,
        "planning_context_ref": context.planning_context_ref,
        "planning_context_digest": context.planning_context_digest,
        "safe_projection_digest": checked_bundle.safe_projection.safe_projection_digest,
        "evidence_set_ref": checked_bundle.evidence_set.evidence_set_ref,
        "evidence_set_digest": checked_bundle.evidence_set.evidence_set_digest,
        **identity,
        "program_ref": context.program_ref,
        "semantic_attempt_ref": context.semantic_attempt_ref,
        "candidate_ref": context.candidate_ref,
        "effect_intent_ref": context.effect_intent_ref,
        "author_command_ref": context.author_command_ref,
        "author_command_digest": context.author_command_digest,
        "attempt_fence_ref": context.attempt_fence_ref,
        "attempt_fence_digest": context.attempt_fence_digest,
        "effect_fence_ref": context.effect_fence_ref,
        "effect_fence_digest": context.effect_fence_digest,
        "delivery_attempt_ref": context.delivery_attempt_ref,
        "delivery_envelope_digest": context.delivery_envelope_digest,
    }
    if tuple(fields) != _COMMAND_FIELDS[:-1]:
        _violate("cognitive_mutation_identity_invalid")
    computed = _domain_separated_digest(_COMMAND_DOMAIN, fields)
    if computed != mutation_command_digest:
        _violate("cognitive_mutation_identity_invalid")
    fields["mutation_command_digest"] = computed
    return RecordPreExecutionPlanDispositionCommandV1(**fields)


def _lineage_from_context(
    context: _semantic.PreExecutionPlanningContextV1,
) -> CanonicalC2B3DLineage:
    if type(context) is not _semantic.PreExecutionPlanningContextV1:
        _violate("invalid_field_type")
    return CanonicalC2B3DLineage(
        **{name: object.__getattribute__(context, name) for name in _L34_FIELDS}
    )


def _build_pre_execution_plan_disposition_recovery_probe_from_basis(
    command: object,
    planning_context: object,
    evidence_bindings: object,
) -> PreExecutionPlanDispositionRecoveryProbeV1:
    checked_command = typing.cast(
        RecordPreExecutionPlanDispositionCommandV1,
        _reconstruct_exact_contract_value(
            command, RecordPreExecutionPlanDispositionCommandV1
        ),
    )
    context = typing.cast(
        _semantic.PreExecutionPlanningContextV1,
        _semantic._reconstruct_exact_semantic_value(
            planning_context, _semantic.PreExecutionPlanningContextV1
        ),
    )
    if type(evidence_bindings) is not tuple or len(evidence_bindings) not in (14, 15):
        _violate("recovery_unresolved")
    bindings = tuple(
        typing.cast(
            _semantic.ModelProposalEvidenceBindingV1,
            _semantic._reconstruct_exact_semantic_value(
                binding, _semantic.ModelProposalEvidenceBindingV1
            ),
        )
        for binding in typing.cast(tuple[object, ...], evidence_bindings)
    )
    selection_key = tuple(
        (name, object.__getattribute__(checked_command, name))
        for name in _K8_FIELDS
    )
    preimage = PreExecutionSelectionHeadPreimageV1(
        selection_key=selection_key,
        expected_current_selection_revision=(
            checked_command.expected_current_selection_revision
        ),
        expected_current_selection_head_digest=(
            checked_command.expected_current_selection_head_digest
        ),
        supersedes_disposition_ref=checked_command.supersedes_disposition_ref,
    )
    locators = _derived_recovery_identity_locators(
        checked_command, context, bindings, preimage
    )
    member_locators = _derived_evidence_member_locators(bindings)
    identity = {
        "command": checked_command.to_mapping(),
        "planning_context": context.to_mapping(),
        "evidence_bindings": tuple(
            binding.to_mapping() for binding in bindings
        ),
        "selection_key": selection_key,
        "expected_preimage": preimage.to_mapping(),
        "identity_locators": locators,
        "evidence_member_locators": member_locators,
    }
    return PreExecutionPlanDispositionRecoveryProbeV1(
        command=checked_command,
        planning_context=context,
        evidence_bindings=bindings,
        selection_key=selection_key,
        expected_preimage=preimage,
        identity_locators=locators,
        evidence_member_locators=member_locators,
        recovery_probe_digest=_domain_separated_digest(
            _RECOVERY_PROBE_DOMAIN, identity
        ),
    )


def _build_pre_execution_plan_disposition_recovery_probe(
    command: object,
    bundle: object,
) -> PreExecutionPlanDispositionRecoveryProbeV1:
    checked_bundle = _semantic._require_exact_pre_execution_bundle(bundle)
    return _build_pre_execution_plan_disposition_recovery_probe_from_basis(
        command,
        checked_bundle.planning_context,
        checked_bundle.evidence_bindings,
    )
