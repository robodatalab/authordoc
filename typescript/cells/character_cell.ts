import type { Document } from "../storydoc";
import { Cell } from "./cell";
import type { CellVisitor } from "./cell_visitor";
import { SalientConceptCell } from "./salient_concept_cell";

export const CHARACTER = "character";

export class CharacterCell extends Cell {
    readonly kind = CHARACTER;
    readonly _concepts: readonly string[];

    constructor(
        readonly title: string = "",
        source: string = "",
        folded: boolean = false,
        at: readonly [number, number] | null = null,
        uniqueId: string = crypto.randomUUID(),
        concepts: readonly string[] = [],
    ) {
        super(source, folded, at, uniqueId);
        this._concepts = Object.freeze([...concepts]);
    }

    concepts(document: Document): SalientConceptCell[] {
        const referenced = this._concepts.map((conceptId) =>
            document.cellWithId(conceptId),
        );
        const concepts = referenced.filter(
            (cell) => cell instanceof SalientConceptCell,
        );
        return concepts;
    }

    withConcepts(concepts: readonly SalientConceptCell[]): CharacterCell {
        const conceptIds = concepts.map((concept) => concept.uniqueId);
        const supporting = new CharacterCell(
            this.title,
            this.source,
            this.folded,
            this.at,
            this.uniqueId,
            conceptIds,
        );
        return supporting;
    }

    withSource(source: string): CharacterCell {
        return new CharacterCell(
            this.title,
            source,
            this.folded,
            this.at,
            this.uniqueId,
            this._concepts,
        );
    }

    withFolded(folded: boolean): CharacterCell {
        return new CharacterCell(
            this.title,
            this.source,
            folded,
            this.at,
            this.uniqueId,
            this._concepts,
        );
    }

    accept<Result>(visitor: CellVisitor<Result>): Result {
        return visitor.visitCharacter(this);
    }
}
