"""
Base classes for the ACP (Agent Communication Protocol) layer.

This module defines abstract base classes for intelligent agents that can
communicate and coordinate to perform complex analysis tasks.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import uuid
from datetime import datetime

from ..core.logging import get_logger
from ..etl.base import BudgetDocument
from ..rag.base import RAGResponse


class MessageType(Enum):
    """Types of messages that can be exchanged between agents."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class AgentStatus(Enum):
    """Status of an agent."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class Message:
    """Represents a message between agents."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    receiver: str = ""
    message_type: MessageType = MessageType.REQUEST
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'sender': self.sender,
            'receiver': self.receiver,
            'message_type': self.message_type.value,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id,
        }


@dataclass
class AgentCapability:
    """Represents a capability that an agent can perform."""
    
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]


@dataclass
class TaskResult:
    """Represents the result of a task execution."""
    
    task_id: str
    agent_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'task_id': self.task_id,
            'agent_id': self.agent_id,
            'success': self.success,
            'result': self.result,
            'error': self.error,
            'execution_time': self.execution_time,
            'metadata': self.metadata,
        }


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.status = AgentStatus.IDLE
        self.capabilities: List[AgentCapability] = []
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.logger = get_logger(f"agent.{name}")
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the agent."""
        pass
    
    @abstractmethod
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process an incoming message."""
        pass
    
    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """Execute a specific task."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """Get list of agent capabilities."""
        pass
    
    async def send_message(self, receiver: str, content: Dict[str, Any], 
                          message_type: MessageType = MessageType.REQUEST) -> str:
        """Send a message to another agent."""
        message = Message(
            sender=self.agent_id,
            receiver=receiver,
            message_type=message_type,
            content=content
        )
        
        self.logger.info(f"Sending message to {receiver}", message_id=message.id)
        # In a real implementation, this would use the ACP protocol
        # For now, we'll implement a simple message passing system
        
        return message.id
    
    async def receive_message(self) -> Optional[Message]:
        """Receive a message from the queue."""
        try:
            message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
            self.logger.info(f"Received message from {message.sender}", message_id=message.id)
            return message
        except asyncio.TimeoutError:
            return None
    
    async def run(self):
        """Main agent loop."""
        self.logger.info(f"Starting agent {self.name}")
        await self.initialize()
        
        while True:
            try:
                message = await self.receive_message()
                if message:
                    self.status = AgentStatus.BUSY
                    response = await self.process_message(message)
                    if response:
                        # Send response back
                        await self.send_message(
                            message.sender, 
                            response.content, 
                            MessageType.RESPONSE
                        )
                    self.status = AgentStatus.IDLE
                else:
                    # No message received, do periodic tasks
                    await self.periodic_tasks()
                    
            except Exception as e:
                self.logger.error(f"Error in agent loop: {str(e)}")
                self.status = AgentStatus.ERROR
                await asyncio.sleep(1)
    
    async def periodic_tasks(self):
        """Perform periodic tasks when idle."""
        pass
    
    def add_capability(self, capability: AgentCapability):
        """Add a capability to the agent."""
        self.capabilities.append(capability)
        self.logger.info(f"Added capability: {capability.name}")


class CoordinatorAgent(BaseAgent):
    """Coordinator agent that orchestrates other agents."""
    
    def __init__(self, agent_id: str = "coordinator"):
        super().__init__(agent_id, "Coordinator")
        self.registered_agents: Dict[str, Dict[str, Any]] = {}
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
    
    async def initialize(self) -> bool:
        """Initialize the coordinator agent."""
        self.logger.info("Initializing Coordinator Agent")
        return True
    
    async def register_agent(self, agent_id: str, capabilities: List[AgentCapability]):
        """Register an agent with the coordinator."""
        self.registered_agents[agent_id] = {
            'capabilities': capabilities,
            'status': AgentStatus.IDLE,
            'last_heartbeat': datetime.now()
        }
        self.logger.info(f"Registered agent: {agent_id}")
    
    async def find_capable_agent(self, required_capability: str) -> Optional[str]:
        """Find an agent capable of performing a specific task."""
        for agent_id, info in self.registered_agents.items():
            for capability in info['capabilities']:
                if capability.name == required_capability:
                    if info['status'] == AgentStatus.IDLE:
                        return agent_id
        return None
    
    async def orchestrate_workflow(self, workflow_id: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Orchestrate a complex workflow across multiple agents."""
        self.logger.info(f"Starting workflow: {workflow_id}")
        
        workflow = {
            'id': workflow_id,
            'tasks': tasks,
            'results': {},
            'status': 'running',
            'start_time': datetime.now()
        }
        
        self.active_workflows[workflow_id] = workflow
        
        try:
            for task in tasks:
                required_capability = task.get('capability')
                agent_id = await self.find_capable_agent(required_capability)
                
                if not agent_id:
                    raise Exception(f"No agent found for capability: {required_capability}")
                
                # Send task to agent
                task_message = Message(
                    sender=self.agent_id,
                    receiver=agent_id,
                    message_type=MessageType.REQUEST,
                    content=task
                )
                
                # In a real implementation, we'd wait for the response
                # For now, we'll simulate task execution
                workflow['results'][task['id']] = {
                    'status': 'completed',
                    'agent': agent_id,
                    'result': f"Task {task['id']} completed by {agent_id}"
                }
            
            workflow['status'] = 'completed'
            workflow['end_time'] = datetime.now()
            
            self.logger.info(f"Workflow completed: {workflow_id}")
            return workflow
            
        except Exception as e:
            workflow['status'] = 'failed'
            workflow['error'] = str(e)
            self.logger.error(f"Workflow failed: {workflow_id}, error: {str(e)}")
            return workflow
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages."""
        content = message.content
        
        if content.get('action') == 'register':
            await self.register_agent(
                message.sender, 
                content.get('capabilities', [])
            )
            return Message(
                sender=self.agent_id,
                receiver=message.sender,
                message_type=MessageType.RESPONSE,
                content={'status': 'registered'}
            )
        
        elif content.get('action') == 'start_workflow':
            workflow = await self.orchestrate_workflow(
                content.get('workflow_id'),
                content.get('tasks', [])
            )
            return Message(
                sender=self.agent_id,
                receiver=message.sender,
                message_type=MessageType.RESPONSE,
                content={'workflow': workflow}
            )
        
        return None
    
    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """Execute a coordination task."""
        task_id = task.get('id', str(uuid.uuid4()))
        
        try:
            if task.get('type') == 'orchestrate':
                workflow = await self.orchestrate_workflow(
                    task.get('workflow_id', str(uuid.uuid4())),
                    task.get('tasks', [])
                )
                
                return TaskResult(
                    task_id=task_id,
                    agent_id=self.agent_id,
                    success=True,
                    result=workflow
                )
            else:
                raise ValueError(f"Unknown task type: {task.get('type')}")
                
        except Exception as e:
            return TaskResult(
                task_id=task_id,
                agent_id=self.agent_id,
                success=False,
                result=None,
                error=str(e)
            )
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get coordinator capabilities."""
        return [
            AgentCapability(
                name="orchestrate_workflow",
                description="Orchestrate complex workflows across multiple agents",
                input_schema={"workflow_id": "string", "tasks": "array"},
                output_schema={"workflow": "object"}
            ),
            AgentCapability(
                name="agent_registry",
                description="Manage agent registration and discovery",
                input_schema={"action": "string"},
                output_schema={"status": "string"}
            )
        ]


class AgentRegistry:
    """Registry for managing agents in the system."""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.logger = get_logger("agent.registry")
    
    def register(self, agent: BaseAgent):
        """Register an agent."""
        self.agents[agent.agent_id] = agent
        self.logger.info(f"Registered agent: {agent.agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """List all registered agent IDs."""
        return list(self.agents.keys())
    
    async def start_all(self):
        """Start all registered agents."""
        tasks = []
        for agent in self.agents.values():
            tasks.append(asyncio.create_task(agent.run()))
        
        await asyncio.gather(*tasks, return_exceptions=True) 