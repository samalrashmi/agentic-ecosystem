"""
Enhanced MCP Server implementation for LangGraph Agentic Ecosystem

This implements enhanced Model Context Protocol patterns following best practices from:
- https://generect.com/blog/langgraph-mcp/
- https://langchain-ai.github.io/langgraph/agents/mcp/

Key improvements:
- Proper resource management
- Enhanced error handling
- Better state persistence
- Streaming support for long-running workflows
"""

import asyncio
import json
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Sequence, AsyncIterator
import logging

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp import types
from mcp.server.stdio import stdio_server

from dotenv import load_dotenv

from .workflow import run_software_development_workflow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize the enhanced MCP server
app = Server("agentic-ecosystem")

# Enhanced project tracking with persistence
class ProjectManager:
    """Enhanced project management with persistence and state tracking."""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.projects_file = self.data_dir / "projects.json"
        self.active_projects: Dict[str, Dict[str, Any]] = {}
        self._load_projects()
    
    def _load_projects(self):
        """Load projects from persistent storage."""
        if self.projects_file.exists():
            try:
                with open(self.projects_file, 'r', encoding='utf-8') as f:
                    saved_projects = json.load(f)
                self.active_projects.update(saved_projects)
                logger.info(f"Loaded {len(saved_projects)} projects from storage")
            except Exception as e:
                logger.error(f"Failed to load projects: {e}")
    
    def _save_projects(self):
        """Save projects to persistent storage."""
        try:
            with open(self.projects_file, 'w', encoding='utf-8') as f:
                json.dump(self.active_projects, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save projects: {e}")
    
    def create_project(self, specification: str, title: str = None, domain: str = None) -> str:
        """Create a new project with enhanced tracking."""
        project_id = str(uuid.uuid4())
        
        project_data = {
            "id": project_id,
            "title": title or "Untitled Project",
            "domain": domain or "General",
            "specification": specification,
            "status": "initiated",
            "created_at": datetime.now().isoformat(),
            "current_phase": "initiating",
            "progress": 0,
            "phases": ["business_analysis", "architecture", "implementation", "testing"],
            "completed_phases": []
        }
        
        self.active_projects[project_id] = project_data
        self._save_projects()
        
        logger.info(f"Created project {project_id}: {title}")
        return project_id
    
    def update_project(self, project_id: str, updates: Dict[str, Any]):
        """Update project with new data."""
        if project_id in self.active_projects:
            self.active_projects[project_id].update(updates)
            self.active_projects[project_id]["updated_at"] = datetime.now().isoformat()
            self._save_projects()
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project data."""
        return self.active_projects.get(project_id)
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects."""
        return list(self.active_projects.values())
    
    # Async methods for web server compatibility
    async def create_project(self, project_id: str, title: str, specification: str, domain: str = "web-application") -> str:
        """Async version of create_project for web server."""
        project_data = {
            "id": project_id,
            "title": title,
            "domain": domain,
            "specification": specification,
            "status": "initiated",
            "created_at": datetime.now().isoformat(),
            "current_phase": "initiating",
            "progress": 0,
            "phases": ["business_analysis", "architecture", "implementation", "testing"],
            "completed_phases": []
        }
        
        self.active_projects[project_id] = project_data
        self._save_projects()
        
        logger.info(f"Created project {project_id}: {title}")
        return project_id
    
    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get project status asynchronously."""
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        return project
    
    async def list_projects_async(self) -> List[Dict[str, Any]]:
        """Async version of list_projects."""
        return self.list_projects()
    
    async def get_project_artifacts(self, project_id: str) -> Dict[str, Any]:
        """Get artifacts for a project."""
        project_dir = Path(__file__).parent.parent.parent / "out" / f"project_{project_id}"
        artifacts = {}
        
        if project_dir.exists():
            for artifact_file in project_dir.glob("*.json"):
                if artifact_file.name != "project_summary.json":
                    artifact_name = artifact_file.stem
                    try:
                        with open(artifact_file, 'r', encoding='utf-8') as f:
                            artifacts[artifact_name] = json.load(f)
                    except Exception as e:
                        logger.error(f"Failed to load artifact {artifact_name}: {e}")
        
        return {
            "project_id": project_id,
            "artifacts": artifacts
        }
    
    async def update_project_status(self, project_id: str, status: str, progress: int = None):
        """Update project status and progress."""
        if project_id in self.active_projects:
            self.active_projects[project_id]["status"] = status
            if progress is not None:
                self.active_projects[project_id]["progress"] = progress
            self.active_projects[project_id]["updated_at"] = datetime.now().isoformat()
            self._save_projects()

# Initialize project manager
project_manager = ProjectManager()


@app.list_resources()
async def list_resources() -> List[types.Resource]:
    """List available resources (project data, artifacts, etc.)."""
    resources = []
    
    # Add project resources
    for project in project_manager.list_projects():
        project_id = project["id"]
        resources.append(
            types.Resource(
                uri=f"project://{project_id}",
                name=f"Project: {project['title']}",
                description=f"Project data and artifacts for {project['title']}",
                mimeType="application/json"
            )
        )
        
        # Add artifact resources if they exist
        project_dir = Path(__file__).parent.parent.parent / "out" / f"project_{project_id}"
        if project_dir.exists():
            for artifact_file in project_dir.glob("*.json"):
                if artifact_file.name != "project_summary.json":
                    resources.append(
                        types.Resource(
                            uri=f"artifact://{project_id}/{artifact_file.stem}",
                            name=f"{project['title']} - {artifact_file.stem.title()}",
                            description=f"Generated artifact: {artifact_file.stem}",
                            mimeType="application/json"
                        )
                    )
    
    return resources


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content."""
    try:
        if uri.startswith("project://"):
            project_id = uri.replace("project://", "")
            project = project_manager.get_project(project_id)
            if project:
                return json.dumps(project, indent=2)
            else:
                raise ValueError(f"Project {project_id} not found")
        
        elif uri.startswith("artifact://"):
            # Parse artifact URI: artifact://project_id/artifact_name
            parts = uri.replace("artifact://", "").split("/")
            if len(parts) != 2:
                raise ValueError("Invalid artifact URI format")
            
            project_id, artifact_name = parts
            artifact_file = Path(__file__).parent.parent.parent / "out" / f"project_{project_id}" / f"{artifact_name}.json"
            
            if artifact_file.exists():
                with open(artifact_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                raise ValueError(f"Artifact {artifact_name} not found for project {project_id}")
        
        else:
            raise ValueError(f"Unsupported URI scheme: {uri}")
    
    except Exception as e:
        logger.error(f"Failed to read resource {uri}: {e}")
        raise


@app.list_tools()
async def list_tools() -> List[types.Tool]:
    """List available tools with enhanced schemas."""
    return [
        types.Tool(
            name="create_project",
            description="Create a new software development project using LangGraph multi-agent workflow with enhanced tracking",
            inputSchema={
                "type": "object",
                "properties": {
                    "specification": {
                        "type": "string",
                        "description": "Detailed project specification and requirements",
                        "minLength": 10
                    },
                    "title": {
                        "type": "string",
                        "description": "Project title",
                        "maxLength": 100
                    },
                    "domain": {
                        "type": "string",
                        "description": "Project domain (e.g., web, mobile, data, api, ml)",
                        "enum": ["web", "mobile", "data", "api", "ml", "desktop", "embedded", "general"]
                    },
                    "priority": {
                        "type": "string",
                        "description": "Project priority level",
                        "enum": ["low", "medium", "high", "urgent"],
                        "default": "medium"
                    }
                },
                "required": ["specification"]
            }
        ),
        types.Tool(
            name="get_project_status",
            description="Get comprehensive status and progress of a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The unique project identifier (UUID format)",
                        "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
                    },
                    "include_artifacts": {
                        "type": "boolean",
                        "description": "Whether to include artifact summaries in the response",
                        "default": False
                    }
                },
                "required": ["project_id"]
            }
        ),
        types.Tool(
            name="list_projects",
            description="List all projects with filtering and sorting options",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by project status",
                        "enum": ["initiated", "in_progress", "completed", "failed"]
                    },
                    "domain": {
                        "type": "string",
                        "description": "Filter by project domain"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of projects to return",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 20
                    }
                }
            }
        ),
        types.Tool(
            name="get_project_artifacts",
            description="Get detailed artifacts generated for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The unique project identifier"
                    },
                    "artifact_type": {
                        "type": "string",
                        "description": "Specific artifact type to retrieve",
                        "enum": ["business_analysis", "system_architecture", "implementation_plan", "test_strategy", "all"]
                    }
                },
                "required": ["project_id"]
            }
        ),
        types.Tool(
            name="monitor_project_progress",
            description="Get real-time progress updates for an active project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The unique project identifier"
                    }
                },
                "required": ["project_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Enhanced tool handling with better error management."""
    
    try:
        logger.info(f"Tool called: {name} with args: {arguments}")
        
        if name == "create_project":
            return await handle_create_project_enhanced(arguments)
        elif name == "get_project_status":
            return await handle_get_project_status_enhanced(arguments)
        elif name == "list_projects":
            return await handle_list_projects_enhanced(arguments)
        elif name == "get_project_artifacts":
            return await handle_get_project_artifacts_enhanced(arguments)
        elif name == "monitor_project_progress":
            return await handle_monitor_project_progress(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        error_result = {
            "error": str(e),
            "tool": name,
            "timestamp": datetime.now().isoformat()
        }
        return [types.TextContent(
            type="text",
            text=json.dumps(error_result, indent=2)
        )]


async def handle_create_project_enhanced(arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Enhanced project creation with validation and tracking."""
    specification = arguments["specification"]
    title = arguments.get("title", "Untitled Project")
    domain = arguments.get("domain", "general")
    priority = arguments.get("priority", "medium")
    
    # Create project with enhanced tracking
    project_id = project_manager.create_project(specification, title, domain)
    
    # Update with additional metadata
    project_manager.update_project(project_id, {
        "priority": priority,
        "estimated_duration": "TBD",
        "complexity": "TBD"
    })
    
    # Start workflow in background with enhanced monitoring
    asyncio.create_task(run_project_workflow_enhanced(project_id, specification))
    
    result = {
        "project_id": project_id,
        "title": title,
        "domain": domain,
        "priority": priority,
        "status": "initiated",
        "message": f"Project '{title}' created successfully. Enhanced LangGraph workflow starting...",
        "created_at": datetime.now().isoformat(),
        "tracking_uri": f"project://{project_id}"
    }
    
    return [types.TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_get_project_status_enhanced(arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Enhanced project status with comprehensive information."""
    project_id = arguments["project_id"]
    include_artifacts = arguments.get("include_artifacts", False)
    
    project = project_manager.get_project(project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")
    
    # Enhance with file system data
    project_dir = Path(__file__).parent.parent.parent / "out" / f"project_{project_id}"
    if project_dir.exists():
        summary_file = project_dir / "project_summary.json"
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
            project.update(summary_data)
        
        # Add artifact information if requested
        if include_artifacts:
            artifacts = {}
            for artifact_file in project_dir.glob("*.json"):
                if artifact_file.name != "project_summary.json":
                    artifacts[artifact_file.stem] = {
                        "file": artifact_file.name,
                        "size": artifact_file.stat().st_size,
                        "modified": datetime.fromtimestamp(artifact_file.stat().st_mtime).isoformat(),
                        "uri": f"artifact://{project_id}/{artifact_file.stem}"
                    }
            project["artifacts"] = artifacts
    
    return [types.TextContent(
        type="text",
        text=json.dumps(project, indent=2)
    )]


async def handle_list_projects_enhanced(arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Enhanced project listing with filtering."""
    status_filter = arguments.get("status")
    domain_filter = arguments.get("domain")
    limit = arguments.get("limit", 20)
    
    projects = project_manager.list_projects()
    
    # Apply filters
    if status_filter:
        projects = [p for p in projects if p.get("status") == status_filter]
    
    if domain_filter:
        projects = [p for p in projects if p.get("domain") == domain_filter]
    
    # Sort by creation date (newest first)
    projects.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Apply limit
    projects = projects[:limit]
    
    result = {
        "projects": projects,
        "total_count": len(projects),
        "filters_applied": {
            "status": status_filter,
            "domain": domain_filter,
            "limit": limit
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return [types.TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_get_project_artifacts_enhanced(arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Enhanced artifact retrieval."""
    project_id = arguments["project_id"]
    artifact_type = arguments.get("artifact_type", "all")
    
    project_dir = Path(__file__).parent.parent.parent / "out" / f"project_{project_id}"
    if not project_dir.exists():
        raise ValueError(f"No artifacts found for project {project_id}")
    
    artifacts = {}
    
    if artifact_type == "all":
        # Get all artifacts
        for artifact_file in project_dir.glob("*.json"):
            if artifact_file.name != "project_summary.json":
                with open(artifact_file, 'r', encoding='utf-8') as f:
                    artifacts[artifact_file.stem] = json.load(f)
    else:
        # Get specific artifact
        artifact_file = project_dir / f"{artifact_type}.json"
        if artifact_file.exists():
            with open(artifact_file, 'r', encoding='utf-8') as f:
                artifacts[artifact_type] = json.load(f)
        else:
            raise ValueError(f"Artifact {artifact_type} not found for project {project_id}")
    
    result = {
        "project_id": project_id,
        "artifacts": artifacts,
        "artifact_count": len(artifacts),
        "retrieved_at": datetime.now().isoformat()
    }
    
    return [types.TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_monitor_project_progress(arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Monitor real-time project progress."""
    project_id = arguments["project_id"]
    
    project = project_manager.get_project(project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")
    
    # Calculate progress based on completed phases
    total_phases = len(project.get("phases", []))
    completed_phases = len(project.get("completed_phases", []))
    progress_percentage = (completed_phases / total_phases * 100) if total_phases > 0 else 0
    
    # Check for recent updates
    project_dir = Path(__file__).parent.parent.parent / "out" / f"project_{project_id}"
    recent_files = []
    if project_dir.exists():
        # Get files modified in the last hour
        one_hour_ago = datetime.now().timestamp() - 3600
        for file_path in project_dir.glob("*.json"):
            if file_path.stat().st_mtime > one_hour_ago:
                recent_files.append({
                    "file": file_path.name,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
    
    result = {
        "project_id": project_id,
        "title": project.get("title", "Unknown"),
        "current_phase": project.get("current_phase", "unknown"),
        "status": project.get("status", "unknown"),
        "progress_percentage": round(progress_percentage, 1),
        "completed_phases": project.get("completed_phases", []),
        "remaining_phases": [p for p in project.get("phases", []) if p not in project.get("completed_phases", [])],
        "recent_activity": recent_files,
        "last_updated": project.get("updated_at", project.get("created_at")),
        "monitoring_timestamp": datetime.now().isoformat()
    }
    
    return [types.TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def run_project_workflow_enhanced(project_id: str, specification: str):
    """Enhanced workflow execution with progress tracking."""
    try:
        logger.info(f"Starting enhanced workflow for project {project_id}")
        
        # Update project status
        project_manager.update_project(project_id, {
            "status": "in_progress",
            "current_phase": "business_analysis",
            "started_at": datetime.now().isoformat()
        })
        
        # Phase tracking callback
        def phase_completed(phase_name: str):
            completed_phases = project_manager.get_project(project_id).get("completed_phases", [])
            completed_phases.append(phase_name)
            project_manager.update_project(project_id, {
                "completed_phases": completed_phases,
                "current_phase": get_next_phase(phase_name)
            })
        
        # Run the LangGraph workflow with enhanced tracking
        final_state = await run_software_development_workflow(
            specification=specification,
            project_id=project_id,
            phase_callback=phase_completed
        )
        
        # Update final status
        project_manager.update_project(project_id, {
            "status": "completed",
            "current_phase": "completed",
            "completed_at": datetime.now().isoformat(),
            "workflow_completed": True,
            "final_state": final_state
        })
        
        logger.info(f"✅ Enhanced workflow completed for project {project_id}")
        
    except Exception as e:
        error_msg = f"Enhanced workflow failed for project {project_id}: {str(e)}"
        logger.error(error_msg)
        
        project_manager.update_project(project_id, {
            "status": "failed",
            "error": error_msg,
            "failed_at": datetime.now().isoformat()
        })


def get_next_phase(current_phase: str) -> str:
    """Get the next phase in the workflow."""
    phases = ["business_analysis", "architecture", "implementation", "testing"]
    try:
        current_index = phases.index(current_phase)
        if current_index < len(phases) - 1:
            return phases[current_index + 1]
        else:
            return "completed"
    except ValueError:
        return "unknown"


async def main():
    """Enhanced main entry point for the MCP server."""
    print("🚀 Starting Enhanced Agentic Ecosystem MCP Server...")
    print("📡 Using advanced Model Context Protocol implementation")
    print("🤖 Enhanced LangGraph multi-agent workflows")
    print("💾 Persistent project management enabled")
    print("📊 Real-time progress monitoring available")
    
    # Run the enhanced MCP server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="agentic-ecosystem-enhanced",
                server_version="2.1.0",
                capabilities=app.get_capabilities(
                    notification_options=types.ClientCapabilities(),
                    experimental_capabilities={}
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
