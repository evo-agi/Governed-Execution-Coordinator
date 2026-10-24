"""Private transaction-internal native post-execution proposal family."""

from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3
import typing

from . import _cognitive_proposal_row_values as _common
from . import _development_decision_row_values as _decision_rows
from ._cognitive_proposal_value_support import _CognitiveProposalContractViolation
from ._post_execution_evidence_values import (
    PostExecutionSemanticReviewInputContextV1, _domain_separated_digest,
)
from ._rw0_d2_handback import RW0D2OfflineRun
from ._rw0_d2b_model_input import RW0D2BInputConflict, require_current_d2_basis
from ._sqlite_rw0_c1 import (
    _read_membership_family, _read_receipt,
    _read_rw0_d2_current_owner_snapshot_after_fencing,
    _verify_evidence_family_rows,
)
from ._section41_post_execution_proposal_mutation_contracts import (
    _COMMITTED_DOMAIN, _GRAPH_DOMAIN, _PHASE, _ROLE_ORDER,
    PostExecutionProposalConflictV1, PostExecutionProposalRecoveryV1,
    RecordPostExecutionProposalCommandV1, RecordPostExecutionProposalResultV1,
    _ordered_typed_mapping, checked_safe_basis_bytes, prepare_record_command,
    safe_basis_digest,
)
from ._section41_post_execution_proposal_row_values import (
    _CONTEXT_COLUMNS, _CONTEXT_SCHEMA, _CONTEXT_TABLE, _RECEIPT_COLUMNS,
    _RECEIPT_SCHEMA, _RECEIPT_TABLE, PostExecutionProposalContextRowV1,
    PostExecutionProposalReceiptRowV1, row_from_tuple, seal_row,
)
from .sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from .sqlite_transition_select_support import (
    _MutationReadCapability, _execute_select_fetch_bounded,
)

__all__: tuple[str, ...] = ()

_COMMON = (
    _common._TABLE_ORDER[0], _common._TABLE_ORDER[2],
    _common._TABLE_ORDER[3], _common._TABLE_ORDER[5],
)
_EVIDENCE_DOMAIN = "governed-execution.nwp-model-proposal-evidence-set.v1.identity"


def _integrity() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def _mutation_failed() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)


def _select(
    capability: object, table: str, columns: tuple[str, ...], where: str,
    params: tuple[object, ...], *, limit: int, order: str = "",
) -> tuple[tuple[object, ...], ...]:
    if table not in (*_COMMON, _CONTEXT_TABLE, _RECEIPT_TABLE,
                     "rw0_evidence_memberships", "development_mutation_receipts",
                     "rw0_phase_instances", "rw0_c1_mutation_receipts"):
        raise _integrity() from None
    sql = (
        f"SELECT {', '.join(columns)} FROM {table} WHERE {where}"
        + (f" ORDER BY {order}" if order else "")
        + f" LIMIT {limit}"
    )
    if limit == 10:
        # The older shared SELECT support deliberately has no 10-row entry.
        # This family owns its one exact nine-plus-one overflow query.
        cursor: sqlite3.Cursor | None = None
        failure = False
        fetched: object = None
        try:
            connection = typing.cast(
                _MutationReadCapability, capability
            )._borrow_connection_for_select()
            if type(connection) is not sqlite3.Connection:
                raise TypeError("invalid nominal capability")
            cursor = connection.execute(sql, params)
            fetched = cursor.fetchmany(10)
        except Exception:
            failure = True
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    failure = True
        if failure or type(fetched) is not list:
            raise _mutation_failed() from None
    else:
        fetched = _execute_select_fetch_bounded(
            capability=typing.cast(_MutationReadCapability, capability),
            sql=sql, parameters=params, limit=limit,
        )
    if any(type(row) is not tuple or len(row) != len(columns) for row in fetched):
        raise _integrity() from None
    return typing.cast(tuple[tuple[object, ...], ...], tuple(fetched))


