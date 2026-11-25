import type { PlaceCell } from "../cells/place_cell";
import type { Document } from "../storydoc";

export class DepthFirstPlacesIterator implements Iterable<PlaceCell> {
    constructor(
        private readonly document: Document,
        private readonly place: PlaceCell,
    ) {}

    *[Symbol.iterator](): Iterator<PlaceCell> {
        const children = this.place.children(this.document);
        for (const child of children) {
            yield child;
            const placesWithinTheChild = new DepthFirstPlacesIterator(
                this.document,
                child,
            );
            yield* placesWithinTheChild;
        }
    }
}
