"""
Proper MCP Server implementation for LangGraph Agentic Ecosystem

This implements a true Model Context Protocol server using the mcp library
as described in: https://langchain-ai.github.io/langgraph/agents/mcp/
"""

import asyncio
import json
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Sequence

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp import types
from mcp.server.stdio import stdio_server

from dotenv import load_dotenv

from .workflow import run_software_development_workflow

# Load environment variables
load_dotenv()

# Initialize the MCP server
app = Server("agentic-ecosystem")

# Track running projects
active_projects: Dict[str, Dict[str, Any]] = {}


@app.list_tools()
async def list_tools() -> List[types.Tool]:
    """List available tools for the agentic ecosystem."""
    return [
        types.Tool(
            name="create_project",
            description="Create a new software development project using LangGraph multi-agent workflow",
            inputSchema={
                "type": "object",
                "properties": {
                    "specification": {
                        "type": "string",
                        "description": "Detailed project specification and requirements"
                    },
                    "title": {
                        "type": "string",
                        "description": "Optional project title"
                    },
                    "domain": {
                        "type": "string",
                        "description": "Optional project domain (e.g., web, mobile, data)"
                    }
                },
                "required": ["specification"]
            }
        ),
        types.Tool(
            name="get_project_status",
            description="Get the status and details of a project",
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
        ),
        types.Tool(
            name="list_projects",
            description="List all projects (active and completed)",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="get_project_artifacts",
            description="Get the generated artifacts for a completed project",
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
    """Handle tool calls for the agentic ecosystem."""
    
    if name == "create_project":
        return await handle_create_project(arguments)
    elif name == "get_project_status":
        return await handle_get_project_status(arguments)
    elif name == "list_projects":
        return await handle_list_projects(arguments)
    elif name == "get_project_artifacts":
        return await handle_get_project_artifacts(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_create_project(arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Handle project creation."""
    try:
        specification = arguments["specification"]
        title = arguments.get("title", "Untitled Project")
        domain = arguments.get("domain", "General")
        
        # Generate unique project ID
        project_id = str(uuid.uuid4())
        
        # Add to active projects tracking
        active_projects[project_id] = {
            "id": project_id,
            "title": title,
            "domain": domain,
            "specification": specification,
            "status": "initiated",
            "created_at": datetime.now().isoformat(),
            "current_phase": "initiating"
        }
        
        # Run workflow in background task
        asyncio.create_task(run_project_workflow_background(project_id, specification))
        
        result = {
            "project_id": project_id,
            "status": "initiated",
            "message": f"Project '{title}' created successfully. LangGraph workflow starting...",
            "created_at": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
        
    except Exception as e:
        error_result = {
            "error": f"Failed to create project: {str(e)}",
            "status": "failed"
        }
        return [types.TextContent(
            type="text", 
            text=json.dumps(error_result, indent=2)
        )]


async def handle_get_project_status(arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Handle getting project status."""
    try:
        project_id = arguments["project_id"]
        
        # Check if project exists in active tracking
        if project_id in active_projects:
            project = active_projects[project_id].copy()
            
            # Check for completion status from file system
            project_dir = Path(__file__).parent.parent.parent / "out" / f"project_{project_id}"
            summary_file = project_dir / "project_summary.json"
            
            if summary_file.exists():
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary_data = json.load(f)
                project.update(summary_data)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(project, indent=2)
            )]
        
        # Try to load from file system
        project_dir = Path(__file__).parent.parent.parent / "out" / f"project_{project_id}"
        if not project_dir.exists():
            error_result = {"error": "Project not found", "project_id": project_id}
            return [types.TextContent(
                type="text",
                text=json.dumps(error_result, indent=2)
            )]
        
        # Load project summary if available
        summary_file = project_dir / "project_summary.json"
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
            return [types.TextContent(
                type="text",
                text=json.dumps(summary_data, indent=2)
            )]
        else:
            result = {
                "project_id": project_id, 
                "status": "unknown", 
                "message": "Project found but status unknown"
            }
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
    except Exception as e:
        error_result = {
            "error": f"Failed to get project status: {str(e)}",
            "project_id": arguments.get("project_id", "unknown")
        }
        return [types.TextContent(
            type="text",
            text=json.dumps(error_result, indent=2)
        )]


async def handle_list_projects(arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Handle listing all projects."""
    try:
        # Get active projects
        projects = list(active_projects.values())
        
        # Also scan the output directory for completed projects
        out_dir = Path(__file__).parent.parent.parent / "out"
        if out_dir.exists():
            for project_dir in out_dir.glob("project_*"):
                project_id = project_dir.name.replace("project_", "")
                if project_id not in active_projects:
                    summary_file = project_dir / "project_summary.json"
                    if summary_file.exists():
                        try:
                            with open(summary_file, 'r', encoding='utf-8') as f:
                                summary_data = json.load(f)
                            projects.append(summary_data)
                        except Exception:
                            pass  # Skip corrupted files
        
        result = {
            "projects": projects,
            "total_count": len(projects),
            "active_count": len(active_projects),
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
        
    except Exception as e:
        error_result = {
            "error": f"Failed to list projects: {str(e)}"
        }
        return [types.TextContent(
            type="text",
            text=json.dumps(error_result, indent=2)
        )]


async def handle_get_project_artifacts(arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Handle getting project artifacts."""
    try:
        project_id = arguments["project_id"]
        
        # Check if project directory exists
        project_dir = Path(__file__).parent.parent.parent / "out" / f"project_{project_id}"
        if not project_dir.exists():
            error_result = {"error": "Project not found", "project_id": project_id}
            return [types.TextContent(
                type="text",
                text=json.dumps(error_result, indent=2)
            )]
        
        # List all artifacts
        artifacts = {}
        
        # Check for each expected artifact type
        artifact_files = {
            "business_analysis": "business_analysis.md",
            "system_architecture": "system_architecture.md", 
            "implementation_plan": "implementation_plan.md",
            "test_strategy": "test_strategy.md",
            "project_summary": "project_summary.json"
        }
        
        for artifact_type, filename in artifact_files.items():
            file_path = project_dir / filename
            if file_path.exists():
                try:
                    if filename.endswith('.json'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            artifacts[artifact_type] = json.load(f)
                    else:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            artifacts[artifact_type] = f.read()
                except Exception as e:
                    artifacts[artifact_type] = f"Error reading file: {str(e)}"
            else:
                artifacts[artifact_type] = None
        
        result = {
            "project_id": project_id,
            "artifacts": artifacts,
            "artifacts_available": {k: v is not None for k, v in artifacts.items()},
            "retrieved_at": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
        
    except Exception as e:
        error_result = {
            "error": f"Failed to get project artifacts: {str(e)}",
            "project_id": arguments.get("project_id", "unknown")
        }
        return [types.TextContent(
            type="text",
            text=json.dumps(error_result, indent=2)
        )]


async def run_project_workflow_background(project_id: str, specification: str):
    """Run the LangGraph workflow for a project in background."""
    try:
        print(f"🔄 Starting LangGraph workflow for project {project_id}")
        
        # Update project status
        if project_id in active_projects:
            active_projects[project_id]["status"] = "running"
            active_projects[project_id]["current_phase"] = "workflow_starting"
        
        # Run the LangGraph workflow
        final_state = run_software_development_workflow(specification, project_id)
        
        # Update project status with final results
        if project_id in active_projects:
            active_projects[project_id].update({
                "status": final_state.get("status", "completed"),
                "current_phase": final_state.get("current_phase", "completed"),
                "completed_at": datetime.now().isoformat(),
                "workflow_completed": True
            })
        
        print(f"✅ LangGraph workflow completed for project {project_id}")
        
    except Exception as e:
        error_msg = f"Workflow failed for project {project_id}: {str(e)}"
        print(f"❌ {error_msg}")
        
        if project_id in active_projects:
            active_projects[project_id].update({
                "status": "failed",
                "error": error_msg,
                "failed_at": datetime.now().isoformat()
            })


async def main():
    """Main entry point for the MCP server."""
    print("🚀 Starting Agentic Ecosystem MCP Server...")
    print("📡 Using proper Model Context Protocol implementation")
    print("🤖 LangGraph multi-agent workflows enabled")
    
    # Run the MCP server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="agentic-ecosystem",
                server_version="2.0.0",
                capabilities=app.get_capabilities(
                    notification_options=types.ClientCapabilities(),
                    experimental_capabilities={}
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
