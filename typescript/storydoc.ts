/**
 * A story and the layout it is published in, in one human-readable file.
 *
 * The file is `<name>.author`, and it is markdown. What makes it a story document
 * is that the markdown is cut into cells, each opened by a marker that says what
 * the cell *is*:
 *
 *     <!-- cell: chapter title="The First Night" -->
 *
 *     The lantern had gone out again.
 *
 *     <!-- cell: image src="art/cover.jpg" full-page="yes" -->
 *
 * The marker is an HTML comment, so every reader that renders markdown renders the
 * document and shows none of the scaffolding, and every editor that opens text can
 * edit it. There is no custom editor a person is obliged to use — which is the
 * whole point of not being a notebook full of escaped JSON strings.
 *
 * Two properties are load-bearing:
 *
 * **The format is open.** A cell's type is any name, and this module knows nothing
 * about most of them. An unrecognised type is carried through parse and save
 * untouched, so a document written by a newer version — or by hand — survives a
 * round trip through an older one rather than losing the cells it could not name.
 *
 * **Plain markdown is already a story document.** A file with no markers at all
 * parses as one `markdown` cell holding the lot. Nothing has to be converted, and a
 * document whose markers are all deleted is still the story.
 *
 * The one ambiguity worth naming: a line inside a cell that itself looks like a
 * marker opens a new cell. Markdown has the same bargain with fences.
 */

import { Cell, splitlines } from "./cells/cell";
import { PlotCell, PlotEdge, PlotNode } from "./cells/plot_cell";
import { SalientConceptCell } from "./cells/salient_concept_cell";
import { TitlePageCell } from "./cells/title_page_cell";
import { AuthorDocDiff } from "./diff";
import { parse, parseSuggestions, serialize } from "./parser";
import type { Suggestion } from "./suggestion";
import { PassagesSynchronizer } from "./synchronizers/passages_synchronizer";

export const EXTENSION = ".author";

/** An .author document */
export class Document {
    private _cells: readonly Cell[];
    private _suggestions: readonly Suggestion[];

    constructor(
        text: string,
        private readonly _path: string | null = null,
    ) {
        this._cells = parse(text);
        this._suggestions = parseSuggestions(text);
        const suggestionWithoutItsCell = this._suggestions.find(
            (suggestion) => this.cellWithId(suggestion.cellId) === undefined,
        );
        if (suggestionWithoutItsCell !== undefined) {
            throw new Error(
                `The suggestion is for cell ${suggestionWithoutItsCell.cellId}, which the document does not have`,
            );
        }
    }

    /**
     * A new document made of `cells`, in their order. The cells are written out
     * and read back, so every cell is as a fresh read of the file gives it, with
     * the lines it is written on.
     *
     * Use it to build a document. To change one, use `withCells` or `withCell`,
     * which keep what points at the story's words in step.
     */
    static fromCells(
        cells: readonly Cell[],
        path: string | null = null,
        suggestions: readonly Suggestion[] = [],
    ): Document {
        const written = new Document("", path);
        written._cells = [...cells];
        written._suggestions = [...suggestions];
        const serialized = written.serialize();
        const built = new Document(serialized, path);
        return built;
    }

    get path(): string | null {
        return this._path;
    }

    /** The cells, in their order: a copy, so changing it changes no document. */
    get cells(): readonly Cell[] {
        const cells = [...this._cells];
        return cells;
    }

    /** @deprecated Use `serialize()`. */
    get text(): string {
        const serialized = this.serialize();
        return serialized;
    }

    /** The document as text, such that `parse(text) == cells`. */
    serialize(): string {
        const serialized = serialize(this._cells, this._suggestions);
        return serialized;
    }

    get suggestions(): readonly Suggestion[] {
        const suggestions = [...this._suggestions];
        return suggestions;
    }

    suggestionFor(cellId: string): Suggestion | undefined {
        return this._suggestions.find((suggestion) => suggestion.cellId === cellId);
    }

    get lines(): string[] {
        const serialized = this.serialize();
        return splitlines(serialized);
    }

    /** What the book says of itself, blank in a document that says nothing. */

    get titlePage(): TitlePageCell {
        return (
            this._cells.find((cell) => cell instanceof TitlePageCell) ??
            new TitlePageCell()
        );
    }

