from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import asyncio
import hashlib
import hmac
import io
import json
import os
import secrets

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import (
    HTMLResponse,
    StreamingResponse,
    PlainTextResponse,
    JSONResponse,
)
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from PIL import Image
import pytesseract


# =========================================================
# EVENT SKIN SYSTEM
# =========================================================

EVENT_TIMEZONE = ZoneInfo("Asia/Kolkata")

EVENT_START_HOUR = 18
EVENT_START_MINUTE = 30

EVENT_END_HOUR = 21
EVENT_END_MINUTE = 30

SKIN_LIFETIME_HOURS = 5

# Server-side signing secret.
# On Render, this can later be supplied as EVENT_SKIN_SECRET.
EVENT_SECRET = os.environ.get(
    "EVENT_SKIN_SECRET"
) or secrets.token_bytes(32)


# Active rewards held in server memory.
#
# reward_id -> reward information
#
# They are deliberately kept in memory rather than written
# to disk/database for this V1 system.
ACTIVE_EVENT_REWARDS = {}


# Prevent the same generated visual fingerprint from being
# reused while an earlier reward is active.
ACTIVE_SKIN_FINGERPRINTS = set()


# Prevent repeated claims from the same browser identity
# during the same event window.
CLAIMED_EVENT_IDENTITIES = set()


def get_india_now():
    """
    Return current time in India.
    """
    return datetime.now(EVENT_TIMEZONE)


def get_event_window(now=None):
    """
    Return today's event start and end.
    """

    if now is None:
        now = get_india_now()

    start = now.replace(
        hour=EVENT_START_HOUR,
        minute=EVENT_START_MINUTE,
        second=0,
        microsecond=0,
    )

    end = now.replace(
        hour=EVENT_END_HOUR,
        minute=EVENT_END_MINUTE,
        second=0,
        microsecond=0,
    )

    return start, end


def event_is_active():
    """
    Check whether the Night Event is currently active.
    """

    now = get_india_now()

    start, end = get_event_window(now)

    return start <= now < end


def current_event_id():
    """
    Each day's event gets its own ID.
    """

    now = get_india_now()

    return now.strftime("%Y-%m-%d")


def sign_reward(reward_id, expires_at):
    """
    Create a server-side HMAC signature.
    """

    message = (
        reward_id
        + "|"
        + expires_at
    ).encode("utf-8")

    return hmac.new(
        EVENT_SECRET,
        message,
        hashlib.sha256,
    ).hexdigest()


def cleanup_expired_rewards():
    """
    Remove expired event rewards and their fingerprints.
    """

    now = datetime.now(EVENT_TIMEZONE)

    expired_ids = []

    for reward_id, reward in ACTIVE_EVENT_REWARDS.items():

        expires_at = datetime.fromisoformat(
            reward["expires_at"]
        )

        if expires_at <= now:
            expired_ids.append(reward_id)

    for reward_id in expired_ids:

        reward = ACTIVE_EVENT_REWARDS.pop(
            reward_id,
            None
        )

        if reward:

            ACTIVE_SKIN_FINGERPRINTS.discard(
                reward["fingerprint"]
            )

            CLAIMED_EVENT_IDENTITIES.discard(
                reward["claim_identity"]
            )


async def event_cleanup_loop():

    while True:

        cleanup_expired_rewards()

        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app):

    cleanup_task = asyncio.create_task(
        event_cleanup_loop()
    )

    try:

        yield

    finally:

        cleanup_task.cancel()


# =========================================================
# RANDOM SKIN GENERATOR
# =========================================================

SKIN_COLORS = [
    "#3B82F6",
    "#EF4444",
    "#22C55E",
    "#A855F7",
    "#F59E0B",
    "#06B6D4",
    "#EC4899",
    "#84CC16",
    "#F97316",
    "#8B5CF6",
    "#14B8A6",
    "#EAB308",
]

SKIN_SECONDARY_COLORS = [
    "#111827",
    "#FFFFFF",
    "#FDE68A",
    "#BFDBFE",
    "#BBF7D0",
    "#FBCFE8",
    "#DDD6FE",
    "#FED7AA",
]

SKIN_PATTERNS = [
    "solid",
    "stripe",
    "checker",
    "dots",
    "cross",
]

SKIN_ACCESSORIES = [
    "none",
    "crown",
    "antenna",
    "horns",
    "visor",
]

SKIN_EYES = [
    "normal",
    "wide",
    "sleepy",
    "pixel",
]

SKIN_GLOWS = [
    "none",
    "soft",
    "bright",
]


