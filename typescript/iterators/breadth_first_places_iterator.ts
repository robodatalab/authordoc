import type { PlaceCell } from "../cells/place_cell";
import type { Document } from "../storydoc";

export class BreadthFirstPlacesIterator implements Iterable<PlaceCell> {
    constructor(
        private readonly document: Document,
        private readonly place: PlaceCell,
    ) {}

    *[Symbol.iterator](): Iterator<PlaceCell> {
        const placesToVisit: PlaceCell[] = [];
        let visiting: PlaceCell | undefined = this.place;
        while (visiting !== undefined) {
            const children = visiting.children(this.document);
            yield* children;
            placesToVisit.push(...children);
            visiting = placesToVisit.shift();
        }
    }
}
