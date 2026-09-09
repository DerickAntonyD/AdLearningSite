from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from PIL import Image
import io


app = FastAPI(title="AdLearningSite")


templates = Jinja2Templates(directory="templates")

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
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