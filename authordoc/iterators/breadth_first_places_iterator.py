from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from authordoc.cells.place_cell import PlaceCell
    from authordoc.storydoc import Document


class BreadthFirstPlacesIterator:
    def __init__(self, document: Document, place: PlaceCell) -> None:
        self._document = document
        self._place = place

    def __iter__(self) -> Iterator[PlaceCell]:
        places_to_visit: deque[PlaceCell] = deque([self._place])
        while places_to_visit:
            visiting = places_to_visit.popleft()
            children = visiting.children(self._document)
            yield from children
            places_to_visit.extend(children)
