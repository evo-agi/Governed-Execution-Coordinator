"""Closed, no-I/O terminal witness for five observed owner head postimages."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

from . import _cognitive_proposal_row_values as _selection
from . import _development_effect_row_values as _effect
from . import _development_program_row_values as _program
from ._rw0_terminal_outcome_contracts import HEAD_ROLES, _canonical, _head, _strict_bytes

__all__: tuple[str, ...] = ()

WITNESS_SCHEMA = "governed-execution.nwp-rw0-terminal-closure-head-witness-set.v1"
# 75 fixed owner columns: refs <=96 bytes, digests 64, timestamps 20,
# bounded enums/integers and fixed schema IDs. 32 KiB exceeds their closed
# canonical maximum while remaining below the command's 48 KiB bound.
WITNESS_BYTE_CEILING = 32768
_COLUMNS = (
    _program._DEVELOPMENT_PROGRAM_HEAD_COLUMNS,
    _program._DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS,
    _selection._TABLE_COLUMNS["development_pre_execution_selection_heads"],
    _effect._DEVELOPMENT_EFFECT_HEAD_COLUMNS,
    _effect._DEVELOPMENT_DELIVERY_HEAD_COLUMNS,
)
_TYPES = (
    _program.DevelopmentProgramHeadRowValue,
    _program.DevelopmentWorkItemHeadRowValue,
    _selection.DevelopmentPreExecutionSelectionHeadRowValue,
    _effect.DevelopmentEffectHeadRowValue,
    _effect.DevelopmentDeliveryHeadRowValue,
)
_OWNERS = ("program_ref", "work_item_ref", "effect_intent_ref",
           "effect_intent_ref", "effect_intent_ref")
_ADAPTERS = (
    _program.development_program_head_row_value_from_row_tuple,
    _program.development_work_item_head_row_value_from_row_tuple,
    None,
    _effect.development_effect_head_row_value_from_row_tuple,
    _effect.development_delivery_head_row_value_from_row_tuple,
)


_COORDINATE_COLUMNS = ("role", "owner_ref", "revision", "digest")
_SCALAR_TYPES = (str, int, type(None))


@dataclass(frozen=True, slots=True, repr=False, init=False, eq=False)
class TerminalHeadWitness:
    canonical_bytes: bytes
    _postimage_scalars: tuple[tuple[object, ...], ...] = field(repr=False)
    _coordinate_scalars: tuple[tuple[object, ...], ...] = field(repr=False)

    def __init__(
        self, canonical_bytes: object, postimages: object, coordinates: object,
    ) -> None:
        decoded = _decoded_postimages(canonical_bytes)
        canonical, checked, projected = _checked_postimages(decoded)
        if canonical != canonical_bytes:
            raise ValueError("noncanonical terminal witness")
        supplied_images = _exact_mapping_tuple(postimages, _COLUMNS)
        supplied_coordinates = _exact_mapping_tuple(
            coordinates, (_COORDINATE_COLUMNS,) * 5)
        for coordinate, role in zip(supplied_coordinates, HEAD_ROLES, strict=True):
            _head(coordinate, role)
        if supplied_images != checked or supplied_coordinates != projected:
            raise ValueError("inconsistent terminal witness components")
        object.__setattr__(self, "canonical_bytes", canonical_bytes)
        object.__setattr__(
            self, "_postimage_scalars",
            tuple(tuple(image[name] for name in columns)
                  for image, columns in zip(checked, _COLUMNS, strict=True)),
        )
        object.__setattr__(
            self, "_coordinate_scalars",
            tuple(tuple(coordinate[name] for name in _COORDINATE_COLUMNS)
                  for coordinate in projected),
        )

    @property
    def postimages(self) -> tuple[dict[str, object], ...]:
        return tuple(dict(zip(columns, values, strict=True))
                     for columns, values in zip(
                         _COLUMNS, self._postimage_scalars, strict=True))

    @property
    def coordinates(self) -> tuple[dict[str, object], ...]:
        return tuple(dict(zip(_COORDINATE_COLUMNS, values, strict=True))
                     for values in self._coordinate_scalars)

    def __eq__(self, other: object) -> bool:
        if type(other) is not TerminalHeadWitness:
            return NotImplemented
        return self.canonical_bytes == other.canonical_bytes

    __hash__ = None


def _exact_mapping_tuple(
    values: object, columns_by_role: tuple[tuple[str, ...], ...],
) -> tuple[dict[str, object], ...]:
    if type(values) is not tuple or len(values) != 5:
        raise ValueError("invalid terminal witness cardinality")
    checked: list[dict[str, object]] = []
    for value, columns in zip(values, columns_by_role, strict=True):
        if type(value) is not dict or any(type(key) is not str for key in value):
            raise ValueError("invalid terminal witness fields")
        if set(value) != set(columns):
            raise ValueError("invalid terminal witness fields")
        if any(type(item) not in _SCALAR_TYPES for item in value.values()):
            raise ValueError("invalid terminal witness scalar")
        checked.append({name: value[name] for name in columns})
    return tuple(checked)


def _decoded_postimages(raw: object) -> tuple[dict[str, object], ...]:
    if type(raw) is not bytes:
        raise ValueError("invalid terminal witness bytes")
    parsed = _strict_bytes(raw, limit=WITNESS_BYTE_CEILING)
    if (type(parsed) is not dict or set(parsed) != {"schema_id", "heads"}
        or type(parsed["schema_id"]) is not str
        or parsed["schema_id"] != WITNESS_SCHEMA
        or type(parsed["heads"]) is not list or len(parsed["heads"]) != 5):
        raise ValueError("invalid terminal witness envelope")
    images: list[dict[str, object]] = []
    for entry, role in zip(cast(list[object], parsed["heads"]), HEAD_ROLES, strict=True):
        if (type(entry) is not dict or set(entry) != {"role", "postimage"}
            or type(entry["role"]) is not str or entry["role"] != role):
            raise ValueError("invalid terminal witness role")
        images.append(cast(dict[str, object], entry["postimage"]))
    return tuple(images)


def _checked_postimages(
    postimages: object,
) -> tuple[bytes, tuple[dict[str, object], ...], tuple[dict[str, object], ...]]:
    supplied = _exact_mapping_tuple(postimages, _COLUMNS)
    checked: list[dict[str, object]] = []
    coordinates: list[dict[str, object]] = []
    for index, (image, columns, adapter, owner, role) in enumerate(zip(
        supplied, _COLUMNS, _ADAPTERS, _OWNERS, HEAD_ROLES, strict=True
    )):
        try:
            if index == 2:
                row = _selection._row_value_from_mapping(
                    "development_pre_execution_selection_heads", image)
                validated = row.to_mapping()
            else:
                assert adapter is not None
                row = adapter(tuple(image[name] for name in columns))
                validated = {name: getattr(row, name) for name in columns}
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            raise
        except Exception:
            raise ValueError("invalid terminal witness owner row") from None
        if (type(validated) is not dict
            or any(type(item) not in _SCALAR_TYPES for item in validated.values())
            or validated != image):
            raise ValueError("invalid terminal witness owner normalization")
        coordinate = _head({"role": role, "owner_ref": validated[owner],
                            "revision": validated["head_revision"],
                            "digest": validated["head_digest"]}, role)
        checked.append(validated)
        coordinates.append(coordinate)
    envelope = {"schema_id": WITNESS_SCHEMA,
                "heads": [{"role": role, "postimage": image}
                          for role, image in zip(HEAD_ROLES, checked, strict=True)]}
    raw = _canonical(envelope)
    if len(raw) > WITNESS_BYTE_CEILING:
        raise ValueError("oversize terminal witness")
    return raw, tuple(checked), tuple(coordinates)


def witness_from_typed(rows: object) -> TerminalHeadWitness:
    if type(rows) is not tuple or len(rows) != 5:
        raise ValueError("invalid terminal witness rows")
    mappings: list[dict[str, object]] = []
    for row, expected, columns in zip(rows, _TYPES, _COLUMNS, strict=True):
        if type(row) is not expected:
            raise ValueError("invalid terminal witness row type")
        if expected is _selection.DevelopmentPreExecutionSelectionHeadRowValue:
            mapping = row.to_mapping()
        else:
            mapping = {name: getattr(row, name) for name in columns}
        mappings.append(mapping)
    raw, checked, coordinates = _checked_postimages(tuple(mappings))
    return TerminalHeadWitness(raw, checked, coordinates)


def witness_from_bytes(raw: object) -> TerminalHeadWitness:
    images = _decoded_postimages(raw)
    _, checked, coordinates = _checked_postimages(images)
    return TerminalHeadWitness(raw, checked, coordinates)
