import { Cell } from "./cell";
import type { CellVisitor } from "./cell_visitor";

export class UnknownCell extends Cell {
    readonly attrs: Readonly<Record<string, string>>;

    constructor(
        readonly kind: string,
        attrs: Readonly<Record<string, string>> = {},
        source: string = "",
        folded: boolean = false,
        at: readonly [number, number] | null = null,
        uniqueId: string = crypto.randomUUID(),
    ) {
        super(source, folded, at, uniqueId);
        // Kept as a frozen copy, whatever record they come as, so that no one
        // changes them in place.
        this.attrs = Object.freeze({ ...attrs });
    }

    withSource(source: string): UnknownCell {
        return new UnknownCell(
            this.kind,
            this.attrs,
            source,
            this.folded,
            this.at,
            this.uniqueId,
        );
    }

    withFolded(folded: boolean): UnknownCell {
        return new UnknownCell(
            this.kind,
            this.attrs,
            this.source,
            folded,
            this.at,
            this.uniqueId,
        );
    }

    accept<Result>(visitor: CellVisitor<Result>): Result {
        return visitor.visitUnknown(this);
    }
}
