import os
import subprocess
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import aiofiles

app = FastAPI(title="Audio Compressor API")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/convert")
async def convert(file: UploadFile = File(...)):
    temp_in_path = None
    temp_out_path = None
    try:
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".tmp"
        fd_in, temp_in_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd_in)

        async with aiofiles.open(temp_in_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024):
                await out_file.write(content)

        fd_out, temp_out_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd_out)

        # Convert video/audio to 16kHz 1-channel mono 48k MP3
        cmd = [
            "ffmpeg", "-y",
            "-i", temp_in_path,
            "-vn",
            "-ar", "16000",
            "-ac", "1",
            "-b:a", "48k",
            temp_out_path
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            err_msg = result.stderr.decode('utf-8', errors='ignore')
            raise Exception(f"FFmpeg conversion failed: {err_msg}")

        async with aiofiles.open(temp_out_path, 'rb') as f:
            data = await f.read()

        return Response(
            content=data,
            media_type="audio/mpeg",
            headers={"Content-Disposition": 'attachment; filename="compressed.mp3"'}
        )

    except Exception as e:
        print(f"Conversion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_in_path and os.path.exists(temp_in_path):
            os.remove(temp_in_path)
        if temp_out_path and os.path.exists(temp_out_path):
            os.remove(temp_out_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
