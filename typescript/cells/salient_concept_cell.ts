import { Cell } from "./cell";
import type { CellVisitor } from "./cell_visitor";
import type { StoryWordRange } from "./story_word_range";

export const SALIENT_CONCEPT = "salient-concept";

export class SalientConceptReference {
    constructor(
        readonly referenceId: string,
        readonly storyWordRange: StoryWordRange,
    ) {}
}

export class SalientConceptCell extends Cell {
    readonly kind = SALIENT_CONCEPT;
    readonly references: readonly SalientConceptReference[];

    constructor(
        readonly title: string = "",
        references: readonly SalientConceptReference[] = [],
        source: string = "",
        folded: boolean = false,
        at: readonly [number, number] | null = null,
        uniqueId: string = crypto.randomUUID(),
    ) {
        super(source, folded, at, uniqueId);
        // Kept as a frozen copy, whatever array they come as, so that no one
        // changes them in place.
        this.references = Object.freeze([...references]);
    }

    withSource(source: string): SalientConceptCell {
        return new SalientConceptCell(
            this.title,
            this.references,
            source,
            this.folded,
            this.at,
            this.uniqueId,
        );
    }

    withFolded(folded: boolean): SalientConceptCell {
        return new SalientConceptCell(
            this.title,
            this.references,
            this.source,
            folded,
            this.at,
            this.uniqueId,
        );
    }

    accept<Result>(visitor: CellVisitor<Result>): Result {
        return visitor.visitSalientConcept(this);
    }
}
