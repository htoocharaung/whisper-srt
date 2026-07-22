import os
import shutil
import tempfile
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import PlainTextResponse
from faster_whisper import WhisperModel
import aiofiles

app = FastAPI(title="Whisper SRT API")

# Initialize model
# We use "base" by default for faster CPU inference. Can be changed to "small", "medium", etc.
MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")
# Use CPU by default for VPS compatibility. Change to "cuda" and compute_type="float16" if GPU is available.
DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "default")

model = None
model_loading = False

def load_model():
    global model, model_loading
    if model is None and not model_loading:
        model_loading = True
        print(f"Loading Whisper model '{MODEL_SIZE}' on {DEVICE} with {COMPUTE_TYPE} precision...")
        try:
            model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
            print("Model loaded successfully.")
        except Exception as e:
            print(f"Error loading model: {e}")
            model = None
        finally:
            model_loading = False
    return model

@app.on_event("startup")
async def startup_event():
    # Trigger model load in background thread on startup
    asyncio.create_task(asyncio.to_thread(load_model))

def format_time(seconds: float) -> str:
    """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_remainder = seconds % 60
    secs = int(seconds_remainder)
    millis = int((seconds_remainder - secs) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

@app.get("")
@app.get("/")
@app.get("/whisper")
async def root():
    return {
        "status": "online",
        "message": "Whisper SRT Transcription API is running",
        "model_loaded": model is not None,
        "endpoints": {
            "health": "/health",
            "transcribe": "POST /transcribe"
        }
    }

@app.get("/health")
async def health_check():
    if model_loading:
        return {"status": "loading", "model": MODEL_SIZE, "device": DEVICE}
    if model is None:
        # Try loading if not loaded
        load_model()
        if model is None:
            raise HTTPException(status_code=503, detail="Model failed to load")
    return {"status": "healthy", "model": MODEL_SIZE, "device": DEVICE}

@app.post("/transcribe", response_class=PlainTextResponse)
async def transcribe(file: UploadFile = File(...)):
    global model
    if model is None:
        model = load_model()
        if model is None:
            raise HTTPException(status_code=503, detail="Whisper model failed to load")

    # Save uploaded file to a temporary location
    try:
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".tmp"
        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        
        async with aiofiles.open(temp_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024):  # 1MB chunks
                await out_file.write(content)
                
        # Perform transcription
        print(f"Transcribing {file.filename}...")
        
        # Run transcription in a separate thread to avoid blocking the event loop
        segments_gen, info = await asyncio.to_thread(
            model.transcribe, 
            temp_path, 
            beam_size=5
        )
        
        print(f"Detected language '{info.language}' with probability {info.language_probability}")
        
        srt_content = []
        # Convert generator to list to force execution inside the thread
        # Note: faster_whisper yields segments, so we process them.
        segments = list(segments_gen)
        
        for i, segment in enumerate(segments, start=1):
            start_time = format_time(segment.start)
            end_time = format_time(segment.end)
            text = segment.text.strip()
            
            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(text)
            srt_content.append("") # Empty line between segments
            
        return "\n".join(srt_content)
        
    except Exception as e:
        print(f"Transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
