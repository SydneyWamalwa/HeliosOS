# app/main.py
from fastapi import FastAPI, HTTPException, Depends, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import requests
import os
import json
from typing import List, Dict, Any, Optional, Union
import shlex, subprocess, uuid, time
from datetime import datetime, timedelta
import logging

# Import our services
from app.ai_models import AIModelManager
from app.webrtc_service import WebRTCService
from dotenv import load_dotenv
import os

load_dotenv()
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("helios.log")
    ]
)
logger = logging.getLogger(__name__)
app.config['HUGGINGFACE_API_KEY'] = os.getenv('HUGGINGFACE_API_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')


app = FastAPI(title="Helios OS - AI Cloud Desktop")

# Add CORS middleware for API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up templates
templates = Jinja2Templates(directory="app/templates")

# Simple in-memory session store (would use Redis or similar in production)
SESSIONS: Dict[str, Dict[str, Any]] = {}

# Simple in-memory profile (would use database in production)
PROFILE: Dict[str, Any] = {"username": "Guest", "prefs": {}}

# Expanded whitelisted commands (only first token is checked)
ALLOWED_CMDS = {
    # File system navigation
    "ls", "pwd", "cd", "find", "grep", "cat", "head", "tail",
    # System info
    "whoami", "date", "uptime", "df", "free", "echo", "ps", "id", "top", "htop",
    # Network
    "ping", "curl", "wget", "netstat", "ifconfig", "ip",
    # Process management (safe ones)
    "kill", "nice", "nohup",
    # File operations (read-only or safe)
    "mkdir", "touch", "cp", "mv", "rm", "rmdir"
}

# Enhanced data models
class SummarizeRequest(BaseModel):
    text: str

class Message(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatRequest(BaseModel):
    messages: List[Message]
    stream: bool = False

class ExecRequest(BaseModel):
    cmd: str
    cwd: Optional[str] = None

class FileRequest(BaseModel):
    path: str
    content: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    path: Optional[str] = None
    max_results: int = 20

class SessionData(BaseModel):
    user_id: str
    username: str
    expires: datetime

class UserPreferences(BaseModel):
    theme: str = "dark"
    desktop_bg: str = "default"
    font_size: str = "medium"
    notifications: bool = True
    shortcuts: Dict[str, str] = {}

class UserProfile(BaseModel):
    username: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    preferences: UserPreferences = UserPreferences()

# Authentication middleware
async def get_session_data(request: Request) -> Optional[SessionData]:
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in SESSIONS:
        return None

    session = SESSIONS[session_id]
    if datetime.now() > session["expires"]:
        # Session expired
        del SESSIONS[session_id]
        return None

    return SessionData(
        user_id=session["user_id"],
        username=session["username"],
        expires=session["expires"]
    )

# API endpoints
@app.get("/")
async def root():
    return {"status": "online", "service": "Helios OS", "version": "1.0.0"}

@app.get("/status")
async def status():
    return {
        "service": "Helios OS",
        "status": "ok",
        "time": int(time.time()),
        "profile": PROFILE,
        "system_info": {
            "uptime": get_system_uptime(),
            "memory": get_memory_usage(),
            "cpu": get_cpu_usage()
        }
    }

@app.post("/auth/login")
async def login(response: Response, username: str = "Guest"):
    # In production, this would validate credentials
    session_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    # Store session (would use Redis in production)
    SESSIONS[session_id] = {
        "user_id": user_id,
        "username": username,
        "expires": datetime.now() + timedelta(hours=24)
    }

    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=86400,  # 24 hours
        samesite="lax"
    )

    return {"ok": True, "username": username}

@app.post("/auth/logout")
async def logout(response: Response, session: Optional[SessionData] = Depends(get_session_data)):
    if session:
        # Clear session from store
        if session.user_id in SESSIONS:
            del SESSIONS[session.user_id]

    # Clear cookie regardless
    response.delete_cookie(key="session_id")
    return {"ok": True}

@app.get("/profile")
async def get_profile(session: Optional[SessionData] = Depends(get_session_data)):
    if not session:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})

    return PROFILE

@app.post("/profile")
async def set_profile(payload: Dict[str, Any], session: Optional[SessionData] = Depends(get_session_data)):
    if not session:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})

    # Update profile (would validate and persist to database in production)
    PROFILE.update(payload)
    return {"ok": True, "profile": PROFILE}

