import type { AuthorDocChangeVisitor } from "../author_doc_change_visitor";
import type { Cell } from "../cells/cell";
import type { CellAdded } from "../changes/cell_added";
import type { CellHeaderChanged } from "../changes/cell_header_changed";
import type { CellRemoved } from "../changes/cell_removed";
import type { CellTextChanged } from "../changes/cell_text_changed";
import type { CellsMoved } from "../changes/cells_moved";
import { writtenAttributeValue } from "../written_attributes";
import { FOLDED, MarkerAttributes, TRUE } from "./marker_attributes";

export const CELL_ADDED = "added";
export const CELL_REMOVED = "removed";
export const CELLS_MOVED = "moved";
export const CELL_HEADER_CHANGED = "header";
export const CELL_TEXT_CHANGED = "text";

export const AT = "at";
export const KIND = "kind";
export const TEXT = "text";
export const FROM = "from";
export const TEXT_REMOVED = "removed";
export const TEXT_WRITTEN = "written";
export const CELL_IDS_BEFORE = "before";
export const CELL_IDS_AFTER = "after";
export const BEFORE = "before-";
export const AFTER = "after-";

export const CELL_IDS_SEPARATOR = ",";

function prefixed(
    prefix: string,
    attributes: Record<string, string>,
): Record<string, string> {
    const named = Object.entries(attributes).map(([name, value]) => [
        `${prefix}${name}`,
        value,
    ]);
    const attributesPrefixed = Object.fromEntries(named);
    return attributesPrefixed;
}

function changeMarker(
    change: string,
    attributes: Record<string, string>,
): string {
    const said = Object.entries(attributes)
        .map(([name, value]) => ` ${name}="${writtenAttributeValue(value)}"`)
        .join("");
    const marker = `<!-- change: ${change}${said} -->`;
    return marker;
}

export class ChangeMarkers implements AuthorDocChangeVisitor<string> {
    private readonly markerAttributes = new MarkerAttributes();

    visitCellAdded(cellAdded: CellAdded): string {
        const header = this.headerOf(cellAdded.cell);
        const headerAfter = prefixed(AFTER, header);
        const cellIndex = String(cellAdded.cellIndex);
        const marker = changeMarker(CELL_ADDED, {
            [AT]: cellIndex,
            [KIND]: cellAdded.cell.kind,
            [TEXT]: cellAdded.cell.source,
            ...headerAfter,
        });
        return marker;
    }

    visitCellRemoved(cellRemoved: CellRemoved): string {
        const header = this.headerOf(cellRemoved.cell);
        const headerBefore = prefixed(BEFORE, header);
        const cellIndex = String(cellRemoved.cellIndex);
        const marker = changeMarker(CELL_REMOVED, {
            [AT]: cellIndex,
            [KIND]: cellRemoved.cell.kind,
            [TEXT]: cellRemoved.cell.source,
            ...headerBefore,
        });
        return marker;
    }

    visitCellsMoved(cellsMoved: CellsMoved): string {
        const cellIdsBefore = cellsMoved.cellIdsBefore.join(CELL_IDS_SEPARATOR);
        const cellIdsAfter = cellsMoved.cellIdsAfter.join(CELL_IDS_SEPARATOR);
        const marker = changeMarker(CELLS_MOVED, {
            [CELL_IDS_BEFORE]: cellIdsBefore,
            [CELL_IDS_AFTER]: cellIdsAfter,
        });
        return marker;
    }

    visitCellHeaderChanged(cellHeaderChanged: CellHeaderChanged): string {
        const before = this.headerOf(cellHeaderChanged.headerBefore);
        const after = this.headerOf(cellHeaderChanged.headerAfter);
        const headerBefore = prefixed(BEFORE, before);
        const headerAfter = prefixed(AFTER, after);
        const marker = changeMarker(CELL_HEADER_CHANGED, {
            [KIND]: cellHeaderChanged.headerAfter.kind,
            ...headerBefore,
            ...headerAfter,
        });
        return marker;
    }

    visitCellTextChanged(cellTextChanged: CellTextChanged): string {
        const fromCharacter = String(cellTextChanged.fromCharacter);
        const marker = changeMarker(CELL_TEXT_CHANGED, {
            [FROM]: fromCharacter,
            [TEXT_REMOVED]: cellTextChanged.textRemoved,
            [TEXT_WRITTEN]: cellTextChanged.textWritten,
        });
        return marker;
    }

    private headerOf(cell: Cell): Record<string, string> {
        const attributesOfTheKind = cell.accept(this.markerAttributes);
        const header = {
            ...attributesOfTheKind,
            ...(cell.folded ? { [FOLDED]: TRUE } : {}),
        };
        return header;
    }
}
