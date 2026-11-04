import { type Document } from "./storydoc";
import { ABOUT } from "./cells/about_cell";
import { BLURB } from "./cells/blurb_cell";
import type { Cell } from "./cells/cell";
import { CHAPTER } from "./cells/chapter_cell";
import { DISCLAIMER } from "./cells/disclaimer_cell";
import { PART } from "./cells/part_cell";
import { PLOT } from "./cells/plot_cell";
import { RECAP } from "./cells/recap_cell";
import { SALIENT_CONCEPT } from "./cells/salient_concept_cell";
import { TABLE_OF_CONTENTS } from "./cells/table_of_contents_cell";
import { TITLE_PAGE } from "./cells/title_page_cell";

export interface CellOfADocument {
    readonly kind: string;
    readonly uniqueId: string;
}

export interface CellsInASection<CellInTheDocument extends CellOfADocument> {
    cell: CellInTheDocument;
    within: CellsInASection<CellInTheDocument>[];
}

export interface WhereACellStands<CellInTheDocument extends CellOfADocument> {
    section: CellsInASection<CellInTheDocument>;
    among: CellsInASection<CellInTheDocument>[];
    under: CellsInASection<CellInTheDocument>[];
}

const KINDS_THAT_STAND_OUTSIDE_THE_STORY = new Set([
    TITLE_PAGE,
    TABLE_OF_CONTENTS,
    DISCLAIMER,
    ABOUT,
    BLURB,
    RECAP,
    SALIENT_CONCEPT,
    PLOT,
]);

export function standsOutsideTheStory(kind: string): boolean {
    return KINDS_THAT_STAND_OUTSIDE_THE_STORY.has(kind);
}

export function opensASection(kind: string): boolean {
    return kind === PART || kind === CHAPTER;
}

export function aSectionOfKindHolds(
    sectionKind: string,
    kind: string,
): boolean {
    if (standsOutsideTheStory(kind)) {
        return false;
    }
    if (sectionKind === PART) {
        return kind !== PART;
    }
    return sectionKind === CHAPTER && !opensASection(kind);
}

export function cellsBySection<CellInTheDocument extends CellOfADocument>(
    cells: readonly CellInTheDocument[],
): CellsInASection<CellInTheDocument>[] {
    const wholeDocument: CellsInASection<CellInTheDocument>[] = [];
    const openSections: CellsInASection<CellInTheDocument>[] = [];
    for (const cell of cells) {
        while (
            openSections.length > 0 &&
            !aSectionOfKindHolds(
                openSections[openSections.length - 1].cell.kind,
                cell.kind,
            )
        ) {
            openSections.pop();
        }
        const section: CellsInASection<CellInTheDocument> = {
            cell,
            within: [],
        };
        (openSections[openSections.length - 1]?.within ?? wholeDocument).push(
            section,
        );
        openSections.push(section);
    }
    return wholeDocument;
}

export function cellsWithinASection<CellInTheDocument extends CellOfADocument>(
    section: CellsInASection<CellInTheDocument>,
): CellInTheDocument[] {
    const cellsHeld = section.within.flatMap((held) =>
        cellsWithinASection(held),
    );
    return [section.cell, ...cellsHeld];
}

export function whereACellStands<CellInTheDocument extends CellOfADocument>(
    sections: CellsInASection<CellInTheDocument>[],
    cellId: string,
    under: CellsInASection<CellInTheDocument>[] = [],
): WhereACellStands<CellInTheDocument> | undefined {
    for (const section of sections) {
        if (section.cell.uniqueId === cellId) {
            return { section, among: sections, under };
        }
        const standing = whereACellStands(section.within, cellId, [
            ...under,
            section,
        ]);
        if (standing) {
            return standing;
        }
    }
    return undefined;
}

function whereTheCellStands(document: Document, cell: Cell): number {
    return document.cells.findIndex(
        (inTheDocument) => inTheDocument.uniqueId === cell.uniqueId,
    );
}

function endOfSection(
    document: Document,
    section: CellsInASection<Cell>,
): number {
    const standsAt = whereTheCellStands(document, section.cell);
    const cellsHeld = cellsWithinASection(section);
    return standsAt + cellsHeld.length;
}

function moveSection(
    document: Document,
    section: CellsInASection<Cell>,
    lands: number,
): Document {
    const standsAt = whereTheCellStands(document, section.cell);
    const cellsHeld = cellsWithinASection(section);
    const cells = [...document.cells];
    const moved = cells.splice(standsAt, cellsHeld.length);
    const landsAfterTheMove =
        lands > standsAt ? lands - cellsHeld.length : lands;
    cells.splice(landsAfterTheMove, 0, ...moved);
    const movedDocument = document.withCells(cells);
    return movedDocument;
}

/**
 * The document with the section the cell opens moved up past the section
 * before it; the same document when there is none to move past.
 */
export function moveTheSectionUp(document: Document, cellId: string): Document {
    const sections = cellsBySection(document.cells);
    const standing = whereACellStands(sections, cellId);
    if (!standing) {
        return document;
    }
    const { section, among, under } = standing;
    const standsAmongAt = among.indexOf(section);
    const goesBefore = among[standsAmongAt - 1] ?? under[under.length - 1];
    if (!goesBefore) {
        return document;
    }
    const lands = whereTheCellStands(document, goesBefore.cell);
    const moved = moveSection(document, section, lands);
    return moved;
}

/**
 * The document with the section the cell opens moved down past the section
 * after it; the same document when there is none to move past.
 */
export function moveTheSectionDown(document: Document, cellId: string): Document {
    const sections = cellsBySection(document.cells);
    const standing = whereACellStands(sections, cellId);
    if (!standing) {
        return document;
    }
    const { section, among, under } = standing;
    const standsAmongAt = among.indexOf(section);
    const nextInTheScope = among[standsAmongAt + 1];
    if (nextInTheScope) {
        const lands = endOfSection(document, nextInTheScope);
        const moved = moveSection(document, section, lands);
        return moved;
    }
    const scopeItLeaves = under[under.length - 1];
    if (!scopeItLeaves) {
        return document;
    }
    const endOfTheScope = endOfSection(document, scopeItLeaves);
    const pastTheCellThatEndsTheScope = endOfTheScope + 1;
    if (pastTheCellThatEndsTheScope > document.cells.length) {
        return document;
    }
    const moved = moveSection(document, section, pastTheCellThatEndsTheScope);
    return moved;
}

/**
 * The document without the section the cell opens; the same document when no
 * section opens with it.
 */
export function removeTheSection(document: Document, cellId: string): Document {
    const sections = cellsBySection(document.cells);
    const standing = whereACellStands(sections, cellId);
    if (!standing) {
        return document;
    }
    const standsAt = whereTheCellStands(document, standing.section.cell);
    const cellsHeld = cellsWithinASection(standing.section);
    const cells = [...document.cells];
    cells.splice(standsAt, cellsHeld.length);
    const removed = document.withCells(cells);
    return removed;
}