def _one(
    capability: object, table: str, columns: tuple[str, ...],
    where: str, params: tuple[object, ...],
) -> tuple[object, ...] | None:
    found = _select(capability, table, columns, where, params, limit=2)
    if len(found) > 1:
        raise _integrity() from None
    return found[0] if found else None


def _common_one(
    capability: object, table: str, where: str, params: tuple[object, ...],
) -> tuple[object, tuple[object, ...]]:
    raw = _one(capability, table, _common._TABLE_COLUMNS[table], where, params)
    if raw is None:
        raise _integrity() from None
    try:
        return _common._row_value_from_tuple(table, raw), raw
    except _CognitiveProposalContractViolation:
        raise _integrity() from None


def _evidence(
    capability: object, proposal_ref: str,
) -> tuple[tuple[object, ...], tuple[tuple[object, ...], ...]]:
    table = _common._TABLE_ORDER[5]
    raws = _select(
        capability, table, _common._TABLE_COLUMNS[table],
        "proposal_ref = ?", (proposal_ref,), limit=10,
        order="role_rank, ordinal",
    )
    if len(raws) != 9:
        raise _integrity() from None
    try:
        rows = tuple(_common._row_value_from_tuple(table, raw) for raw in raws)
    except _CognitiveProposalContractViolation:
        raise _integrity() from None
    if tuple((row.evidence_role, row.role_rank, row.ordinal)
             for row in rows) != tuple((name, rank, 0)
                                       for rank, name in enumerate(_ROLE_ORDER, 5)):
        raise _integrity() from None
    if any(row.required_for_selection != 1 for row in rows):
        raise _integrity() from None
    return rows, raws


def _evidence_set_digest(
    proposal_ref: str, evidence_set_ref: str, rows: tuple[object, ...],
) -> str:
    identity = {
        "evidence_set_ref": evidence_set_ref,
        "proposal_ref": proposal_ref,
        "proposal_phase": _PHASE,
        "entries": tuple({
            "evidence_role": row.evidence_role,
            "role_rank": row.role_rank,
            "ordinal": row.ordinal,
            "evidence_ref": row.evidence_ref,
            "evidence_digest": row.evidence_digest,
            "evidence_binding_digest": row.evidence_binding_digest,
        } for row in rows),
    }
    return _domain_separated_digest(_EVIDENCE_DOMAIN, identity)


def _member_graph(
    command: RecordPostExecutionProposalCommandV1,
    context: PostExecutionProposalContextRowV1,
    source: object, artifact: object, proposal: object,
    evidence: tuple[object, ...],
) -> str:
    members = (
        ("source_invocation", source.source_invocation_digest),
        ("artifact_binding", artifact.artifact_binding_digest),
        ("model_proposal", proposal.proposal_digest),
        ("post_context", context.context_row_digest),
        *((role, row.evidence_binding_digest)
          for role, row in zip(_ROLE_ORDER, evidence, strict=True)),
    )
    return _domain_separated_digest(_GRAPH_DOMAIN, {
        "mutation_ref": command.mutation_ref,
        "command_digest": command.command_digest,
        "members": [{"role": role, "digest": digest} for role, digest in members],
    })


def _committed_digest(
    command: RecordPostExecutionProposalCommandV1,
    context: PostExecutionProposalContextRowV1,
    graph: str, committed_at: str,
) -> str:
    return _domain_separated_digest(_COMMITTED_DOMAIN, {
        "mutation_ref": command.mutation_ref,
        "command_digest": command.command_digest,
        "proposal_ref": command.proposal_ref,
        "context_ref": command.context_ref,
        "context_row_digest": context.context_row_digest,
        "mutation_graph_digest": graph,
        "committed_at": committed_at,
        "outcome": "proposal_recorded",
    })


