#!/usr/bin/env python3
"""
Command Line Interface for the Agentic Ecosystem

This CLI provides an easy way to interact with the agentic ecosystem,
create projects, and monitor progress.
"""

import asyncio
import json
import sys
import os
from typing import Optional, Dict, Any
from pathlib import Path
import httpx
import websockets
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.layout import Layout
from rich.text import Text


console = Console()


class AgenticEcosystemCLI:
    """CLI client for the Agentic Ecosystem."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.websocket = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        if self.websocket:
            await self.websocket.close()
    
    async def check_server_health(self) -> bool:
        """Check if the server is running and healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False
    
    async def create_project(self, specification: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Create a new project."""
        try:
            payload = {"specification": specification}
            if title:
                payload["title"] = title
            
            response = await self.client.post(f"{self.base_url}/projects", json=payload)
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get project status."""
        try:
            response = await self.client.get(f"{self.base_url}/projects/{project_id}")
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise Exception(f"Project {project_id} not found")
            raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    async def send_clarification(self, project_id: str, clarification: str) -> Dict[str, Any]:
        """Send clarification for a project."""
        try:
            payload = {"project_id": project_id, "clarification": clarification}
            response = await self.client.post(
                f"{self.base_url}/projects/{project_id}/clarifications",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    async def list_projects(self) -> Dict[str, Any]:
        """List all projects."""
        try:
            response = await self.client.get(f"{self.base_url}/projects")
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    async def get_project_workflow(self, project_id: str) -> Dict[str, Any]:
        """Get project workflow history."""
        try:
            response = await self.client.get(f"{self.base_url}/projects/{project_id}/workflow")
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    async def monitor_project_realtime(self, project_id: str):
        """Monitor project progress in real-time via WebSocket."""
        try:
            ws_url = f"ws://localhost:8000/ws/cli_{int(datetime.now().timestamp())}"
            
            async with websockets.connect(ws_url) as websocket:
                self.websocket = websocket
                
                # Subscribe to project updates
                await websocket.send(json.dumps({
                    "type": "subscribe_project",
                    "project_id": project_id
                }))
                
                console.print(f"[green]Monitoring project {project_id} in real-time...[/green]")
                console.print("[dim]Press Ctrl+C to stop monitoring[/dim]")
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        self._display_realtime_update(data)
                    except json.JSONDecodeError:
                        console.print(f"[red]Invalid message received: {message}[/red]")
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped monitoring[/yellow]")
        except Exception as e:
            console.print(f"[red]WebSocket error: {str(e)}[/red]")
    
    def _display_realtime_update(self, data: Dict[str, Any]):
        """Display real-time update in a formatted way."""
        update_type = data.get("type", "unknown")
        
        if update_type == "subscription_confirmed":
            console.print(f"[green]✓ {data.get('message', 'Subscribed to updates')}[/green]")
        elif update_type == "project_update":
            message = data.get("message", "No message")
            timestamp = data.get("timestamp", "Unknown time")
            console.print(f"[blue]{timestamp}[/blue] - {message}")
        elif update_type == "pong":
            # Skip ping/pong messages
            pass
        else:
            console.print(f"[dim]Update: {json.dumps(data, indent=2)}[/dim]")


@click.group()
@click.option('--server', default='http://localhost:8000', help='Server URL')
@click.pass_context
def cli(ctx, server):
    """Agentic Ecosystem CLI - Interact with the agent-based development platform."""
    ctx.ensure_object(dict)
    ctx.obj['server'] = server


@cli.command()
@click.pass_context
async def health(ctx):
    """Check server health status."""
    server_url = ctx.obj['server']
    
    async with AgenticEcosystemCLI(server_url) as client:
        with console.status("[bold green]Checking server health..."):
            is_healthy = await client.check_server_health()
        
        if is_healthy:
            console.print("[green]✓ Server is healthy and running[/green]")
            
            # Get detailed health info
            try:
                response = await client.client.get(f"{server_url}/health")
                health_data = response.json()
                
                # Display agent statuses
                agents = health_data.get("agents", {})
                if agents:
                    table = Table(title="Agent Status")
                    table.add_column("Agent", style="cyan")
                    table.add_column("Status", style="green")
                    table.add_column("Last Activity", style="dim")
                    
                    for agent_name, agent_info in agents.items():
                        status = agent_info.get("status", "unknown")
                        last_activity = agent_info.get("last_activity", "unknown")
                        
                        status_style = "green" if status == "idle" else "yellow" if status == "working" else "red"
                        table.add_row(
                            agent_name.replace("_", " ").title(),
                            f"[{status_style}]{status}[/{status_style}]",
                            last_activity
                        )
                    
                    console.print(table)
                
            except Exception as e:
                console.print(f"[yellow]Warning: Could not get detailed health info: {str(e)}[/yellow]")
        else:
            console.print(f"[red]✗ Server is not accessible at {server_url}[/red]")
            console.print("[dim]Make sure the server is running with: python -m src.mcp_servers.main_server[/dim]")


@cli.command()
@click.option('--file', '-f', type=click.File('r'), help='Read specification from file')
@click.option('--title', '-t', help='Project title')
@click.pass_context
async def create(ctx, file, title):
    """Create a new project."""
    server_url = ctx.obj['server']
    
    # Get specification
    if file:
        specification = file.read()
    else:
        console.print("[bold]Enter your project specification:[/bold]")
        console.print("[dim]Describe what you want to build. Be as detailed as possible.[/dim]")
        console.print("[dim]Press Ctrl+D when finished.[/dim]")
        
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        
        specification = "\n".join(lines).strip()
        
        if not specification:
            console.print("[red]Error: No specification provided[/red]")
            return
    
    async with AgenticEcosystemCLI(server_url) as client:
        # Check server health first
        if not await client.check_server_health():
            console.print(f"[red]Error: Server is not accessible at {server_url}[/red]")
            return
        
        with console.status("[bold green]Creating project..."):
            try:
                result = await client.create_project(specification, title)
                
                project_id = result.get("project_id")
                console.print(f"[green]✓ Project created successfully![/green]")
                console.print(f"[blue]Project ID: {project_id}[/blue]")
                console.print(f"[dim]Status: {result.get('status', 'unknown')}[/dim]")
                console.print(f"[dim]Message: {result.get('message', 'No message')}[/dim]")
                
                # Ask if user wants to monitor progress
                if Confirm.ask("Do you want to monitor the project progress in real-time?"):
                    await client.monitor_project_realtime(project_id)
                
            except Exception as e:
                console.print(f"[red]Error creating project: {str(e)}[/red]")


@cli.command()
@click.argument('project_id')
@click.pass_context
async def status(ctx, project_id):
    """Get project status."""
    server_url = ctx.obj['server']
    
    async with AgenticEcosystemCLI(server_url) as client:
        try:
            with console.status(f"[bold green]Getting status for project {project_id}..."):
                project_status = await client.get_project_status(project_id)
            
            # Create status panel
            status_content = f"""
[bold]Current Phase:[/bold] {project_status.get('current_phase', 'Unknown')}
[bold]Progress:[/bold] {project_status.get('completion_percentage', 0):.1f}%
[bold]Active Agents:[/bold] {', '.join(project_status.get('active_agents', []))}
[bold]Last Updated:[/bold] {project_status.get('last_updated', 'Unknown')}

[bold]Next Actions:[/bold]
{chr(10).join(f"• {action}" for action in project_status.get('next_actions', []))}
"""
            
            if project_status.get('issues'):
                status_content += f"""
[bold red]Issues:[/bold red]
{chr(10).join(f"• {issue}" for issue in project_status.get('issues', []))}
"""
            
            panel = Panel(
                status_content.strip(),
                title=f"Project {project_id} Status",
                border_style="blue"
            )
            
            console.print(panel)
            
        except Exception as e:
            console.print(f"[red]Error getting project status: {str(e)}[/red]")


@cli.command()
@click.pass_context
async def list(ctx):
    """List all projects."""
    server_url = ctx.obj['server']
    
    async with AgenticEcosystemCLI(server_url) as client:
        try:
            with console.status("[bold green]Fetching projects..."):
                result = await client.list_projects()
            
            projects = result.get("projects", [])
            
            if not projects:
                console.print("[yellow]No projects found[/yellow]")
                return
            
            table = Table(title="All Projects")
            table.add_column("Project ID", style="cyan")
            table.add_column("Phase", style="green")
            table.add_column("Progress", style="yellow")
            table.add_column("Last Updated", style="dim")
            
            for project in projects:
                progress = f"{project.get('completion_percentage', 0):.1f}%"
                table.add_row(
                    project.get('project_id', 'Unknown'),
                    project.get('current_phase', 'Unknown'),
                    progress,
                    project.get('last_updated', 'Unknown')
                )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error listing projects: {str(e)}[/red]")


@cli.command()
@click.argument('project_id')
@click.pass_context
async def workflow(ctx, project_id):
    """Show project workflow history."""
    server_url = ctx.obj['server']
    
    async with AgenticEcosystemCLI(server_url) as client:
        try:
            with console.status(f"[bold green]Getting workflow for project {project_id}..."):
                result = await client.get_project_workflow(project_id)
            
            workflow = result.get("workflow", [])
            
            if not workflow:
                console.print("[yellow]No workflow history found[/yellow]")
                return
            
            table = Table(title=f"Workflow History - Project {project_id}")
            table.add_column("Time", style="dim")
            table.add_column("From", style="cyan")
            table.add_column("To", style="green")
            table.add_column("Type", style="yellow")
            table.add_column("Content", style="white")
            
            for step in workflow:
                content = step.get('content', '')
                if len(content) > 50:
                    content = content[:47] + "..."
                
                table.add_row(
                    step.get('timestamp', 'Unknown')[:19],  # Trim timestamp
                    step.get('from_agent', 'Unknown'),
                    step.get('to_agent', 'Unknown'),
                    step.get('message_type', 'Unknown'),
                    content
                )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error getting workflow: {str(e)}[/red]")


@cli.command()
@click.argument('project_id')
@click.pass_context
async def clarify(ctx, project_id):
    """Send clarification for a project."""
    server_url = ctx.obj['server']
    
    console.print(f"[bold]Sending clarification for project {project_id}[/bold]")
    console.print("[dim]Enter your clarification. Press Ctrl+D when finished.[/dim]")
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    clarification = "\n".join(lines).strip()
    
    if not clarification:
        console.print("[red]Error: No clarification provided[/red]")
        return
    
    async with AgenticEcosystemCLI(server_url) as client:
        try:
            with console.status("[bold green]Sending clarification..."):
                result = await client.send_clarification(project_id, clarification)
            
            console.print(f"[green]✓ {result.get('message', 'Clarification sent successfully')}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error sending clarification: {str(e)}[/red]")


@cli.command()
@click.argument('project_id')
@click.pass_context
async def monitor(ctx, project_id):
    """Monitor project progress in real-time."""
    server_url = ctx.obj['server']
    
    async with AgenticEcosystemCLI(server_url) as client:
        await client.monitor_project_realtime(project_id)


# Convert async commands to sync for Click
def async_command(f):
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

# Apply async decorator to all commands
for command_name in ['health', 'create', 'status', 'list', 'workflow', 'clarify', 'monitor']:
    command = cli.commands[command_name]
    command.callback = async_command(command.callback)


if __name__ == '__main__':
    cli()
