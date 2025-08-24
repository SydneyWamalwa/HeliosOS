"""
Application Manager for HeliosOS
Manages containerized open-source applications and their lifecycle
"""

import asyncio
import json
import logging
import os
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

class ApplicationStatus(Enum):
    """Application status states"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

class ApplicationCategory(Enum):
    """Application categories for different user types"""
    BUSINESS = "business"
    STUDENT = "student"
    PROGRAMMER = "programmer"
    GENERAL = "general"

@dataclass
class ApplicationDefinition:
    """Definition of an application that can be managed"""
    name: str
    display_name: str
    description: str
    category: ApplicationCategory
    container_image: str
    container_name: str
    ports: Dict[str, int]  # internal_port: external_port
    volumes: Dict[str, str]  # host_path: container_path
    environment: Dict[str, str]
    command: Optional[List[str]] = None
    dependencies: List[str] = None  # Other applications this depends on
    ai_controllable: bool = True
    web_interface: bool = False
    web_port: Optional[int] = None

@dataclass
class ApplicationInstance:
    """Running instance of an application"""
    definition: ApplicationDefinition
    container_id: str
    status: ApplicationStatus
    pid: Optional[int] = None
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    error_message: Optional[str] = None
    resource_usage: Optional[Dict[str, Any]] = None

class ApplicationManager:
    """Manages containerized applications for HeliosOS"""
    
    def __init__(self):
        self.applications: Dict[str, ApplicationDefinition] = {}
        self.running_instances: Dict[str, ApplicationInstance] = {}
        self._initialize_applications()
    
    def _initialize_applications(self):
        """Initialize the catalog of available applications"""
        
        # Business Applications
        self.applications["libreoffice"] = ApplicationDefinition(
            name="libreoffice",
            display_name="LibreOffice Suite",
            description="Complete office suite with Writer, Calc, and Impress",
            category=ApplicationCategory.BUSINESS,
            container_image="libreoffice/online:latest",
            container_name="helios-libreoffice",
            ports={"9980": 9980},
            volumes={"/tmp/libreoffice": "/tmp"},
            environment={"domain": "localhost:9980"},
            web_interface=True,
            web_port=9980
        )
        
        self.applications["odoo"] = ApplicationDefinition(
            name="odoo",
            display_name="Odoo ERP",
            description="Open source ERP and CRM system",
            category=ApplicationCategory.BUSINESS,
            container_image="odoo:16",
            container_name="helios-odoo",
            ports={"8069": 8069},
            volumes={"/var/lib/odoo": "/var/lib/odoo"},
            environment={"POSTGRES_DB": "postgres", "POSTGRES_USER": "odoo", "POSTGRES_PASSWORD": "odoo"},
            dependencies=["postgresql"],
            web_interface=True,
            web_port=8069
        )
        
        self.applications["rocketchat"] = ApplicationDefinition(
            name="rocketchat",
            display_name="Rocket.Chat",
            description="Open source team communication platform",
            category=ApplicationCategory.BUSINESS,
            container_image="rocket.chat:latest",
            container_name="helios-rocketchat",
            ports={"3000": 3000},
            volumes={"/app/uploads": "/app/uploads"},
            environment={"ROOT_URL": "http://localhost:3000", "MONGO_URL": "mongodb://mongo:27017/rocketchat"},
            dependencies=["mongodb"],
            web_interface=True,
            web_port=3000
        )
        
        # Student Applications
        self.applications["joplin"] = ApplicationDefinition(
            name="joplin",
            display_name="Joplin Notes",
            description="Open source note taking and to-do application",
            category=ApplicationCategory.STUDENT,
            container_image="joplin/server:latest",
            container_name="helios-joplin",
            ports={"22300": 22300},
            volumes={"/var/lib/joplin": "/var/lib/joplin"},
            environment={"APP_PORT": "22300", "APP_BASE_URL": "http://localhost:22300"},
            web_interface=True,
            web_port=22300
        )
        
        self.applications["zotero"] = ApplicationDefinition(
            name="zotero",
            display_name="Zotero",
            description="Research assistant for collecting and organizing sources",
            category=ApplicationCategory.STUDENT,
            container_image="linuxserver/zotero:latest",
            container_name="helios-zotero",
            ports={"3000": 3000},
            volumes={"/config": "/config"},
            environment={"PUID": "1000", "PGID": "1000"},
            web_interface=True,
            web_port=3000
        )
        
        # Programmer Applications
        self.applications["vscode"] = ApplicationDefinition(
            name="vscode",
            display_name="VS Code Server",
            description="Visual Studio Code in the browser",
            category=ApplicationCategory.PROGRAMMER,
            container_image="codercom/code-server:latest",
            container_name="helios-vscode",
            ports={"8080": 8080},
            volumes={"/home/coder": "/home/coder", "/var/run/docker.sock": "/var/run/docker.sock"},
            environment={"PASSWORD": "helios123"},
            web_interface=True,
            web_port=8080
        )
        
        self.applications["gitea"] = ApplicationDefinition(
            name="gitea",
            display_name="Gitea",
            description="Lightweight Git service",
            category=ApplicationCategory.PROGRAMMER,
            container_image="gitea/gitea:latest",
            container_name="helios-gitea",
            ports={"3000": 3000, "22": 2222},
            volumes={"/data": "/data", "/etc/timezone": "/etc/timezone", "/etc/localtime": "/etc/localtime"},
            environment={"USER_UID": "1000", "USER_GID": "1000"},
            web_interface=True,
            web_port=3000
        )
        
        self.applications["portainer"] = ApplicationDefinition(
            name="portainer",
            display_name="Portainer",
            description="Container management interface",
            category=ApplicationCategory.PROGRAMMER,
            container_image="portainer/portainer-ce:latest",
            container_name="helios-portainer",
            ports={"9000": 9000},
            volumes={"/var/run/docker.sock": "/var/run/docker.sock", "/portainer_data": "/data"},
            environment={},
            web_interface=True,
            web_port=9000
        )
        
        # General Applications
        self.applications["firefox"] = ApplicationDefinition(
            name="firefox",
            display_name="Firefox Browser",
            description="Open source web browser",
            category=ApplicationCategory.GENERAL,
            container_image="linuxserver/firefox:latest",
            container_name="helios-firefox",
            ports={"3000": 3000},
            volumes={"/config": "/config"},
            environment={"PUID": "1000", "PGID": "1000"},
            web_interface=True,
            web_port=3000
        )
        
        # Database Services (Dependencies)
        self.applications["postgresql"] = ApplicationDefinition(
            name="postgresql",
            display_name="PostgreSQL Database",
            description="Open source relational database",
            category=ApplicationCategory.GENERAL,
            container_image="postgres:15",
            container_name="helios-postgresql",
            ports={"5432": 5432},
            volumes={"/var/lib/postgresql/data": "/var/lib/postgresql/data"},
            environment={"POSTGRES_DB": "postgres", "POSTGRES_USER": "postgres", "POSTGRES_PASSWORD": "helios123"},
            ai_controllable=False
        )
        
        self.applications["mongodb"] = ApplicationDefinition(
            name="mongodb",
            display_name="MongoDB Database",
            description="Open source document database",
            category=ApplicationCategory.GENERAL,
            container_image="mongo:6",
            container_name="helios-mongodb",
            ports={"27017": 27017},
            volumes={"/data/db": "/data/db"},
            environment={},
            ai_controllable=False
        )
    
    async def list_applications(self, category: Optional[ApplicationCategory] = None) -> List[Dict[str, Any]]:
        """List available applications, optionally filtered by category"""
        apps = []
        for app_def in self.applications.values():
            if category is None or app_def.category == category:
                app_info = asdict(app_def)
                app_info["status"] = self.get_application_status(app_def.name)
                apps.append(app_info)
        return apps
    
    async def start_application(self, app_name: str) -> Dict[str, Any]:
        """Start an application container"""
        try:
            if app_name not in self.applications:
                return {"success": False, "error": f"Application '{app_name}' not found"}
            
            app_def = self.applications[app_name]
            
            # Check if already running
            if app_name in self.running_instances:
                instance = self.running_instances[app_name]
                if instance.status == ApplicationStatus.RUNNING:
                    return {"success": True, "message": f"{app_def.display_name} is already running"}
            
            # Start dependencies first
            if app_def.dependencies:
                for dep in app_def.dependencies:
                    dep_result = await self.start_application(dep)
                    if not dep_result.get("success"):
                        return {"success": False, "error": f"Failed to start dependency: {dep}"}
            
            # Build docker run command
            cmd = ["docker", "run", "-d", "--name", app_def.container_name]
            
            # Add port mappings
            for internal_port, external_port in app_def.ports.items():
                cmd.extend(["-p", f"{external_port}:{internal_port}"])
            
            # Add volume mappings
            for host_path, container_path in app_def.volumes.items():
                # Create host directory if it doesn't exist
                if not host_path.startswith("/var/run") and not host_path.startswith("/etc"):
                    os.makedirs(host_path, exist_ok=True)
                cmd.extend(["-v", f"{host_path}:{container_path}"])
            
            # Add environment variables
            for env_key, env_value in app_def.environment.items():
                cmd.extend(["-e", f"{env_key}={env_value}"])
            
            # Add the image
            cmd.append(app_def.container_image)
            
            # Add command if specified
            if app_def.command:
                cmd.extend(app_def.command)
            
            # Execute the docker run command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                container_id = stdout.decode().strip()
                
                # Create application instance
                instance = ApplicationInstance(
                    definition=app_def,
                    container_id=container_id,
                    status=ApplicationStatus.RUNNING,
                    started_at=datetime.now()
                )
                
                self.running_instances[app_name] = instance
                
                result = {
                    "success": True,
                    "message": f"{app_def.display_name} started successfully",
                    "container_id": container_id,
                    "web_url": f"http://localhost:{app_def.web_port}" if app_def.web_interface else None
                }
                
                logger.info(f"Started application {app_name}: {container_id}")
                return result
            else:
                error_msg = stderr.decode().strip()
                logger.error(f"Failed to start application {app_name}: {error_msg}")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            logger.error(f"Exception starting application {app_name}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def stop_application(self, app_name: str) -> Dict[str, Any]:
        """Stop an application container"""
        try:
            if app_name not in self.running_instances:
                return {"success": False, "error": f"Application '{app_name}' is not running"}
            
            instance = self.running_instances[app_name]
            
            # Stop the container
            process = await asyncio.create_subprocess_exec(
                "docker", "stop", instance.container_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Remove the container
                await asyncio.create_subprocess_exec(
                    "docker", "rm", instance.container_id,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Update instance status
                instance.status = ApplicationStatus.STOPPED
                instance.stopped_at = datetime.now()
                
                # Remove from running instances
                del self.running_instances[app_name]
                
                logger.info(f"Stopped application {app_name}")
                return {
                    "success": True,
                    "message": f"{instance.definition.display_name} stopped successfully"
                }
            else:
                error_msg = stderr.decode().strip()
                logger.error(f"Failed to stop application {app_name}: {error_msg}")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            logger.error(f"Exception stopping application {app_name}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def restart_application(self, app_name: str) -> Dict[str, Any]:
        """Restart an application"""
        stop_result = await self.stop_application(app_name)
        if not stop_result.get("success"):
            return stop_result
        
        # Wait a moment for cleanup
        await asyncio.sleep(2)
        
        return await self.start_application(app_name)
    
    def get_application_status(self, app_name: str) -> str:
        """Get the current status of an application"""
        if app_name in self.running_instances:
            return self.running_instances[app_name].status.value
        return ApplicationStatus.STOPPED.value
    
    async def get_application_info(self, app_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an application"""
        if app_name not in self.applications:
            return None
        
        app_def = self.applications[app_name]
        info = asdict(app_def)
        info["status"] = self.get_application_status(app_name)
        
        if app_name in self.running_instances:
            instance = self.running_instances[app_name]
            info["instance"] = {
                "container_id": instance.container_id,
                "started_at": instance.started_at.isoformat() if instance.started_at else None,
                "resource_usage": instance.resource_usage
            }
        
        return info
    
    async def get_running_applications(self) -> List[Dict[str, Any]]:
        """Get list of currently running applications"""
        running = []
        for app_name, instance in self.running_instances.items():
            app_info = asdict(instance.definition)
            app_info["status"] = instance.status.value
            app_info["container_id"] = instance.container_id
            app_info["started_at"] = instance.started_at.isoformat() if instance.started_at else None
            running.append(app_info)
        return running
    
    async def execute_application_action(self, app_name: str, action: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a specific action within an application"""
        if app_name not in self.applications:
            return {"success": False, "error": f"Application '{app_name}' not found"}
        
        app_def = self.applications[app_name]
        
        if not app_def.ai_controllable:
            return {"success": False, "error": f"Application '{app_name}' is not AI controllable"}
        
        # For now, this is a placeholder implementation
        # In a full implementation, this would interface with application-specific APIs
        
        if action == "open_document" and app_name == "libreoffice":
            return await self._libreoffice_open_document(parameters)
        elif action == "create_project" and app_name == "vscode":
            return await self._vscode_create_project(parameters)
        else:
            return {
                "success": False,
                "error": f"Action '{action}' not supported for application '{app_name}'"
            }
    
    async def _libreoffice_open_document(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Open a document in LibreOffice"""
        # Placeholder implementation
        document_path = parameters.get("document_path", "")
        return {
            "success": True,
            "message": f"Document '{document_path}' opened in LibreOffice",
            "action": "open_document"
        }
    
    async def _vscode_create_project(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project in VS Code"""
        # Placeholder implementation
        project_name = parameters.get("project_name", "")
        project_type = parameters.get("project_type", "general")
        return {
            "success": True,
            "message": f"Project '{project_name}' created in VS Code",
            "action": "create_project",
            "project_type": project_type
        }
    
    async def cleanup_stopped_containers(self):
        """Clean up stopped containers"""
        try:
            # Remove stopped containers
            process = await asyncio.create_subprocess_exec(
                "docker", "container", "prune", "-f",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            logger.info("Cleaned up stopped containers")
            
        except Exception as e:
            logger.error(f"Failed to cleanup containers: {str(e)}")

# Global instance
application_manager = ApplicationManager()

