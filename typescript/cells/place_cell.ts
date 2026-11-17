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
    ) {
        super(source, folded, at, uniqueId);
    }

    withSource(source: string): PlaceCell {
        return new PlaceCell(
            this.title,
            source,
            this.folded,
            this.at,
            this.uniqueId,
        );
    }

    withFolded(folded: boolean): PlaceCell {
        return new PlaceCell(
            this.title,
            this.source,
            folded,
            this.at,
            this.uniqueId,
        );
    }

    accept<Result>(visitor: CellVisitor<Result>): Result {
        return visitor.visitPlace(this);
    }
}
