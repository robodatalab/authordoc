import type { AuthorDocSynchronizer } from "../author_doc_synchronizer";
import { AuthorDocDiff } from "../diff";
import { Document } from "../storydoc";
import type { AboutCell } from "../cells/about_cell";
import type { BlurbCell } from "../cells/blurb_cell";
import type { Cell } from "../cells/cell";
import type { CellVisitor } from "../cells/cell_visitor";
import type { ChapterCell } from "../cells/chapter_cell";
import type { DisclaimerCell } from "../cells/disclaimer_cell";
import type { DividerCell } from "../cells/divider_cell";
import type { ImageCell } from "../cells/image_cell";
import type { MarkdownCell } from "../cells/markdown_cell";
import type { NoteCell } from "../cells/note_cell";
import type { PartCell } from "../cells/part_cell";
import { PlotCell } from "../cells/plot_cell";
import type { RecapCell } from "../cells/recap_cell";
import {
    SalientConceptCell,
    SalientConceptReference,
} from "../cells/salient_concept_cell";
import { StoryWordRange } from "../cells/story_word_range";
import type { TableOfContentsCell } from "../cells/table_of_contents_cell";
import type { TitlePageCell } from "../cells/title_page_cell";
import type { UnknownCell } from "../cells/unknown_cell";
import {
    StoryWordsIterator,
    type StoryWord,
} from "../iterators/story_words_iterator";

class WordsAnEditReplaced {
    constructor(
        readonly firstOldWord: number,
        readonly endOfOldWords: number,
        readonly firstNewWord: number,
        readonly endOfNewWords: number,
    ) {}

    fallsWithin(range: StoryWordRange): boolean {
        if (this.firstOldWord === this.endOfOldWords) {
            return (
                range.firstWord < this.firstOldWord &&
                this.firstOldWord <= range.lastWord
            );
        }
        return (
            this.firstOldWord <= range.lastWord &&
            this.endOfOldWords > range.firstWord
        );
    }
}

function sameRange(one: StoryWordRange | null, other: StoryWordRange): boolean {
    return one !== null && one.firstWord === other.firstWord && one.lastWord === other.lastWord;
}

class WhereTheStoryWordsWent {
    constructor(
        private readonly newNumberOfEachOldWord: ReadonlyMap<number, number>,
        private readonly wordsTheEditsReplaced: readonly WordsAnEditReplaced[],
    ) {}

    rangeKeptInStep(range: StoryWordRange): StoryWordRange | null {
        const wordsItCovers: number[] = [];
        for (let word = range.firstWord; word <= range.lastWord; word += 1) {
            const newNumber = this.newNumberOfEachOldWord.get(word);
            if (newNumber !== undefined) {
                wordsItCovers.push(newNumber);
            }
        }
        for (const edit of this.wordsTheEditsReplaced) {
            if (
                edit.firstNewWord < edit.endOfNewWords &&
                edit.fallsWithin(range)
            ) {
                wordsItCovers.push(edit.firstNewWord, edit.endOfNewWords - 1);
            }
        }
        if (wordsItCovers.length === 0) {
            return null;
        }
        const firstWord = Math.min(...wordsItCovers);
        const lastWord = Math.max(...wordsItCovers);
        return new StoryWordRange(firstWord, lastWord);
    }
}

function storyWordsOfEachCell(document: Document): Map<string, StoryWord[]> {
    const storyWordsOfEachCell = new Map<string, StoryWord[]>();
    const storyWords = new StoryWordsIterator(document);
    for (const word of storyWords) {
        const wordsOfTheCell = storyWordsOfEachCell.get(word.cellId) ?? [];
        wordsOfTheCell.push(word);
        storyWordsOfEachCell.set(word.cellId, wordsOfTheCell);
    }
    return storyWordsOfEachCell;
}

function wordsBothEndsOfTheCellShare(
    oldWords: readonly StoryWord[],
    newWords: readonly StoryWord[],
): { wordsAtTheStart: number; wordsAtTheEnd: number } {
    const wordsInTheShorter = Math.min(oldWords.length, newWords.length);
    let wordsAtTheStart = 0;
    while (
        wordsAtTheStart < wordsInTheShorter &&
        oldWords[wordsAtTheStart].text === newWords[wordsAtTheStart].text
    ) {
        wordsAtTheStart += 1;
    }
    let wordsAtTheEnd = 0;
    while (
        wordsAtTheEnd < wordsInTheShorter - wordsAtTheStart &&
        oldWords[oldWords.length - 1 - wordsAtTheEnd].text ===
            newWords[newWords.length - 1 - wordsAtTheEnd].text
    ) {
        wordsAtTheEnd += 1;
    }
    return { wordsAtTheStart, wordsAtTheEnd };
}

