"""
FastAPI Web Server for Agentic Ecosystem UI

This module provides a web interface for interacting with the 
agentic ecosystem through the enhanced MCP server.
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from fastapi import FastAPI, WebSocket, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Import the enhanced MCP server and workflow
import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from langgraph_agents.enhanced_mcp_server import ProjectManager
from langgraph_agents.workflow import SoftwareDevelopmentWorkflow

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agentic Ecosystem Web Interface", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global state
project_manager = ProjectManager()
active_connections: Dict[str, WebSocket] = {}
active_workflows: Dict[str, asyncio.Task] = {}

# Pydantic models
class ProjectRequest(BaseModel):
    title: str
    specification: str
    domain: Optional[str] = "web-application"

class ProjectResponse(BaseModel):
    project_id: str
    status: str
    message: str

class BAOnlyRequest(BaseModel):
    title: str
    requirements: str
    export_format: Optional[str] = "markdown"

class BAOnlyResponse(BaseModel):
    project_id: str
    specification: Dict[str, Any]
    token_count: int
    export_url: str
    timestamp: str
    status: str
    saved_files: List[str] = []
    output_directory: Optional[str] = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: dict):
        disconnected_clients = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

manager = ConnectionManager()

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    try:
        html_path = Path(__file__).parent.parent / "static" / "index.html"
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error loading page: {str(e)}</h1>", status_code=500)

@app.get("/agents/health")
async def agents_health():
    """Get the health status of all agents."""
    return JSONResponse({
        "status": "healthy",
        "agents": {
            "ba_agent": {"status": "idle", "message": "Ready to analyze requirements"},
            "architect_agent": {"status": "idle", "message": "Ready to design architecture"},
            "developer_agent": {"status": "idle", "message": "Ready to implement code"},
            "tester_agent": {"status": "idle", "message": "Ready to create tests"},
            "orchestrator_agent": {"status": "idle", "message": "Ready to coordinate"}
        }
    })

@app.post("/projects", response_model=ProjectResponse)
async def create_project(project: ProjectRequest):
    """Create a new project and start the workflow."""
    try:
        # Generate project ID
        project_id = str(uuid.uuid4())
        
        # Create project in project manager
        await project_manager.create_project(
            project_id=project_id,
            title=project.title,
            specification=project.specification
        )
        
        # Start the workflow in the background
        asyncio.create_task(run_workflow_background(project_id, project.specification))
        
        # Broadcast project creation
        await manager.broadcast({
            "type": "project_created",
            "project_id": project_id,
            "title": project.title,
            "status": "started"
        })
        
        return ProjectResponse(
            project_id=project_id,
            status="created",
            message="Project created successfully"
        )
        
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}")
async def get_project_status(project_id: str):
    """Get the status of a specific project."""
    try:
        status = await project_manager.get_project_status(project_id)
        return JSONResponse(status)
    except Exception as e:
        logger.error(f"Error getting project status: {e}")
        raise HTTPException(status_code=404, detail="Project not found")

@app.get("/projects")
async def list_projects():
    """List all projects."""
    try:
        projects = await project_manager.list_projects()
        return JSONResponse({"projects": projects})
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}/artifacts")
async def get_project_artifacts(project_id: str):
    """Get artifacts for a specific project."""
    try:
        # Check if project exists
        project = await project_manager.get_project_status(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get project artifacts from the file system
        project_dir = Path(__file__).parent.parent / "out" / f"project_{project_id}"
        artifacts_list = []
        
        if project_dir.exists():
            # Look for all types of artifact files
            artifact_patterns = ["*.md", "*.json", "*.py", "*.html", "*.css", "*.js", "*.txt", "*.yaml", "*.yml"]
            
            for pattern in artifact_patterns:
                for artifact_file in project_dir.glob(pattern):
                    if artifact_file.name != "project_summary.json":  # Skip internal files
                        try:
                            file_stats = artifact_file.stat()
                            
                            # Determine artifact type and title
                            file_ext = artifact_file.suffix.lower()
                            if "architecture" in artifact_file.name.lower():
                                artifact_type = "Architecture Design"
                                title = "System Architecture Document"
                            elif "requirements" in artifact_file.name.lower() or "ba_" in artifact_file.name.lower():
                                artifact_type = "Business Analysis"
                                title = "Requirements & User Stories"
                            elif "test" in artifact_file.name.lower():
                                artifact_type = "Test Strategy"
                                title = "Test Cases & QA Report"
                            elif file_ext in ['.py', '.js', '.html', '.css']:
                                artifact_type = "Source Code"
                                title = f"Implementation - {artifact_file.name}"
                            elif file_ext in ['.md']:
                                artifact_type = "Documentation"
                                title = f"Documentation - {artifact_file.stem.replace('_', ' ').title()}"
                            else:
                                artifact_type = "Other"
                                title = artifact_file.name
                            
                            artifacts_list.append({
                                "id": artifact_file.stem,
                                "name": artifact_file.name,
                                "title": title,
                                "type": artifact_type,
                                "size": f"{file_stats.st_size / 1024:.1f} KB",
                                "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                                "path": str(artifact_file.relative_to(project_dir)),
                                "download_url": f"/projects/{project_id}/artifacts/{artifact_file.stem}/download",
                                "view_url": f"/projects/{project_id}/artifacts/{artifact_file.stem}/view"
                            })
                        except Exception as e:
                            logger.error(f"Error processing artifact {artifact_file}: {e}")
        
        return JSONResponse({
            "project_id": project_id,
            "artifacts": artifacts_list,
            "total_count": len(artifacts_list),
            "project_folder": f"/out/project_{project_id}"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project artifacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}/artifacts/{artifact_id}/view")
async def view_artifact(project_id: str, artifact_id: str):
    """View the content of a specific artifact."""
    try:
        project_dir = Path(__file__).parent.parent / "out" / f"project_{project_id}"
        
        # Find the artifact file (try different extensions)
        artifact_file = None
        for pattern in ["*.md", "*.json", "*.py", "*.html", "*.css", "*.js", "*.txt", "*.yaml", "*.yml"]:
            potential_files = list(project_dir.glob(f"{artifact_id}.*"))
            if potential_files:
                artifact_file = potential_files[0]
                break
        
        if not artifact_file or not artifact_file.exists():
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        # Read and return the content
        with open(artifact_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Determine content type
        file_ext = artifact_file.suffix.lower()
        if file_ext == '.json':
            content_type = "application/json"
        elif file_ext in ['.html']:
            content_type = "text/html"
        elif file_ext in ['.css']:
            content_type = "text/css"
        elif file_ext in ['.js']:
            content_type = "application/javascript"
        else:
            content_type = "text/plain"
        
        return HTMLResponse(
            content=f"<pre style='white-space: pre-wrap; font-family: monospace; padding: 20px;'>{content}</pre>",
            headers={"Content-Type": "text/html"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing artifact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}/artifacts/{artifact_id}/download")
async def download_artifact(project_id: str, artifact_id: str):
    """Download a specific artifact."""
    try:
        project_dir = Path(__file__).parent.parent / "out" / f"project_{project_id}"
        
        # Find the artifact file
        artifact_file = None
        for pattern in ["*.md", "*.json", "*.py", "*.html", "*.css", "*.js", "*.txt", "*.yaml", "*.yml"]:
            potential_files = list(project_dir.glob(f"{artifact_id}.*"))
            if potential_files:
                artifact_file = potential_files[0]
                break
        
        if not artifact_file or not artifact_file.exists():
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        return FileResponse(
            path=str(artifact_file),
            filename=artifact_file.name,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading artifact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# BA-only mode endpoints
@app.post("/ba/specification", response_model=BAOnlyResponse)
async def generate_ba_specification(request: BAOnlyRequest):
    """Generate functional specification using BA agent only."""
    try:
        # Import and initialize the standalone BA service
        from ba_service import get_ba_service
        
        ba_service = get_ba_service()
        
        # Generate the specification
        result = await ba_service.generate_standalone_specification(
            requirements=request.requirements,
            project_title=request.title
        )
        
        # Store the result for export
        project_id = result["project_id"]
        
        return BAOnlyResponse(
            project_id=project_id,
            specification=result["specification"],
            token_count=result["token_count"],
            export_url=f"/ba/specification/{project_id}/export?format={request.export_format}",
            timestamp=result["specification"]["timestamp"],
            status=result["status"],
            saved_files=result.get("saved_files", []),
            output_directory=result.get("output_directory")
        )
        
    except Exception as e:
        logger.error(f"Error generating BA specification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ba/specification/{project_id}/export")
async def export_ba_specification(project_id: str, format: str = "markdown"):
    """Export the BA specification in the requested format."""
    try:
        # Import and initialize the standalone BA service
        from ba_service import get_ba_service
        
        ba_service = get_ba_service()
        
        # Export the specification
        content = await ba_service.export_specification_document(project_id, format)
        
        if format.lower() == "markdown":
            return HTMLResponse(
                content=f"<pre>{content}</pre>",
                headers={"Content-Disposition": f"attachment; filename=specification_{project_id}.md"}
            )
        elif format.lower() == "json":
            return JSONResponse(
                content=json.loads(content),
                headers={"Content-Disposition": f"attachment; filename=specification_{project_id}.json"}
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
            
    except Exception as e:
        logger.error(f"Error exporting BA specification: {e}")
        raise HTTPException(status_code=404, detail="Specification not found")

@app.post("/ba/specification/stream")
async def generate_ba_specification_stream(request: BAOnlyRequest):
    """Generate functional specification with real-time progress updates."""
    try:
        from ba_service import get_ba_service
        from fastapi.responses import StreamingResponse
        import asyncio
        import json
        
        ba_service = get_ba_service()
        
        # Store progress updates and final result
        progress_updates = []
        final_result = None
        generation_complete = False
        generation_error = None
        
        async def progress_callback(message: str):
            progress_updates.append({
                "type": "progress",
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
        
        async def run_generation():
            nonlocal final_result, generation_complete, generation_error
            try:
                result = await ba_service.generate_standalone_specification(
                    requirements=request.requirements,
                    project_title=request.title,
                    progress_callback=progress_callback
                )
                final_result = result
                generation_complete = True
            except Exception as e:
                generation_error = str(e)
                generation_complete = True
        
        async def event_stream():
            # Start the generation task
            generation_task = asyncio.create_task(run_generation())
            
            last_sent = 0
            
            while not generation_complete:
                # Send new progress updates
                if len(progress_updates) > last_sent:
                    for i in range(last_sent, len(progress_updates)):
                        yield f"data: {json.dumps(progress_updates[i])}\n\n"
                    last_sent = len(progress_updates)
                
                await asyncio.sleep(0.1)
            
            # Wait for generation to complete
            await generation_task
            
            # Send final result or error
            if generation_error:
                yield f"data: {json.dumps({'type': 'error', 'message': generation_error})}\n\n"
            elif final_result:
                yield f"data: {json.dumps({'type': 'complete', 'result': final_result})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Unknown error occurred'})}\n\n"
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating BA specification with streaming: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket, client_id)
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await manager.send_personal_message({"type": "pong"}, client_id)
            elif message.get("type") == "subscribe_project":
                project_id = message.get("project_id")
                if project_id:
                    # Send current project status
                    try:
                        status = await project_manager.get_project_status(project_id)
                        await manager.send_personal_message({
                            "type": "project_status",
                            "project_id": project_id,
                            "data": status
                        }, client_id)
                    except Exception as e:
                        logger.error(f"Error getting project status for WebSocket: {e}")
                        
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        manager.disconnect(client_id)

async def run_workflow_background(project_id: str, specification: str):
    """Run the LangGraph workflow in the background with progress updates."""
    try:
        logger.info(f"Starting workflow for project {project_id}")
        
        # Create workflow
        workflow_instance = SoftwareDevelopmentWorkflow()
        workflow = workflow_instance.workflow
        
        # Define callback for progress updates
        async def progress_callback(stage: str, data: Dict[str, Any] = None):
            """Callback to send progress updates via WebSocket."""
            logger.info(f"Workflow progress: {stage}")
            
            # Map workflow stages to agent activities and progress
            stage_info = {
                "requirements_analysis": {
                    "agent": "ba_agent",
                    "progress": 25,
                    "message": "Analyzing business requirements 📋"
                },
                "architecture_design": {
                    "agent": "architect_agent", 
                    "progress": 40,
                    "message": "Designing system architecture 🏗️"
                },
                "development": {
                    "agent": "developer_agent",
                    "progress": 60, 
                    "message": "Implementing the solution 💻"
                },
                "testing": {
                    "agent": "tester_agent",
                    "progress": 80,
                    "message": "Creating comprehensive tests 🧪"
                },
                "completed": {
                    "agent": "orchestrator_agent",
                    "progress": 100,
                    "message": "Project completed successfully! 🎉"
                }
            }
            
            info = stage_info.get(stage, {
                "agent": "orchestrator_agent",
                "progress": 10,
                "message": f"Working on {stage}..."
            })
            
            # Send agent status update
            await manager.broadcast({
                "type": "agent_status",
                "agent_id": info["agent"],
                "status": "working" if stage != "completed" else "completed", 
                "message": info["message"]
            })
            
            # Send workflow progress update
            await manager.broadcast({
                "type": "workflow_update",
                "project_id": project_id,
                "stage": stage,
                "progress": info["progress"],
                "message": info["message"],
                "data": data
            })
            
            # Update project status in manager
            await project_manager.update_project_status(
                project_id=project_id,
                status=stage,
                progress=info["progress"]
            )
        
        # Set the callback on the workflow
        if hasattr(workflow_instance, 'set_progress_callback'):
            workflow_instance.set_progress_callback(progress_callback)
        
        # Execute workflow using the proper async method
        result = await workflow_instance.arun_project(
            specification=specification,
            project_id=project_id,
            phase_callback=progress_callback
        )
        
        logger.info(f"Workflow completed for project {project_id}")
        
        # Final completion notification
        await progress_callback("completed", result)
        
        # Set all agents back to idle
        for agent in ["ba_agent", "architect_agent", "developer_agent", "tester_agent", "orchestrator_agent"]:
            await manager.broadcast({
                "type": "agent_status",
                "agent_id": agent,
                "status": "idle",
                "message": "Ready for next project 😴"
            })
            
    except Exception as e:
        logger.error(f"Workflow error for project {project_id}: {e}")
        
        # Send error notification
        await manager.broadcast({
            "type": "error",
            "project_id": project_id,
            "message": str(e)
        })
        
        # Set all agents to error state
        for agent in ["ba_agent", "architect_agent", "developer_agent", "tester_agent", "orchestrator_agent"]:
            await manager.broadcast({
                "type": "agent_status", 
                "agent_id": agent,
                "status": "error",
                "message": "Workflow failed 😞"
            })

# Additional API endpoints for artifact management
@app.get("/api/artifacts/{agent_name}")
async def get_agent_artifacts(agent_name: str):
    """Get artifacts created by a specific agent."""
    try:
        # This would integrate with your artifact storage system
        return JSONResponse({
            "agent": agent_name,
            "artifacts": []  # Placeholder
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/artifacts/view/{artifact_id}")
async def view_artifact(artifact_id: str):
    """View a specific artifact."""
    try:
        # This would fetch and return the artifact content
        return JSONResponse({
            "artifact_id": artifact_id,
            "content": "Artifact content would go here"  # Placeholder
        })
    except Exception as e:
        raise HTTPException(status_code=404, detail="Artifact not found")

@app.get("/api/artifacts/download/{artifact_id}")
async def download_artifact(artifact_id: str):
    """Download a specific artifact."""
    try:
        # This would serve the artifact file for download
        return JSONResponse({
            "download_url": f"/static/artifacts/{artifact_id}"  # Placeholder
        })
    except Exception as e:
        raise HTTPException(status_code=404, detail="Artifact not found")

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "web_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