def generate_unique_skin():

    for _ in range(100):

        skin = {

            "primary":
                secrets.choice(
                    SKIN_COLORS
                ),

            "secondary":
                secrets.choice(
                    SKIN_SECONDARY_COLORS
                ),

            "pattern":
                secrets.choice(
                    SKIN_PATTERNS
                ),

            "accessory":
                secrets.choice(
                    SKIN_ACCESSORIES
                ),

            "eyes":
                secrets.choice(
                    SKIN_EYES
                ),

            "glow":
                secrets.choice(
                    SKIN_GLOWS
                ),

            # Random values make visually similar
            # combinations less likely.
            "pattern_offset":
                secrets.randbelow(1000),

            "accessory_variant":
                secrets.randbelow(1000),

            "eye_variant":
                secrets.randbelow(1000),

        }

        canonical = json.dumps(
            skin,
            sort_keys=True,
            separators=(",", ":"),
        )

        fingerprint = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

        if fingerprint not in ACTIVE_SKIN_FINGERPRINTS:

            return skin, fingerprint

    raise RuntimeError(
        "Could not generate a unique event skin."
    )


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="AdLearningSite",
    lifespan=lifespan,
)

templates = Jinja2Templates(
    directory="templates"
)


app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)


app.mount(
    "/game-assets",
    StaticFiles(directory="game"),
    name="game-assets",
)


# =========================================================
# TESSERACT OCR
# =========================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"D:\visionBotAI\Tools\tesseract.exe"
)


# =========================================================
# HOME
# =========================================================

@app.get(
    "/",
    response_class=HTMLResponse
)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


# =========================================================
# IMAGE COMPRESSOR
# =========================================================

@app.get(
    "/image-compressor",
    response_class=HTMLResponse
)
async def image_compressor(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="tools/image_compressor.html"
    )


@app.post("/compress-image")
async def compress_image(
    file: UploadFile = File(...)
):

    data = await file.read()

    image = Image.open(
        io.BytesIO(data)
    )

    if image.mode in (
        "RGBA",
        "LA",
        "P"
    ):

        image = image.convert("RGB")

    output = io.BytesIO()

    image.save(
        output,
        format="JPEG",
        quality=70,
        optimize=True,
    )

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="image/jpeg",
        headers={
            "Content-Disposition":
                'attachment; filename="compressed.jpg"'
        }
    )


# =========================================================
# IMAGE TO TEXT
# =========================================================

@app.get(
    "/image-to-text",
    response_class=HTMLResponse
)
async def image_to_text(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="tools/image_to_text.html"
    )


@app.post(
    "/extract-text",
    response_class=HTMLResponse
)
async def extract_text(
    request: Request,
    file: UploadFile = File(...)
):

    data = await file.read()

    image = Image.open(
        io.BytesIO(data)
    )

    text = pytesseract.image_to_string(
        image
    )

    return templates.TemplateResponse(
        request=request,
        name="tools/image_to_text.html",
        context={
            "request": request,
            "text": text,
        }
    )


# =========================================================
# IMAGE RESIZER
# =========================================================

@app.get(
    "/image-resizer",
    response_class=HTMLResponse
)
async def image_resizer(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="tools/image_resizer.html"
    )


@app.post("/resize-image")
async def resize_image(
    file: UploadFile = File(...),
    width: int = Form(...),
    height: int = Form(...)
):

    data = await file.read()

    image = Image.open(
        io.BytesIO(data)
    )

    width = max(
        1,
        min(width, 5000)
    )

    height = max(
        1,
        min(height, 5000)
    )

    resized = image.resize(
        (width, height),
        Image.Resampling.LANCZOS,
    )

    if resized.mode in (
        "RGBA",
        "LA",
        "P"
    ):

        resized = resized.convert(
            "RGB"
        )

    output = io.BytesIO()

    resized.save(
        output,
        format="JPEG",
        quality=90,
        optimize=True,
    )

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="image/jpeg",
        headers={
            "Content-Disposition":
                'attachment; filename="resized.jpg"'
        }
    )


# =========================================================
# IMAGE CONVERTER
# =========================================================

@app.get(
    "/image-converter",
    response_class=HTMLResponse
)
async def image_converter(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="tools/image_converter.html"
    )


@app.post("/convert-image")
async def convert_image(
    file: UploadFile = File(...),
    output_format: str = Form(...)
):

    data = await file.read()

    image = Image.open(
        io.BytesIO(data)
    )

    output_format = output_format.upper()

    allowed_formats = {
        "JPEG": "JPEG",
        "PNG": "PNG",
        "WEBP": "WEBP",
    }

    if output_format not in allowed_formats:

        output_format = "PNG"

    if output_format == "JPEG":

        if image.mode in (
            "RGBA",
            "LA",
            "P"
        ):

            image = image.convert(
                "RGB"
            )

    output = io.BytesIO()

    image.save(
        output,
        format=allowed_formats[
            output_format
        ],
    )

    output.seek(0)

    extension = {
        "JPEG": "jpg",
        "PNG": "png",
        "WEBP": "webp",
    }[output_format]

    return StreamingResponse(
        output,
        media_type=(
            "image/jpeg"
            if output_format == "JPEG"
            else f"image/{output_format.lower()}"
        ),
        headers={
            "Content-Disposition":
                f'attachment; filename="converted.{extension}"'
        }
    )


