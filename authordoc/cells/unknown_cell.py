from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import TYPE_CHECKING, TypeVar
from uuid import uuid4

from authordoc.cells.cell import Cell

if TYPE_CHECKING:
    from authordoc.cells.cell_visitor import CellVisitor

_Result = TypeVar("_Result")


@dataclass(frozen=True)
class UnknownCell(Cell):
    kind: str
    attrs: Mapping[str, str] = field(default_factory=dict)
    source: str = ""
    folded: bool = False
    at: tuple[int, int] | None = field(default=None, compare=False)
    _unique_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        # Kept as a read-only view of a copy, whatever mapping they come as, so that
        # no one changes them in place.
        attrs = dict(self.attrs)
        read_only = MappingProxyType(attrs)
        object.__setattr__(self, "attrs", read_only)

    def with_source(self, source: str) -> UnknownCell:
        return replace(self, source=source)

    def with_folded(self, folded: bool) -> UnknownCell:
        return replace(self, folded=folded)

    def accept(self, visitor: CellVisitor[_Result]) -> _Result:
        return visitor.visit_unknown(self)
