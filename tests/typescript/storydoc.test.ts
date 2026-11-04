import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it, vi } from "vitest";

import { Document } from "../../typescript/storydoc";
import { MarkdownCell } from "../../typescript/cells/markdown_cell";
import {
    SalientConceptCell,
    SalientConceptReference,
} from "../../typescript/cells/salient_concept_cell";
import {
    PlotCell,
    PlotEdge,
    PlotNode,
} from "../../typescript/cells/plot_cell";
import { StoryWordRange } from "../../typescript/cells/story_word_range";
import { UnknownCell } from "../../typescript/cells/unknown_cell";
import type { Cell } from "../../typescript/cells/cell";
import { ChapterCell } from "../../typescript/cells/chapter_cell";
import {
    moveTheSectionDown,
    moveTheSectionUp,
    removeTheSection,
} from "../../typescript/story_sections";
import {
    StoryTextSpan,
    StoryWord,
    StoryWordsIterator,
} from "../../typescript/iterators/story_words_iterator";
import { parse } from "../../typescript/parser";

interface CorpusCase {
    name: string;
    text: string;
    cells: { kind: string; source: string; id: string }[];
    dumped: string;
}

const CORPUS: { cases: CorpusCase[] } = JSON.parse(
    readFileSync(join(__dirname, "../storydoc_corpus.json"), "utf-8"),
);

describe("the shared corpus — the same documents authordoc/parser.py reads", () => {
    it.each(CORPUS.cases)("reads $name", ({ text, cells }) => {
        const parsed = parse(text).map((cell) => ({
            kind: cell.kind,
            source: cell.source,
            id: cell.uniqueId,
        }));

        expect(parsed).toEqual(cells);
    });

    it.each(CORPUS.cases)(
        "writes back byte for byte: $name",
        ({ text, dumped }) => {
            const document = new Document(text);

            const written = document.text;

            expect(written).toBe(dumped);
        },
    );

    it.each(CORPUS.cases)("survives a round trip: $name", ({ text }) => {
        const document = new Document(text);
        const written = document.text;

        const readBack = new Document(written);
        const writtenAgain = readBack.text;

        expect(writtenAgain).toBe(written);
    });
});

describe("a salient concept's references", () => {
    it("are read with their ids", () => {
        const document = new Document(
            '<!-- cell: salient-concept id="k1" title="Door" words="r1:2-3, r2:0-1" -->\n',
        );

        const [salientConcept] = document.cells;

        expect(salientConcept).toMatchObject({
            references: [
                new SalientConceptReference("r1", new StoryWordRange(2, 3)),
                new SalientConceptReference("r2", new StoryWordRange(0, 1)),
            ],
        });
    });

    it("are given an id when written without one", () => {
        vi.spyOn(crypto, "randomUUID").mockReturnValueOnce(
            "3f1c0e2a-0000-4000-8000-000000000001",
        );
        const document = new Document(
            '<!-- cell: salient-concept id="k1" title="Door" words="2-3" -->\n',
        );

        const [salientConcept] = document.cells;

        expect(salientConcept).toMatchObject({
            references: [
                new SalientConceptReference(
                    "3f1c0e2a-0000-4000-8000-000000000001",
                    new StoryWordRange(2, 3),
                ),
            ],
        });
    });

    it("are written with their ids", () => {
        const salientConcept = new SalientConceptCell(
            "Door",
            [
                new SalientConceptReference("r1", new StoryWordRange(2, 3)),
                new SalientConceptReference("r2", new StoryWordRange(0, 1)),
            ],
            "",
            false,
            null,
            "k1",
        );

        const written = Document.fromCells([salientConcept]).text;

        expect(written).toBe(
            '<!-- cell: salient-concept id="k1" title="Door" words="r1:2-3, r2:0-1" -->\n',
        );
    });
});

