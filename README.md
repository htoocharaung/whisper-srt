# Whisper SRT API

A production-ready Whisper transcription API built with FastAPI and `faster-whisper`, designed to run behind a Traefik reverse proxy on a VPS.

## Deployment Instructions

1. **Transfer Files**: Ensure this directory (`whisper-srt`) is on your VPS.
2. **Network Requirement**: Make sure Traefik is running and the `n8n-stack_default` Docker network exists.
3. **Build & Run**:
   ```bash
   cd whisper-srt
   docker-compose up -d --build
   ```
4. **Check Logs**:
   ```bash
   docker-compose logs -f whisper
   ```
   Wait until you see `Application startup complete` and `Model loaded successfully`.

## Usage

### Health Check

Verify the API is running and the model is loaded:

```bash
curl http://<YOUR_VPS_IP>/whisper/health
```
*(If you have HTTPS configured through Traefik, change `http://` to `https://`)*

### Transcribe Audio

Send an audio file via POST request to get a `.srt` file back. Note that the Traefik router `/whisper` automatically strips the prefix and passes `/transcribe` to the container.

```bash
curl -X POST \
  -F "file=@/path/to/your/audio.mp3" \
  http://<YOUR_VPS_IP>/whisper/transcribe \
  -o output.srt
```

## How it solves your issues:
1. **Missing Dependency**: `python-multipart` is included in `requirements.txt`.
2. **Wrong port mapping**: The API runs on `8000` internally, and Traefik correctly proxies to `8000` via the `loadbalancer.server.port` label. We no longer expose `8023` to the host.
3. **ISP Port Blocking**: Since Traefik handles the traffic, it will use ports 80/443, avoiding custom port blocks.
4. **Traefik 404 Intercept**: We added the `traefik.http.middlewares.whisper-strip-prefix.stripprefix.prefixes=/whisper` middleware.
5. **Network**: The `docker-compose.yml` connects the container to `n8n-stack_default`.
6. **Certificate Error**: Included entrypoints for `web` (HTTP) and `websecure` (HTTPS) so you can hit it over HTTP raw IP if HTTPS fails.
