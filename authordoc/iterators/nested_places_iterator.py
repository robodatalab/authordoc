from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from typing import TYPE_CHECKING

from authordoc.cells.place_cell import PlaceCell

if TYPE_CHECKING:
    from authordoc.storydoc import Document


class NestedPlacesIterator:
    def __init__(self, document: Document, place: PlaceCell) -> None:
        self._document = document
        self._place = place

    def __iter__(self) -> Iterator[PlaceCell]:
        places_to_visit: deque[PlaceCell] = deque([self._place])
        while places_to_visit:
            visiting = places_to_visit.popleft()
            within = _places_directly_within(visiting, self._document)
            yield from within
            places_to_visit.extend(within)


def _places_directly_within(place: PlaceCell, document: Document) -> list[PlaceCell]:
    places = [cell for cell in document.cells if isinstance(cell, PlaceCell)]
    within: list[PlaceCell] = []
    for candidate in places:
        ancestors = candidate.ancestors(document)
        if ancestors and ancestors[0].unique_id == place.unique_id:
            within.append(candidate)
    return within
