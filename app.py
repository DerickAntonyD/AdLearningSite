from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Form
from PIL import Image
import pytesseract
import io


app = FastAPI(title="AdLearningSite")

templates = Jinja2Templates(directory="templates")

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)
app.mount(
    "/game-assets",
    StaticFiles(directory="game"),
    name="game-assets"
)


# Tesseract OCR executable
pytesseract.pytesseract.tesseract_cmd = (
    r"D:\visionBotAI\Tools\tesseract.exe"
)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.get("/image-compressor", response_class=HTMLResponse)
async def image_compressor(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="tools/image_compressor.html"
    )


@app.post("/compress-image")
async def compress_image(file: UploadFile = File(...)):

    data = await file.read()

    image = Image.open(io.BytesIO(data))

    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGB")

    output = io.BytesIO()

    image.save(
        output,
        format="JPEG",
        quality=70,
        optimize=True
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


@app.get("/image-to-text", response_class=HTMLResponse)
async def image_to_text(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="tools/image_to_text.html"
    )


@app.post("/extract-text", response_class=HTMLResponse)
async def extract_text(
    request: Request,
    file: UploadFile = File(...)
):

    data = await file.read()

    image = Image.open(io.BytesIO(data))

    text = pytesseract.image_to_string(image)

    return templates.TemplateResponse(
        request=request,
        name="tools/image_to_text.html",
        context={
            "request": request,
            "text": text
        }
    )

@app.get("/image-resizer", response_class=HTMLResponse)
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

    image = Image.open(io.BytesIO(data))

    # Prevent invalid dimensions
    width = max(1, min(width, 5000))
    height = max(1, min(height, 5000))

    resized = image.resize(
        (width, height),
        Image.Resampling.LANCZOS
    )

    if resized.mode in ("RGBA", "LA", "P"):
        resized = resized.convert("RGB")

    output = io.BytesIO()

    resized.save(
        output,
        format="JPEG",
        quality=90,
        optimize=True
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

@app.get("/image-converter", response_class=HTMLResponse)
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

    image = Image.open(io.BytesIO(data))

    output_format = output_format.upper()

    allowed_formats = {
        "JPEG": "JPEG",
        "PNG": "PNG",
        "WEBP": "WEBP"
    }

    if output_format not in allowed_formats:
        output_format = "PNG"

    if output_format == "JPEG":
        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGB")

    output = io.BytesIO()

    image.save(
        output,
        format=allowed_formats[output_format]
    )

    output.seek(0)

    extension = {
        "JPEG": "jpg",
        "PNG": "png",
        "WEBP": "webp"
    }[output_format]

    return StreamingResponse(
        output,
        media_type=f"image/{'jpeg' if output_format == 'JPEG' else output_format.lower()}",
        headers={
            "Content-Disposition":
                f'attachment; filename="converted.{extension}"'
        }
    )

@app.get("/text-tools", response_class=HTMLResponse)
async def text_tools(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="tools/text_tools.html"
    )

@app.get("/image-cropper", response_class=HTMLResponse)
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

    image = Image.open(io.BytesIO(data))

    # Keep crop coordinates inside the image
    left = max(0, min(left, image.width - 1))
    top = max(0, min(top, image.height - 1))
    right = max(left + 1, min(right, image.width))
    bottom = max(top + 1, min(bottom, image.height))

    cropped = image.crop((left, top, right, bottom))

    if cropped.mode in ("RGBA", "LA", "P"):
        cropped = cropped.convert("RGB")

    output = io.BytesIO()

    cropped.save(
        output,
        format="JPEG",
        quality=90,
        optimize=True
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

@app.get("/game", response_class=HTMLResponse)
async def game(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="game.html"
    )