/* =========================================================
   PROCEDURAL INFINITE LEVEL GENERATOR
========================================================= */


/* =========================================================
   PLAYER PHYSICS
========================================================= */

const PLAYER_WIDTH = 35;

const PLAYER_HEIGHT = 50;

const MOVE_SPEED = 5;

const JUMP_POWER = -12;

const GRAVITY = 0.6;


/* =========================================================
   REACHABILITY TEST
========================================================= */

function canReachPlatform(
    previous,
    next
) {

    /*
     * Try multiple launch positions.
     *
     * This is better than checking only
     * the center of the platform.
     */

    const launchPositions = [

        previous.x + 25,

        previous.x +
        previous.width / 2,

        previous.x +
        previous.width - 25

    ];


    for (
        const startX of launchPositions
    ) {

        let x =
            startX;


        let y =
            previous.y -
            PLAYER_HEIGHT;


        let velocityY =
            JUMP_POWER;


        /*
         * Simulate jump.
         */

        for (
            let frame = 0;
            frame < 120;
            frame++
        ) {

            /*
             * Player can control horizontal
             * movement while jumping.
             *
             * Try moving toward the target.
             */

            const targetCenter =
                next.x +
                next.width / 2;


            const playerCenter =
                x +
                PLAYER_WIDTH / 2;


            if (
                playerCenter <
                targetCenter
            ) {

                x += MOVE_SPEED;

            }

            else {

                x -= MOVE_SPEED;

            }


            /*
             * Vertical physics.
             */

            y +=
                velocityY;


            velocityY +=
                GRAVITY;


            const playerBottom =
                y +
                PLAYER_HEIGHT;


            /*
             * Check landing.
             */

            if (

                velocityY >= 0

                &&

                playerBottom >=
                next.y

                &&

                y <=
                next.y + 12

                &&

                x +
                PLAYER_WIDTH >
                next.x

                &&

                x <
                next.x +
                next.width

            ) {

                return true;

            }


            /*
             * If player has moved far
             * beyond the target, this
             * launch attempt failed.
             */

            if (
                x >
                next.x +
                next.width +
                100
            ) {

                break;

            }


            if (
                x +
                PLAYER_WIDTH <
                next.x -
                100
            ) {

                break;

            }


            /*
             * Fell too far.
             */

            if (
                y > 650
            ) {

                break;

            }

        }

    }


    return false;

}


/* =========================================================
   VALIDATE LEVEL
========================================================= */

function validateLevel(
    platforms
) {

    if (

        !platforms

        ||

        platforms.length < 2

    ) {

        return false;

    }


    /*
     * Check every consecutive jump.
     */

    for (
        let i = 1;
        i < platforms.length;
        i++
    ) {

        const previous =
            platforms[i - 1];


        const next =
            platforms[i];


        if (
            !canReachPlatform(
                previous,
                next
            )
        ) {

            return false;

        }

    }


    return true;

}


/* =========================================================
   CREATE SPIKES
========================================================= */

function createSpikes(
    platforms,
    difficulty
) {

    const spikes = [];


    /*
     * Don't place spikes on:
     *
     * 0 = starting platform
     * last = goal platform
     */

    for (
        let i = 1;
        i < platforms.length - 1;
        i++
    ) {

        const platform =
            platforms[i];


        /*
         * Small platforms get fewer
         * hazards.
         */

        if (
            platform.width < 125
        ) {

            continue;

        }


        /*
         * Probability increases
         * with difficulty.
         */

        const chance =
            Math.min(
                0.18 +
                difficulty * 0.035,
                0.50
            );


        if (
            Math.random() >
            chance
        ) {

            continue;

        }


        /*
         * Don't completely block
         * the platform.
         */

        const spikeWidth =
            difficulty >= 8
                ? 28
                : 24;


        /*
         * Keep spikes away from
         * platform edges.
         */

        const minX =
            platform.x + 25;


        const maxX =
            platform.x +
            platform.width -
            spikeWidth -
            25;


        if (
            maxX <= minX
        ) {

            continue;

        }


        const spikeX =
            minX +
            Math.random() *
            (maxX - minX);


        spikes.push({

            x:
                spikeX,

            y:
                platform.y - 20,

            width:
                spikeWidth,

            height:
                20

        });

    }


    return spikes;

}


/* =========================================================
   CREATE MOVING PLATFORMS
========================================================= */