describe("a plot's events", () => {
    const THE_PLOT = [
        '<!-- cell: plot id="p2" title="Captain Varn and her daughter" edges="x1:e1>e2" -->',
        "",
        '<ol title="How Captain Varn gave her life to buy her daughter time.">',
        '<li id="e1" timestamp="1.1" location="earth, Varn\'s house" words="412-468">Captain Varn watches the news with her daughter.</li>',
        '<li id="e2" timestamp="1.4" location="earth, command center">Varn is given command of the corvette.</li>',
        "</ol>",
        "",
    ].join("\n");

    it("are read with their timestamp, location, words and summary", () => {
        const [plot] = new Document(THE_PLOT).cells;

        expect(plot).toMatchObject({
            title: "Captain Varn and her daughter",
            overview: "How Captain Varn gave her life to buy her daughter time.",
            nodes: [
                new PlotNode(
                    "e1",
                    new StoryWordRange(412, 468),
                    "1.1",
                    "earth, Varn's house",
                    "Captain Varn watches the news with her daughter.",
                ),
                new PlotNode(
                    "e2",
                    null,
                    "1.4",
                    "earth, command center",
                    "Varn is given command of the corvette.",
                ),
            ],
            edges: [new PlotEdge("x1", "e1", "e2")],
        });
    });

    it("are written in the order the plot gives them, the words only of an event the story tells", () => {
        const plot = new PlotCell(
            "The door",
            [
                new PlotNode("e2", null, "1.2", "the hall", "She opens the door."),
                new PlotNode("e1", new StoryWordRange(2, 3), "1.1", "the hall", "She finds the door."),
            ],
            [new PlotEdge("x1", "e1", "e2")],
            "She finds a door, and opens it.",
            false,
            null,
            "p1",
        );

        const written = Document.fromCells([plot]).text;

        expect(written).toBe(
            [
                '<!-- cell: plot id="p1" title="The door" edges="x1:e1>e2" -->',
                "",
                '<ol title="She finds a door, and opens it.">',
                '<li id="e2" timestamp="1.2" location="the hall">She opens the door.</li>',
                '<li id="e1" timestamp="1.1" location="the hall" words="2-3">She finds the door.</li>',
                "</ol>",
                "",
            ].join("\n"),
        );
    });

    it("are none in a body that is not a list of them, which is all overview", () => {
        const [plot] = new Document(
            '<!-- cell: plot id="p1" title="The door" -->\n\nShe finds the door.\n',
        ).cells;

        expect(plot).toMatchObject({
            overview: "She finds the door.",
            nodes: [],
        });
    });

    it("are kept when the overview is rewritten", () => {
        const [plot] = new Document(THE_PLOT).cells as PlotCell[];

        const redescribed = plot.withOverview("How a mother bought her daughter time.");

        expect(redescribed.overview).toBe("How a mother bought her daughter time.");
        expect(redescribed.nodes).toEqual(plot.nodes);
    });

    it("are read again from the body when the body is rewritten", () => {
        const [plot] = new Document(THE_PLOT).cells as PlotCell[];

        const rewritten = plot.withSource(
            '<ol title="A mother.">\n<li id="e1" timestamp="2.1" location="orbit">Varn calls her daughter.</li>\n</ol>',
        );

        expect(rewritten).toMatchObject({
            overview: "A mother.",
            nodes: [new PlotNode("e1", null, "2.1", "orbit", "Varn calls her daughter.")],
            edges: plot.edges,
        });
    });

    it("are found by their id", () => {
        const [plot] = new Document(THE_PLOT).cells as PlotCell[];

        const found = plot.getNodeById("e2");

        expect(found).toBe(plot.nodes[1]);
    });

    it("are not found by an id no event has", () => {
        const [plot] = new Document(THE_PLOT).cells as PlotCell[];

        expect(() => plot.getNodeById("e3")).toThrow();
    });

    it("take a new moment, place, summary and words, one at a time", () => {
        const [plot] = new Document(THE_PLOT).cells as PlotCell[];
        const [event] = plot.nodes;

        const timed = event.withTimestamp("2.1");
        const moved = timed.withLocation("orbit");
        const retold = moved.withSummary("Varn calls her daughter.");
        const untold = retold.withStoryWordRange(null);

        expect(untold).toEqual(new PlotNode("e1", null, "2.1", "orbit", "Varn calls her daughter."));
        expect(event.summary).toBe("Captain Varn watches the news with her daughter.");
    });

    it("one is put in place of the event of its id", () => {
        const [plot] = new Document(THE_PLOT).cells as PlotCell[];
        const [first, second] = plot.nodes;
        const retold = second.withSummary("Varn takes command of the corvette.");

        const replotted = plot.withNode(retold);

        expect(replotted.nodes).toEqual([first, retold]);
        expect(replotted.edges).toEqual(plot.edges);
        expect(plot.nodes).toEqual([first, second]);
    });
});

