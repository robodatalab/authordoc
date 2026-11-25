from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from authordoc.cells.place_cell import PlaceCell
    from authordoc.storydoc import Document


class DepthFirstPlacesIterator:
    def __init__(self, document: Document, place: PlaceCell) -> None:
        self._document = document
        self._place = place

    def __iter__(self) -> Iterator[PlaceCell]:
        children = self._place.children(self._document)
        for child in children:
            yield child
            places_within_the_child = DepthFirstPlacesIterator(self._document, child)
            yield from places_within_the_child
