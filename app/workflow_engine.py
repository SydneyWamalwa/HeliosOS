"""
Workflow Engine for HeliosOS
Enables creation and execution of automated multi-step workflows
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import uuid

from app.ai_command_processor import ai_command_processor
from app.application_manager import application_manager

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepType(Enum):
    """Types of workflow steps"""
    COMMAND = "command"
    APPLICATION = "application"
    DELAY = "delay"
    CONDITION = "condition"
    LOOP = "loop"

@dataclass
class WorkflowStep:
    """Individual step in a workflow"""
    id: str
    type: StepType
    name: str
    description: str
    parameters: Dict[str, Any]
    timeout: int = 30  # seconds
    retry_count: int = 0
    on_failure: str = "stop"  # stop, continue, retry

@dataclass
class WorkflowDefinition:
    """Definition of a workflow"""
    id: str
    name: str
    display_name: str
    description: str
    category: str
    steps: List[WorkflowStep]
    variables: Dict[str, Any]
    created_by: str
    created_at: datetime
    tags: List[str]
    is_public: bool = False

@dataclass
class WorkflowExecution:
    """Runtime execution of a workflow"""
    id: str
    workflow_id: str
    status: WorkflowStatus
    current_step: int
    started_at: datetime
    completed_at: Optional[datetime]
    executed_by: str
    results: List[Dict[str, Any]]
    error_message: Optional[str] = None
    context: Dict[str, Any] = None

class WorkflowEngine:
    """Engine for creating and executing workflows"""
    
    def __init__(self):
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self._initialize_default_workflows()
    
    def _initialize_default_workflows(self):
        """Initialize default workflows for different user types"""
        
        # Business workflows
        self.workflows["morning_business"] = WorkflowDefinition(
            id="morning_business",
            name="morning_business",
            display_name="Morning Business Routine",
            description="Start your business day with essential applications",
            category="business",
            steps=[
                WorkflowStep(
                    id="step_1",
                    type=StepType.APPLICATION,
                    name="Launch Firefox",
                    description="Open web browser for email and web access",
                    parameters={"action": "start", "application": "firefox"}
                ),
                WorkflowStep(
                    id="step_2",
                    type=StepType.DELAY,
                    name="Wait for Firefox",
                    description="Allow Firefox to fully load",
                    parameters={"duration": 3}
                ),
                WorkflowStep(
                    id="step_3",
                    type=StepType.APPLICATION,
                    name="Launch LibreOffice Calc",
                    description="Open spreadsheet application",
                    parameters={"action": "start", "application": "libreoffice"}
                ),
                WorkflowStep(
                    id="step_4",
                    type=StepType.APPLICATION,
                    name="Launch Rocket.Chat",
                    description="Open team communication",
                    parameters={"action": "start", "application": "rocketchat"}
                ),
                WorkflowStep(
                    id="step_5",
                    type=StepType.COMMAND,
                    name="System Status",
                    description="Display system status",
                    parameters={"command": "show system status"}
                )
            ],
            variables={},
            created_by="system",
            created_at=datetime.now(),
            tags=["business", "morning", "productivity"],
            is_public=True
        )
        
        # Developer workflows
        self.workflows["dev_environment"] = WorkflowDefinition(
            id="dev_environment",
            name="dev_environment",
            display_name="Development Environment Setup",
            description="Setup complete development environment",
            category="programmer",
            steps=[
                WorkflowStep(
                    id="step_1",
                    type=StepType.APPLICATION,
                    name="Launch VS Code",
                    description="Open code editor",
                    parameters={"action": "start", "application": "vscode"}
                ),
                WorkflowStep(
                    id="step_2",
                    type=StepType.APPLICATION,
                    name="Launch Gitea",
                    description="Open Git repository manager",
                    parameters={"action": "start", "application": "gitea"}
                ),
                WorkflowStep(
                    id="step_3",
                    type=StepType.APPLICATION,
                    name="Launch Portainer",
                    description="Open container management",
                    parameters={"action": "start", "application": "portainer"}
                ),
                WorkflowStep(
                    id="step_4",
                    type=StepType.COMMAND,
                    name="Open Terminal",
                    description="Launch terminal for command line access",
                    parameters={"command": "open terminal"}
                )
            ],
            variables={},
            created_by="system",
            created_at=datetime.now(),
            tags=["programming", "development", "setup"],
            is_public=True
        )
        
        # Student workflows
        self.workflows["study_session"] = WorkflowDefinition(
            id="study_session",
            name="study_session",
            display_name="Study Session Setup",
            description="Prepare environment for productive studying",
            category="student",
            steps=[
                WorkflowStep(
                    id="step_1",
                    type=StepType.APPLICATION,
                    name="Launch Joplin",
                    description="Open note-taking application",
                    parameters={"action": "start", "application": "joplin"}
                ),
                WorkflowStep(
                    id="step_2",
                    type=StepType.APPLICATION,
                    name="Launch Zotero",
                    description="Open reference manager",
                    parameters={"action": "start", "application": "zotero"}
                ),
                WorkflowStep(
                    id="step_3",
                    type=StepType.APPLICATION,
                    name="Launch Firefox",
                    description="Open browser for research",
                    parameters={"action": "start", "application": "firefox"}
                ),
                WorkflowStep(
                    id="step_4",
                    type=StepType.COMMAND,
                    name="Create Study Folder",
                    description="Create folder for today's study materials",
                    parameters={"command": f"create folder study_{datetime.now().strftime('%Y%m%d')}"}
                )
            ],
            variables={},
            created_by="system",
            created_at=datetime.now(),
            tags=["student", "study", "research"],
            is_public=True
        )
        
        # General productivity workflows
        self.workflows["quick_start"] = WorkflowDefinition(
            id="quick_start",
            name="quick_start",
            display_name="Quick Start",
            description="Basic setup for general computer use",
            category="general",
            steps=[
                WorkflowStep(
                    id="step_1",
                    type=StepType.APPLICATION,
                    name="Launch Firefox",
                    description="Open web browser",
                    parameters={"action": "start", "application": "firefox"}
                ),
                WorkflowStep(
                    id="step_2",
                    type=StepType.COMMAND,
                    name="Open File Manager",
                    description="Launch file manager",
                    parameters={"command": "open file manager"}
                ),
                WorkflowStep(
                    id="step_3",
                    type=StepType.COMMAND,
                    name="System Status",
                    description="Show system information",
                    parameters={"command": "show system status"}
                )
            ],
            variables={},
            created_by="system",
            created_at=datetime.now(),
            tags=["general", "basic", "startup"],
            is_public=True
        )
    
    async def list_workflows(self, category: Optional[str] = None, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available workflows"""
        workflows = []
        for workflow in self.workflows.values():
            if category and workflow.category != category:
                continue
            
            # Include public workflows and user's own workflows
            if workflow.is_public or (user_id and workflow.created_by == user_id):
                workflow_info = asdict(workflow)
                workflow_info['step_count'] = len(workflow.steps)
                workflow_info['estimated_duration'] = self._estimate_workflow_duration(workflow)
                workflows.append(workflow_info)
        
        return workflows
    
    def _estimate_workflow_duration(self, workflow: WorkflowDefinition) -> int:
        """Estimate workflow execution duration in seconds"""
        total_duration = 0
        for step in workflow.steps:
            if step.type == StepType.DELAY:
                total_duration += step.parameters.get('duration', 1)
            elif step.type == StepType.APPLICATION:
                total_duration += 5  # Estimated app launch time
            elif step.type == StepType.COMMAND:
                total_duration += 2  # Estimated command execution time
            else:
                total_duration += 1
        return total_duration
    
    async def execute_workflow(self, workflow_id: str, user_id: str, context: Dict[str, Any] = None) -> str:
        """Execute a workflow and return execution ID"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow '{workflow_id}' not found")
        
        workflow = self.workflows[workflow_id]
        execution_id = str(uuid.uuid4())
        
        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            current_step=0,
            started_at=datetime.now(),
            completed_at=None,
            executed_by=user_id,
            results=[],
            context=context or {}
        )
        
        self.executions[execution_id] = execution
        
        # Start execution in background
        asyncio.create_task(self._execute_workflow_steps(execution_id))
        
        return execution_id
    
    async def _execute_workflow_steps(self, execution_id: str):
        """Execute workflow steps"""
        try:
            execution = self.executions[execution_id]
            workflow = self.workflows[execution.workflow_id]
            
            execution.status = WorkflowStatus.RUNNING
            
            for i, step in enumerate(workflow.steps):
                execution.current_step = i
                
                logger.info(f"Executing workflow {workflow.name}, step {i+1}: {step.name}")
                
                try:
                    result = await self._execute_step(step, execution.context)
                    execution.results.append({
                        'step_id': step.id,
                        'step_name': step.name,
                        'success': True,
                        'result': result,
                        'executed_at': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"Step {step.name} failed: {e}")
                    execution.results.append({
                        'step_id': step.id,
                        'step_name': step.name,
                        'success': False,
                        'error': str(e),
                        'executed_at': datetime.now().isoformat()
                    })
                    
                    if step.on_failure == "stop":
                        execution.status = WorkflowStatus.FAILED
                        execution.error_message = f"Step '{step.name}' failed: {str(e)}"
                        execution.completed_at = datetime.now()
                        return
                    elif step.on_failure == "retry" and step.retry_count > 0:
                        # Implement retry logic here
                        pass
                    # Continue to next step if on_failure == "continue"
            
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.now()
            logger.info(f"Workflow {workflow.name} completed successfully")
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
    
    async def _execute_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step"""
        if step.type == StepType.COMMAND:
            return await self._execute_command_step(step, context)
        elif step.type == StepType.APPLICATION:
            return await self._execute_application_step(step, context)
        elif step.type == StepType.DELAY:
            return await self._execute_delay_step(step, context)
        else:
            raise ValueError(f"Unsupported step type: {step.type}")
    
    async def _execute_command_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command step"""
        command = step.parameters.get('command')
        if not command:
            raise ValueError("Command step missing 'command' parameter")
        
        # Use the AI command processor to execute the command
        result = await ai_command_processor.process_command(command, context)
        
        return {
            'type': 'command',
            'command': command,
            'success': result.success,
            'message': result.message,
            'data': result.data
        }
    
    async def _execute_application_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an application step"""
        action = step.parameters.get('action')
        application = step.parameters.get('application')
        
        if not action or not application:
            raise ValueError("Application step missing 'action' or 'application' parameter")
        
        if action == 'start':
            result = await application_manager.start_application(application)
        elif action == 'stop':
            result = await application_manager.stop_application(application)
        elif action == 'restart':
            result = await application_manager.restart_application(application)
        else:
            raise ValueError(f"Unsupported application action: {action}")
        
        return {
            'type': 'application',
            'action': action,
            'application': application,
            'success': result.get('success', False),
            'message': result.get('message', ''),
            'data': result
        }
    
    async def _execute_delay_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a delay step"""
        duration = step.parameters.get('duration', 1)
        await asyncio.sleep(duration)
        
        return {
            'type': 'delay',
            'duration': duration,
            'success': True,
            'message': f"Waited for {duration} seconds"
        }
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a workflow execution"""
        if execution_id not in self.executions:
            return None
        
        execution = self.executions[execution_id]
        workflow = self.workflows[execution.workflow_id]
        
        return {
            'execution_id': execution_id,
            'workflow_name': workflow.display_name,
            'status': execution.status.value,
            'current_step': execution.current_step,
            'total_steps': len(workflow.steps),
            'started_at': execution.started_at.isoformat(),
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'results': execution.results,
            'error_message': execution.error_message
        }
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution"""
        if execution_id not in self.executions:
            return False
        
        execution = self.executions[execution_id]
        if execution.status == WorkflowStatus.RUNNING:
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.now()
            return True
        
        return False
    
    async def create_workflow(self, workflow_data: Dict[str, Any], user_id: str) -> str:
        """Create a new custom workflow"""
        workflow_id = str(uuid.uuid4())
        
        # Validate and create workflow steps
        steps = []
        for step_data in workflow_data.get('steps', []):
            step = WorkflowStep(
                id=step_data.get('id', str(uuid.uuid4())),
                type=StepType(step_data['type']),
                name=step_data['name'],
                description=step_data.get('description', ''),
                parameters=step_data.get('parameters', {}),
                timeout=step_data.get('timeout', 30),
                retry_count=step_data.get('retry_count', 0),
                on_failure=step_data.get('on_failure', 'stop')
            )
            steps.append(step)
        
        workflow = WorkflowDefinition(
            id=workflow_id,
            name=workflow_data['name'],
            display_name=workflow_data.get('display_name', workflow_data['name']),
            description=workflow_data.get('description', ''),
            category=workflow_data.get('category', 'custom'),
            steps=steps,
            variables=workflow_data.get('variables', {}),
            created_by=user_id,
            created_at=datetime.now(),
            tags=workflow_data.get('tags', []),
            is_public=workflow_data.get('is_public', False)
        )
        
        self.workflows[workflow_id] = workflow
        return workflow_id
    
    def delete_workflow(self, workflow_id: str, user_id: str) -> bool:
        """Delete a custom workflow"""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        
        # Only allow deletion of user's own workflows or if user is admin
        if workflow.created_by != user_id and not workflow.is_public:
            return False
        
        del self.workflows[workflow_id]
        return True
    
    def get_workflow_templates(self) -> List[Dict[str, Any]]:
        """Get workflow templates for creating new workflows"""
        templates = [
            {
                'name': 'simple_app_launcher',
                'display_name': 'Simple App Launcher',
                'description': 'Template for launching multiple applications',
                'steps': [
                    {
                        'type': 'application',
                        'name': 'Launch App 1',
                        'parameters': {'action': 'start', 'application': 'firefox'}
                    },
                    {
                        'type': 'delay',
                        'name': 'Wait',
                        'parameters': {'duration': 2}
                    },
                    {
                        'type': 'application',
                        'name': 'Launch App 2',
                        'parameters': {'action': 'start', 'application': 'vscode'}
                    }
                ]
            },
            {
                'name': 'command_sequence',
                'display_name': 'Command Sequence',
                'description': 'Template for executing a sequence of commands',
                'steps': [
                    {
                        'type': 'command',
                        'name': 'First Command',
                        'parameters': {'command': 'show system status'}
                    },
                    {
                        'type': 'command',
                        'name': 'Second Command',
                        'parameters': {'command': 'open file manager'}
                    }
                ]
            }
        ]
        return templates

# Global instance
workflow_engine = WorkflowEngine()