@app.post("/summarize")
async def summarize(req: SummarizeRequest, session: Optional[SessionData] = Depends(get_session_data)):
    # Log usage (would store in database in production)
    user_id = session.user_id if session else "anonymous"
    print(f"Summarize request from user {user_id}, length: {len(req.text)}")

    text = (req.text or "").strip()
    if not text:
        return {"summary": ""}

    # Use our AI model manager to handle the request
    result = AIModelManager.get_summary(text)

    # Log completion
    print(f"Summarize complete for user {user_id}, result length: {len(result.get('summary', ''))}")

    return result

@app.post("/chat")
async def chat(req: ChatRequest, session: Optional[SessionData] = Depends(get_session_data)):
    # Log usage (would store in database in production)
    user_id = session.user_id if session else "anonymous"
    print(f"Chat request from user {user_id}, messages: {len(req.messages)}")

    # Convert Pydantic models to dictionaries for the AI manager
    messages = [msg.dict() for msg in req.messages] if req.messages else []

    # Use our AI model manager to handle the request
    result = AIModelManager.get_chat_response(messages)

    # Log completion
    print(f"Chat complete for user {user_id}, reply length: {len(result.get('reply', ''))}")

    return result

# System utility functions
def get_system_uptime() -> str:
    """Get system uptime in a human-readable format"""
    try:
        completed = subprocess.run(["uptime"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2, text=True)
        if completed.returncode == 0:
            return completed.stdout.strip()
        return "Unknown"
    except Exception:
        return "Unknown"

def get_memory_usage() -> Dict[str, Any]:
    """Get memory usage statistics"""
    try:
        completed = subprocess.run(["free", "-m"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2, text=True)
        if completed.returncode == 0:
            lines = completed.stdout.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 7:
                    return {
                        "total": int(parts[1]),
                        "used": int(parts[2]),
                        "free": int(parts[3]),
                        "shared": int(parts[4]),
                        "buffers": int(parts[5]),
                        "cache": int(parts[6]),
                        "unit": "MB"
                    }
        return {"error": "Could not parse memory info"}
    except Exception as e:
        return {"error": str(e)}

def get_cpu_usage() -> Dict[str, Any]:
    """Get CPU usage statistics"""
    try:
        # Simple CPU usage estimate using top
        completed = subprocess.run(
            ["top", "-bn1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=2,
            text=True
        )
        if completed.returncode == 0:
            lines = completed.stdout.strip().split('\n')
            cpu_line = next((line for line in lines if "%Cpu(s)" in line), None)
            if cpu_line:
                parts = cpu_line.split()
                user = float(parts[1])
                system = float(parts[3])
                idle = float(parts[7])
                return {
                    "user": user,
                    "system": system,
                    "idle": idle,
                    "total": user + system
                }
        return {"error": "Could not parse CPU info"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/exec")
async def exec_cmd(req: ExecRequest, session: Optional[SessionData] = Depends(get_session_data)):
    """
    Execute a *whitelisted* command inside the container and return stdout/stderr.
    WARNING: This endpoint runs commands on the container. It only allows a restricted set for safety.
    """
    # Log usage (would store in database in production)
    user_id = session.user_id if session else "anonymous"
    print(f"Exec request from user {user_id}, command: {req.cmd}")

    cmdline = (req.cmd or "").strip()
    if not cmdline:
        raise HTTPException(status_code=400, detail="empty command")

    # Parse command
    try:
        parts = shlex.split(cmdline)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"failed to parse command: {e}")

    if len(parts) == 0:
        raise HTTPException(status_code=400, detail="empty command")

    if parts[0] not in ALLOWED_CMDS:
        raise HTTPException(status_code=403, detail=f"command '{parts[0]}' not allowed")

    # Set working directory if provided
    cwd = req.cwd if req.cwd else None

    # Run safely with timeout and capture
    try:
        completed = subprocess.run(
            parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,  # Extended timeout for more complex commands
            text=True,
            cwd=cwd
        )

        result = {
            "cmd": cmdline,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr
        }

        # Log completion
        print(f"Exec complete for user {user_id}, return code: {completed.returncode}")

        return result
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="command timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# File system operations
@app.get("/fs/list")
async def list_directory(path: str = "/", session: Optional[SessionData] = Depends(get_session_data)):
    """
    List contents of a directory
    """
    if not session:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})

    # Sanitize path to prevent directory traversal attacks
    path = os.path.normpath(path)
    if path.startswith(".."):
        raise HTTPException(status_code=400, detail="Invalid path")

    try:
        # Use ls command for safety and consistency
        completed = subprocess.run(
            ["ls", "-la", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            text=True
        )

        if completed.returncode != 0:
            return {"error": completed.stderr}

        # Parse ls output
        entries = []
        lines = completed.stdout.strip().split('\n')

        # Skip the total line and parse the rest
        for line in lines[1:] if lines else []:
            parts = line.split()
            if len(parts) >= 9:
                permissions = parts[0]
                size = parts[4]
                date = " ".join(parts[5:8])
                name = " ".join(parts[8:])

                is_dir = permissions.startswith("d")
                entries.append({
                    "name": name,
                    "path": os.path.join(path, name),
                    "size": size,
                    "is_directory": is_dir,
                    "permissions": permissions,
                    "modified": date
                })

        return {
            "path": path,
            "entries": entries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fs/read")
async def read_file(path: str, session: Optional[SessionData] = Depends(get_session_data)):
    """
    Read contents of a file
    """
    if not session:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})

    # Sanitize path to prevent directory traversal attacks
    path = os.path.normpath(path)
    if path.startswith(".."):
        raise HTTPException(status_code=400, detail="Invalid path")

    try:
        # Check if file exists and is a file (not a directory)
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="File not found")

        if not os.path.isfile(path):
            raise HTTPException(status_code=400, detail="Path is not a file")

        # Read file content
        with open(path, "r") as f:
            content = f.read()

        return {
            "path": path,
            "content": content,
            "size": os.path.getsize(path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fs/write")
async def write_file(req: FileRequest, session: Optional[SessionData] = Depends(get_session_data)):
    """
    Write content to a file
    """
    if not session:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})

    # Sanitize path to prevent directory traversal attacks
    path = os.path.normpath(req.path)
    if path.startswith(".."):
        raise HTTPException(status_code=400, detail="Invalid path")

    try:
        # Ensure parent directory exists
        parent_dir = os.path.dirname(path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        # Write content to file
        with open(path, "w") as f:
            f.write(req.content or "")

        return {
            "path": path,
            "size": os.path.getsize(path),
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fs/delete")
async def delete_file(req: FileRequest, session: Optional[SessionData] = Depends(get_session_data)):
    """
    Delete a file or directory
    """
    if not session:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})

    # Sanitize path to prevent directory traversal attacks
    path = os.path.normpath(req.path)
    if path.startswith(".."):
        raise HTTPException(status_code=400, detail="Invalid path")

    try:
        # Check if path exists
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Path not found")

        # Delete file or directory
        if os.path.isfile(path):
            os.remove(path)
        else:
            # Use rmdir for empty directories or rm -r for non-empty
            try:
                os.rmdir(path)  # Will fail if directory is not empty
            except OSError:
                # Directory not empty, use rm -r
                subprocess.run(
                    ["rm", "-r", path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5,
                    check=True
                )

        return {
            "path": path,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fs/search")
async def search_files(req: SearchRequest, session: Optional[SessionData] = Depends(get_session_data)):
    """
    Search for files matching a pattern
    """
    if not session:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})

    # Sanitize path to prevent directory traversal attacks
    path = os.path.normpath(req.path or "/")
    if path.startswith(".."):
        raise HTTPException(status_code=400, detail="Invalid path")

    try:
        # Use find command for searching
        completed = subprocess.run(
            ["find", path, "-name", f"*{req.query}*", "-type", "f"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            text=True
        )

        if completed.returncode != 0:
            return {"error": completed.stderr}

        # Parse results
        results = []
        lines = completed.stdout.strip().split('\n')

        for line in lines:
            if line.strip():
                file_path = line.strip()
                results.append({
                    "path": file_path,
                    "name": os.path.basename(file_path),
                    "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
                })

                # Limit results
                if len(results) >= req.max_results:
                    break

        return {
            "query": req.query,
            "path": path,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Application management
@app.get("/apps/list")
async def list_applications(session: Optional[SessionData] = Depends(get_session_data)):
    """
    List available applications in the system
    """
    if not session:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})

    # In a real system, this would query a database or package manager
    # For this POC, we'll return a static list of common Linux applications
    apps = [
        {
            "name": "Terminal",
            "id": "terminal",
            "icon": "/static/icons/terminal.svg",
            "command": "xterm",
            "category": "System",
            "description": "Command-line interface for executing commands"
        },
        {
            "name": "Text Editor",
            "id": "text-editor",
            "icon": "/static/icons/text-editor.svg",
            "command": "xterm -e nano",
            "category": "Utilities",
            "description": "Simple text editor for creating and editing files"
        },
        {
            "name": "File Manager",
            "id": "file-manager",
            "icon": "/static/icons/file-manager.svg",
            "command": "xterm -e mc",
            "category": "Utilities",
            "description": "Browse and manage files and directories"
        },
        {
            "name": "System Monitor",
            "id": "system-monitor",
            "icon": "/static/icons/system-monitor.svg",
            "command": "xterm -e htop",
            "category": "System",
            "description": "Monitor system resources and processes"
        },
        {
            "name": "Web Browser",
            "id": "browser",
            "icon": "/static/icons/web-browser.svg",
            "command": "firefox",
            "category": "Internet",
            "description": "Browse the web and access online resources"
        },
        {
            "name": "Calculator",
            "id": "calculator",
            "icon": "/static/icons/calculator.svg",
            "command": "xcalc",
            "category": "Utilities",
            "description": "Perform basic and scientific calculations"
        },
        {
            "name": "Image Viewer",
            "id": "image-viewer",
            "icon": "/static/icons/image-viewer.svg",
            "command": "eog",
            "category": "Graphics",
            "description": "View and manage images and photos"
        },
        {
            "name": "Media Player",
            "id": "media-player",
            "icon": "/static/icons/media-player.svg",
            "command": "vlc",
            "category": "Multimedia",
            "description": "Play audio and video files"
        },
        {
            "name": "Settings",
            "id": "settings",
            "icon": "/static/icons/settings.svg",
            "command": "xterm -e nano ~/.config/helios/settings.json",
            "category": "System",
            "description": "Configure system preferences and options"
        }
    ]

    return {
        "applications": apps
    }