    get title(): string {
        return this.titlePage.title || "Anonymous";
    }

    cellWithId(cellId: string): Cell | undefined {
        return this._cells.find((cell) => cell.uniqueId === cellId);
    }

    /**
     * The first cell of `cellType` whose kind is `kind`; undefined when the
     * document has no such cell.
     */
    getCell<C extends Cell>(
        cellType: abstract new (...args: never[]) => C,
        kind: string,
    ): C | undefined {
        const found = this._cells.find(
            (cell): cell is C => cell instanceof cellType && cell.kind === kind,
        );
        return found;
    }

    /**
     * A new document made of `cells`, in their order: a cell with a new id is
     * added where it stands, and a cell left out is removed. Whatever points at
     * the story's words keeps pointing at the same words. No document is
     * changed: the one you hold stays as it is.
     */
    withCells(cells: readonly Cell[]): Document {
        const written = Document.fromCells(
            cells,
            this._path,
            this._suggestions,
        );
        const change = AuthorDocDiff.diff(this, written);
        const synchronizer = new PassagesSynchronizer();
        const passagesMoved = synchronizer.synchronize(this, change);
        const synchronized = passagesMoved.applyTheDiff(written);
        return synchronized;
    }

    /**
     * A new document with `cell` in the place of the cell with its id, kept in
     * step as `withCells` keeps it.
     */
    withCell(cell: Cell): Document {
        const replaced = this._cells.map((held) => (held.uniqueId === cell.uniqueId ? cell : held));
        const withTheCell = this.withCells(replaced);
        return withTheCell;
    }

    withSuggestion(suggestion: Suggestion): Document {
        const others = this._suggestions.filter(
            (held) => held.cellId !== suggestion.cellId,
        );
        const withTheSuggestion = Document.fromCells(this._cells, this._path, [
            ...others,
            suggestion,
        ]);
        return withTheSuggestion;
    }

    withoutSuggestion(cellId: string): Document {
        const others = this._suggestions.filter(
            (held) => held.cellId !== cellId,
        );
        const withoutTheSuggestion = Document.fromCells(
            this._cells,
            this._path,
            others,
        );
        return withoutTheSuggestion;
    }

    salientConcepts(): SalientConceptCell[] {
        return this._cells.filter((cell) => cell instanceof SalientConceptCell);
    }

    plots(): PlotCell[] {
        return this._cells.filter((cell) => cell instanceof PlotCell);
    }

    getPlotOfEdge(edge: PlotEdge): PlotCell {
        const plot = this.plots().find((plot) =>
            plot.edges.some(
                (edgeOfThePlot) =>
                    edgeOfThePlot.edgeId === edge.edgeId &&
                    edgeOfThePlot.fromNodeId === edge.fromNodeId &&
                    edgeOfThePlot.toNodeId === edge.toNodeId,
            ),
        );
        if (plot === undefined) {
            throw new Error(edge.edgeId);
        }
        return plot;
    }

    getPlotOfNode(node: PlotNode): PlotCell {
        const plot = this.plots().find((plot) =>
            plot.nodes.some(
                (nodeOfThePlot) =>
                    nodeOfThePlot.nodeId === node.nodeId &&
                    nodeOfThePlot.storyWordRange?.firstWord === node.storyWordRange?.firstWord &&
                    nodeOfThePlot.storyWordRange?.lastWord === node.storyWordRange?.lastWord &&
                    nodeOfThePlot.timestamp === node.timestamp &&
                    nodeOfThePlot.placeId === node.placeId &&
                    nodeOfThePlot.characterIds.length === node.characterIds.length &&
                    nodeOfThePlot.characterIds.every(
                        (characterId, at) => characterId === node.characterIds[at],
                    ) &&
                    nodeOfThePlot.summary === node.summary,
            ),
        );
        if (plot === undefined) {
            throw new Error(node.nodeId);
        }
        return plot;
    }

    toString(): string {
        return this.serialize();
    }

    /** The cell `line` falls in. */

    cellAt(line: number): Cell | null {
        for (const cell of this._cells) {
            if (cell.at && cell.at[0] <= line && line <= cell.at[1]) {
                return cell;
            }
        }
        return null;
    }
}
