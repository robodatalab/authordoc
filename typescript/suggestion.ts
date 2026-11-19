import type { AuthorDocDiff } from "./diff";

export class Suggestion {
    constructor(
        readonly cellId: string,
        private readonly diffProposed: AuthorDocDiff,
    ) {}

    diff(): AuthorDocDiff {
        return this.diffProposed;
    }

    withTheDiff(diff: AuthorDocDiff): Suggestion {
        const suggestion = new Suggestion(this.cellId, diff);
        return suggestion;
    }
}
