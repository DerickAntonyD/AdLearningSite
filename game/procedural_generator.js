function canReachPlatform(previous, next) {

    const previousRight = previous.x + previous.width;

    const horizontalGap = next.x - previousRight;

    // Maximum horizontal distance our player can
    // reasonably cross with the current movement.
    const MAX_JUMP_DISTANCE = 260;

    // Don't allow a platform to be absurdly higher/lower.
    const verticalDifference =
        Math.abs(next.y - previous.y);

    const MAX_VERTICAL_DIFFERENCE = 150;

    return (
        horizontalGap >= 0 &&
        horizontalGap <= MAX_JUMP_DISTANCE &&
        verticalDifference <= MAX_VERTICAL_DIFFERENCE
    );
}


function validateLevel(platforms) {

    if (!platforms || platforms.length < 2) {
        return false;
    }

    for (let i = 1; i < platforms.length; i++) {

        if (
            !canReachPlatform(
                platforms[i - 1],
                platforms[i]
            )
        ) {
            return false;
        }
    }

    return true;
}


function generateOneLevel(levelNumber) {

    const difficulty =
        Math.min(
            10,
            Math.floor(levelNumber / 5) + 1
        );

    const MAX_ATTEMPTS = 100;

    for (
        let attempt = 0;
        attempt < MAX_ATTEMPTS;
        attempt++
    ) {

        const platforms = [];

        let x = 0;

        // Starting platform
        platforms.push({
            x: 0,
            y: 430,
            width: 220,
            height: 30
        });

        const platformCount =
            8 + difficulty;


        for (
            let i = 0;
            i < platformCount;
            i++
        ) {

            const previous =
                platforms[platforms.length - 1];


            // Difficulty increases the possible gap,
            // but NEVER beyond the validator's limit.

            const maxGap =
                Math.min(
                    220,
                    100 + difficulty * 10
                );

            const gap =
                40 +
                Math.random() *
                (maxGap - 40);


            x =
                previous.x +
                previous.width +
                gap;


            const width =
                Math.max(
                    100,
                    180 -
                    difficulty * 5 +
                    Math.random() * 40
                );


            const minY =
                Math.max(
                    180,
                    previous.y - 120
                );

            const maxY =
                Math.min(
                    430,
                    previous.y + 120
                );


            const y =
                minY +
                Math.random() *
                (maxY - minY);


            platforms.push({
                x: x,
                y: y,
                width: width,
                height: 30
            });
        }


        // Check every jump.
        if (validateLevel(platforms)) {

            const last =
                platforms[platforms.length - 1];

            return {
                level: levelNumber,

                platforms: platforms,

                goal: {
                    x:
                        last.x +
                        last.width -
                        35,

                    y:
                        last.y -
                        70,

                    width: 30,

                    height: 70
                }
            };
        }
    }


    // Extremely unlikely fallback.
    console.warn(
        `Could not generate level ${levelNumber}`
    );

    return null;
}


function generateProceduralLevels(
    startLevel,
    count
) {

    const generated = [];

    for (
        let levelNumber = startLevel;
        levelNumber < startLevel + count;
        levelNumber++
    ) {

        const level =
            generateOneLevel(levelNumber);


        if (level !== null) {
            generated.push(level);
        }
    }

    return generated;
}