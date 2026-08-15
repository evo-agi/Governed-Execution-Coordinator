"""Pure private C2B2 decision, receipt, and supplied-graph row values."""

from __future__ import annotations

import typing

from ._development_row_value_support import (
    _ImmutableValue,
    _RowValueValidationError,
    _canonical_identity_bytes,
    _domain_separated_digest,
    _new_database_integrity_error,
    _require_constant_string,
    _require_enum,
    _require_matching_digest,
    _require_nonempty_string,
    _require_nonnegative_integer,
    _require_optional_enum,
    _require_optional_nonnegative_integer,
    _require_optional_positive_integer,
    _require_optional_safe_ref,
    _require_optional_sha256,
    _require_positive_integer,
    _require_reason_code,
    _require_safe_ref,
    _require_sha256,
    _require_utc_timestamp,
    _row_tuple_to_private_mapping,
)


__all__: tuple[str, ...] = ()


_DEVELOPMENT_DECISION_COLUMNS = (
    "schema_id", "mutation_ref", "decision_ref", "program_ref", "decision_kind",
    "decision_variant", "basis_decision_ref", "basis_program_version_ref",
    "basis_program_version_number", "expected_program_head_revision",
    "resulting_program_version_ref", "resulting_program_version_number",
    "selected_semantic_attempt_ref", "selected_candidate_ref",
    "selected_attempt_fence_ref", "selected_attempt_fence_digest",
    "target_effect_intent_ref", "target_effect_class", "target_effect_fence_ref",
    "target_effect_fence_digest", "expected_target_effect_head_revision",
    "target_delivery_attempt_ref", "originating_command_ref",
    "originating_command_digest", "target_capsule_manifest_ref",
    "target_portable_capsule_digest", "coding_global_stop_ref",
    "coding_global_stop_version", "source_directive_ref", "source_directive_digest",
    "source_evidence_ref", "source_evidence_digest", "preassigned_semantic_attempt_ref",
    "preassigned_candidate_ref", "preassigned_effect_intent_ref",
    "preassigned_effect_fence_ref", "preassigned_delivery_attempt_ref",
    "resulting_accepted_intent_revision_ref", "resulting_work_item_ref",
    "resulting_work_item_revision_ref", "reason_code", "decided_at", "decision_digest",
)
_DEVELOPMENT_MUTATION_RECEIPT_COLUMNS = (
    "schema_id", "mutation_ref", "mutation_family", "command_schema_id",
    "command_digest", "program_ref", "decision_ref", "result_program_version_ref",
    "result_semantic_attempt_ref", "result_effect_intent_ref",
    "result_effect_fence_ref", "result_delivery_attempt_ref", "result_observation_ref",
    "result_decision_ref", "result_class", "result_projection_digest",
    "mutation_graph_digest", "outcome", "committed_at",
)

_DEVELOPMENT_DECISION_SCHEMA = "governed-execution.nwp-development-decision.v1"
_DEVELOPMENT_DECISION_DOMAIN = _DEVELOPMENT_DECISION_SCHEMA + ".identity"
_DEVELOPMENT_MUTATION_RECEIPT_SCHEMA = (
    "governed-execution.nwp-development-mutation-receipt.v1"
)
_DEVELOPMENT_MUTATION_RECEIPT_DOMAIN = (
    _DEVELOPMENT_MUTATION_RECEIPT_SCHEMA + ".identity"
)

_DECISION_KINDS = (
    "initialize", "accept", "repair", "replan", "terminal_reject", "block",
    "redeliver", "cancel",
)
_DECISION_VARIANTS = (
    "program_genesis", "candidate_acceptance", "candidate_repair", "program_replan",
    "attempt_selecting_replan", "program_terminal_reject", "program_block",
    "productive_redelivery", "cancellation_redelivery", "effect_cancellation",
)
_TARGET_EFFECT_CLASSES = (
    "author_candidate", "cancel_effect", "local_git_commit", "review_candidate",
    "validate_candidate",
)
_MUTATION_FAMILIES = (
    "initialize_development_program",
    "establish_development_author_effect_intent",
    "establish_development_bound_effect_intent",
    "ingest_development_source_observation",
    "record_development_progression_decision",
)
_COMMAND_SCHEMA_IDS = (
    "governed-execution.nwp-initialize-development-program-command.v1",
    "governed-execution.nwp-establish-development-author-effect-intent-command.v1",
    "governed-execution.nwp-establish-development-bound-effect-intent-command.v1",
    "governed-execution.nwp-ingest-development-source-observation-command.v1",
    "governed-execution.nwp-record-development-progression-decision-command.v1",
)
_RESULT_CLASSES = (
    "development_program_initialized",
    "development_author_effect_intent_established",
    "development_bound_effect_intent_established",
    "development_source_observation_ingested",
    "development_progression_decision_recorded",
)

_INITIALIZE_RESULT_SCHEMA = (
    "governed-execution.nwp-initialize-development-program-result.v1"
)
_AUTHOR_EFFECT_RESULT_SCHEMA = (
    "governed-execution.nwp-establish-development-author-effect-intent-result.v1"
)
_BOUND_EFFECT_RESULT_SCHEMA = (
    "governed-execution.nwp-establish-development-bound-effect-intent-result.v1"
)
_OBSERVATION_RESULT_SCHEMA = (
    "governed-execution.nwp-ingest-development-source-observation-result.v1"
)
_PROGRESSION_RESULT_SCHEMA = (
    "governed-execution.nwp-record-development-progression-decision-result.v1"
)
_INITIALIZE_RESULT_DOMAIN = _INITIALIZE_RESULT_SCHEMA + ".identity"
_AUTHOR_EFFECT_RESULT_DOMAIN = _AUTHOR_EFFECT_RESULT_SCHEMA + ".identity"
_BOUND_EFFECT_RESULT_DOMAIN = _BOUND_EFFECT_RESULT_SCHEMA + ".identity"
_OBSERVATION_RESULT_DOMAIN = _OBSERVATION_RESULT_SCHEMA + ".identity"
_PROGRESSION_RESULT_DOMAIN = _PROGRESSION_RESULT_SCHEMA + ".identity"


class _DecisionVariantValue(_ImmutableValue):
    __slots__ = ("_values",)


class _ProgramGenesisDecision(_DecisionVariantValue):
    __slots__ = ()
    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn: raise TypeError("subclassing disabled")


class _CandidateAcceptanceDecision(_DecisionVariantValue):
    __slots__ = ()
    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn: raise TypeError("subclassing disabled")


class _CandidateRepairDecision(_DecisionVariantValue):
    __slots__ = ()
    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn: raise TypeError("subclassing disabled")


