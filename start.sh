#!/usr/bin/env bash
set -euo pipefail

# Environment defaults
: "${DISPLAY:=:1}"
: "${NOVNC_PORT:=8080}"
: "${VNC_PASS:=aurora123}"

# Ensure noVNC index points to our custom web UI
if [ -f /opt/noVNC/vnc.html ]; then
  echo "noVNC already has vnc.html"
else
  cp -f /opt/app/web/index.html /opt/noVNC/vnc.html || true
fi

# Start virtual X server
Xvfb ${DISPLAY} -screen 0 1280x800x24 > /tmp/xvfb.log 2>&1 &

# Give X a brief moment
sleep 0.6

# Start a lightweight window manager
fluxbox > /tmp/fluxbox.log 2>&1 &

# Start a test xterm so there's something to show (detached)
xterm -geometry 100x30+10+10 &

# Start x11vnc connected to Xvfb
# Using -nopw for POC; in production use -rfbauth with password file
x11vnc -display ${DISPLAY} -nopw -forever -shared -rfbport 5901 > /tmp/x11vnc.log 2>&1 &

sleep 0.6

# Start websockify to bridge websocket -> VNC and serve noVNC web UI
# Using bundled websockify run script
/opt/noVNC/utils/websockify/run --web /opt/noVNC ${NOVNC_PORT} localhost:5901 > /tmp/websockify.log 2>&1 &

# Start the FastAPI assistant (on port 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info > /tmp/uvicorn.log 2>&1 &

# Wait for any process to exit (keeps container running)
wait -n
