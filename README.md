# Whisper ASR Webservice (Docker + Traefik)

A production-ready Whisper transcription API built with `ahmetoner/whisper-asr-webservice` (using `faster-whisper`), configured to run behind Traefik on your VPS.

## Deployment Instructions

1. **Pull & Run**:
   ```bash
   cd whisper-srt
   git pull origin master
   docker-compose up -d
   ```
2. **Check Logs**:
   ```bash
   docker-compose logs -f whisper
   ```

## Usage

### Interactive API Documentation / OpenAPI Docs
Visit in your browser:
```
http://<YOUR_VPS_IP>/whisper/docs
```

### Transcribe Audio to .SRT

Send an audio file to the `/whisper/asr` endpoint with `task=transcribe` and `output=srt`:

```bash
curl -X POST \
  -F "audio_file=@/path/to/your/audio.mp3" \
  "http://<YOUR_VPS_IP>/whisper/asr?task=transcribe&output=srt" \
  -o output.srt
```

### Transcribe Audio to JSON / VTT / TXT

To get JSON instead of SRT:
```bash
curl -X POST \
  -F "audio_file=@audio.mp3" \
  "http://<YOUR_VPS_IP>/whisper/asr?task=transcribe&output=json"
```

## How it Solves All Previous VPS Issues:
1. **Official Image**: Uses pre-built `ahmetoner/whisper-asr-webservice` containing all C++/FFmpeg/python-multipart dependencies.
2. **No Port Exposure**: Listens internally on port `9000` via Traefik; no custom host ports exposed.
3. **Traefik Integration**: Strip-prefix middleware routes `/whisper/*` requests cleanly to the webservice.
4. **Network**: Connected to `n8n-stack_default`.
