import { describe, expect, it } from "vitest";

import { CellRemoved } from "../../typescript/changes/cell_removed";
import { AuthorDocDiff } from "../../typescript/diff";
import { Document } from "../../typescript/storydoc";
import { Suggestion } from "../../typescript/suggestion";

const WITH_A_SUGGESTION =
    '<!-- cell: markdown id="c1" -->\n\nShe saw the door.\n\n' +
    '<!-- suggestion: id="c1" -->\n' +
    '<!-- change: text from="16" removed="" written=" at last" -->\n\n' +
    '<!-- cell: markdown id="c2" -->\n\nHe heard the bell.\n';

const THE_CHAPTER_BEFORE =
    '<!-- cell: chapter id="h1" title="Bell" -->\n\nThe bell rings.\n';

const THE_CHAPTER_AFTER =
    '<!-- cell: chapter id="h1" title="The bell tolls" folded="true" -->\n\nThe bell tolls at night.\n';

describe("Suggestion — a change proposed to a cell, kept beside it as the diff the diff tool takes", () => {
    it("is read after the cell it patches, leaving the cells as they are", () => {
        const document = new Document(WITH_A_SUGGESTION);

        const [suggestion] = document.suggestions;

        expect([
            document.cells.map((cell) => cell.source),
            document.suggestions.length,
            suggestion.cellId,
        ]).toEqual([["She saw the door.", "He heard the bell."], 1, "c1"]);
    });

    it("carries a diff that patches its cell", () => {
        const document = new Document(WITH_A_SUGGESTION);
        const suggestion = document.suggestionFor("c1")!;

        const patched = suggestion.diff().applyTheDiff(document);

        expect(patched.cellWithId("c1")?.source).toBe("She saw the door at last.");
    });

    it("is written back as it was read", () => {
        const document = new Document(WITH_A_SUGGESTION);

        expect(document.serialize()).toBe(WITH_A_SUGGESTION);
    });

    it("is written back by the deprecated text, too, until it is retired", () => {
        const document = new Document(WITH_A_SUGGESTION);

        expect(document.text).toBe(WITH_A_SUGGESTION);
    });

    it("keeps every change of the diff the diff tool gives, through writing and reading back", () => {
        const before = new Document(THE_CHAPTER_BEFORE);
        const after = new Document(THE_CHAPTER_AFTER);
        const diff = AuthorDocDiff.diff(before, after);
        const suggestion = new Suggestion("h1", diff);
        const suggested = before.withSuggestion(suggestion);

        const readBack = new Document(suggested.serialize());
        const patched = readBack.suggestionFor("h1")!.diff().applyTheDiff(readBack);
        const patchedWritten = Document.fromCells(patched.cells).serialize();

        expect(patchedWritten).toBe(THE_CHAPTER_AFTER);
    });

    it("is refused for a cell the document does not have, when added to it", () => {
        const document = new Document('<!-- cell: markdown id="c1" -->\n\nShe saw the door.\n');
        const emptyDiff = new AuthorDocDiff([]);
        const suggestion = new Suggestion("c9", emptyDiff);

        expect(() => document.withSuggestion(suggestion)).toThrow(
            "The suggestion is for cell c9, which the document does not have",
        );
    });

    it("is refused for a cell the document does not have, when the document is built with it", () => {
        const document = new Document('<!-- cell: markdown id="c1" -->\n\nShe saw the door.\n');
        const emptyDiff = new AuthorDocDiff([]);
        const suggestion = new Suggestion("c9", emptyDiff);

        expect(() => Document.fromCells(document.cells, null, [suggestion])).toThrow(
            "The suggestion is for cell c9, which the document does not have",
        );
    });

    it("is refused for a cell the document does not have, when read", () => {
        const text =
            '<!-- cell: markdown id="c1" -->\n\nShe saw the door.\n\n' +
            '<!-- suggestion: id="c9" -->\n' +
            '<!-- change: text from="0" removed="" written="He heard the bell." -->\n';

        expect(() => new Document(text)).toThrow(
            "The suggestion is for cell c9, which the document does not have",
        );
    });

    it("is one per cell: a new one for a cell takes the place of the one before", () => {
        const document = new Document(WITH_A_SUGGESTION);
        const emptyDiff = new AuthorDocDiff([]);

        const suggestion = new Suggestion("c1", emptyDiff);

        const resuggested = document.withSuggestion(suggestion);

        expect([resuggested.suggestions.length, resuggested.suggestionFor("c1")?.diff()]).toEqual([1, emptyDiff]);
    });

    it("can be taken off its cell", () => {
        const document = new Document(WITH_A_SUGGESTION);

        const withoutIt = document.withoutSuggestion("c1");

        expect([withoutIt.suggestions, withoutIt.serialize()]).toEqual([
            [],
            '<!-- cell: markdown id="c1" -->\n\nShe saw the door.\n\n<!-- cell: markdown id="c2" -->\n\nHe heard the bell.\n',
        ]);
    });

    it("stays with the document while its cells change", () => {
        const document = new Document(WITH_A_SUGGESTION);
        const [, heHeard] = document.cells;

        const heHeardTwice = heHeard.withSource("He heard the bell twice.");

        const changed = document.withCell(heHeardTwice);

        expect(changed.suggestionFor("c1")?.cellId).toBe("c1");
    });

    it("deleting a cell deletes its suggestion", () => {
        const document = new Document(WITH_A_SUGGESTION);
        const [sheSaw, heHeard] = document.cells;
        const sheSawRemoved = new CellRemoved(0, sheSaw);
        const removal = new AuthorDocDiff([sheSawRemoved]);

        const deletedWithCells = document.withCells([heHeard]);
        const deletedWithADiff = removal.applyTheDiff(document);

        expect([deletedWithCells.suggestions, deletedWithADiff.suggestions]).toEqual([[], []]);
    });

    it("gives its diff, and a suggestion with another diff in its place", () => {
        const diff = new AuthorDocDiff([]);
        const otherDiff = new AuthorDocDiff([]);
        const suggestion = new Suggestion("c1", diff);

        const updated = suggestion.withTheDiff(otherDiff);

        expect([suggestion.diff(), updated.cellId, updated.diff()]).toEqual([diff, "c1", otherDiff]);
        expect(updated.diff()).toBe(otherDiff);
    });
});
