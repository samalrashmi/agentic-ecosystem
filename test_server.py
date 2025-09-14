#!/usr/bin/env python3
"""
Simple test server for the Agentic Ecosystem.
Tests the enhanced agents and UI functionality.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from langgraph_agents.agent_tools import (
    analyze_business_requirements,
    design_system_architecture,
    generate_implementation_plan,
    create_test_strategy
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agentic Ecosystem Test Server")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class ProjectRequest(BaseModel):
    specification: str
    title: str
    domain: str = "web-application"

class WebSocketManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                self.disconnect(connection)

manager = WebSocketManager()

@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    """Serve the main UI."""
    with open("static/index.html", "r") as f:
        return HTMLResponse(f.read())

@app.post("/projects")
async def create_project(request: ProjectRequest):
    """Create a new project and start the agent workflow."""
    try:
        # Generate unique project ID
        project_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Creating project {project_id}: {request.title}")
        
        # Start the workflow in background
        asyncio.create_task(run_agent_workflow(project_id, request.specification))
        
        return JSONResponse({
            "project_id": project_id,
            "status": "created",
            "title": request.title,
            "message": "Project created successfully! Agents are starting work."
        })
        
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    logger.info(f"Client {client_id} connected")
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"Client {client_id} disconnected")

@app.get("/agents/health")
async def get_agent_health():
    """Get agent health status."""
    return JSONResponse({
        "status": "healthy",
        "agents": {
            "orchestrator": {"status": "idle", "is_healthy": True},
            "ba": {"status": "idle", "is_healthy": True},
            "architect": {"status": "idle", "is_healthy": True},
            "developer": {"status": "idle", "is_healthy": True},
            "tester": {"status": "idle", "is_healthy": True}
        }
    })

async def run_agent_workflow(project_id: str, specification: str):
    """Run the complete agent workflow with real-time status updates."""
    try:
        logger.info(f"Starting workflow for project {project_id}")
        
        # Stage 1: Business Analysis
        await manager.send_message({
            "type": "workflow_update",
            "stage": "requirements_analysis",
            "project_id": project_id
        })
        
        logger.info("Running business analysis...")
        requirements = analyze_business_requirements.invoke({
            "specification": specification,
            "project_id": project_id
        })
        
        await asyncio.sleep(2)  # Simulate processing time
        
        # Stage 2: Architecture Design
        await manager.send_message({
            "type": "workflow_update",
            "stage": "architecture_design",
            "project_id": project_id
        })
        
        logger.info("Running architecture design...")
        architecture = design_system_architecture.invoke({
            "user_stories": str(requirements),
            "project_id": project_id,
            "requirements": ""
        })
        
        await asyncio.sleep(3)  # Simulate processing time
        
        # Stage 3: Implementation Planning
        await manager.send_message({
            "type": "workflow_update",
            "stage": "development",
            "project_id": project_id
        })
        
        logger.info("Running implementation planning...")
        implementation = generate_implementation_plan.invoke({
            "architecture": str(architecture),
            "project_id": project_id
        })
        
        await asyncio.sleep(4)  # Simulate processing time
        
        # Stage 4: Testing Strategy
        await manager.send_message({
            "type": "workflow_update", 
            "stage": "testing",
            "project_id": project_id
        })
        
        logger.info("Running test strategy creation...")
        test_strategy = create_test_strategy.invoke({
            "implementation_plan": str(implementation),
            "project_id": project_id
        })
        
        await asyncio.sleep(2)  # Simulate processing time
        
        # Stage 5: Completion
        await manager.send_message({
            "type": "workflow_update",
            "stage": "completed",
            "project_id": project_id
        })
        
        logger.info(f"Workflow completed for project {project_id}")
        
        # Send completion notification
        await manager.send_message({
            "type": "project_completed",
            "project_id": project_id,
            "artifacts": {
                "requirements": len(requirements.get("functional_requirements", [])),
                "architecture": architecture.get("technology_used", "Unknown"),
                "implementation": len(implementation.get("implementation_phases", [])),
                "testing": len(test_strategy.get("test_categories", []))
            }
        })
        
    except Exception as e:
        logger.error(f"Workflow error for project {project_id}: {e}")
        await manager.send_message({
            "type": "error",
            "project_id": project_id,
            "message": str(e)
        })

@app.get("/projects/{project_id}/status")
async def get_project_status(project_id: str):
    """Get project status and artifacts."""
    try:
        # Check if project exists in output directory
        project_dir = Path("out") / f"project_{project_id}"
        
        if not project_dir.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # List available artifacts
        artifacts = []
        for file in project_dir.glob("*.json"):
            artifacts.append({
                "name": file.stem,
                "type": file.stem.split("_")[0],
                "created": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            })
        
        return JSONResponse({
            "project_id": project_id,
            "status": "completed" if artifacts else "in_progress",
            "artifacts": artifacts,
            "artifact_count": len(artifacts)
        })
        
    except Exception as e:
        logger.error(f"Error getting project status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting Agentic Ecosystem Test Server...")
    print("📡 Enhanced LLM-powered agents with real-time status tracking")
    print("🎯 Features: Business Analysis → Architecture → Development → Testing")
    print()
    print("🌐 Server will be available at: http://localhost:8000")
    print("📊 Real-time WebSocket updates enabled")
    print("💾 Project artifacts saved to /out directory")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