class _ProgramReplanDecision(_DecisionVariantValue):
    __slots__ = ()
    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn: raise TypeError("subclassing disabled")


class _AttemptSelectingReplanDecision(_DecisionVariantValue):
    __slots__ = ()
    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn: raise TypeError("subclassing disabled")


class _ProgramTerminalRejectDecision(_DecisionVariantValue):
    __slots__ = ()
    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn: raise TypeError("subclassing disabled")


class _ProgramBlockDecision(_DecisionVariantValue):
    __slots__ = ()
    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn: raise TypeError("subclassing disabled")


class _ProductiveRedeliveryDecision(_DecisionVariantValue):
    __slots__ = ()
    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn: raise TypeError("subclassing disabled")


class _CancellationRedeliveryDecision(_DecisionVariantValue):
    __slots__ = ()
    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn: raise TypeError("subclassing disabled")


class _EffectCancellationDecision(_DecisionVariantValue):
    __slots__ = ()
    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn: raise TypeError("subclassing disabled")


class DevelopmentDecisionRowValue(_ImmutableValue):
    __slots__ = ("_values",)
    __hash__ = None

    @property
    def decision(self) -> _DecisionVariantValue: return typing.cast(_DecisionVariantValue,self._values[0])
    @property
    def variant_value(self) -> _DecisionVariantValue: return self.decision
    def _field(self, index: int) -> object: return self.decision._values[index]
    @property
    def schema_id(self)->str:return typing.cast(str,self._field(0))
    @property
    def mutation_ref(self)->str:return typing.cast(str,self._field(1))
    @property
    def decision_ref(self)->str:return typing.cast(str,self._field(2))
    @property
    def program_ref(self)->str:return typing.cast(str,self._field(3))
    @property
    def decision_kind(self)->str:return typing.cast(str,self._field(4))
    @property
    def decision_variant(self)->str:return typing.cast(str,self._field(5))
    @property
    def basis_decision_ref(self)->str|None:return typing.cast(str|None,self._field(6))
    @property
    def basis_program_version_ref(self)->str|None:return typing.cast(str|None,self._field(7))
    @property
    def basis_program_version_number(self)->int|None:return typing.cast(int|None,self._field(8))
    @property
    def expected_program_head_revision(self)->int:return typing.cast(int,self._field(9))
    @property
    def resulting_program_version_ref(self)->str|None:return typing.cast(str|None,self._field(10))
    @property
    def resulting_program_version_number(self)->int|None:return typing.cast(int|None,self._field(11))
    @property
    def selected_semantic_attempt_ref(self)->str|None:return typing.cast(str|None,self._field(12))
    @property
    def selected_candidate_ref(self)->str|None:return typing.cast(str|None,self._field(13))
    @property
    def selected_attempt_fence_ref(self)->str|None:return typing.cast(str|None,self._field(14))
    @property
    def selected_attempt_fence_digest(self)->str|None:return typing.cast(str|None,self._field(15))
    @property
    def target_effect_intent_ref(self)->str|None:return typing.cast(str|None,self._field(16))
    @property
    def target_effect_class(self)->str|None:return typing.cast(str|None,self._field(17))
    @property
    def target_effect_fence_ref(self)->str|None:return typing.cast(str|None,self._field(18))
    @property
    def target_effect_fence_digest(self)->str|None:return typing.cast(str|None,self._field(19))
    @property
    def expected_target_effect_head_revision(self)->int|None:return typing.cast(int|None,self._field(20))
    @property
    def target_delivery_attempt_ref(self)->str|None:return typing.cast(str|None,self._field(21))
    @property
    def originating_command_ref(self)->str|None:return typing.cast(str|None,self._field(22))
    @property
    def originating_command_digest(self)->str|None:return typing.cast(str|None,self._field(23))
    @property
    def target_capsule_manifest_ref(self)->str|None:return typing.cast(str|None,self._field(24))
    @property
    def target_portable_capsule_digest(self)->str|None:return typing.cast(str|None,self._field(25))
    @property
    def coding_global_stop_ref(self)->str:return typing.cast(str,self._field(26))
    @property
    def coding_global_stop_version(self)->int:return typing.cast(int,self._field(27))
    @property
    def source_directive_ref(self)->str|None:return typing.cast(str|None,self._field(28))
    @property
    def source_directive_digest(self)->str|None:return typing.cast(str|None,self._field(29))
    @property
    def source_evidence_ref(self)->str|None:return typing.cast(str|None,self._field(30))
    @property
    def source_evidence_digest(self)->str|None:return typing.cast(str|None,self._field(31))
    @property
    def preassigned_semantic_attempt_ref(self)->str|None:return typing.cast(str|None,self._field(32))
    @property
    def preassigned_candidate_ref(self)->str|None:return typing.cast(str|None,self._field(33))
    @property
    def preassigned_effect_intent_ref(self)->str|None:return typing.cast(str|None,self._field(34))
    @property
    def preassigned_effect_fence_ref(self)->str|None:return typing.cast(str|None,self._field(35))
    @property
    def preassigned_delivery_attempt_ref(self)->str|None:return typing.cast(str|None,self._field(36))
    @property
    def resulting_accepted_intent_revision_ref(self)->str|None:return typing.cast(str|None,self._field(37))
    @property
    def resulting_work_item_ref(self)->str|None:return typing.cast(str|None,self._field(38))
    @property
    def resulting_work_item_revision_ref(self)->str|None:return typing.cast(str|None,self._field(39))
    @property
    def reason_code(self)->str:return typing.cast(str,self._field(40))
    @property
    def decided_at(self)->str:return typing.cast(str,self._field(41))
    @property
    def decision_digest(self)->str:return typing.cast(str,self._values[1])

    def identity_mapping(self)->dict[str,object]:
        return {
            "schema_id":self.schema_id,"mutation_ref":self.mutation_ref,
            "decision_ref":self.decision_ref,"program_ref":self.program_ref,
            "decision_kind":self.decision_kind,"decision_variant":self.decision_variant,
            "basis_decision_ref":self.basis_decision_ref,
            "basis_program_version_ref":self.basis_program_version_ref,
            "basis_program_version_number":self.basis_program_version_number,
            "expected_program_head_revision":self.expected_program_head_revision,
            "resulting_program_version_ref":self.resulting_program_version_ref,
            "resulting_program_version_number":self.resulting_program_version_number,
            "selected_semantic_attempt_ref":self.selected_semantic_attempt_ref,
            "selected_candidate_ref":self.selected_candidate_ref,
            "selected_attempt_fence_ref":self.selected_attempt_fence_ref,
            "selected_attempt_fence_digest":self.selected_attempt_fence_digest,
            "target_effect_intent_ref":self.target_effect_intent_ref,
            "target_effect_class":self.target_effect_class,
            "target_effect_fence_ref":self.target_effect_fence_ref,
            "target_effect_fence_digest":self.target_effect_fence_digest,
            "expected_target_effect_head_revision":self.expected_target_effect_head_revision,
            "target_delivery_attempt_ref":self.target_delivery_attempt_ref,
            "originating_command_ref":self.originating_command_ref,
            "originating_command_digest":self.originating_command_digest,
            "target_capsule_manifest_ref":self.target_capsule_manifest_ref,
            "target_portable_capsule_digest":self.target_portable_capsule_digest,
            "coding_global_stop_ref":self.coding_global_stop_ref,
            "coding_global_stop_version":self.coding_global_stop_version,
            "source_directive_ref":self.source_directive_ref,
            "source_directive_digest":self.source_directive_digest,
            "source_evidence_ref":self.source_evidence_ref,
            "source_evidence_digest":self.source_evidence_digest,
            "preassigned_semantic_attempt_ref":self.preassigned_semantic_attempt_ref,
            "preassigned_candidate_ref":self.preassigned_candidate_ref,
            "preassigned_effect_intent_ref":self.preassigned_effect_intent_ref,
            "preassigned_effect_fence_ref":self.preassigned_effect_fence_ref,
            "preassigned_delivery_attempt_ref":self.preassigned_delivery_attempt_ref,
            "resulting_accepted_intent_revision_ref":self.resulting_accepted_intent_revision_ref,
            "resulting_work_item_ref":self.resulting_work_item_ref,
            "resulting_work_item_revision_ref":self.resulting_work_item_revision_ref,
            "reason_code":self.reason_code,"decided_at":self.decided_at,
        }

    def canonical_identity_bytes(self)->bytes:return _canonical_identity_bytes(self.identity_mapping())
    def computed_digest(self)->str:return _domain_separated_digest(_DEVELOPMENT_DECISION_DOMAIN,self.identity_mapping())
    @classmethod
    def _from_validated(cls,variant:_DecisionVariantValue,digest:str)->DevelopmentDecisionRowValue:
        result=object.__new__(cls);object.__setattr__(result,"_values",(variant,digest));return result
    def __init_subclass__(cls,**kwargs:object)->typing.NoReturn:raise TypeError("subclassing disabled")


