# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from typing import List, Dict, Any
import shlex, subprocess, uuid, time

app = FastAPI(title="Aurora / Leo Assist")

HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY", None)
HF_BASE = "https://api-inference.huggingface.co/models/"

# Simple in-memory profile (POC)
PROFILE: Dict[str, Any] = {"username": "Guest", "prefs": {}}

# Whitelisted commands (only first token is checked)
ALLOWED_CMDS = {
    "ls", "pwd", "whoami", "date", "uptime", "df", "free", "echo", "ps", "id"
}

class SummarizeRequest(BaseModel):
    text: str

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class ExecRequest(BaseModel):
    cmd: str

@app.get("/status")
async def status():
    return {"service": "aurora/leo", "status": "ok", "time": int(time.time()), "profile": PROFILE}

@app.post("/profile")
async def set_profile(payload: Dict[str, Any]):
    # minimal profile set endpoint
    PROFILE.update(payload)
    return {"ok": True, "profile": PROFILE}

@app.get("/")
async def root():
    return {"status": "aurora ok", "assistant": "leo"}

@app.post("/summarize")
async def summarize(req: SummarizeRequest):
    text = (req.text or "").strip()
    if not text:
        return {"summary": ""}
    if HUGGINGFACE_API_KEY:
        model = "facebook/bart-large-cnn"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        payload = {"inputs": text}
        try:
            resp = requests.post(HF_BASE + model, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            out = resp.json()
            if isinstance(out, list) and len(out) > 0 and "summary_text" in out[0]:
                return {"summary": out[0]["summary_text"]}
            return {"summary": str(out)}
        except Exception as e:
            return {"error": "HuggingFace call failed", "detail": str(e)}
    # Mock fallback
    short = text if len(text) <= 200 else text[:197] + "..."
    return {"summary": f"[MOCK SUMMARY] {short}"}

@app.post("/chat")
async def chat(req: ChatRequest):
    msgs = req.messages or []
    last = msgs[-1].content if msgs else ""
    persona_preamble = (
        "You are Leo, an extremely helpful, friendly, and concise AI assistant embedded in the Aurora OS. "
        "You help users operate the streamed desktop, summarize text, run small diagnostics, and explain results clearly. "
        "Be polite, include short actionable steps when relevant, and ask clarifying questions only if essential."
    )
    prompt = persona_preamble + "\n\nUser: " + last + "\nLeo:"
    if HUGGINGFACE_API_KEY:
        # Lightweight text gen proxy (POC)
        model = "gpt2"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        payload = {"inputs": prompt, "options": {"wait_for_model": True}}
        try:
            resp = requests.post(HF_BASE + model, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            out = resp.json()
            if isinstance(out, dict) and "generated_text" in out:
                reply = out["generated_text"]
            elif isinstance(out, list) and len(out) > 0 and isinstance(out[0], dict) and "generated_text" in out[0]:
                reply = out[0]["generated_text"]
            else:
                reply = str(out)
            # Trim echo of the prompt if present
            if reply.startswith(prompt):
                reply = reply[len(prompt):].strip()
            return {"reply": reply}
        except Exception as e:
            return {"reply": f"[HF proxy failed] {str(e)}"}
    # No HF key: implement helpful mock heuristics
    txt = last.lower().strip()
    if txt.startswith("summarize") or txt.startswith("summarise"):
        body = last.split(":", 1)[-1].strip() if ":" in last else last
        if len(body) > 200:
            body = body[:197] + "..."
        return {"reply": f"[MOCK SUMMARY] {body}"}
    if "open terminal" in txt or "open the terminal" in txt:
        return {"reply": "To interact with the OS, click 'Open raw VNC' or open the desktop pane on the left. You can also run a safe command from the 'Run Command' panel."}
    if "help" in txt or txt.startswith("how do i"):
        return {"reply": "I am Leo. I can summarize text, run small diagnostic commands (ls, df, uptime), and guide you through using the streamed desktop. Try: 'Summarize: <text>' or use the Run Command panel."}
    if "screenshot" in txt or "describe" in txt:
        return {"reply": "I can't access pixels in this POC. Use the VNC view to see the desktop visually. If you need a textual summary, paste text or ask me to run a command that outputs info."}
    # default friendly reply
    safe = last if len(last) < 400 else last[:400] + "..."
    return {"reply": f"[Leo]: I received: \"{safe}\" — how would you like me to help? Try 'Summarize:' or use the Run Command panel."}

@app.post("/exec")
async def exec_cmd(req: ExecRequest):
    """
    Execute a *whitelisted* command inside the container and return stdout/stderr.
    WARNING: This endpoint runs commands on the container. It only allows a restricted set for safety.
    """
    cmdline = (req.cmd or "").strip()
    if not cmdline:
        raise HTTPException(status_code=400, detail="empty command")
    # parse
    try:
        parts = shlex.split(cmdline)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"failed to parse command: {e}")
    if len(parts) == 0:
        raise HTTPException(status_code=400, detail="empty command")
    if parts[0] not in ALLOWED_CMDS:
        raise HTTPException(status_code=403, detail=f"command '{parts[0]}' not allowed in POC")
    # Run safely with timeout and capture
    try:
        completed = subprocess.run(parts, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=8, text=True)
        return {
            "cmd": cmdline,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="command timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
