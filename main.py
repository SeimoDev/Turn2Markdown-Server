import os
import time
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import aiofiles
from markitdown import MarkItDown
from starlette.responses import JSONResponse
from urllib.parse import unquote

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

async def delete_files(file_path: str, output_path: str, delay: int):
    await asyncio.sleep(delay)
    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists(output_path):
        os.remove(output_path)

@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    if not os.path.exists('tmp'):
        os.makedirs('tmp')

    if not os.path.exists('output'):
        os.makedirs('output')

    original_filename = os.path.splitext(file.filename)[0]
    timestamp = int(time.time())
    file_extension = os.path.splitext(file.filename)[1]
    new_filename = f"{timestamp}{file_extension}"
    file_path = f"tmp/{new_filename}"

    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    markitdown = MarkItDown()
    result = markitdown.convert(file_path)

    output_path = f"output/{original_filename}.md"
    async with aiofiles.open(output_path, 'w', encoding='utf-8') as out_file:
        await out_file.write(result.text_content)

    # Schedule file deletion after 10 minutes (600 seconds)
    asyncio.create_task(delete_files(file_path, output_path, 600))

    return {"original_filename": original_filename, "new_filename": new_filename}

@app.get("/output/{filename}")
async def get_file(filename: str):
    decoded_filename = unquote(filename)
    file_path = f"output/{decoded_filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )