"""
MCP Server for the Agentic Ecosystem

This server implements the Model Context Protocol (MCP) for agent communication
and provides RESTful APIs for external system integration.
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from ..orchestrator.orchestrator_agent import OrchestratorAgent
from ..agents.ba_agent import BAAgent
from ..agents.architect_agent import ArchitectAgent
from ..agents.developer_agent import DeveloperAgent
from ..agents.tester_agent import TesterAgent
from ..models import (
    AgentType, Message, MessageType, Priority, ProjectSpecification, ProjectStatus
)
from ..utils import get_logger, configure_logging


# Configure logging
configure_logging()
logger = get_logger("mcp_server")


# Pydantic models for API
class ProjectCreateRequest(BaseModel):
    specification: str
    title: Optional[str] = None
    domain: Optional[str] = None


class ProjectCreateResponse(BaseModel):
    project_id: str
    status: str
    message: str


class ClarificationRequest(BaseModel):
    project_id: str
    clarification: str


class WebSocketMessage(BaseModel):
    type: str
    project_id: Optional[str] = None
    content: str
    timestamp: Optional[str] = None


class AgenticEcosystemMCPServer:
    """Main MCP Server for the Agentic Ecosystem."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="Agentic Ecosystem MCP Server",
            description="Model Context Protocol server for agent-based software development",
            version="1.0.0"
        )
        
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize agents
        self.agents: Dict[AgentType, Any] = {}
        self.orchestrator: Optional[OrchestratorAgent] = None
        
        # WebSocket connections
        self.websocket_connections: Dict[str, WebSocket] = {}
        
        # Setup routes
        self._setup_routes()
        
        logger.info("MCP Server initialized")
    
    async def start_agents(self):
        """Initialize and start all agents."""
        try:
            # Create agents
            self.orchestrator = OrchestratorAgent()
            self.agents[AgentType.ORCHESTRATOR] = self.orchestrator
            self.agents[AgentType.BA] = BAAgent()
            self.agents[AgentType.ARCHITECT] = ArchitectAgent()
            self.agents[AgentType.DEVELOPER] = DeveloperAgent()
            self.agents[AgentType.TESTER] = TesterAgent()
            
            # Start all agents
            for agent in self.agents.values():
                await agent.start()
            
            logger.info("All agents started successfully")
            
        except Exception as e:
            logger.error(f"Error starting agents: {str(e)}")
            raise
    
    async def stop_agents(self):
        """Stop all agents."""
        try:
            for agent in self.agents.values():
                await agent.stop()
            
            logger.info("All agents stopped")
            
        except Exception as e:
            logger.error(f"Error stopping agents: {str(e)}")
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/")
        async def root():
            return {
                "message": "Agentic Ecosystem MCP Server",
                "version": "1.0.0",
                "status": "running",
                "agents": list(self.agents.keys()) if self.agents else []
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            agent_statuses = {}
            if self.agents:
                for agent_type, agent in self.agents.items():
                    try:
                        status = await agent.get_status()
                        agent_statuses[agent_type.value] = {
                            "status": status.status,
                            "last_activity": status.last_activity.isoformat()
                        }
                    except Exception as e:
                        agent_statuses[agent_type.value] = {"status": "error", "error": str(e)}
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "agents": agent_statuses
            }
        
        @self.app.post("/projects", response_model=ProjectCreateResponse)
        async def create_project(request: ProjectCreateRequest):
            """Create a new project."""
            try:
                if not self.orchestrator:
                    raise HTTPException(status_code=503, detail="Orchestrator not available")
                
                project_id = await self.orchestrator.start_project(request.specification)
                
                return ProjectCreateResponse(
                    project_id=project_id,
                    status="created",
                    message="Project created successfully and analysis started"
                )
                
            except Exception as e:
                logger.error(f"Error creating project: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/projects/{project_id}")
        async def get_project_status(project_id: str):
            """Get project status."""
            try:
                if not self.orchestrator:
                    raise HTTPException(status_code=503, detail="Orchestrator not available")
                
                status = await self.orchestrator.get_project_status(project_id)
                if not status:
                    raise HTTPException(status_code=404, detail="Project not found")
                
                return {
                    "project_id": project_id,
                    "current_phase": status.current_phase,
                    "completion_percentage": status.completion_percentage,
                    "active_agents": [agent.value for agent in status.active_agents],
                    "next_actions": status.next_actions,
                    "issues": status.issues,
                    "last_updated": status.last_updated.isoformat()
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting project status: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/projects/{project_id}/clarifications")
        async def send_clarification(project_id: str, request: ClarificationRequest):
            """Send user clarification."""
            try:
                if not self.orchestrator:
                    raise HTTPException(status_code=503, detail="Orchestrator not available")
                
                success = await self.orchestrator.send_user_clarification(
                    project_id, request.clarification
                )
                
                if success:
                    return {"status": "success", "message": "Clarification sent successfully"}
                else:
                    raise HTTPException(status_code=400, detail="No pending clarification request found")
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error sending clarification: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/projects")
        async def list_projects():
            """List all projects."""
            try:
                if not self.orchestrator:
                    raise HTTPException(status_code=503, detail="Orchestrator not available")
                
                all_projects = await self.orchestrator.get_all_projects()
                
                projects_list = []
                for project_id, status in all_projects.items():
                    projects_list.append({
                        "project_id": project_id,
                        "current_phase": status.current_phase,
                        "completion_percentage": status.completion_percentage,
                        "last_updated": status.last_updated.isoformat()
                    })
                
                return {"projects": projects_list}
                
            except Exception as e:
                logger.error(f"Error listing projects: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/projects/{project_id}/workflow")
        async def get_project_workflow(project_id: str):
            """Get project workflow history."""
            try:
                if not self.orchestrator:
                    raise HTTPException(status_code=503, detail="Orchestrator not available")
                
                workflow = await self.orchestrator.get_project_workflow_history(project_id)
                
                workflow_data = []
                for message in workflow:
                    workflow_data.append({
                        "id": message.id,
                        "from_agent": message.from_agent.value,
                        "to_agent": message.to_agent.value,
                        "message_type": message.message_type.value,
                        "content": message.content[:200] + "..." if len(message.content) > 200 else message.content,
                        "timestamp": message.timestamp.isoformat(),
                        "metadata": message.metadata
                    })
                
                return {"workflow": workflow_data}
                
            except Exception as e:
                logger.error(f"Error getting project workflow: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.websocket_connections[client_id] = websocket
            
            try:
                while True:
                    # Receive messages from client
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    # Handle different message types
                    if message_data.get("type") == "subscribe_project":
                        project_id = message_data.get("project_id")
                        # Store subscription (in a real implementation)
                        await websocket.send_text(json.dumps({
                            "type": "subscription_confirmed",
                            "project_id": project_id,
                            "message": f"Subscribed to project {project_id} updates"
                        }))
                    
                    elif message_data.get("type") == "ping":
                        await websocket.send_text(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }))
                
            except WebSocketDisconnect:
                if client_id in self.websocket_connections:
                    del self.websocket_connections[client_id]
                logger.info(f"WebSocket client {client_id} disconnected")
            except Exception as e:
                logger.error(f"WebSocket error for client {client_id}: {str(e)}")
                if client_id in self.websocket_connections:
                    del self.websocket_connections[client_id]
        
        @self.app.get("/agents/{agent_type}/status")
        async def get_agent_status(agent_type: str):
            """Get status of a specific agent."""
            try:
                agent_enum = AgentType(agent_type)
                agent = self.agents.get(agent_enum)
                
                if not agent:
                    raise HTTPException(status_code=404, detail="Agent not found")
                
                status = await agent.get_status()
                return {
                    "agent_id": status.agent_id,
                    "agent_type": status.agent_type.value,
                    "status": status.status,
                    "current_task": status.current_task,
                    "assigned_projects": status.assigned_projects,
                    "last_activity": status.last_activity.isoformat()
                }
                
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid agent type")
            except Exception as e:
                logger.error(f"Error getting agent status: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def broadcast_to_websockets(self, message: Dict[str, Any]):
        """Broadcast message to all connected WebSocket clients."""
        disconnected_clients = []
        message_json = json.dumps(message)
        
        for client_id, websocket in self.websocket_connections.items():
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending to WebSocket client {client_id}: {str(e)}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            if client_id in self.websocket_connections:
                del self.websocket_connections[client_id]
    
    async def run(self):
        """Run the MCP server."""
        try:
            # Start agents first
            await self.start_agents()
            
            # Start the FastAPI server
            config = uvicorn.Config(
                app=self.app,
                host=self.host,
                port=self.port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            
            logger.info(f"Starting MCP server on {self.host}:{self.port}")
            await server.serve()
            
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Error running server: {str(e)}")
            raise
        finally:
            await self.stop_agents()


async def main():
    """Main entry point for the MCP server."""
    import os
    
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_SERVER_PORT", "8000"))
    
    server = AgenticEcosystemMCPServer(host=host, port=port)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