class _ResultProjectionValue(_ImmutableValue):
    __slots__ = ()
    _DOMAIN = ""

    def canonical_identity_bytes(self) -> bytes:
        return _canonical_identity_bytes(self.identity_mapping())

    def computed_digest(self) -> str:
        return _domain_separated_digest(self._DOMAIN, self.identity_mapping())


class _InitializeDevelopmentProgramResultProjection(_ResultProjectionValue):
    __slots__=("_values",)
    _DOMAIN=_INITIALIZE_RESULT_DOMAIN
    @property
    def schema_id(self)->str:return typing.cast(str,self._values[0])
    @property
    def program_ref(self)->str:return typing.cast(str,self._values[1])
    @property
    def decision_ref(self)->str:return typing.cast(str,self._values[2])
    @property
    def result_program_version_ref(self)->str:return typing.cast(str,self._values[3])
    @property
    def result_decision_ref(self)->str:return typing.cast(str,self._values[4])
    @property
    def result_projection_digest(self)->str:return typing.cast(str,self._values[5])
    def identity_mapping(self)->dict[str,object]:return {"schema_id":self.schema_id,"program_ref":self.program_ref,"decision_ref":self.decision_ref,"result_program_version_ref":self.result_program_version_ref,"result_decision_ref":self.result_decision_ref}
    @classmethod
    def _from_validated(cls,values:tuple[object,...])->_InitializeDevelopmentProgramResultProjection:
        result=object.__new__(cls);object.__setattr__(result,"_values",values);return result
    def __init_subclass__(cls,**kwargs:object)->typing.NoReturn:raise TypeError("subclassing disabled")


class _EstablishDevelopmentAuthorEffectIntentResultProjection(_ResultProjectionValue):
    __slots__=("_values",)
    _DOMAIN=_AUTHOR_EFFECT_RESULT_DOMAIN
    @property
    def schema_id(self)->str:return typing.cast(str,self._values[0])
    @property
    def program_ref(self)->str:return typing.cast(str,self._values[1])
    @property
    def decision_ref(self)->str:return typing.cast(str,self._values[2])
    @property
    def result_program_version_ref(self)->str:return typing.cast(str,self._values[3])
    @property
    def result_semantic_attempt_ref(self)->str:return typing.cast(str,self._values[4])
    @property
    def result_effect_intent_ref(self)->str:return typing.cast(str,self._values[5])
    @property
    def result_effect_fence_ref(self)->str:return typing.cast(str,self._values[6])
    @property
    def result_delivery_attempt_ref(self)->str:return typing.cast(str,self._values[7])
    @property
    def result_projection_digest(self)->str:return typing.cast(str,self._values[8])
    def identity_mapping(self)->dict[str,object]:return {"schema_id":self.schema_id,"program_ref":self.program_ref,"decision_ref":self.decision_ref,"result_program_version_ref":self.result_program_version_ref,"result_semantic_attempt_ref":self.result_semantic_attempt_ref,"result_effect_intent_ref":self.result_effect_intent_ref,"result_effect_fence_ref":self.result_effect_fence_ref,"result_delivery_attempt_ref":self.result_delivery_attempt_ref}
    @classmethod
    def _from_validated(cls,values:tuple[object,...])->_EstablishDevelopmentAuthorEffectIntentResultProjection:
        result=object.__new__(cls);object.__setattr__(result,"_values",values);return result
    def __init_subclass__(cls,**kwargs:object)->typing.NoReturn:raise TypeError("subclassing disabled")


