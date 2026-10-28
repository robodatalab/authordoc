export class StoryWordRange {
    constructor(
        readonly firstWord: number,
        readonly lastWord: number,
    ) {}

    overlaps(other: StoryWordRange): boolean {
        return this.firstWord <= other.lastWord && other.firstWord <= this.lastWord;
    }
}
