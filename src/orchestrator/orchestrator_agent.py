import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from .base_agent import BaseAgent
from ..models import (
    AgentType, Message, MessageType, Priority, ProjectSpecification,
    ProjectStatus, AgentState
)


class OrchestratorAgent(BaseAgent):
    """Orchestrator Agent responsible for coordinating all agents and managing project workflow."""
    
    def __init__(self, agent_id: str = None, **kwargs):
        super().__init__(
            agent_id=agent_id or "orchestrator_agent_001",
            agent_type=AgentType.ORCHESTRATOR,
            **kwargs
        )
        
        # Orchestrator-specific attributes
        self.projects: Dict[str, ProjectSpecification] = {}
        self.project_statuses: Dict[str, ProjectStatus] = {}
        self.agent_states: Dict[AgentType, AgentState] = {}
        self.workflow_history: Dict[str, List[Message]] = {}
        self.user_sessions: Dict[str, str] = {}  # session_id -> project_id
    
    def get_agent_persona_prompt(self) -> str:
        """Get the Orchestrator agent persona prompt."""
        return """You are the Orchestrator Agent in an enterprise software development ecosystem.

Your responsibilities include:
1. Receiving user specifications and initiating projects
2. Coordinating communication between BA, Architect, Developer, and Tester agents
3. Managing project workflows and ensuring proper sequence of activities
4. Monitoring agent states and project progress
5. Handling user interactions and clarification requests
6. Providing project status updates and final delivery
7. Managing error conditions and workflow recovery

You have comprehensive oversight of:
- Project lifecycle management
- Agent coordination and communication patterns
- Workflow state management
- User interaction handling
- Quality assurance throughout the process
- Final project delivery and sign-off

Always maintain project coherence, ensure proper communication flow between agents, and provide clear status updates to users."""
    
    async def process_message(self, message: Message):
        """Process incoming messages based on type and sender."""
        try:
            # Record message in workflow history
            if message.project_id not in self.workflow_history:
                self.workflow_history[message.project_id] = []
            self.workflow_history[message.project_id].append(message)
            
            if message.message_type == MessageType.SPECIFICATION:
                await self._handle_user_specification(message)
            elif message.message_type == MessageType.QUERY:
                await self._handle_agent_query(message)
            elif message.message_type == MessageType.STATUS:
                await self._handle_status_update(message)
            elif message.message_type == MessageType.ERROR:
                await self._handle_error(message)
            elif message.message_type == MessageType.RESPONSE:
                await self._handle_response(message)
            else:
                self.logger.warning(f"Unhandled message type: {message.message_type} from {message.from_agent}")
        
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            await self._handle_orchestrator_error(message, str(e))
    
    async def _handle_user_specification(self, message: Message):
        """Handle initial user specification and start the project workflow."""
        try:
            # Create new project
            project_spec = ProjectSpecification(
                id=message.project_id,
                title=f"Project {message.project_id}",
                description=message.content,
                domain=self._determine_initial_domain(message.content)
            )
            
            self.projects[message.project_id] = project_spec
            
            # Initialize project status
            project_status = ProjectStatus(
                project_id=message.project_id,
                current_phase="requirements_analysis",
                completion_percentage=0.0,
                active_agents=[AgentType.BA],
                next_actions=["BA Agent analyzing requirements"]
            )
            
            self.project_statuses[message.project_id] = project_status
            
            # Send specification to BA Agent
            await self.send_message(
                to_agent=AgentType.BA,
                message_type=MessageType.SPECIFICATION,
                content=message.content,
                project_id=message.project_id,
                metadata={"initiated_by": "user", "orchestrator_id": self.agent_id}
            )
            
            # Send confirmation to user (via API response or WebSocket)
            await self._notify_user(
                message.project_id,
                f"Project {message.project_id} initiated successfully. BA Agent is analyzing your requirements."
            )
            
            self.logger.info(f"Project {message.project_id} workflow initiated")
            
        except Exception as e:
            self.logger.error(f"Error handling user specification: {str(e)}")
            await self._notify_user(message.project_id, f"Error starting project: {str(e)}")
    
    async def _handle_agent_query(self, message: Message):
        """Handle queries from agents that need user input."""
        try:
            if message.from_agent == AgentType.BA:
                # BA agent needs clarification from user
                await self._handle_ba_clarification_request(message)
            elif message.from_agent == AgentType.ARCHITECT:
                # Architect agent needs clarification
                await self._handle_architect_clarification_request(message)
            elif message.from_agent == AgentType.DEVELOPER:
                # Developer agent needs clarification
                await self._handle_developer_clarification_request(message)
            elif message.from_agent == AgentType.TESTER:
                # Tester agent needs clarification
                await self._handle_tester_clarification_request(message)
            
            # Update project status
            await self._update_project_status(
                message.project_id,
                current_phase="awaiting_clarification",
                next_actions=[f"Waiting for user response to {message.from_agent.value} agent query"]
            )
            
        except Exception as e:
            self.logger.error(f"Error handling agent query: {str(e)}")
    
    async def _handle_ba_clarification_request(self, message: Message):
        """Handle clarification requests from BA agent."""
        user_message = f"""
        The Business Analyst needs some clarifications about your requirements:

        {message.content}

        Please provide detailed answers so we can proceed with the analysis.
        """
        
        await self._notify_user(message.project_id, user_message)
        
        # Store pending clarification
        metadata = message.metadata
        metadata["pending_clarification"] = True
        metadata["clarification_type"] = "requirements"
    
    async def _handle_architect_clarification_request(self, message: Message):
        """Handle clarification requests from Architect agent."""
        user_message = f"""
        The System Architect needs technical clarifications:

        {message.content}

        Please provide the requested technical details.
        """
        
        await self._notify_user(message.project_id, user_message)
    
    async def _handle_developer_clarification_request(self, message: Message):
        """Handle clarification requests from Developer agent."""
        user_message = f"""
        The Developer needs technical clarifications for implementation:

        {message.content}

        Please provide the implementation details requested.
        """
        
        await self._notify_user(message.project_id, user_message)
    
    async def _handle_tester_clarification_request(self, message: Message):
        """Handle clarification requests from Tester agent."""
        user_message = f"""
        The QA Tester needs clarifications about testing requirements:

        {message.content}

        Please provide the testing details requested.
        """
        
        await self._notify_user(message.project_id, user_message)
    
    async def _handle_status_update(self, message: Message):
        """Handle status updates from agents."""
        try:
            project_id = message.project_id
            from_agent = message.from_agent
            
            # Update project status based on the agent update
            if from_agent == AgentType.BA:
                await self._handle_ba_status_update(message)
            elif from_agent == AgentType.ARCHITECT:
                await self._handle_architect_status_update(message)
            elif from_agent == AgentType.DEVELOPER:
                await self._handle_developer_status_update(message)
            elif from_agent == AgentType.TESTER:
                await self._handle_tester_status_update(message)
            
            # Notify user of progress
            await self._notify_user_of_progress(message)
            
        except Exception as e:
            self.logger.error(f"Error handling status update: {str(e)}")
    
    async def _handle_ba_status_update(self, message: Message):
        """Handle status updates from BA agent."""
        metadata = message.metadata
        phase = metadata.get("phase", "unknown")
        
        if phase == "test_preparation_complete":
            await self._update_project_status(
                message.project_id,
                current_phase="test_preparation",
                completion_percentage=20.0,
                active_agents=[AgentType.TESTER],
                next_actions=["QA Agent preparing test cases"]
            )
        elif phase == "development_complete":
            await self._update_project_status(
                message.project_id,
                current_phase="qa_testing",
                completion_percentage=70.0,
                active_agents=[AgentType.TESTER],
                next_actions=["QA Agent testing application"]
            )
    
    async def _handle_architect_status_update(self, message: Message):
        """Handle status updates from Architect agent."""
        await self._update_project_status(
            message.project_id,
            current_phase="architecture_design",
            completion_percentage=30.0,
            active_agents=[AgentType.ARCHITECT, AgentType.BA],
            next_actions=["BA Agent reviewing architecture design"]
        )
    
    async def _handle_developer_status_update(self, message: Message):
        """Handle status updates from Developer agent."""
        metadata = message.metadata
        phase = metadata.get("phase", "unknown")
        
        if phase == "development_complete":
            await self._update_project_status(
                message.project_id,
                current_phase="development_complete",
                completion_percentage=60.0,
                active_agents=[AgentType.TESTER],
                next_actions=["QA Agent testing developed application"]
            )
    
    async def _handle_tester_status_update(self, message: Message):
        """Handle status updates from Tester agent."""
        metadata = message.metadata
        qa_signoff = metadata.get("qa_signoff", False)
        
        if qa_signoff:
            await self._handle_project_completion(message)
        else:
            await self._update_project_status(
                message.project_id,
                current_phase="qa_review",
                completion_percentage=85.0,
                active_agents=[AgentType.DEVELOPER],
                next_actions=["Developer fixing issues identified by QA"]
            )
    
    async def _handle_project_completion(self, message: Message):
        """Handle project completion and final delivery."""
        try:
            project_id = message.project_id
            
            # Update project status to completed
            await self._update_project_status(
                project_id,
                current_phase="completed",
                completion_percentage=100.0,
                active_agents=[],
                next_actions=["Project completed and ready for deployment"]
            )
            
            # Generate final project summary
            final_summary = await self._generate_final_project_summary(project_id)
            
            # Notify user of completion
            completion_message = f"""
            🎉 Project {project_id} Completed Successfully!

            {final_summary}

            Your application has been developed, tested, and is ready for deployment.
            All artifacts and documentation have been generated and are available for download.
            """
            
            await self._notify_user(project_id, completion_message)
            
            self.logger.info(f"Project {project_id} completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error handling project completion: {str(e)}")
    
    async def _generate_final_project_summary(self, project_id: str) -> str:
        """Generate a comprehensive project summary."""
        try:
            project_spec = self.projects.get(project_id)
            workflow_messages = self.workflow_history.get(project_id, [])
            
            summary_prompt = f"""
            Generate a comprehensive project completion summary:
            
            Project: {project_spec.title if project_spec else project_id}
            Description: {project_spec.description if project_spec else 'N/A'}
            Workflow Messages: {len(workflow_messages)} agent interactions
            
            Create a summary covering:
            1. Project objectives and requirements
            2. Architecture decisions made
            3. Development approach and technologies used
            4. Testing coverage and quality assurance
            5. Final deliverables
            6. Deployment readiness
            
            Keep it concise but comprehensive for executive summary.
            """
            
            system_message = self.get_agent_persona_prompt()
            summary = await self.query_llm(summary_prompt, system_message)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating project summary: {str(e)}")
            return f"Project {project_id} completed with {len(self.workflow_history.get(project_id, []))} agent interactions."
    
    async def _handle_error(self, message: Message):
        """Handle error messages from agents."""
        try:
            error_details = f"""
            Error in Project {message.project_id}:
            
            Agent: {message.from_agent.value}
            Error: {message.content}
            
            The system is attempting to recover from this error.
            """
            
            await self._notify_user(message.project_id, error_details)
            
            # Update project status to indicate error state
            await self._update_project_status(
                message.project_id,
                current_phase="error_recovery",
                next_actions=[f"Recovering from {message.from_agent.value} agent error"]
            )
            
            # Attempt error recovery
            await self._attempt_error_recovery(message)
            
        except Exception as e:
            self.logger.error(f"Error handling agent error: {str(e)}")
    
    async def _attempt_error_recovery(self, error_message: Message):
        """Attempt to recover from agent errors."""
        try:
            recovery_strategies = {
                AgentType.BA: self._recover_ba_error,
                AgentType.ARCHITECT: self._recover_architect_error,
                AgentType.DEVELOPER: self._recover_developer_error,
                AgentType.TESTER: self._recover_tester_error
            }
            
            recovery_func = recovery_strategies.get(error_message.from_agent)
            if recovery_func:
                await recovery_func(error_message)
            else:
                # Generic recovery - restart the workflow from the last stable state
                await self._restart_workflow_from_last_stable_state(error_message.project_id)
            
        except Exception as e:
            self.logger.error(f"Error in recovery attempt: {str(e)}")
            await self._escalate_error(error_message.project_id, str(e))
    
    async def _recover_ba_error(self, error_message: Message):
        """Recover from BA agent errors."""
        # Try to reinitialize BA agent with simplified requirements
        simplified_spec = f"Simplified version of original specification for project {error_message.project_id}"
        
        await self.send_message(
            to_agent=AgentType.BA,
            message_type=MessageType.SPECIFICATION,
            content=simplified_spec,
            project_id=error_message.project_id,
            metadata={"recovery_attempt": True, "original_error": error_message.content}
        )
    
    async def _recover_architect_error(self, error_message: Message):
        """Recover from Architect agent errors."""
        # Request simplified architecture
        recovery_request = f"Please provide a simplified architecture design for project {error_message.project_id}"
        
        await self.send_message(
            to_agent=AgentType.ARCHITECT,
            message_type=MessageType.SPECIFICATION,
            content=recovery_request,
            project_id=error_message.project_id,
            metadata={"recovery_attempt": True}
        )
    
    async def _recover_developer_error(self, error_message: Message):
        """Recover from Developer agent errors."""
        # Request simplified implementation
        recovery_request = f"Please implement a simplified version for project {error_message.project_id}"
        
        await self.send_message(
            to_agent=AgentType.DEVELOPER,
            message_type=MessageType.SPECIFICATION,
            content=recovery_request,
            project_id=error_message.project_id,
            metadata={"recovery_attempt": True}
        )
    
    async def _recover_tester_error(self, error_message: Message):
        """Recover from Tester agent errors."""
        # Request simplified testing
        recovery_request = f"Please perform basic testing for project {error_message.project_id}"
        
        await self.send_message(
            to_agent=AgentType.TESTER,
            message_type=MessageType.SPECIFICATION,
            content=recovery_request,
            project_id=error_message.project_id,
            metadata={"recovery_attempt": True}
        )
    
    async def _escalate_error(self, project_id: str, error_details: str):
        """Escalate unrecoverable errors to user."""
        escalation_message = f"""
        ⚠️ Critical Error in Project {project_id}
        
        The system encountered an unrecoverable error and cannot continue automatically.
        
        Error Details: {error_details}
        
        Please review the project requirements and restart the project if needed.
        Support has been notified of this issue.
        """
        
        await self._notify_user(project_id, escalation_message)
        
        # Update project status to failed
        await self._update_project_status(
            project_id,
            current_phase="failed",
            completion_percentage=0.0,
            active_agents=[],
            next_actions=["Manual intervention required"],
            issues=[f"Critical error: {error_details}"]
        )
    
    async def _handle_response(self, message: Message):
        """Handle responses from agents."""
        # Route responses appropriately
        if message.metadata.get("clarification_response"):
            # This is a response to user clarification - forward to the original requesting agent
            original_requester = message.metadata.get("original_requester", AgentType.BA)
            
            await self.send_message(
                to_agent=original_requester,
                message_type=MessageType.RESPONSE,
                content=message.content,
                project_id=message.project_id,
                metadata={"user_clarification": True}
            )
    
    async def _update_project_status(
        self,
        project_id: str,
        current_phase: Optional[str] = None,
        completion_percentage: Optional[float] = None,
        active_agents: Optional[List[AgentType]] = None,
        next_actions: Optional[List[str]] = None,
        issues: Optional[List[str]] = None
    ):
        """Update project status."""
        try:
            if project_id not in self.project_statuses:
                self.project_statuses[project_id] = ProjectStatus(
                    project_id=project_id,
                    current_phase="unknown",
                    completion_percentage=0.0,
                    active_agents=[],
                    next_actions=[]
                )
            
            status = self.project_statuses[project_id]
            
            if current_phase:
                status.current_phase = current_phase
            if completion_percentage is not None:
                status.completion_percentage = completion_percentage
            if active_agents is not None:
                status.active_agents = active_agents
            if next_actions is not None:
                status.next_actions = next_actions
            if issues is not None:
                status.issues.extend(issues)
            
            status.last_updated = datetime.now()
            
            self.logger.info(f"Updated project {project_id} status: {current_phase} ({completion_percentage}%)")
            
        except Exception as e:
            self.logger.error(f"Error updating project status: {str(e)}")
    
    async def _notify_user(self, project_id: str, message: str):
        """Notify user of project updates (via WebSocket, API, etc.)."""
        try:
            # In a real implementation, this would send via WebSocket or store for API retrieval
            notification = {
                "project_id": project_id,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "type": "project_update"
            }
            
            self.logger.info(f"User notification for project {project_id}: {message[:100]}...")
            
            # Store notification for API retrieval
            # In a real implementation, this would go to a database or message queue
            
        except Exception as e:
            self.logger.error(f"Error notifying user: {str(e)}")
    
    async def _notify_user_of_progress(self, status_message: Message):
        """Notify user of project progress based on agent status updates."""
        project_id = status_message.project_id
        from_agent = status_message.from_agent.value
        
        progress_message = f"""
        📊 Project Progress Update
        
        Agent: {from_agent}
        Update: {status_message.content}
        
        Current Status: {self.project_statuses.get(project_id, ProjectStatus(project_id=project_id, current_phase='unknown', completion_percentage=0.0, active_agents=[], next_actions=[])).current_phase}
        Progress: {self.project_statuses.get(project_id, ProjectStatus(project_id=project_id, current_phase='unknown', completion_percentage=0.0, active_agents=[], next_actions=[])).completion_percentage}%
        """
        
        await self._notify_user(project_id, progress_message)
    
    def _determine_initial_domain(self, specification: str) -> str:
        """Determine initial project domain from specification."""
        spec_lower = specification.lower()
        
        if any(keyword in spec_lower for keyword in ["bank", "finance", "payment", "trading"]):
            return "financial"
        elif any(keyword in spec_lower for keyword in ["manufactur", "factory", "production"]):
            return "manufacturing"
        elif any(keyword in spec_lower for keyword in ["health", "medical", "hospital"]):
            return "healthcare"
        elif any(keyword in spec_lower for keyword in ["ecommerce", "shop", "retail"]):
            return "ecommerce"
        elif any(keyword in spec_lower for keyword in ["education", "school", "student"]):
            return "education"
        elif any(keyword in spec_lower for keyword in ["logistics", "shipping", "delivery"]):
            return "logistics"
        else:
            return "general"
    
    async def _restart_workflow_from_last_stable_state(self, project_id: str):
        """Restart workflow from the last stable state."""
        try:
            # Find the last successful state in workflow history
            workflow = self.workflow_history.get(project_id, [])
            
            # For simplicity, restart from BA agent
            if project_id in self.projects:
                project_spec = self.projects[project_id]
                
                await self.send_message(
                    to_agent=AgentType.BA,
                    message_type=MessageType.SPECIFICATION,
                    content=project_spec.description,
                    project_id=project_id,
                    metadata={"workflow_restart": True}
                )
                
                await self._update_project_status(
                    project_id,
                    current_phase="workflow_restart",
                    next_actions=["Restarting workflow from requirements analysis"]
                )
        
        except Exception as e:
            self.logger.error(f"Error restarting workflow: {str(e)}")
            await self._escalate_error(project_id, f"Workflow restart failed: {str(e)}")
    
    async def _handle_orchestrator_error(self, original_message: Message, error: str):
        """Handle errors in the orchestrator itself."""
        self.logger.error(f"Orchestrator error: {error}")
        
        error_notification = f"""
        🚨 System Error
        
        The orchestrator encountered an error while processing your request.
        Error: {error}
        
        Please try again or contact support if the issue persists.
        """
        
        await self._notify_user(original_message.project_id, error_notification)
    
    # Public API methods for external interaction
    
    async def start_project(self, user_specification: str, session_id: Optional[str] = None) -> str:
        """Start a new project from user specification."""
        project_id = str(uuid.uuid4())
        
        if session_id:
            self.user_sessions[session_id] = project_id
        
        # Create and send specification message
        spec_message = Message(
            id=str(uuid.uuid4()),
            from_agent=AgentType.ORCHESTRATOR,  # Representing user input
            to_agent=AgentType.ORCHESTRATOR,
            message_type=MessageType.SPECIFICATION,
            content=user_specification,
            project_id=project_id
        )
        
        await self.process_message(spec_message)
        return project_id
    
    async def send_user_clarification(self, project_id: str, clarification: str) -> bool:
        """Send user clarification response."""
        try:
            clarification_message = Message(
                id=str(uuid.uuid4()),
                from_agent=AgentType.ORCHESTRATOR,  # Representing user
                to_agent=AgentType.ORCHESTRATOR,
                message_type=MessageType.RESPONSE,
                content=clarification,
                project_id=project_id,
                metadata={"user_clarification": True}
            )
            
            # Find which agent needs the clarification and forward it
            workflow = self.workflow_history.get(project_id, [])
            pending_queries = [msg for msg in workflow if msg.message_type == MessageType.QUERY and not msg.metadata.get("resolved", False)]
            
            if pending_queries:
                latest_query = pending_queries[-1]
                requesting_agent = latest_query.from_agent
                
                await self.send_message(
                    to_agent=requesting_agent,
                    message_type=MessageType.RESPONSE,
                    content=clarification,
                    project_id=project_id,
                    metadata={"user_clarification": True, "original_query_id": latest_query.id}
                )
                
                # Mark query as resolved
                latest_query.metadata["resolved"] = True
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error sending user clarification: {str(e)}")
            return False
    
    async def get_project_status(self, project_id: str) -> Optional[ProjectStatus]:
        """Get current project status."""
        return self.project_statuses.get(project_id)
    
    async def get_all_projects(self) -> Dict[str, ProjectStatus]:
        """Get status of all projects."""
        return self.project_statuses.copy()
    
    async def get_project_workflow_history(self, project_id: str) -> List[Message]:
        """Get workflow history for a project."""
        return self.workflow_history.get(project_id, [])