class _EstablishDevelopmentBoundEffectIntentResultProjection(_ResultProjectionValue):
    __slots__=("_values",)
    _DOMAIN=_BOUND_EFFECT_RESULT_DOMAIN
    @property
    def schema_id(self)->str:return typing.cast(str,self._values[0])
    @property
    def program_ref(self)->str:return typing.cast(str,self._values[1])
    @property
    def decision_ref(self)->str:return typing.cast(str,self._values[2])
    @property
    def result_program_version_ref(self)->str:return typing.cast(str,self._values[3])
    @property
    def result_semantic_attempt_ref(self)->str:return typing.cast(str,self._values[4])
    @property
    def result_effect_intent_ref(self)->str:return typing.cast(str,self._values[5])
    @property
    def result_effect_fence_ref(self)->str:return typing.cast(str,self._values[6])
    @property
    def result_delivery_attempt_ref(self)->str:return typing.cast(str,self._values[7])
    @property
    def result_projection_digest(self)->str:return typing.cast(str,self._values[8])
    def identity_mapping(self)->dict[str,object]:return {"schema_id":self.schema_id,"program_ref":self.program_ref,"decision_ref":self.decision_ref,"result_program_version_ref":self.result_program_version_ref,"result_semantic_attempt_ref":self.result_semantic_attempt_ref,"result_effect_intent_ref":self.result_effect_intent_ref,"result_effect_fence_ref":self.result_effect_fence_ref,"result_delivery_attempt_ref":self.result_delivery_attempt_ref}
    @classmethod
    def _from_validated(cls,values:tuple[object,...])->_EstablishDevelopmentBoundEffectIntentResultProjection:
        result=object.__new__(cls);object.__setattr__(result,"_values",values);return result
    def __init_subclass__(cls,**kwargs:object)->typing.NoReturn:raise TypeError("subclassing disabled")


class _IngestDevelopmentSourceObservationResultProjection(_ResultProjectionValue):
    __slots__=("_values",)
    _DOMAIN=_OBSERVATION_RESULT_DOMAIN
    @property
    def schema_id(self)->str:return typing.cast(str,self._values[0])
    @property
    def program_ref(self)->str:return typing.cast(str,self._values[1])
    @property
    def result_observation_ref(self)->str:return typing.cast(str,self._values[2])
    @property
    def result_projection_digest(self)->str:return typing.cast(str,self._values[3])
    def identity_mapping(self)->dict[str,object]:return {"schema_id":self.schema_id,"program_ref":self.program_ref,"result_observation_ref":self.result_observation_ref}
    @classmethod
    def _from_validated(cls,values:tuple[object,...])->_IngestDevelopmentSourceObservationResultProjection:
        result=object.__new__(cls);object.__setattr__(result,"_values",values);return result
    def __init_subclass__(cls,**kwargs:object)->typing.NoReturn:raise TypeError("subclassing disabled")


class _RecordDevelopmentProgressionDecisionResultProjection(_ResultProjectionValue):
    __slots__=("_values",)
    _DOMAIN=_PROGRESSION_RESULT_DOMAIN
    @property
    def schema_id(self)->str:return typing.cast(str,self._values[0])
    @property
    def program_ref(self)->str:return typing.cast(str,self._values[1])
    @property
    def decision_ref(self)->str:return typing.cast(str,self._values[2])
    @property
    def result_program_version_ref(self)->str:return typing.cast(str,self._values[3])
    @property
    def result_decision_ref(self)->str:return typing.cast(str,self._values[4])
    @property
    def result_projection_digest(self)->str:return typing.cast(str,self._values[5])
    def identity_mapping(self)->dict[str,object]:return {"schema_id":self.schema_id,"program_ref":self.program_ref,"decision_ref":self.decision_ref,"result_program_version_ref":self.result_program_version_ref,"result_decision_ref":self.result_decision_ref}
    @classmethod
    def _from_validated(cls,values:tuple[object,...])->_RecordDevelopmentProgressionDecisionResultProjection:
        result=object.__new__(cls);object.__setattr__(result,"_values",values);return result
    def __init_subclass__(cls,**kwargs:object)->typing.NoReturn:raise TypeError("subclassing disabled")


class DevelopmentMutationReceiptRowValue(_ImmutableValue):
    __slots__=("_values",)
    @property
    def schema_id(self)->str:return typing.cast(str,self._values[0])
    @property
    def mutation_ref(self)->str:return typing.cast(str,self._values[1])
    @property
    def mutation_family(self)->str:return typing.cast(str,self._values[2])
    @property
    def command_schema_id(self)->str:return typing.cast(str,self._values[3])
    @property
    def command_digest(self)->str:return typing.cast(str,self._values[4])
    @property
    def program_ref(self)->str:return typing.cast(str,self._values[5])
    @property
    def decision_ref(self)->str|None:return typing.cast(str|None,self._values[6])
    @property
    def result_program_version_ref(self)->str|None:return typing.cast(str|None,self._values[7])
    @property
    def result_semantic_attempt_ref(self)->str|None:return typing.cast(str|None,self._values[8])
    @property
    def result_effect_intent_ref(self)->str|None:return typing.cast(str|None,self._values[9])
    @property
    def result_effect_fence_ref(self)->str|None:return typing.cast(str|None,self._values[10])
    @property
    def result_delivery_attempt_ref(self)->str|None:return typing.cast(str|None,self._values[11])
    @property
    def result_observation_ref(self)->str|None:return typing.cast(str|None,self._values[12])
    @property
    def result_decision_ref(self)->str|None:return typing.cast(str|None,self._values[13])
    @property
    def result_class(self)->str:return typing.cast(str,self._values[14])
    @property
    def result_projection_digest(self)->str:return typing.cast(str,self._values[15])
    @property
    def mutation_graph_digest(self)->str:return typing.cast(str,self._values[16])
    @property
    def outcome(self)->str:return typing.cast(str,self._values[17])
    @property
    def committed_at(self)->str:return typing.cast(str,self._values[18])
    @property
    def result_projection(self)->_ResultProjectionValue:return typing.cast(_ResultProjectionValue,self._values[19])
    @classmethod
    def _from_validated(cls,values:tuple[object,...],projection:_ResultProjectionValue)->DevelopmentMutationReceiptRowValue:
        result=object.__new__(cls);object.__setattr__(result,"_values",values+(projection,));return result
    def __init_subclass__(cls,**kwargs:object)->typing.NoReturn:raise TypeError("subclassing disabled")


class DevelopmentMutationGraphEntry(_ImmutableValue):
    __slots__=("_values",)
    @property
    def role(self)->str:return typing.cast(str,self._values[0])
    @property
    def ordinal(self)->int:return typing.cast(int,self._values[1])
    @property
    def record_ref(self)->str:return typing.cast(str,self._values[2])
    @property
    def record_digest(self)->str:return typing.cast(str,self._values[3])
    @classmethod
    def _from_validated(cls,values:tuple[object,...])->DevelopmentMutationGraphEntry:
        result=object.__new__(cls);object.__setattr__(result,"_values",values);return result
    def __init_subclass__(cls,**kwargs:object)->typing.NoReturn:raise TypeError("subclassing disabled")


def _all_present(values: tuple[object, ...]) -> bool:
    return all(value is not None for value in values)


