class LevelManager {

    constructor() {

        this.levels = [];

        this.generatedUntil = 0;

        this.generating = false;

        this.BATCH_SIZE = 10;

        this.BUFFER_SIZE = 5;

        this.loadInitialLevels();
    }


    loadInitialLevels() {

        this.levels = [...LEVELS];

        this.generatedUntil =
            this.levels.length;

        console.log(
            `🎮 Loaded ${this.generatedUntil} fixed levels`
        );
    }


    getLevel(levelNumber) {

        const index =
            levelNumber - 1;

        if (
            index < 0 ||
            index >= this.levels.length
        ) {

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


    /*
     * Keep at least BUFFER_SIZE levels
     * ahead of the player.
     */
    shouldGenerate(currentLevel) {

        const remaining =
            this.generatedUntil - currentLevel;

        return (
            remaining <= this.BUFFER_SIZE &&
            !this.generating
        );
    }


    async generateNextBatch() {

        if (this.generating) {

            return;
        }

        this.generating = true;

        const startLevel =
            this.generatedUntil + 1;

        console.log(
            `🚀 Generating levels ${startLevel}-${startLevel + this.BATCH_SIZE - 1}...`
        );


        /*
         * Small delay makes generation
         * happen outside the immediate
         * gameplay step.
         */
        await new Promise(resolve => {

            setTimeout(resolve, 0);

        });


        const newLevels =
            generateProceduralLevels(
                startLevel,
                this.BATCH_SIZE
            );


        if (newLevels.length > 0) {

            this.levels.push(
                ...newLevels
            );

            this.generatedUntil =
                this.levels.length;


            console.log(
                `✅ Levels ready: 1-${this.generatedUntil}`
            );

        }


        this.generating = false;
    }
}