def _result(
    command: RecordPostExecutionProposalCommandV1,
    context: PostExecutionProposalContextRowV1,
    receipt: PostExecutionProposalReceiptRowV1,
    disposition: str,
) -> RecordPostExecutionProposalResultV1:
    return RecordPostExecutionProposalResultV1(
        mutation_ref=command.mutation_ref,
        command_digest=command.command_digest,
        disposition=disposition,
        proposal_ref=command.proposal_ref,
        context_ref=command.context_ref,
        context_row_digest=context.context_row_digest,
        mutation_graph_digest=receipt.mutation_graph_digest,
        committed_result_digest=receipt.committed_result_digest,
        receipt_digest=receipt.receipt_digest,
        committed_at=receipt.committed_at,
    )


@dataclass(frozen=True, slots=True, repr=False)
class CheckedPostExecutionProposalFamilyV1:
    command: RecordPostExecutionProposalCommandV1
    context: PostExecutionProposalContextRowV1
    receipt: PostExecutionProposalReceiptRowV1
    input_context: PostExecutionSemanticReviewInputContextV1
    source: object
    artifact: object
    proposal: object
    evidence: tuple[object, ...]
    private_reader_tuples: tuple[tuple[object, ...], ...]
    result: RecordPostExecutionProposalResultV1


def _check_witness(capability: object, basis: dict[str, object]) -> None:
    witness = basis["d2_checkpoint_witness"]
    phase_ref = basis["context_v02"]["phase_basis_ref"]
    phase_digest = basis["context_v02"]["phase_basis_digest"]
    for member in witness["checked_memberships"]:
        family = _read_membership_family(
            capability, phase_basis_ref=phase_ref,
            membership_ref=member["membership_ref"],
        )
        receipt = _read_receipt(capability, member["mutation_ref"])
        if family is None or receipt is None:
            raise _integrity() from None
        _verify_evidence_family_rows(family, receipt, capability=capability)
        actual = family.membership
        if (actual.value("phase_basis_ref") != phase_ref
                or actual.value("phase_basis_digest") != phase_digest
                or actual.value("kind_rank") != member["kind_rank"]
                or actual.value("membership_digest") != member["membership_digest"]
                or actual.value("admitted_by_mutation_ref") != member["mutation_ref"]
                or actual.value("admission_graph_digest") != member["admission_graph_digest"]):
            raise _integrity() from None
    for effect in witness["bound_effects"]:
        raw = _one(
            capability, "development_mutation_receipts",
            _decision_rows._DEVELOPMENT_MUTATION_RECEIPT_COLUMNS,
            "mutation_ref = ?", (effect["mutation_ref"],),
        )
        if raw is None:
            raise _integrity() from None
        try:
            row = _decision_rows.development_mutation_receipt_row_value_from_row_tuple(raw)
        except Exception:
            raise _integrity() from None
        if row.mutation_graph_digest != effect["receipt_graph_digest"]:
            raise _integrity() from None


