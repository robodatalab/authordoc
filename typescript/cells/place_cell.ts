import type { Document } from "../storydoc";
import { Cell } from "./cell";
import type { CellVisitor } from "./cell_visitor";

export const PLACE = "place";

export class PlaceCell extends Cell {
    readonly kind = PLACE;

    constructor(
        readonly title: string = "",
        source: string = "",
        folded: boolean = false,
        at: readonly [number, number] | null = null,
        uniqueId: string = crypto.randomUUID(),
        readonly _parent: string = "",
    ) {
        super(source, folded, at, uniqueId);
    }

    parent(document: Document): PlaceCell | undefined {
        const referenced = document.cellWithId(this._parent);
        const parent = referenced instanceof PlaceCell ? referenced : undefined;
        return parent;
    }

    withParent(parent: PlaceCell | null): PlaceCell {
        const parentId = parent?.uniqueId ?? "";
        const placed = new PlaceCell(
            this.title,
            this.source,
            this.folded,
            this.at,
            this.uniqueId,
            parentId,
        );
        return placed;
    }

    withSource(source: string): PlaceCell {
        return new PlaceCell(
            this.title,
            source,
            this.folded,
            this.at,
            this.uniqueId,
            this._parent,
        );
    }

    withFolded(folded: boolean): PlaceCell {
        return new PlaceCell(
            this.title,
            this.source,
            folded,
            this.at,
            this.uniqueId,
            this._parent,
        );
    }

    accept<Result>(visitor: CellVisitor<Result>): Result {
        return visitor.visitPlace(this);
    }
}