describe("a plot's edges", () => {
    it("belong to the plot that has them", () => {
        const theDoor = new PlotCell(
            "The door",
            [new PlotNode("e1", null), new PlotNode("e2", null)],
            [new PlotEdge("x1", "e1", "e2")],
            "",
            false,
            null,
            "p1",
        );
        const theBell = new PlotCell(
            "The bell",
            [new PlotNode("e3", null), new PlotNode("e4", null)],
            [new PlotEdge("x2", "e3", "e4")],
            "",
            false,
            null,
            "p2",
        );
        const document = Document.fromCells([theDoor, theBell]);

        const plot = document.getPlotOfEdge(new PlotEdge("x2", "e3", "e4"));

        expect(plot.title).toBe("The bell");
    });
});

describe("the plot of an event", () => {
    const writtenDocument = () =>
        Document.fromCells([
            new PlotCell(
                "The door",
                [new PlotNode("e1", null), new PlotNode("e2", null)],
                [new PlotEdge("x1", "e1", "e2")],
                "",
                false,
                null,
                "p1",
            ),
            new PlotCell(
                "The bell",
                [new PlotNode("e3", null), new PlotNode("e4", null)],
                [new PlotEdge("x2", "e3", "e4")],
                "",
                false,
                null,
                "p2",
            ),
        ]);

    it.each([
        ["in the first plot", new PlotNode("e1", null), "The door"],
        ["in the second plot", new PlotNode("e4", null), "The bell"],
    ] as const)("belong to the plot that has them: %s", (_, node, expectedTitle) => {
        const document = writtenDocument();

        const plot = document.getPlotOfNode(node);

        expect(plot.title).toBe(expectedTitle);
    });
});

describe("a plot's edges of an event", () => {
    // e1 leads to e2 and to e3, and e2 leads to e3.
    const thePlot = () =>
        new PlotCell(
            "The door",
            [new PlotNode("e1", null), new PlotNode("e2", null), new PlotNode("e3", null)],
            [new PlotEdge("x1", "e1", "e2"), new PlotEdge("x2", "e1", "e3"), new PlotEdge("x3", "e2", "e3")],
            "",
            false,
            null,
            "p1",
        );

    it.each([
        ["none lead to the first event", new PlotNode("e1", null), []],
        ["one leads to an event", new PlotNode("e2", null), [new PlotEdge("x1", "e1", "e2")]],
        [
            "two lead to an event",
            new PlotNode("e3", null),
            [new PlotEdge("x2", "e1", "e3"), new PlotEdge("x3", "e2", "e3")],
        ],
    ] as const)("inbound are the edges that lead to the event: %s", (_, node, expected) => {
        const plot = thePlot();

        const inbound = plot.inboundEdges(node);

        expect(inbound).toEqual(expected);
    });

    it.each([
        [
            "two leave an event",
            new PlotNode("e1", null),
            [new PlotEdge("x1", "e1", "e2"), new PlotEdge("x2", "e1", "e3")],
        ],
        ["one leaves an event", new PlotNode("e2", null), [new PlotEdge("x3", "e2", "e3")]],
        ["none leave the last event", new PlotNode("e3", null), []],
    ] as const)("outbound are the edges that leave the event: %s", (_, node, expected) => {
        const plot = thePlot();

        const outbound = plot.outboundEdges(node);

        expect(outbound).toEqual(expected);
    });
});

describe("replacing a cell", () => {
    const writtenDocument = () =>
        Document.fromCells([
            new MarkdownCell("The lantern had gone out.", false, null, "m1"),
            new MarkdownCell("The door stood open.", false, null, "m2"),
        ]);

    it("gives a new document with the cell in the place of the one with its id", () => {
        const document = writtenDocument();
        const lantern = document.cellWithId("m1") as MarkdownCell;
        const lit = lantern.withSource("The lantern was lit.");

        const replaced = document.withCell(lit);

        expect(replaced.cells.map((cell) => cell.source)).toEqual([
            "The lantern was lit.",
            "The door stood open.",
        ]);
        expect(replaced.text).toContain("The lantern was lit.");
    });

    it("leaves the document it is asked of as it was", () => {
        const document = writtenDocument();
        const cellsBefore = [...document.cells];
        const lit = new MarkdownCell("The lantern was lit.", false, null, "m1");

        document.withCell(lit);

        expect(document.cells).toEqual(cellsBefore);
    });

    it("gives the same cells when no cell has the id", () => {
        const document = writtenDocument();
        const bell = new MarkdownCell("A bell rang.", false, null, "m3");

        const replaced = document.withCell(bell);

        expect(replaced.cells).toEqual(document.cells);
    });
});

