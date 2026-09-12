import os
import shutil
import tempfile
import traceback

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from omr import image_to_musicxml
from solfege_engine import score_to_solfege

app = FastAPI(title="Solfege from Sheet Music")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}


@app.post("/api/convert")
async def convert(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}. Use PNG or JPG.")

    tmp_dir = tempfile.mkdtemp(prefix="upload_")
    img_path = os.path.join(tmp_dir, f"input{ext}")

    try:
        with open(img_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        musicxml_path = image_to_musicxml(img_path)
        result = score_to_solfege(musicxml_path)
        return {"success": True, **result}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Conversion failed: {str(e)}")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# Serve the frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