function createMovingPlatforms(
    platforms,
    difficulty
) {

    const movingPlatforms = [];


    /*
     * Moving platforms are additional
     * optional platforms.
     *
     * They don't replace the guaranteed
     * static route.
     */

    for (
        let i = 1;
        i < platforms.length;
        i++
    ) {

        const previous =
            platforms[i - 1];


        const next =
            platforms[i];


        /*
         * Only add moving platforms
         * when the gap is meaningful.
         */

        const gap =
            next.x -
            (
                previous.x +
                previous.width
            );


        if (
            gap < 80
        ) {

            continue;

        }


        /*
         * More moving platforms
         * at higher difficulty.
         */

        const chance =
            Math.min(
                0.15 +
                difficulty * 0.025,
                0.40
            );


        if (
            Math.random() >
            chance
        ) {

            continue;

        }


        const width =
            Math.max(
                90,
                125 -
                difficulty * 2
            );


        /*
         * Place the moving platform
         * roughly between the two
         * static platforms.
         */

        const centerX =
            (
                previous.x +
                previous.width +
                next.x
            ) / 2;


        const centerY =
            (
                previous.y +
                next.y
            ) / 2;


        const axis =
            Math.random() < 0.55
                ? "x"
                : "y";


        const range =
            axis === "x"
                ? Math.min(
                    45,
                    Math.max(
                        25,
                        gap / 3
                    )
                )
                : Math.min(
                    55,
                    Math.max(
                        25,
                        Math.abs(
                            next.y -
                            previous.y
                        ) / 2
                    )
                );


        const platform = {

            x:
                centerX -
                width / 2,

            y:
                centerY,

            width:
                width,

            height:
                22,

            axis:
                axis,

            range:
                range,

            speed:
                0.018 +
                Math.random() *
                0.012,

            time:
                Math.random() *
                Math.PI * 2

        };


        /*
         * Store starting positions
         * for animation.
         */

        platform.startX =
            platform.x;


        platform.startY =
            platform.y;


        platform.deltaX = 0;

        platform.deltaY = 0;


        movingPlatforms.push(
            platform
        );

    }


    return movingPlatforms;

}


/* =========================================================
   GENERATE ONE LEVEL
========================================================= */

function generateOneLevel(
    levelNumber
) {

    /*
     * Difficulty rises gradually.
     *
     * Level 1-4   = easy
     * Level 5-9   = medium
     * Level 10+   = harder
     */

    const difficulty =
        Math.min(
            10,
            Math.floor(
                (levelNumber - 1) / 5
            ) + 1
        );


    /*
     * More attempts at higher
     * difficulty.
     */

    const MAX_ATTEMPTS =
        150;


    for (
        let attempt = 0;
        attempt < MAX_ATTEMPTS;
        attempt++
    ) {

        const platforms = [];


        /* =================================================
           START PLATFORM
        ================================================= */

        platforms.push({

            x: 0,

            y: 430,

            width:
                Math.max(
                    190,
                    250 -
                    difficulty * 7
                ),

            height: 30

        });


        let x = 0;


        /*
         * Number of platforms.
         */

        const platformCount =
            8 +
            difficulty;


        /* =================================================
           BUILD PLATFORM CHAIN
        ================================================= */

        for (
            let i = 0;
            i < platformCount;
            i++
        ) {

            const previous =
                platforms[
                    platforms.length - 1
                ];


            /*
             * Gap increases slightly
             * with difficulty.
             */

            const minGap =
                45 +
                difficulty * 2;


            const maxGap =
                110 +
                difficulty * 5;


            const gap =
                minGap +
                Math.random() *
                (
                    maxGap -
                    minGap
                );


            x =
                previous.x +
                previous.width +
                gap;


            /*
             * Platform width.
             */

            const width =
                Math.max(
                    120,
                    195 -
                    difficulty * 5 +
                    Math.random() * 30
                );


            /*
             * Vertical movement.
             *
             * Keep jumps within a
             * reasonable range.
             */

            const verticalRange =
                Math.min(
                    80 +
                    difficulty * 2,
                    110
                );


            const minY =
                Math.max(
                    260,
                    previous.y -
                    verticalRange
                );


            const maxY =
                Math.min(
                    430,
                    previous.y +
                    verticalRange
                );


            const y =
                minY +
                Math.random() *
                (
                    maxY -
                    minY
                );


            platforms.push({

                x: x,

                y: y,

                width: width,

                height: 30

            });

        }


        /* =================================================
           GUARANTEE REACHABILITY
        ================================================= */

        if (
            !validateLevel(
                platforms
            )
        ) {

            continue;

        }


        /* =================================================
           HAZARDS
        ================================================= */

        const spikes =
            createSpikes(
                platforms,
                difficulty
            );


        /* =================================================
           MOVING PLATFORMS
        ================================================= */

        const movingPlatforms =
            createMovingPlatforms(
                platforms,
                difficulty
            );


        /* =================================================
           GOAL
        ================================================= */

        const last =
            platforms[
                platforms.length - 1
            ];


        const goal = {

            x:
                last.x +
                last.width -
                35,

            y:
                last.y -
                70,

            width: 30,

            height: 70

        };


        /* =================================================
           RETURN LEVEL
        ================================================= */

        return {

            level:
                levelNumber,

            difficulty:
                difficulty,

            platforms:
                platforms,

            spikes:
                spikes,

            movingPlatforms:
                movingPlatforms,

            goal:
                goal

        };

    }


    /*
     * Failed to generate.
     */

    console.warn(
        "⚠️ Could not generate level " +
        levelNumber
    );


    return null;

}


/* =========================================================
   GENERATE BATCH
========================================================= */

function generateProceduralLevels(
    startLevel,
    count
) {

    const generated = [];


    for (
        let levelNumber = startLevel;
        levelNumber <
        startLevel + count;
        levelNumber++
    ) {

        const level =
            generateOneLevel(
                levelNumber
            );


        if (
            level !== null
        ) {

            generated.push(
                level
            );

        }

    }


    console.log(
        "🎮 Generated " +
        generated.length +
        " procedural levels."
    );


    return generated;

}