// The story's words: "She(0) saw(1) the(2) door.(3)" in c2, "He(4) heard(5)
// the(6) bell.(7)" in c3. The concept points at "the bell.", the event at all of c3.
const SHE_SAW = new MarkdownCell("She saw the door.", false, null, "c2");
const HE_HEARD = new MarkdownCell("He heard the bell.", false, null, "c3");
const IT_RANG = new MarkdownCell("It rang.", false, null, "c4");
const THE_BELL = new SalientConceptCell(
    "Bell",
    [new SalientConceptReference("r1", new StoryWordRange(6, 7))],
    "What he heard.",
    false,
    null,
    "k1",
);
const THE_PLOT = new PlotCell(
    "The bell",
    [new PlotNode("n-bell", new StoryWordRange(4, 7))],
    [],
    "",
    false,
    null,
    "p1",
);

describe("changing a document", () => {
    const writtenDocument = () => Document.fromCells([SHE_SAW, HE_HEARD, THE_BELL, THE_PLOT]);

    it.each([
        [
            "a word written before them moves them on",
            new MarkdownCell("She saw the old door.", false, null, "c2"),
            [new SalientConceptReference("r1", new StoryWordRange(7, 8))],
            new StoryWordRange(5, 8),
        ],
        [
            "a word of theirs written over keeps them",
            new MarkdownCell("He heard the bells.", false, null, "c3"),
            [new SalientConceptReference("r1", new StoryWordRange(6, 7))],
            new StoryWordRange(4, 7),
        ],
        [
            "the words they point at deleted lose them",
            new MarkdownCell("He heard", false, null, "c3"),
            [],
            new StoryWordRange(4, 5),
        ],
    ] as const)(
        "with a cell keeps passages and events on their words: %s",
        (_, cell, expectedReferences, expectedWords) => {
            const document = writtenDocument();

            const changed = document.withCell(cell);

            const [concept] = changed.salientConcepts();
            const [plot] = changed.plots();
            const [event] = plot.nodes;
            expect(concept.references).toEqual(expectedReferences);
            expect(event.storyWordRange).toEqual(expectedWords);
        },
    );

    it.each([
        [
            "a cell added before them moves them on",
            [SHE_SAW, IT_RANG, HE_HEARD, THE_BELL, THE_PLOT],
            [new SalientConceptReference("r1", new StoryWordRange(8, 9))],
            new StoryWordRange(6, 9),
        ],
        [
            "a cell before them taken out moves them back",
            [HE_HEARD, THE_BELL, THE_PLOT],
            [new SalientConceptReference("r1", new StoryWordRange(2, 3))],
            new StoryWordRange(0, 3),
        ],
        [
            "the cell they stand in moved takes them with it",
            [HE_HEARD, SHE_SAW, THE_BELL, THE_PLOT],
            [new SalientConceptReference("r1", new StoryWordRange(2, 3))],
            new StoryWordRange(0, 3),
        ],
        ["the cell they stand in taken out loses them", [SHE_SAW, THE_BELL, THE_PLOT], [], null],
    ] as const)(
        "with cells keeps passages and events on their words: %s",
        (_, cells, expectedReferences, expectedWords) => {
            const document = writtenDocument();

            const changed = document.withCells(cells);

            const [concept] = changed.salientConcepts();
            const [plot] = changed.plots();
            const [event] = plot.nodes;
            expect(concept.references).toEqual(expectedReferences);
            expect(event.storyWordRange).toEqual(expectedWords);
        },
    );

    it("has cells that are a copy that changes no document", () => {
        const document = writtenDocument();
        const cells = document.cells;

        // @ts-expect-error: a document's cells are read-only.
        cells.splice(0);

        expect(document.cells).toHaveLength(4);
    });

    it("has cells that cannot be set", () => {
        const document = writtenDocument();

        expect(() => {
            // @ts-expect-error: a document has no setter for its cells.
            document.cells = [];
        }).toThrow(TypeError);
    });

    it("has a path that cannot be set", () => {
        const document = writtenDocument();

        expect(() => {
            // @ts-expect-error: a document has no setter for its path.
            document.path = "elsewhere.author";
        }).toThrow(TypeError);
    });
});

