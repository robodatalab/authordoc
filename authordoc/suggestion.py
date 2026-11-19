from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from authordoc.diff import AuthorDocDiff


@dataclass(frozen=True)
class Suggestion:
    cell_id: str
    _diff: AuthorDocDiff

    def diff(self) -> AuthorDocDiff:
        return self._diff

    def with_the_diff(self, diff: AuthorDocDiff) -> Suggestion:
        suggestion = Suggestion(self.cell_id, diff)
        return suggestion
