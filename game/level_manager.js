class LevelManager {

    constructor() {
        this.levels = [];
        this.generatedUntil = 0;
        this.generating = false;

        this.loadInitialLevels();
    }

    loadInitialLevels() {

        // First 10 levels come from levels.js
        this.levels = [...LEVELS];

        this.generatedUntil = this.levels.length;

        console.log(
            `Loaded ${this.generatedUntil} levels`
        );
    }


    getLevel(levelNumber) {

        const index = levelNumber - 1;

        if (index < 0 || index >= this.levels.length) {
            return null;
        }

        return this.levels[index];
    }


    hasLevel(levelNumber) {

        return (
            levelNumber >= 1 &&
            levelNumber <= this.levels.length
        );
    }


    shouldGenerate(currentLevel) {

        // When the player reaches 5 levels before
        // the end of the available levels,
        // start preparing the next batch.

        return (
            currentLevel >= this.generatedUntil - 5 &&
            !this.generating
        );
    }


    async generateNextBatch() {

        if (this.generating) {
            return;
        }

        this.generating = true;

        console.log(
            "🚀 Preparing next 10 levels..."
        );

        /*
         * For now we use our free procedural generator.
         *
         * Later this function can optionally call
         * a local AI model.
         */

        const newLevels =
            generateProceduralLevels(
                this.generatedUntil + 1,
                10
            );

        this.levels.push(...newLevels);

        this.generatedUntil =
            this.levels.length;

        this.generating = false;

        console.log(
            `✅ Levels ready: 1-${this.generatedUntil}`
        );
    }
}