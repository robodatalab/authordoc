from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from authordoc.diff import AuthorDocDiff
    from authordoc.storydoc import Document


class AuthorDocSynchronizer(ABC):
    @abstractmethod
    def synchronize(self, before: Document, change: AuthorDocDiff) -> AuthorDocDiff: ...