def _all_absent(values: tuple[object, ...]) -> bool:
    return all(value is None for value in values)


def _decision_identity_from_values(values: tuple[object, ...]) -> dict[str, object]:
    return {
        "schema_id":values[0],"mutation_ref":values[1],"decision_ref":values[2],
        "program_ref":values[3],"decision_kind":values[4],"decision_variant":values[5],
        "basis_decision_ref":values[6],"basis_program_version_ref":values[7],
        "basis_program_version_number":values[8],"expected_program_head_revision":values[9],
        "resulting_program_version_ref":values[10],"resulting_program_version_number":values[11],
        "selected_semantic_attempt_ref":values[12],"selected_candidate_ref":values[13],
        "selected_attempt_fence_ref":values[14],"selected_attempt_fence_digest":values[15],
        "target_effect_intent_ref":values[16],"target_effect_class":values[17],
        "target_effect_fence_ref":values[18],"target_effect_fence_digest":values[19],
        "expected_target_effect_head_revision":values[20],"target_delivery_attempt_ref":values[21],
        "originating_command_ref":values[22],"originating_command_digest":values[23],
        "target_capsule_manifest_ref":values[24],"target_portable_capsule_digest":values[25],
        "coding_global_stop_ref":values[26],"coding_global_stop_version":values[27],
        "source_directive_ref":values[28],"source_directive_digest":values[29],
        "source_evidence_ref":values[30],"source_evidence_digest":values[31],
        "preassigned_semantic_attempt_ref":values[32],"preassigned_candidate_ref":values[33],
        "preassigned_effect_intent_ref":values[34],"preassigned_effect_fence_ref":values[35],
        "preassigned_delivery_attempt_ref":values[36],
        "resulting_accepted_intent_revision_ref":values[37],
        "resulting_work_item_ref":values[38],"resulting_work_item_revision_ref":values[39],
        "reason_code":values[40],"decided_at":values[41],
    }