@app.post("/apps/launch")
async def launch_application(app_name: str, session: Optional[SessionData] = Depends(get_session_data)):
    """
    Launch an application in the desktop environment
    """
    if not session:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})

    # Map of allowed applications and their commands
    allowed_apps = {
        "terminal": "xterm",
        "text-editor": "xterm -e nano",
        "file-manager": "xterm -e mc",
        "system-monitor": "xterm -e htop",
        "browser": "firefox",
        "calculator": "xcalc",
        "image-viewer": "eog",
        "media-player": "vlc",
        "settings": "xterm -e nano ~/.config/helios/settings.json"
    }

    if app_name.lower() not in allowed_apps:
        raise HTTPException(status_code=403, detail=f"Application '{app_name}' not allowed or not found")

    command = allowed_apps[app_name.lower()]

    try:
        # Launch the application in the background
        process = subprocess.Popen(
            command.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )

        # Log the application launch
        logger.info(f"User {session.username} launched application: {app_name}")

        # Don't wait for it to complete
        return {
            "app": app_name,
            "pid": process.pid,
            "success": True
        }
    except Exception as e:
        logger.error(f"Failed to launch application {app_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# WebRTC Endpoints
@app.websocket("/ws/webrtc")
async def webrtc_signaling(websocket: WebSocket):
    """
    WebSocket endpoint for WebRTC signaling
    """
    try:
        await WebRTCService.handle_websocket(websocket)
    except WebSocketDisconnect:
        logger.info("WebRTC client disconnected")
    except Exception as e:
        logger.error(f"WebRTC error: {str(e)}")

@app.get("/webrtc/config")
async def get_webrtc_config(session: Optional[SessionData] = Depends(get_session_data)):
    """
    Get WebRTC configuration for the client
    """
    # In production, you would use TURN servers for NAT traversal
    return {
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]}
            # Add TURN servers for production
        ],
        "iceTransportPolicy": "all",
        "sdpSemantics": "unified-plan"
    }

@app.get("/webrtc/status")
async def get_webrtc_status():
    """
    Get status of WebRTC service
    """
    return {
        "active_connections": len(WebRTCService.pc_connections),
        "status": "online"
    }
