import { PlaceCell } from "../cells/place_cell";
import type { Document } from "../storydoc";

export class NestedPlacesIterator implements Iterable<PlaceCell> {
    constructor(
        private readonly document: Document,
        private readonly place: PlaceCell,
    ) {}

    *[Symbol.iterator](): Iterator<PlaceCell> {
        const placesToVisit: PlaceCell[] = [];
        let visiting: PlaceCell | undefined = this.place;
        while (visiting !== undefined) {
            const within = placesDirectlyWithin(visiting, this.document);
            yield* within;
            placesToVisit.push(...within);
            visiting = placesToVisit.shift();
        }
    }
}

function placesDirectlyWithin(
    place: PlaceCell,
    document: Document,
): PlaceCell[] {
    const places = document.cells.filter((cell) => cell instanceof PlaceCell);
    const within = places.filter((candidate) => {
        const [parent] = candidate.ancestors(document);
        return parent?.uniqueId === place.uniqueId;
    });
    return within;
}