def _validated_decision_variant(
    mapping: dict[str, object],
) -> _DecisionVariantValue:
    values = (
        _require_constant_string(mapping["schema_id"], _DEVELOPMENT_DECISION_SCHEMA),
        _require_safe_ref(mapping["mutation_ref"]),
        _require_safe_ref(mapping["decision_ref"]),
        _require_safe_ref(mapping["program_ref"]),
        _require_enum(mapping["decision_kind"], _DECISION_KINDS),
        _require_enum(mapping["decision_variant"], _DECISION_VARIANTS),
        _require_optional_safe_ref(mapping["basis_decision_ref"]),
        _require_optional_safe_ref(mapping["basis_program_version_ref"]),
        _require_optional_positive_integer(mapping["basis_program_version_number"]),
        _require_nonnegative_integer(mapping["expected_program_head_revision"]),
        _require_optional_safe_ref(mapping["resulting_program_version_ref"]),
        _require_optional_positive_integer(mapping["resulting_program_version_number"]),
        _require_optional_safe_ref(mapping["selected_semantic_attempt_ref"]),
        _require_optional_safe_ref(mapping["selected_candidate_ref"]),
        _require_optional_safe_ref(mapping["selected_attempt_fence_ref"]),
        _require_optional_sha256(mapping["selected_attempt_fence_digest"]),
        _require_optional_safe_ref(mapping["target_effect_intent_ref"]),
        _require_optional_enum(mapping["target_effect_class"], _TARGET_EFFECT_CLASSES),
        _require_optional_safe_ref(mapping["target_effect_fence_ref"]),
        _require_optional_sha256(mapping["target_effect_fence_digest"]),
        _require_optional_nonnegative_integer(mapping["expected_target_effect_head_revision"]),
        _require_optional_safe_ref(mapping["target_delivery_attempt_ref"]),
        _require_optional_safe_ref(mapping["originating_command_ref"]),
        _require_optional_sha256(mapping["originating_command_digest"]),
        _require_optional_safe_ref(mapping["target_capsule_manifest_ref"]),
        _require_optional_sha256(mapping["target_portable_capsule_digest"]),
        _require_safe_ref(mapping["coding_global_stop_ref"]),
        _require_nonnegative_integer(mapping["coding_global_stop_version"]),
        _require_optional_safe_ref(mapping["source_directive_ref"]),
        _require_optional_sha256(mapping["source_directive_digest"]),
        _require_optional_safe_ref(mapping["source_evidence_ref"]),
        _require_optional_sha256(mapping["source_evidence_digest"]),
        _require_optional_safe_ref(mapping["preassigned_semantic_attempt_ref"]),
        _require_optional_safe_ref(mapping["preassigned_candidate_ref"]),
        _require_optional_safe_ref(mapping["preassigned_effect_intent_ref"]),
        _require_optional_safe_ref(mapping["preassigned_effect_fence_ref"]),
        _require_optional_safe_ref(mapping["preassigned_delivery_attempt_ref"]),
        _require_optional_safe_ref(mapping["resulting_accepted_intent_revision_ref"]),
        _require_optional_safe_ref(mapping["resulting_work_item_ref"]),
        _require_optional_safe_ref(mapping["resulting_work_item_revision_ref"]),
        _require_reason_code(mapping["reason_code"]),
        _require_utc_timestamp(mapping["decided_at"]),
    )
    kind = typing.cast(str, values[4])
    variant_name = typing.cast(str, values[5])
    basis = values[6:9]
    result_version = values[10:12]
    selection = values[12:16]
    target_effect = values[16:21]
    target_delivery = values[21:22]
    originating_command = values[22:24]
    capsule = values[24:26]
    source = values[28:32]
    preassigned_attempt = values[32:34]
    preassigned_effect = values[34:36]
    preassigned_delivery = values[36:37]
    result_intent = values[37:38]
    result_work = values[38:40]

    variant: _DecisionVariantValue
    if (
        kind == "initialize" and variant_name == "program_genesis"
        and _all_absent(basis) and _all_present(result_version)
        and _all_absent(selection) and _all_absent(target_effect)
        and _all_absent(target_delivery) and _all_absent(originating_command)
        and _all_absent(capsule) and _all_absent(source)
        and _all_present(preassigned_attempt) and _all_absent(preassigned_effect)
        and _all_absent(preassigned_delivery) and _all_absent(result_intent)
        and _all_absent(result_work) and values[9] == 0 and values[11] == 1
    ):
        variant = object.__new__(_ProgramGenesisDecision)
    elif (
        kind == "accept" and variant_name == "candidate_acceptance"
        and _all_present(basis) and _all_present(result_version)
        and _all_present(selection) and _all_absent(target_effect)
        and _all_absent(target_delivery) and _all_absent(originating_command)
        and _all_absent(capsule) and _all_absent(source)
        and _all_absent(preassigned_attempt) and _all_absent(preassigned_effect)
        and _all_absent(preassigned_delivery) and _all_absent(result_intent)
        and _all_absent(result_work)
    ):
        variant = object.__new__(_CandidateAcceptanceDecision)
    elif (
        kind == "repair" and variant_name == "candidate_repair"
        and _all_present(basis) and _all_present(result_version)
        and _all_present(selection) and _all_absent(target_effect)
        and _all_absent(target_delivery) and _all_absent(originating_command)
        and _all_absent(capsule) and _all_absent(source)
        and _all_present(preassigned_attempt) and _all_absent(preassigned_effect)
        and _all_absent(preassigned_delivery) and _all_absent(result_intent)
        and _all_absent(result_work)
    ):
        variant = object.__new__(_CandidateRepairDecision)
    elif (
        kind == "replan" and variant_name == "program_replan"
        and _all_present(basis) and _all_present(result_version)
        and _all_absent(selection) and _all_absent(target_effect)
        and _all_absent(target_delivery) and _all_absent(originating_command)
        and _all_absent(capsule) and _all_absent(source)
        and _all_absent(preassigned_attempt) and _all_absent(preassigned_effect)
        and _all_absent(preassigned_delivery) and _all_present(result_intent)
        and _all_absent(result_work)
    ):
        variant = object.__new__(_ProgramReplanDecision)
    elif (
        kind == "replan" and variant_name == "attempt_selecting_replan"
        and _all_present(basis) and _all_present(result_version)
        and _all_present(selection) and _all_absent(target_effect)
        and _all_absent(target_delivery) and _all_absent(originating_command)
        and _all_absent(capsule) and _all_absent(source)
        and _all_present(preassigned_attempt) and _all_absent(preassigned_effect)
        and _all_absent(preassigned_delivery) and _all_present(result_intent)
        and _all_present(result_work)
    ):
        variant = object.__new__(_AttemptSelectingReplanDecision)
    elif (
        kind == "terminal_reject" and variant_name == "program_terminal_reject"
        and _all_present(basis) and _all_present(result_version)
        and _all_present(selection) and _all_absent(target_effect)
        and _all_absent(target_delivery) and _all_absent(originating_command)
        and _all_absent(capsule) and _all_absent(source)
        and _all_absent(preassigned_attempt) and _all_absent(preassigned_effect)
        and _all_absent(preassigned_delivery) and _all_absent(result_intent)
        and _all_absent(result_work)
    ):
        variant = object.__new__(_ProgramTerminalRejectDecision)
    elif (
        kind == "block" and variant_name == "program_block"
        and _all_present(basis) and _all_present(result_version)
        and _all_absent(selection) and _all_absent(target_effect)
        and _all_absent(target_delivery) and _all_absent(originating_command)
        and _all_absent(capsule) and _all_absent(source)
        and _all_absent(preassigned_attempt) and _all_absent(preassigned_effect)
        and _all_absent(preassigned_delivery) and _all_absent(result_intent)
        and _all_absent(result_work)
    ):
        variant = object.__new__(_ProgramBlockDecision)
    elif (
        kind == "redeliver" and variant_name == "productive_redelivery"
        and _all_present(basis) and _all_absent(result_version)
        and _all_present(selection) and _all_present(target_effect)
        and _all_present(target_delivery) and _all_present(originating_command)
        and _all_absent(capsule) and _all_absent(source)
        and _all_absent(preassigned_attempt) and _all_absent(preassigned_effect)
        and _all_present(preassigned_delivery) and _all_absent(result_intent)
        and _all_absent(result_work)
        and values[17] in ("author_candidate", "validate_candidate", "review_candidate")
    ):
        variant = object.__new__(_ProductiveRedeliveryDecision)
    elif (
        kind == "redeliver" and variant_name == "cancellation_redelivery"
        and _all_present(basis) and _all_absent(result_version)
        and _all_present(selection) and _all_present(target_effect)
        and _all_present(target_delivery) and _all_present(originating_command)
        and _all_absent(capsule) and _all_absent(source)
        and _all_absent(preassigned_attempt) and _all_absent(preassigned_effect)
        and _all_present(preassigned_delivery) and _all_absent(result_intent)
        and _all_absent(result_work) and values[17] == "cancel_effect"
    ):
        variant = object.__new__(_CancellationRedeliveryDecision)
    elif (
        kind == "cancel" and variant_name == "effect_cancellation"
        and _all_present(basis) and _all_absent(result_version)
        and _all_present(selection) and _all_present(target_effect)
        and _all_absent(target_delivery) and _all_present(originating_command)
        and _all_present(source) and _all_absent(preassigned_attempt)
        and _all_present(preassigned_effect) and _all_present(preassigned_delivery)
        and _all_absent(result_intent) and _all_absent(result_work)
        and values[17] in ("author_candidate", "validate_candidate", "review_candidate")
        and (
            (values[17] == "author_candidate" and _all_absent(capsule))
            or (values[17] in ("validate_candidate", "review_candidate") and _all_present(capsule))
        )
    ):
        variant = object.__new__(_EffectCancellationDecision)
    else:
        raise _RowValueValidationError() from None
    object.__setattr__(variant, "_values", values)
    return variant


def _attempt_decision(
    row: object,
) -> tuple[DevelopmentDecisionRowValue | None, BaseException | None]:
    mapping: dict[str, object] | None = None
    result: DevelopmentDecisionRowValue | None = None
    error: BaseException | None = None
    try:
        mapping = _row_tuple_to_private_mapping(columns=_DEVELOPMENT_DECISION_COLUMNS,row=row)
        variant = _validated_decision_variant(mapping)
        identity = _decision_identity_from_values(variant._values)
        digest = _require_matching_digest(
            domain=_DEVELOPMENT_DECISION_DOMAIN,
            identity=identity,
            stored_digest=mapping["decision_digest"],
        )
        result = DevelopmentDecisionRowValue._from_validated(variant,digest)
    except _RowValueValidationError:
        error = _new_database_integrity_error()
    finally:
        mapping = None
        row = None
    return result,error


def development_decision_row_value_from_row_tuple(row:object)->DevelopmentDecisionRowValue:
    result,error=_attempt_decision(row)
    row=None
    if error is not None:raise error from None
    return typing.cast(DevelopmentDecisionRowValue,result)


