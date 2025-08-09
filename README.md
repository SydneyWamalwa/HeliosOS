# Aurora Cloud-Stream POC (local)

## Prerequisites
- Docker and Docker Compose installed
- Git (optional)

## Local run
1. Build and run:
   docker-compose build
   docker-compose up

2. Visit the desktop in your browser:
   http://localhost:8080

   - Open the assistant docs:
     http://localhost:8000/docs

   - The web client is served at http://localhost:8080/vnc.html (embedded UI)

## Using the assistant
- Paste text into the textarea and press Summarize.
- If you want real summaries, set the HUGGINGFACE_API_KEY env var in docker-compose.yml.

## Notes & next steps
- This POC uses x11vnc + noVNC to stream a Lightweight desktop (fluxbox + xterm).
- For production:
  - Replace x11vnc -nopw with -rfbauth and store the password securely.
  - Add a session broker and time-limited tunnels per authenticated user.
  - Replace VNC pipeline with a WebRTC SFU (Janus / mediasoup) for lower latency.