# =========================================================
# TEXT TOOLS
# =========================================================

@app.get(
    "/text-tools",
    response_class=HTMLResponse
)
async def text_tools(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="tools/text_tools.html"
    )


# =========================================================
# IMAGE CROPPER
# =========================================================

@app.get(
    "/image-cropper",
    response_class=HTMLResponse
)
async def image_cropper(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="tools/image_cropper.html"
    )


@app.post("/crop-image")
async def crop_image(
    file: UploadFile = File(...),
    left: int = Form(...),
    top: int = Form(...),
    right: int = Form(...),
    bottom: int = Form(...)
):

    data = await file.read()

    image = Image.open(
        io.BytesIO(data)
    )

    left = max(
        0,
        min(left, image.width - 1)
    )

    top = max(
        0,
        min(top, image.height - 1)
    )

    right = max(
        left + 1,
        min(right, image.width)
    )

    bottom = max(
        top + 1,
        min(bottom, image.height)
    )

    cropped = image.crop(
        (
            left,
            top,
            right,
            bottom
        )
    )

    if cropped.mode in (
        "RGBA",
        "LA",
        "P"
    ):

        cropped = cropped.convert(
            "RGB"
        )

    output = io.BytesIO()

    cropped.save(
        output,
        format="JPEG",
        quality=90,
        optimize=True,
    )

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="image/jpeg",
        headers={
            "Content-Disposition":
                'attachment; filename="cropped.jpg"'
        }
    )


# =========================================================
# GAME
# =========================================================

@app.get(
    "/game",
    response_class=HTMLResponse
)
async def game(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="game.html"
    )


# =========================================================
# NIGHT EVENT STATUS
# =========================================================

@app.get("/api/event/status")
async def event_status():

    cleanup_expired_rewards()

    now = get_india_now()

    start, end = get_event_window(now)

    active = (
        start <= now < end
    )

    if active:

        remaining_seconds = int(
            (
                end - now
            ).total_seconds()
        )

    else:

        if now < start:

            next_start = start

        else:

            next_start = start + timedelta(
                days=1
            )

        remaining_seconds = int(
            (
                next_start - now
            ).total_seconds()
        )

    return {
        "active": active,
        "event_id": current_event_id(),
        "timezone": "Asia/Kolkata",
        "start": start.isoformat(),
        "end": end.isoformat(),
        "seconds_until_change":
            remaining_seconds,
    }


# =========================================================
# CLAIM EVENT SKIN
# =========================================================

@app.post("/api/event/claim")
async def claim_event_skin(
    request: Request
):

    cleanup_expired_rewards()

    if not event_is_active():

        raise HTTPException(
            status_code=403,
            detail="The Night Event is not active right now."
        )

    body = await request.json()

    claim_identity = str(
        body.get("claim_identity", "")
    ).strip()

    if (
        not claim_identity
        or len(claim_identity) < 16
        or len(claim_identity) > 128
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid event identity."
        )

    event_id = current_event_id()

    identity_key = (
        event_id
        + ":"
        + claim_identity
    )

    if identity_key in CLAIMED_EVENT_IDENTITIES:

        raise HTTPException(
            status_code=409,
            detail="This event reward has already been claimed."
        )

    skin, fingerprint = (
        generate_unique_skin()
    )

    reward_id = (
        "EVT-"
        + event_id
        + "-"
        + secrets.token_hex(12)
    )

    created_at = get_india_now()

    expires_at = (
        created_at
        + timedelta(
            hours=SKIN_LIFETIME_HOURS
        )
    )

    expires_string = (
        expires_at.isoformat()
    )

    signature = sign_reward(
        reward_id,
        expires_string,
    )

    ACTIVE_SKIN_FINGERPRINTS.add(
        fingerprint
    )

    CLAIMED_EVENT_IDENTITIES.add(
        identity_key
    )

    ACTIVE_EVENT_REWARDS[
        reward_id
    ] = {

        "reward_id":
            reward_id,

        "event_id":
            event_id,

        "skin":
            skin,

        "fingerprint":
            fingerprint,

        "claim_identity":
            identity_key,

        "created_at":
            created_at.isoformat(),

        "expires_at":
            expires_string,

        "signature":
            signature,

    }

    return JSONResponse({

        "success":
            True,

        "reward_id":
            reward_id,

        "event_id":
            event_id,

        "skin":
            skin,

        "created_at":
            created_at.isoformat(),

        "expires_at":
            expires_string,

        "signature":
            signature,

    })


# =========================================================
# ADS.TXT
# =========================================================

@app.get(
    "/ads.txt",
    response_class=PlainTextResponse
)
async def ads_txt():

    return (
        "google.com, "
        "pub-5103140968395570, "
        "DIRECT, "
        "f08c47fec0942fa0"
    )