def _validated_receipt_and_projection(
    mapping: dict[str, object],
) -> tuple[tuple[object, ...], _ResultProjectionValue]:
    values = (
        _require_constant_string(mapping["schema_id"], _DEVELOPMENT_MUTATION_RECEIPT_SCHEMA),
        _require_safe_ref(mapping["mutation_ref"]),
        _require_enum(mapping["mutation_family"], _MUTATION_FAMILIES),
        _require_enum(mapping["command_schema_id"], _COMMAND_SCHEMA_IDS),
        _require_sha256(mapping["command_digest"]),
        _require_safe_ref(mapping["program_ref"]),
        _require_optional_safe_ref(mapping["decision_ref"]),
        _require_optional_safe_ref(mapping["result_program_version_ref"]),
        _require_optional_safe_ref(mapping["result_semantic_attempt_ref"]),
        _require_optional_safe_ref(mapping["result_effect_intent_ref"]),
        _require_optional_safe_ref(mapping["result_effect_fence_ref"]),
        _require_optional_safe_ref(mapping["result_delivery_attempt_ref"]),
        _require_optional_safe_ref(mapping["result_observation_ref"]),
        _require_optional_safe_ref(mapping["result_decision_ref"]),
        _require_enum(mapping["result_class"], _RESULT_CLASSES),
        _require_sha256(mapping["result_projection_digest"]),
        _require_sha256(mapping["mutation_graph_digest"]),
        _require_constant_string(mapping["outcome"], "committed"),
        _require_utc_timestamp(mapping["committed_at"]),
    )
    family=values[2]; command_schema=values[3]; result_class=values[14]
    decision_ref=values[6]; version_ref=values[7]; attempt_ref=values[8]
    effect_intent_ref=values[9]; effect_fence_ref=values[10]
    delivery_ref=values[11]; observation_ref=values[12]; result_decision_ref=values[13]
    stored_digest=values[15]
    projection: _ResultProjectionValue
    if (
        family == "initialize_development_program"
        and command_schema == _COMMAND_SCHEMA_IDS[0]
        and result_class == _RESULT_CLASSES[0]
        and decision_ref is not None and version_ref is not None
        and attempt_ref is None and effect_intent_ref is None and effect_fence_ref is None
        and delivery_ref is None and observation_ref is None
        and result_decision_ref == decision_ref
    ):
        projection_values=(
            _INITIALIZE_RESULT_SCHEMA,values[5],decision_ref,version_ref,result_decision_ref,
        )
        identity={"schema_id":projection_values[0],"program_ref":projection_values[1],
            "decision_ref":projection_values[2],"result_program_version_ref":projection_values[3],
            "result_decision_ref":projection_values[4]}
        digest=_require_matching_digest(domain=_INITIALIZE_RESULT_DOMAIN,identity=identity,stored_digest=stored_digest)
        projection=_InitializeDevelopmentProgramResultProjection._from_validated(projection_values+(digest,))
    elif (
        family == "establish_development_author_effect_intent"
        and command_schema == _COMMAND_SCHEMA_IDS[1]
        and result_class == _RESULT_CLASSES[1]
        and decision_ref is not None and version_ref is not None and attempt_ref is not None
        and effect_intent_ref is not None and effect_fence_ref is not None
        and delivery_ref is not None and observation_ref is None and result_decision_ref is None
    ):
        projection_values=(
            _AUTHOR_EFFECT_RESULT_SCHEMA,values[5],decision_ref,version_ref,attempt_ref,
            effect_intent_ref,effect_fence_ref,delivery_ref,
        )
        identity={"schema_id":projection_values[0],"program_ref":projection_values[1],
            "decision_ref":projection_values[2],"result_program_version_ref":projection_values[3],
            "result_semantic_attempt_ref":projection_values[4],
            "result_effect_intent_ref":projection_values[5],
            "result_effect_fence_ref":projection_values[6],
            "result_delivery_attempt_ref":projection_values[7]}
        digest=_require_matching_digest(domain=_AUTHOR_EFFECT_RESULT_DOMAIN,identity=identity,stored_digest=stored_digest)
        projection=_EstablishDevelopmentAuthorEffectIntentResultProjection._from_validated(projection_values+(digest,))
    elif (
        family == "establish_development_bound_effect_intent"
        and command_schema == _COMMAND_SCHEMA_IDS[2]
        and result_class == _RESULT_CLASSES[2]
        and decision_ref is not None and version_ref is not None and attempt_ref is not None
        and effect_intent_ref is not None and effect_fence_ref is not None
        and delivery_ref is not None and observation_ref is None and result_decision_ref is None
    ):
        projection_values=(
            _BOUND_EFFECT_RESULT_SCHEMA,values[5],decision_ref,version_ref,attempt_ref,
            effect_intent_ref,effect_fence_ref,delivery_ref,
        )
        identity={"schema_id":projection_values[0],"program_ref":projection_values[1],
            "decision_ref":projection_values[2],"result_program_version_ref":projection_values[3],
            "result_semantic_attempt_ref":projection_values[4],
            "result_effect_intent_ref":projection_values[5],
            "result_effect_fence_ref":projection_values[6],
            "result_delivery_attempt_ref":projection_values[7]}
        digest=_require_matching_digest(domain=_BOUND_EFFECT_RESULT_DOMAIN,identity=identity,stored_digest=stored_digest)
        projection=_EstablishDevelopmentBoundEffectIntentResultProjection._from_validated(projection_values+(digest,))
    elif (
        family == "ingest_development_source_observation"
        and command_schema == _COMMAND_SCHEMA_IDS[3]
        and result_class == _RESULT_CLASSES[3]
        and decision_ref is None and version_ref is None and attempt_ref is None
        and effect_intent_ref is None and effect_fence_ref is None and delivery_ref is None
        and observation_ref is not None and result_decision_ref is None
    ):
        projection_values=(_OBSERVATION_RESULT_SCHEMA,values[5],observation_ref)
        identity={"schema_id":projection_values[0],"program_ref":projection_values[1],
            "result_observation_ref":projection_values[2]}
        digest=_require_matching_digest(domain=_OBSERVATION_RESULT_DOMAIN,identity=identity,stored_digest=stored_digest)
        projection=_IngestDevelopmentSourceObservationResultProjection._from_validated(projection_values+(digest,))
    elif (
        family == "record_development_progression_decision"
        and command_schema == _COMMAND_SCHEMA_IDS[4]
        and result_class == _RESULT_CLASSES[4]
        and decision_ref is not None and version_ref is not None
        and attempt_ref is None and effect_intent_ref is None and effect_fence_ref is None
        and delivery_ref is None and observation_ref is None
        and result_decision_ref == decision_ref
    ):
        projection_values=(
            _PROGRESSION_RESULT_SCHEMA,values[5],decision_ref,version_ref,result_decision_ref,
        )
        identity={"schema_id":projection_values[0],"program_ref":projection_values[1],
            "decision_ref":projection_values[2],"result_program_version_ref":projection_values[3],
            "result_decision_ref":projection_values[4]}
        digest=_require_matching_digest(domain=_PROGRESSION_RESULT_DOMAIN,identity=identity,stored_digest=stored_digest)
        projection=_RecordDevelopmentProgressionDecisionResultProjection._from_validated(projection_values+(digest,))
    else:
        raise _RowValueValidationError() from None
    return values,projection