def read_checked_family_after_fencing(
    capability: object, command: RecordPostExecutionProposalCommandV1,
) -> CheckedPostExecutionProposalFamilyV1 | None:
    """Receipt first; verify every persisted owner before command association."""
    if type(command) is not RecordPostExecutionProposalCommandV1:
        raise _integrity() from None
    raw_receipt = _one(
        capability, _RECEIPT_TABLE, _RECEIPT_COLUMNS,
        "mutation_ref = ?", (command.mutation_ref,),
    )
    if raw_receipt is None:
        return None
    try:
        receipt = typing.cast(PostExecutionProposalReceiptRowV1,
                              row_from_tuple(_RECEIPT_TABLE, raw_receipt))
        raw_context = _one(capability, _CONTEXT_TABLE, _CONTEXT_COLUMNS,
                           "context_ref = ?", (receipt.context_ref,))
        if raw_context is None:
            raise _integrity()
        context = typing.cast(PostExecutionProposalContextRowV1,
                              row_from_tuple(_CONTEXT_TABLE, raw_context))
        basis = json.loads(context.safe_basis_bytes)
        checked_safe_basis_bytes(context.safe_basis_bytes)
        input_context = PostExecutionSemanticReviewInputContextV1.from_mapping(
            _ordered_typed_mapping(
                PostExecutionSemanticReviewInputContextV1, basis["context_v02"]
            )
        )
        source, raw_source = _common_one(
            capability, _common._TABLE_ORDER[0],
            "source_invocation_ref = ?", (receipt.source_invocation_ref,),
        )
        artifact, raw_artifact = _common_one(
            capability, _common._TABLE_ORDER[2],
            "artifact_ref = ?", (receipt.artifact_ref,),
        )
        proposal, raw_proposal = _common_one(
            capability, _common._TABLE_ORDER[3],
            "proposal_ref = ?", (receipt.proposal_ref,),
        )
        evidence, raw_evidence = _evidence(capability, receipt.proposal_ref)
        _check_witness(capability, basis)
        if (receipt.proposal_phase != _PHASE
                or context.proposal_phase != _PHASE
                or receipt.context_digest != context.context_digest
                or receipt.proposal_ref != context.proposal_ref
                or receipt.proposal_digest != context.proposal_digest
                or receipt.phase_basis_ref != context.phase_basis_ref
                or receipt.phase_basis_digest != context.phase_basis_digest
                or receipt.safe_basis_digest != context.safe_basis_digest
                or input_context.input_context_ref != context.context_ref
                or input_context.input_context_digest != context.context_digest
                or input_context.phase_basis_ref != context.phase_basis_ref
                or input_context.phase_basis_digest != context.phase_basis_digest
                or source.source_invocation_digest != receipt.source_invocation_digest
                or source.context_ref != context.context_ref
                or source.context_digest != context.context_digest
                or source.artifact_ref != receipt.artifact_ref
                or source.artifact_digest != receipt.artifact_digest
                or artifact.artifact_digest != receipt.artifact_digest
                or artifact.artifact_binding_digest != receipt.artifact_binding_digest
                or proposal.proposal_digest != receipt.proposal_digest
                or proposal.source_invocation_ref != receipt.source_invocation_ref
                or proposal.source_invocation_digest != receipt.source_invocation_digest
                or proposal.artifact_ref != receipt.artifact_ref
                or proposal.artifact_digest != receipt.artifact_digest
                or proposal.context_ref != context.context_ref
                or proposal.context_digest != context.context_digest
                or proposal.evidence_set_ref != receipt.evidence_set_ref
                or proposal.evidence_set_digest != receipt.evidence_set_digest
                or any(row.proposal_ref != receipt.proposal_ref
                       or row.proposal_phase != _PHASE
                       or row.evidence_set_ref != receipt.evidence_set_ref
                       for row in evidence)
                or _evidence_set_digest(
                    receipt.proposal_ref, receipt.evidence_set_ref, evidence
                ) != receipt.evidence_set_digest):
            raise _integrity()
        # The command association is evaluated only after historical graph
        # integrity. A caller cannot make an alien receipt an exact replay.
        if (
            receipt.mutation_command_digest != command.command_digest
            or receipt.context_ref != command.context_ref
            or receipt.context_digest != command.context_digest
            or receipt.proposal_ref != command.proposal_ref
            or receipt.proposal_digest != command.proposal_digest
            or receipt.source_invocation_ref != command.source_invocation_ref
            or receipt.source_invocation_digest != command.source_invocation_digest
            or receipt.artifact_ref != command.artifact_ref
            or receipt.artifact_digest != command.artifact_digest
            or receipt.artifact_binding_digest != command.artifact_binding_digest
            or receipt.evidence_set_ref != command.evidence_set_ref
            or receipt.evidence_set_digest != command.evidence_set_digest
            or receipt.phase_basis_ref != command.phase_basis_ref
            or receipt.phase_basis_digest != command.phase_basis_digest
            or receipt.safe_basis_digest != command.safe_basis_digest
            or receipt.c1_mutation_ref != command.c1_mutation_ref
            or receipt.c1_membership_ref != command.c1_membership_ref
            or tuple((row.evidence_role, row.role_rank, row.ordinal,
                      entry.typed_schema_id, row.evidence_ref,
                      row.evidence_digest) for row, entry in zip(
                          evidence, input_context.role_entries, strict=True))
            != tuple((item.role, item.rank, item.ordinal, item.schema_id,
                      item.ref, item.digest) for item in command.evidence_selectors)
        ):
            raise ValueError("post_execution_proposal_identity_conflict") from None
        graph = _member_graph(command, context, source, artifact, proposal, evidence)
        if (receipt.mutation_graph_digest != graph
                or receipt.committed_result_digest != _committed_digest(
                    command, context, graph, receipt.committed_at
                )):
            raise _integrity()
        return CheckedPostExecutionProposalFamilyV1(
            command, context, receipt, input_context, source, artifact,
            proposal, evidence, (raw_source, raw_artifact, raw_proposal, *raw_evidence),
            _result(command, context, receipt, "exact_replay"),
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except ValueError as exc:
        if str(exc) == "post_execution_proposal_identity_conflict":
            raise
        raise _integrity() from None
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _integrity() from None


def _route_probe(capability: object, command: RecordPostExecutionProposalCommandV1) -> bool:
    probes = (
        (_common._TABLE_ORDER[0], ("source_invocation_ref",), "source_invocation_ref = ?",
         (command.source_invocation_ref,)),
        (_common._TABLE_ORDER[2], ("artifact_ref",), "artifact_ref = ?",
         (command.artifact_ref,)),
        (_common._TABLE_ORDER[3], ("proposal_ref",), "proposal_ref = ?",
         (command.proposal_ref,)),
        (_CONTEXT_TABLE, ("context_ref",), "context_ref = ?",
         (command.context_ref,)),
        (_CONTEXT_TABLE, ("proposal_ref",), "proposal_ref = ?",
         (command.proposal_ref,)),
        (_RECEIPT_TABLE, ("mutation_ref",), "mutation_ref = ?",
         (command.mutation_ref,)),
        (_RECEIPT_TABLE, ("proposal_ref",), "proposal_ref = ?",
         (command.proposal_ref,)),
        (_common._TABLE_ORDER[5], ("proposal_ref",), "proposal_ref = ?",
         (command.proposal_ref,)),
        (_common._TABLE_ORDER[5], ("evidence_set_ref",), "evidence_set_ref = ?",
         (command.evidence_set_ref,)),
        ("rw0_c1_mutation_receipts", ("mutation_ref",), "mutation_ref = ?",
         (command.c1_mutation_ref,)),
        ("rw0_evidence_memberships", ("membership_ref",), "membership_ref = ?",
         (command.c1_membership_ref,)),
    )
    for table, columns, where, params in probes:
        if _select(capability, table, columns, where, params, limit=2):
            return True
    return False


def recover_after_fencing(
    capability: object, command: RecordPostExecutionProposalCommandV1,
) -> PostExecutionProposalRecoveryV1:
    try:
        checked = read_checked_family_after_fencing(capability, command)
        if checked is not None:
            return PostExecutionProposalRecoveryV1("committed_exact", checked.result)
        phase = _one(
            capability, "rw0_phase_instances", ("phase_basis_digest",),
            "phase_basis_ref = ?", (command.phase_basis_ref,),
        )
        if phase != (command.phase_basis_digest,) or _route_probe(capability, command):
            return PostExecutionProposalRecoveryV1("unresolved")
        return PostExecutionProposalRecoveryV1("definitely_not_committed")
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return PostExecutionProposalRecoveryV1("unresolved")


def _insert(connection: sqlite3.Connection, table: str, columns: tuple[str, ...],
            values: tuple[object, ...]) -> None:
    sql = (f"INSERT INTO {table} ({', '.join(columns)}) VALUES ("
           + ", ".join("?" for _ in columns) + ")")
    try:
        cursor = connection.execute(sql, values)
        if cursor.rowcount != 1:
            raise _integrity()
        cursor.close()
    except SQLiteMutationStoreError:
        raise
    except sqlite3.Error:
        raise _mutation_failed() from None


def write_fresh_after_fencing(
    *, capability: object, connection: sqlite3.Connection,
    command: RecordPostExecutionProposalCommandV1, run: RW0D2OfflineRun,
    safe_basis_bytes: bytes, transaction_timestamp: str,
) -> RecordPostExecutionProposalResultV1 | PostExecutionProposalConflictV1:
    if (type(connection) is not sqlite3.Connection
            or type(command) is not RecordPostExecutionProposalCommandV1
            or type(run) is not RW0D2OfflineRun
            or checked_safe_basis_bytes(safe_basis_bytes) != safe_basis_bytes
            or safe_basis_digest(safe_basis_bytes) != command.safe_basis_digest):
        raise _integrity() from None
    run._require_open_owner()
    handback = run.handback
    handback.validate()
    if handback.status != "preadmission_ready":
        raise _integrity() from None
    try:
        expected_command, expected_safe_basis = prepare_record_command(run)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity() from None
    if (command != expected_command
            or safe_basis_bytes != expected_safe_basis
            or command.safe_basis_digest != safe_basis_digest(expected_safe_basis)
            or command.command_digest != expected_command.command_digest):
        raise _integrity() from None
    checkpoint = handback.evidence_checkpoint
    basis = checkpoint.d1_handback.phase_basis
    current = _read_rw0_d2_current_owner_snapshot_after_fencing(
        capability=capability, basis=basis, observed_at=transaction_timestamp,
    )
    try:
        try:
            require_current_d2_basis(checkpoint, current)
        except RW0D2BInputConflict:
            return PostExecutionProposalConflictV1(
                "currentness_conflict", command.mutation_ref, command.command_digest,
            )
        # B-time stop/lineage is retained in the original supplied V10. Do
        # not replace it with a newly sampled identity.
        prior_stop = handback.evidence_supply.role_supplies[7].to_mapping()
        prior_stop_value = prior_stop["typed_canonical_value"]
        stale = (current.global_stop_updated_at
                 != prior_stop_value["global_stop_updated_at"]
                 or handback.input_context.constructed_at > transaction_timestamp
                 or handback.proposal.proposal_created_at > transaction_timestamp
                 or handback.model_source_invocation.source_invocation_completed_at > transaction_timestamp)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity() from None
    if stale:
        return PostExecutionProposalConflictV1(
            "currentness_conflict", command.mutation_ref, command.command_digest,
        )
    if _route_probe(capability, command):
        return PostExecutionProposalConflictV1(
            "route_conflict", command.mutation_ref, command.command_digest,
        )
    try:
        source = _common._row_value_from_mapping(
            _common._TABLE_ORDER[0], handback.model_source_invocation.to_mapping()
        )
        artifact = _common._row_value_from_mapping(
            _common._TABLE_ORDER[2], handback.artifact_binding.to_mapping()
        )
        proposal = _common._row_value_from_mapping(
            _common._TABLE_ORDER[3], handback.proposal.to_mapping()
        )
        evidence = tuple(_common._row_value_from_mapping(
            _common._TABLE_ORDER[5], value.to_mapping()
        ) for value in handback.evidence_bindings)
        if len(evidence) != 9 or any(
            (row.evidence_role, row.role_rank, row.ordinal,
             entry.typed_schema_id, row.evidence_ref,
             row.evidence_digest) !=
            (selector.role, selector.rank, selector.ordinal, selector.schema_id,
             selector.ref, selector.digest)
            for row, entry, selector in zip(
                evidence, handback.input_context.role_entries,
                command.evidence_selectors, strict=True,
            )
        ):
            raise _integrity()
        context = typing.cast(PostExecutionProposalContextRowV1, seal_row(
            _CONTEXT_TABLE, {
                "schema_id": _CONTEXT_SCHEMA,
                "proposal_phase": _PHASE,
                "context_ref": command.context_ref,
                "context_digest": command.context_digest,
                "proposal_ref": command.proposal_ref,
                "proposal_digest": command.proposal_digest,
                "phase_basis_ref": command.phase_basis_ref,
                "phase_basis_digest": command.phase_basis_digest,
                "safe_basis_bytes": safe_basis_bytes,
                "safe_basis_digest": command.safe_basis_digest,
            }
        ))
        for table, row in (
            (_common._TABLE_ORDER[0], source),
            (_common._TABLE_ORDER[2], artifact),
            (_common._TABLE_ORDER[3], proposal),
        ):
            mapping = row.to_mapping()
            _insert(connection, table, _common._TABLE_COLUMNS[table],
                    tuple(mapping[name] for name in _common._TABLE_COLUMNS[table]))
        _insert(connection, _CONTEXT_TABLE, _CONTEXT_COLUMNS, context.as_tuple())
        for row in evidence:
            table = _common._TABLE_ORDER[5]
            mapping = row.to_mapping()
            _insert(connection, table, _common._TABLE_COLUMNS[table],
                    tuple(mapping[name] for name in _common._TABLE_COLUMNS[table]))
        # Exact same-transaction gate, after all owner writes and before
        # constructing or inserting a receipt.
        actual_proposal, _ = _common_one(
            capability, _common._TABLE_ORDER[3],
            "proposal_ref = ?", (command.proposal_ref,),
        )
        actual_evidence, _ = _evidence(capability, command.proposal_ref)
        if (actual_proposal.to_mapping() != proposal.to_mapping()
                or tuple(row.to_mapping() for row in actual_evidence)
                != tuple(row.to_mapping() for row in evidence)
                or _evidence_set_digest(
                    command.proposal_ref, command.evidence_set_ref, actual_evidence
                ) != command.evidence_set_digest):
            raise _integrity()
        graph = _member_graph(command, context, source, artifact, proposal, evidence)
        committed = _committed_digest(command, context, graph, transaction_timestamp)
        receipt = typing.cast(PostExecutionProposalReceiptRowV1, seal_row(
            _RECEIPT_TABLE, {
                "schema_id": _RECEIPT_SCHEMA,
                "mutation_ref": command.mutation_ref,
                "mutation_command_digest": command.command_digest,
                "proposal_phase": _PHASE,
                "context_ref": command.context_ref,
                "context_digest": command.context_digest,
                "proposal_ref": command.proposal_ref,
                "proposal_digest": command.proposal_digest,
                "phase_basis_ref": command.phase_basis_ref,
                "phase_basis_digest": command.phase_basis_digest,
                "source_invocation_ref": command.source_invocation_ref,
                "source_invocation_digest": command.source_invocation_digest,
                "artifact_ref": command.artifact_ref,
                "artifact_digest": command.artifact_digest,
                "artifact_binding_digest": command.artifact_binding_digest,
                "evidence_set_ref": command.evidence_set_ref,
                "evidence_set_digest": command.evidence_set_digest,
                "safe_basis_digest": command.safe_basis_digest,
                "c1_mutation_ref": command.c1_mutation_ref,
                "c1_membership_ref": command.c1_membership_ref,
                "mutation_graph_digest": graph,
                "committed_result_digest": committed,
                "committed_outcome": "proposal_recorded",
                "committed_at": transaction_timestamp,
            }
        ))
        _insert(connection, _RECEIPT_TABLE, _RECEIPT_COLUMNS, receipt.as_tuple())
        checked = read_checked_family_after_fencing(capability, command)
        if checked is None or checked.receipt != receipt:
            raise _integrity()
        return _result(command, context, receipt, "fresh_committed")
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _integrity() from None
