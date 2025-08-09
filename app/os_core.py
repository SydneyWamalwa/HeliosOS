"""
HeliosOS - AI Operating System Core
Designed for cloud streaming with user-centric design
"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import websockets
import threading
import time

@dataclass
class UserSession:
    """Represents a user's cloud session"""
    session_id: str
    user_id: str
    desktop_id: str
    created_at: datetime
    last_activity: datetime
    preferences: Dict[str, Any]
    active_apps: List[str]
    clipboard: str = ""
    screen_resolution: str = "1920x1080"
    bandwidth_limit: int = 10000  # kbps

@dataclass
class DesktopInstance:
    """Represents a cloud desktop instance"""
    desktop_id: str
    os_type: str = "linux"
    cpu_cores: int = 4
    memory_gb: int = 8
    storage_gb: int = 50
    gpu_enabled: bool = True
    status: str = "ready"  # ready, active, suspended, terminated
    assigned_user: Optional[str] = None
    created_at: datetime = None
    last_used: datetime = None

class HeliosOSCore:
    """Core operating system for cloud streaming"""

    def __init__(self):
        self.active_sessions: Dict[str, UserSession] = {}
        self.desktop_pool: Dict[str, DesktopInstance] = {}
        self.system_stats = {
            "total_users": 0,
            "active_sessions": 0,
            "available_desktops": 0,
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "network_usage": 0.0
        }
        self._initialize_desktop_pool()
        self._start_monitoring()

    def _initialize_desktop_pool(self):
        """Initialize cloud desktop instances"""
        for i in range(10):  # Start with 10 ready instances
            desktop = DesktopInstance(
                desktop_id=f"desktop-{i:03d}",
                created_at=datetime.now()
            )
            self.desktop_pool[desktop.desktop_id] = desktop

    def _start_monitoring(self):
        """Start system monitoring thread"""
        def monitor():
            while True:
                self._update_system_stats()
                time.sleep(5)

        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()

    def _update_system_stats(self):
        """Update system statistics"""
        self.system_stats.update({
            "active_sessions": len(self.active_sessions),
            "available_desktops": len([d for d in self.desktop_pool.values() if d.status == "ready"]),
            "cpu_usage": 45.2,  # Mock data - would be real in production
            "memory_usage": 67.8,
            "network_usage": 23.4
        })

    async def create_session(self, user_id: str, preferences: Dict[str, Any]) -> UserSession:
        """Create a new user session with cloud desktop"""
        session_id = str(uuid.uuid4())

        # Find available desktop
        available_desktop = None
        for desktop in self.desktop_pool.values():
            if desktop.status == "ready":
                available_desktop = desktop
                break

        if not available_desktop:
            raise Exception("No available desktops")

        # Create session
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            desktop_id=available_desktop.desktop_id,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            preferences=preferences,
            active_apps=[]
        )

        self.active_sessions[session_id] = session
        available_desktop.status = "active"
        available_desktop.assigned_user = user_id
        available_desktop.last_used = datetime.now()

        return session

    async def end_session(self, session_id: str):
        """End a user session and free resources"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            desktop = self.desktop_pool[session.desktop_id]

            # Clean up desktop
            desktop.status = "ready"
            desktop.assigned_user = None

            # Remove session
            del self.active_sessions[session_id]

    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID"""
        return self.active_sessions.get(session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions"""
        return [asdict(session) for session in self.active_sessions.values()]

    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        return self.system_stats.copy()

# Global OS instance
os_core = HeliosOSCore()