def _attempt_mutation_receipt(
    row: object,
) -> tuple[DevelopmentMutationReceiptRowValue | None, BaseException | None]:
    mapping:dict[str,object]|None=None
    result:DevelopmentMutationReceiptRowValue|None=None
    error:BaseException|None=None
    try:
        mapping=_row_tuple_to_private_mapping(columns=_DEVELOPMENT_MUTATION_RECEIPT_COLUMNS,row=row)
        values,projection=_validated_receipt_and_projection(mapping)
        result=DevelopmentMutationReceiptRowValue._from_validated(values,projection)
    except _RowValueValidationError:
        error=_new_database_integrity_error()
    finally:
        mapping=None
        row=None
    return result,error


def development_mutation_receipt_row_value_from_row_tuple(
    row:object,
)->DevelopmentMutationReceiptRowValue:
    result,error=_attempt_mutation_receipt(row)
    row=None
    if error is not None:raise error from None
    return typing.cast(DevelopmentMutationReceiptRowValue,result)


def _attempt_graph_entry(
    role:object,
    ordinal:object,
    record_ref:object,
    record_digest:object,
)->tuple[DevelopmentMutationGraphEntry|None,BaseException|None]:
    result:DevelopmentMutationGraphEntry|None=None
    error:BaseException|None=None
    try:
        result=DevelopmentMutationGraphEntry._from_validated((
            _require_nonempty_string(role),
            _require_nonnegative_integer(ordinal),
            _require_safe_ref(record_ref),
            _require_sha256(record_digest),
        ))
    except _RowValueValidationError:
        error=_new_database_integrity_error()
    finally:
        role=None;ordinal=None;record_ref=None;record_digest=None
    return result,error


def development_mutation_graph_entry(
    *,role:object,ordinal:object,record_ref:object,record_digest:object,
)->DevelopmentMutationGraphEntry:
    result,error=_attempt_graph_entry(role,ordinal,record_ref,record_digest)
    role=None;ordinal=None;record_ref=None;record_digest=None
    if error is not None:raise error from None
    return typing.cast(DevelopmentMutationGraphEntry,result)


def _receipt_graph_identity(
    receipt:DevelopmentMutationReceiptRowValue,
    entries:tuple[DevelopmentMutationGraphEntry,...],
)->dict[str,object]:
    return {
        "schema_id":receipt.schema_id,"mutation_ref":receipt.mutation_ref,
        "mutation_family":receipt.mutation_family,"command_schema_id":receipt.command_schema_id,
        "command_digest":receipt.command_digest,"program_ref":receipt.program_ref,
        "decision_ref":receipt.decision_ref,
        "result_program_version_ref":receipt.result_program_version_ref,
        "result_semantic_attempt_ref":receipt.result_semantic_attempt_ref,
        "result_effect_intent_ref":receipt.result_effect_intent_ref,
        "result_effect_fence_ref":receipt.result_effect_fence_ref,
        "result_delivery_attempt_ref":receipt.result_delivery_attempt_ref,
        "result_observation_ref":receipt.result_observation_ref,
        "result_decision_ref":receipt.result_decision_ref,"result_class":receipt.result_class,
        "result_projection_digest":receipt.result_projection_digest,"outcome":receipt.outcome,
        "committed_at":receipt.committed_at,
        "graph_entries":tuple(
            {"role":entry.role,"ordinal":entry.ordinal,"record_ref":entry.record_ref,
             "record_digest":entry.record_digest}
            for entry in entries
        ),
    }


def _attempt_graph_digest(
    receipt:object,
    graph_entries:object,
)->tuple[str|None,BaseException|None]:
    result:str|None=None
    error:BaseException|None=None
    try:
        if type(receipt) is not DevelopmentMutationReceiptRowValue:
            raise _RowValueValidationError() from None
        if type(graph_entries) is not tuple:
            raise _RowValueValidationError() from None
        entries=typing.cast(tuple[object,...],graph_entries)
        if any(type(entry) is not DevelopmentMutationGraphEntry for entry in entries):
            raise _RowValueValidationError() from None
        typed_entries=typing.cast(tuple[DevelopmentMutationGraphEntry,...],entries)
        role_ordinals:set[tuple[str,int]]=set()
        role_refs:set[tuple[str,str]]=set()
        for entry in typed_entries:
            role_ordinal=(entry.role,entry.ordinal)
            role_ref=(entry.role,entry.record_ref)
            if role_ordinal in role_ordinals or role_ref in role_refs:
                raise _RowValueValidationError() from None
            role_ordinals.add(role_ordinal)
            role_refs.add(role_ref)
        identity=_receipt_graph_identity(
            typing.cast(DevelopmentMutationReceiptRowValue,receipt),
            typed_entries,
        )
        result=_domain_separated_digest(_DEVELOPMENT_MUTATION_RECEIPT_DOMAIN,identity)
    except _RowValueValidationError:
        error=_new_database_integrity_error()
    finally:
        receipt=None;graph_entries=None
    return result,error


def compute_development_mutation_graph_digest(
    *,
    receipt:DevelopmentMutationReceiptRowValue,
    graph_entries:tuple[DevelopmentMutationGraphEntry,...],
)->str:
    result,error=_attempt_graph_digest(receipt,graph_entries)
    receipt=None;graph_entries=None
    if error is not None:raise error from None
    return typing.cast(str,result)


def require_development_mutation_graph_digest_matches_supplied_entries(
    *,
    receipt:DevelopmentMutationReceiptRowValue,
    graph_entries:tuple[DevelopmentMutationGraphEntry,...],
)->None:
    stored_digest:object=None
    result,error=_attempt_graph_digest(receipt,graph_entries)
    if type(receipt) is DevelopmentMutationReceiptRowValue:
        stored_digest=receipt.mutation_graph_digest
    receipt=None;graph_entries=None
    if error is None and result != stored_digest:
        error=_new_database_integrity_error()
    stored_digest=None
    if error is not None:raise error from None