describe("changing a section", () => {
    const writtenDocument = () =>
        Document.fromCells([
            new ChapterCell("One", "", false, null, "ch1"),
            SHE_SAW,
            new ChapterCell("Two", "", false, null, "ch2"),
            HE_HEARD,
            THE_BELL,
            THE_PLOT,
        ]);

    it.each([
        [
            "moved up takes its passages and events with it",
            moveTheSectionUp,
            "ch2",
            [new SalientConceptReference("r1", new StoryWordRange(2, 3))],
            new StoryWordRange(0, 3),
        ],
        [
            "moved down moves the passages and events after it back",
            moveTheSectionDown,
            "ch1",
            [new SalientConceptReference("r1", new StoryWordRange(2, 3))],
            new StoryWordRange(0, 3),
        ],
        [
            "removed moves the passages and events after it back",
            removeTheSection,
            "ch1",
            [new SalientConceptReference("r1", new StoryWordRange(2, 3))],
            new StoryWordRange(0, 3),
        ],
        ["removed loses the passages and events in it", removeTheSection, "ch2", [], null],
    ] as const)(
        "keeps passages and events on their words: %s",
        (_, change, cellId, expectedReferences, expectedWords) => {
            const document = writtenDocument();

            const changed = change(document, cellId);

            const [concept] = changed.salientConcepts();
            const [plot] = changed.plots();
            const [event] = plot.nodes;
            expect(concept.references).toEqual(expectedReferences);
            expect(event.storyWordRange).toEqual(expectedWords);
        },
    );
});

describe("getting a cell", () => {
    const writtenDocument = () =>
        Document.fromCells([
            new MarkdownCell("The lantern had gone out.", false, null, "m1"),
            new UnknownCell("epigraph", {}, "A line.", false, null, "e1"),
            new UnknownCell("epigraph", {}, "Another line.", false, null, "e2"),
        ]);

    it("gives a cell of a known type", () => {
        const document = writtenDocument();

        const found = document.getCell(MarkdownCell, "markdown");

        expect(found).toEqual(
            expect.objectContaining({ uniqueId: "m1", source: "The lantern had gone out." }),
        );
    });

    it.each([
        [
            "the first of two cells of the kind",
            "epigraph",
            expect.objectContaining({ uniqueId: "e1", source: "A line." }),
        ],
        ["none when no cell has the kind", "dedication", undefined],
        ["none when the cell of the kind is of another type", "markdown", undefined],
    ] as const)("gives the first unknown cell with the kind: %s", (_, kind, expected) => {
        const document = writtenDocument();

        const found = document.getCell(UnknownCell, kind);

        expect(found).toEqual(expected);
    });
});