function whereTheStoryWordsWent(
    before: Document,
    after: Document,
): WhereTheStoryWordsWent {
    const newNumberOfEachOldWord = new Map<number, number>();
    const wordsTheEditsReplaced: WordsAnEditReplaced[] = [];
    const storyWordsBefore = storyWordsOfEachCell(before);
    const storyWordsAfter = storyWordsOfEachCell(after);
    for (const [cellId, oldWords] of storyWordsBefore) {
        const newWords = storyWordsAfter.get(cellId);
        if (newWords === undefined) {
            continue;
        }
        const { wordsAtTheStart, wordsAtTheEnd } = wordsBothEndsOfTheCellShare(
            oldWords,
            newWords,
        );
        for (let word = 0; word < wordsAtTheStart; word += 1) {
            newNumberOfEachOldWord.set(
                oldWords[word].number,
                newWords[word].number,
            );
        }
        for (let word = 0; word < wordsAtTheEnd; word += 1) {
            const oldWord = oldWords[oldWords.length - 1 - word];
            const newWord = newWords[newWords.length - 1 - word];
            newNumberOfEachOldWord.set(oldWord.number, newWord.number);
        }
        if (
            wordsAtTheStart + wordsAtTheEnd <
            Math.max(oldWords.length, newWords.length)
        ) {
            const firstOldWord = oldWords[0].number;
            const firstNewWord = newWords[0].number;
            const wordsTheEditReplaced = new WordsAnEditReplaced(
                firstOldWord + wordsAtTheStart,
                firstOldWord + oldWords.length - wordsAtTheEnd,
                firstNewWord + wordsAtTheStart,
                firstNewWord + newWords.length - wordsAtTheEnd,
            );
            wordsTheEditsReplaced.push(wordsTheEditReplaced);
        }
    }
    return new WhereTheStoryWordsWent(
        newNumberOfEachOldWord,
        wordsTheEditsReplaced,
    );
}

/**
 * A range the change leaves as it was counts the story's words as they stood
 * before it, and moves with them; a range the change sets, new or different,
 * counts them as they stand after it, and is kept as the change writes it. So
 * the order the change writes its cells in makes no difference.
 */
class PassagesKeptInStep implements CellVisitor<Cell> {
    constructor(
        private readonly before: Document,
        private readonly whereTheWordsWent: WhereTheStoryWordsWent,
    ) {}

    visitSalientConcept(cell: SalientConceptCell): SalientConceptCell {
        const held = this.before.cellWithId(cell.uniqueId);
        const referencesBefore = held instanceof SalientConceptCell ? held.references : [];
        const referencesKeptInStep: SalientConceptReference[] = [];
        for (const reference of cell.references) {
            const referenceBefore = referencesBefore.find(
                (before) => before.referenceId === reference.referenceId,
            );
            if (!sameRange(referenceBefore?.storyWordRange ?? null, reference.storyWordRange)) {
                referencesKeptInStep.push(reference);
                continue;
            }
            const rangeKeptInStep = this.whereTheWordsWent.rangeKeptInStep(
                reference.storyWordRange,
            );
            if (rangeKeptInStep !== null) {
                const referenceKeptInStep = new SalientConceptReference(
                    reference.referenceId,
                    rangeKeptInStep,
                );
                referencesKeptInStep.push(referenceKeptInStep);
            }
        }
        return new SalientConceptCell(
            cell.title,
            referencesKeptInStep,
            cell.source,
            cell.folded,
            cell.at,
            cell.uniqueId,
        );
    }

    // An event outlives the words that told it: when they are gone, it is
    // simply told by none.
    visitPlot(cell: PlotCell): PlotCell {
        const held = this.before.cellWithId(cell.uniqueId);
        const nodesBefore = held instanceof PlotCell ? held.nodes : [];
        const nodesKeptInStep = cell.nodes.map((node) => {
            const nodeBefore = nodesBefore.find((before) => before.nodeId === node.nodeId);
            if (
                node.storyWordRange === null ||
                !sameRange(nodeBefore?.storyWordRange ?? null, node.storyWordRange)
            ) {
                return node;
            }
            const rangeKeptInStep = this.whereTheWordsWent.rangeKeptInStep(
                node.storyWordRange,
            );
            return node.withStoryWordRange(rangeKeptInStep);
        });
        return new PlotCell(
            cell.title,
            nodesKeptInStep,
            cell.edges,
            cell.overview,
            cell.folded,
            cell.at,
            cell.uniqueId,
            cell._concepts,
        );
    }

    visitMarkdown(cell: MarkdownCell): MarkdownCell {
        return cell;
    }

    visitChapter(cell: ChapterCell): ChapterCell {
        return cell;
    }

    visitPart(cell: PartCell): PartCell {
        return cell;
    }

    visitDivider(cell: DividerCell): DividerCell {
        return cell;
    }

    visitTitlePage(cell: TitlePageCell): TitlePageCell {
        return cell;
    }

    visitImage(cell: ImageCell): ImageCell {
        return cell;
    }

    visitTableOfContents(cell: TableOfContentsCell): TableOfContentsCell {
        return cell;
    }

    visitDisclaimer(cell: DisclaimerCell): DisclaimerCell {
        return cell;
    }

    visitAbout(cell: AboutCell): AboutCell {
        return cell;
    }

    visitBlurb(cell: BlurbCell): BlurbCell {
        return cell;
    }

    visitNote(cell: NoteCell): NoteCell {
        return cell;
    }

    visitRecap(cell: RecapCell): RecapCell {
        return cell;
    }

    visitUnknown(cell: UnknownCell): UnknownCell {
        return cell;
    }
}

export class PassagesSynchronizer implements AuthorDocSynchronizer {
    synchronize(before: Document, change: AuthorDocDiff): AuthorDocDiff {
        const after = change.applyTheDiff(before);
        const whereTheWordsWent = whereTheStoryWordsWent(before, after);
        const passagesKeptInStep = new PassagesKeptInStep(before, whereTheWordsWent);
        const cellsWithTheirPassagesInStep = after.cells.map((cell) =>
            cell.accept<Cell>(passagesKeptInStep),
        );
        const documentWithItsPassagesInStep = Document.fromCells(
            cellsWithTheirPassagesInStep,
            after.path,
        );
        return AuthorDocDiff.diff(after, documentWithItsPassagesInStep);
    }
}
