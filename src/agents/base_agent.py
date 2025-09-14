import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import uuid

from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

from ..models import (
    AgentType, Message, MessageType, Priority, ProjectSpecification,
    AgentState, ProjectArtifact
)
from ..utils.message_broker import MessageBroker
from ..utils.logger import get_logger


class BaseAgent(ABC):
    """Base class for all agents in the agentic ecosystem."""
    
    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        model_name: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.logger = get_logger(f"{agent_type.value}_agent")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Initialize memory for conversation context
        self.memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Agent state
        self.state = AgentState(
            agent_id=agent_id,
            agent_type=agent_type,
            status="idle"
        )
        
        # Message broker for A2A communication
        self.message_broker = MessageBroker()
        
        # Current projects and tasks
        self.current_projects: Dict[str, ProjectSpecification] = {}
        self.task_queue: List[Message] = []
        
        self.logger.info(f"Initialized {agent_type.value} agent with ID: {agent_id}")
    
    async def start(self):
        """Start the agent and begin listening for messages."""
        await self.message_broker.connect()
        await self.message_broker.subscribe(
            topic=f"agents/{self.agent_type.value}",
            callback=self.handle_message
        )
        self.state.status = "idle"
        self.logger.info(f"Agent {self.agent_id} started and listening for messages")
    
    async def stop(self):
        """Stop the agent and cleanup resources."""
        await self.message_broker.disconnect()
        self.state.status = "stopped"
        self.logger.info(f"Agent {self.agent_id} stopped")
    
    async def handle_message(self, message: Message):
        """Handle incoming messages from other agents."""
        try:
            self.logger.info(f"Received message from {message.from_agent}: {message.message_type}")
            
            # Add to task queue
            self.task_queue.append(message)
            
            # Process if not currently busy
            if self.state.status == "idle":
                await self.process_next_task()
                
        except Exception as e:
            self.logger.error(f"Error handling message: {str(e)}")
            await self.send_error_message(message, str(e))
    
    async def process_next_task(self):
        """Process the next task in the queue."""
        if not self.task_queue:
            return
        
        message = self.task_queue.pop(0)
        self.state.status = "working"
        self.state.current_task = f"{message.message_type.value} from {message.from_agent.value}"
        
        try:
            await self.process_message(message)
        except Exception as e:
            self.logger.error(f"Error processing task: {str(e)}")
            await self.send_error_message(message, str(e))
        finally:
            self.state.status = "idle"
            self.state.current_task = None
            
            # Process next task if any
            if self.task_queue:
                await self.process_next_task()
    
    @abstractmethod
    async def process_message(self, message: Message):
        """Process a specific message. Must be implemented by subclasses."""
        pass
    
    async def send_message(
        self,
        to_agent: AgentType,
        message_type: MessageType,
        content: str,
        project_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        priority: Priority = Priority.MEDIUM
    ):
        """Send a message to another agent."""
        message = Message(
            id=str(uuid.uuid4()),
            from_agent=self.agent_type,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            project_id=project_id,
            metadata=metadata or {},
            priority=priority
        )
        
        await self.message_broker.publish(
            topic=f"agents/{to_agent.value}",
            message=message
        )
        
        self.logger.info(f"Sent {message_type.value} message to {to_agent.value}")
    
    async def send_error_message(self, original_message: Message, error: str):
        """Send an error message back to the sender."""
        await self.send_message(
            to_agent=original_message.from_agent,
            message_type=MessageType.ERROR,
            content=f"Error processing your {original_message.message_type.value}: {error}",
            project_id=original_message.project_id,
            metadata={"original_message_id": original_message.id},
            priority=Priority.HIGH
        )
    
    async def query_llm(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Query the LLM with the given prompt and context."""
        try:
            messages = []
            
            if system_message:
                messages.append(SystemMessage(content=system_message))
            
            # Add conversation history
            chat_history = self.memory.chat_memory.messages
            messages.extend(chat_history[-10:])  # Keep last 10 messages for context
            
            # Add current prompt with context
            if context:
                prompt_with_context = f"{prompt}\n\nContext: {json.dumps(context, indent=2)}"
            else:
                prompt_with_context = prompt
            
            messages.append(HumanMessage(content=prompt_with_context))
            
            # Get response from LLM
            response = await self.llm.agenerate([messages])
            result = response.generations[0][0].text
            
            # Save to memory
            self.memory.chat_memory.add_user_message(prompt_with_context)
            self.memory.chat_memory.add_ai_message(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error querying LLM: {str(e)}")
            raise
    
    async def create_artifact(
        self,
        project_id: str,
        artifact_type: str,
        name: str,
        content: str,
        file_path: Optional[str] = None
    ) -> ProjectArtifact:
        """Create a project artifact."""
        artifact = ProjectArtifact(
            id=str(uuid.uuid4()),
            project_id=project_id,
            artifact_type=artifact_type,
            name=name,
            content=content,
            file_path=file_path,
            created_by=self.agent_type
        )
        
        # Store artifact (in a real implementation, this would go to a database)
        self.logger.info(f"Created artifact: {artifact.name} ({artifact.artifact_type})")
        
        return artifact
    
    def get_agent_persona_prompt(self) -> str:
        """Get the agent-specific persona prompt. Should be overridden by subclasses."""
        return f"You are a {self.agent_type.value} agent in an enterprise software development ecosystem."
    
    async def get_status(self) -> AgentState:
        """Get current agent status."""
        self.state.last_activity = datetime.now()
        return self.state