describe("a plot's concepts", () => {
    const THE_STORY = [
        '<!-- cell: salient-concept id="k1" title="Motherhood" -->',
        "",
        "A mother puts her child first.",
        '<!-- cell: salient-concept id="k2" title="The promise" -->',
        "",
        "A promise is kept whatever it costs.",
        '<!-- cell: plot id="p1" title="Captain Varn and her daughter" concepts="k2, k1" -->',
        "",
        '<ol title="How Captain Varn gave her life to buy her daughter time.">',
        "</ol>",
        "",
    ].join("\n");

    it("are the salient concepts the plot references, in its order", () => {
        const document = new Document(THE_STORY);
        const [plot] = document.plots();

        const concepts = plot.concepts(document);

        const [motherhood, promise] = document.salientConcepts();
        expect(concepts).toEqual([promise, motherhood]);
    });

    it("leave out a concept the document no longer has", () => {
        const document = new Document(THE_STORY);
        const [plot] = document.plots();
        const [motherhood] = document.salientConcepts();
        const withoutThePromise = Document.fromCells([motherhood, plot]);

        const concepts = plot.concepts(withoutThePromise);

        expect(concepts).toEqual([motherhood]);
    });

    it("are the ones given when replaced", () => {
        const document = new Document(THE_STORY);
        const [plot] = document.plots();
        const [motherhood] = document.salientConcepts();

        const referencing = plot.withConcepts([motherhood]);

        const concepts = referencing.concepts(document);
        expect(concepts).toEqual([motherhood]);
    });

    it("are written into the plot's marker", () => {
        const motherhood = new SalientConceptCell("Motherhood", [], "", false, null, "k1");
        const promise = new SalientConceptCell("The promise", [], "", false, null, "k2");
        const plot = new PlotCell("The door", [], [], "She finds the door.", false, null, "p1");

        const referencing = plot.withConcepts([motherhood, promise]);

        const written = Document.fromCells([referencing]).text;

        expect(written).toBe(
            [
                '<!-- cell: plot id="p1" title="The door" concepts="k1, k2" -->',
                "",
                '<ol title="She finds the door.">',
                "</ol>",
                "",
            ].join("\n"),
        );
    });

    it("are kept when the body is rewritten", () => {
        const document = new Document(THE_STORY);
        const [plot] = document.plots();

        const rewritten = plot.withSource('<ol title="A mother.">\n</ol>');

        const concepts = rewritten.concepts(document);
        const [motherhood, promise] = document.salientConcepts();
        expect(concepts).toEqual([promise, motherhood]);
    });

    it("are kept when the plot is retitled", () => {
        const document = new Document(THE_STORY);
        const [plot] = document.plots();

        const retitled = plot.withTitle("A mother");

        const concepts = retitled.concepts(document);
        const [motherhood, promise] = document.salientConcepts();
        expect([retitled.title, concepts]).toEqual(["A mother", [promise, motherhood]]);
    });

    it("are kept when the events change", () => {
        const document = new Document(THE_STORY);
        const [plot] = document.plots();
        const nodes = [new PlotNode("e1", null, "1", "earth", "Varn calls her daughter.")];

        const withTheNodes = plot.withNodes(nodes);

        const concepts = withTheNodes.concepts(document);
        const [motherhood, promise] = document.salientConcepts();
        expect([withTheNodes.nodes, concepts]).toEqual([nodes, [promise, motherhood]]);
    });

    it("are kept when the edges change", () => {
        const document = new Document(THE_STORY);
        const [plot] = document.plots();
        const edges = [new PlotEdge("x1", "e1", "e2")];

        const withTheEdges = plot.withEdges(edges);

        const concepts = withTheEdges.concepts(document);
        const [motherhood, promise] = document.salientConcepts();
        expect([withTheEdges.edges, concepts]).toEqual([edges, [promise, motherhood]]);
    });
});

describe("story word ranges", () => {
    it.each([
        ["sharing words", new StoryWordRange(2, 5), new StoryWordRange(4, 8), true],
        ["sharing one word", new StoryWordRange(2, 4), new StoryWordRange(4, 8), true],
        ["one inside the other", new StoryWordRange(2, 8), new StoryWordRange(4, 5), true],
        ["apart", new StoryWordRange(2, 3), new StoryWordRange(4, 8), false],
    ] as const)("overlap when they share a word: %s", (_, one, other, expected) => {
        const overlapping = one.overlaps(other);
        const overlappingTheOtherWay = other.overlaps(one);

        expect([overlapping, overlappingTheOtherWay]).toEqual([expected, expected]);
    });
});

describe("the story text of a document", () => {
    it.each([
        {
            words: "within a cell",
            text: "<!-- cell: markdown -->\n\nShe saw the door.\n",
            startWordIdx: 2,
            endWordIdx: 3,
            storyText: "the door.",
        },
        {
            words: "of one word",
            text: "<!-- cell: markdown -->\n\nShe saw the door.\n",
            startWordIdx: 0,
            endWordIdx: 0,
            storyText: "She",
        },
        {
            words: "across paragraphs of a cell",
            text: "<!-- cell: markdown -->\n\nShe saw the door.\n\nHe heard the bell.\n",
            startWordIdx: 2,
            endWordIdx: 5,
            storyText: "the door.\n\nHe heard",
        },
        {
            words: "across markdown cells",
            text: "<!-- cell: markdown -->\n\nShe saw the door.\n\n<!-- cell: markdown -->\n\nHe heard the bell.\n",
            startWordIdx: 3,
            endWordIdx: 5,
            storyText: "door.\n\nHe heard",
        },
        {
            words: "past cells other than markdown, which hold no story words",
            text: '<!-- cell: chapter title="One Night" -->\n\n<!-- cell: markdown -->\n\nShe saw the door.\n\n<!-- cell: note -->\n\nNot a story word.\n\n<!-- cell: markdown -->\n\nHe heard the bell.\n',
            startWordIdx: 4,
            endWordIdx: 4,
            storyText: "He",
        },
        {
            words: "around a run without a letter or a digit, which is not a word",
            text: "<!-- cell: markdown -->\n\nShe — saw 2 doors.\n",
            startWordIdx: 0,
            endWordIdx: 2,
            storyText: "She — saw 2",
        },
        {
            words: "after a run of letters outside ascii alone, which is not a word",
            text: "<!-- cell: markdown -->\n\nShe saw é café.\n",
            startWordIdx: 2,
            endWordIdx: 2,
            storyText: "café.",
        },
        {
            words: "after the words of a comment in a markdown cell, which are story words",
            text: "<!-- cell: markdown -->\n\nShe saw <!-- a note --> the door.\n",
            startWordIdx: 4,
            endWordIdx: 5,
            storyText: "the door.",
        },
        {
            words: "starting past the end",
            text: "<!-- cell: markdown -->\n\nShe saw the door.\n",
            startWordIdx: 10,
            endWordIdx: 12,
            storyText: "",
        },
        {
            words: "running past the end",
            text: "<!-- cell: markdown -->\n\nShe saw the door.\n",
            startWordIdx: 2,
            endWordIdx: 12,
            storyText: "the door.",
        },
    ])(
        "is the text the story words $words cover",
        ({ text, startWordIdx, endWordIdx, storyText }) => {
            const document = new Document(text);
            const storyWords = new StoryWordsIterator(document);
            const range = new StoryWordRange(startWordIdx, endWordIdx);

            const textCovered = storyWords.text(range);

            expect(textCovered).toBe(storyText);
        },
    );
});

function storyWhereSheSaw(): Document {
    return new Document(
        [
            '<!-- cell: chapter title="One" id="c1" -->',
            "",
            '<!-- cell: markdown id="c2" -->',
            "",
            "She saw the door.",
            "",
            '<!-- cell: note id="n1" -->',
            "",
            "<!--\nNot a story word.\n-->",
            "",
            '<!-- cell: markdown id="c3" -->',
            "",
            "He heard the bell.",
            "",
        ].join("\n"),
    );
}

describe("the story's words", () => {
    it("are the words of the markdown cells, numbered across them", () => {
        const storyWords = new StoryWordsIterator(storyWhereSheSaw());

        const words = Array.from(storyWords, (word) => word.text);

        expect(words).toEqual([
            "She",
            "saw",
            "the",
            "door.",
            "He",
            "heard",
            "the",
            "bell.",
        ]);
    });

    it("know where in their cell they stand", () => {
        const storyWords = new StoryWordsIterator(storyWhereSheSaw());

        const words = Array.from(storyWords);

        expect(words[5]).toEqual(new StoryWord(5, "c3", "heard", 3, 8));
    });
});

describe("the text a range of story words covers", () => {
    it("is one span in every cell the range reaches", () => {
        const storyWords = new StoryWordsIterator(storyWhereSheSaw());
        const range = new StoryWordRange(2, 5);

        const spans = storyWords.spans(range);

        expect(spans).toEqual([
            new StoryTextSpan("c2", 8, 17),
            new StoryTextSpan("c3", 0, 8),
        ]);
    });
});

describe("the story words a selection covers", () => {
    it("are every word the selection touches in its cell", () => {
        const storyWords = new StoryWordsIterator(storyWhereSheSaw());

        const range = storyWords.rangeBetween("c3", 4, 10);

        expect(range).toEqual(new StoryWordRange(5, 6));
    });

    it("are none when the selection touches no word", () => {
        const storyWords = new StoryWordsIterator(storyWhereSheSaw());

        const range = storyWords.rangeBetween("c1", 0, 3);

        expect(range).toBeNull();
    });
});
