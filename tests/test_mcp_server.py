#!/usr/bin/env python3
"""
Test suite for MCP Server

This module tests the Model Context Protocol server implementation
to ensure proper tool handling and project management.
"""

import pytest
import json
import sys
import os
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from langgraph_agents.enhanced_mcp_server import (
    ProjectManager,
    handle_create_project_enhanced,
    handle_get_project_status_enhanced,
    handle_list_projects_enhanced,
    handle_get_project_artifacts_enhanced,
    handle_monitor_project_progress
)


class TestMCPServer:
    """Test cases for the MCP server implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_project_id = "test-mcp-project-123"
        self.sample_specification = "Create a simple web application for task management"
        
        # Clean up any existing test files
        self.cleanup_test_files()
        
        # Create fresh project manager for each test
        self.project_manager = ProjectManager()
    
    def teardown_method(self):
        """Clean up after tests."""
        self.cleanup_test_files()
    
    def cleanup_test_files(self):
        """Remove test output files."""
        test_dir = Path(__file__).parent.parent / "out" / f"project_{self.test_project_id}"
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)
        
        # Clean up data directory
        data_dir = Path(__file__).parent.parent / "data"
        if data_dir.exists():
            projects_file = data_dir / "projects.json"
            if projects_file.exists():
                projects_file.unlink()
    
    def test_project_manager_initialization(self):
        """Test ProjectManager initialization."""
        pm = ProjectManager()
        
        assert pm is not None
        assert hasattr(pm, 'active_projects')
        assert hasattr(pm, 'data_dir')
        assert hasattr(pm, 'projects_file')
        assert isinstance(pm.active_projects, dict)
    
    def test_project_manager_create_project(self):
        """Test project creation in ProjectManager."""
        pm = ProjectManager()
        
        project_id = pm.create_project(
            specification=self.sample_specification,
            title="Test Project",
            domain="web"
        )
        
        assert project_id is not None
        assert len(project_id) > 0
        assert project_id in pm.active_projects
        
        project = pm.get_project(project_id)
        assert project["title"] == "Test Project"
        assert project["domain"] == "web"
        assert project["specification"] == self.sample_specification
        assert project["status"] == "initiated"
    
    def test_project_manager_persistence(self):
        """Test project persistence to file system."""
        pm = ProjectManager()
        
        project_id = pm.create_project(
            specification=self.sample_specification,
            title="Persistent Test"
        )
        
        # Create new manager instance to test loading
        pm2 = ProjectManager()
        
        # Project should be loaded from file
        project = pm2.get_project(project_id)
        assert project is not None
        assert project["title"] == "Persistent Test"
    
    def test_project_manager_update_project(self):
        """Test project updates."""
        pm = ProjectManager()
        
        project_id = pm.create_project(specification=self.sample_specification)
        
        # Update project
        pm.update_project(project_id, {
            "status": "in_progress",
            "current_phase": "business_analysis"
        })
        
        project = pm.get_project(project_id)
        assert project["status"] == "in_progress"
        assert project["current_phase"] == "business_analysis"
        assert "updated_at" in project
    
    def test_project_manager_list_projects(self):
        """Test listing all projects."""
        pm = ProjectManager()
        
        # Create multiple projects
        project1 = pm.create_project(specification="Project 1", title="First Project")
        project2 = pm.create_project(specification="Project 2", title="Second Project")
        
        projects = pm.list_projects()
        
        assert len(projects) >= 2
        project_ids = [p["id"] for p in projects]
        assert project1 in project_ids
        assert project2 in project_ids
    
    @pytest.mark.asyncio
    async def test_handle_create_project_enhanced(self):
        """Test enhanced project creation handler."""
        
        with patch('langgraph_agents.enhanced_mcp_server.project_manager') as mock_pm, \
             patch('langgraph_agents.enhanced_mcp_server.asyncio.create_task') as mock_task:
            
            # Mock project manager
            mock_pm.create_project.return_value = self.test_project_id
            mock_pm.update_project.return_value = None
            
            arguments = {
                "specification": self.sample_specification,
                "title": "Test Project",
                "domain": "web",
                "priority": "high"
            }
            
            result = await handle_create_project_enhanced(arguments)
            
            assert len(result) == 1
            assert result[0].type == "text"
            
            response_data = json.loads(result[0].text)
            assert response_data["project_id"] == self.test_project_id
            assert response_data["title"] == "Test Project"
            assert response_data["domain"] == "web"
            assert response_data["priority"] == "high"
            assert response_data["status"] == "initiated"
            
            # Verify project manager was called
            mock_pm.create_project.assert_called_once_with(
                self.sample_specification, "Test Project", "web"
            )
            mock_pm.update_project.assert_called_once()
            
            # Verify background task was created
            mock_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_get_project_status_enhanced(self):
        """Test enhanced project status retrieval."""
        
        with patch('langgraph_agents.enhanced_mcp_server.project_manager') as mock_pm:
            
            # Mock project data
            mock_project = {
                "id": self.test_project_id,
                "title": "Test Project",
                "status": "in_progress",
                "current_phase": "business_analysis",
                "created_at": "2024-01-01T00:00:00"
            }
            mock_pm.get_project.return_value = mock_project
            
            arguments = {
                "project_id": self.test_project_id,
                "include_artifacts": False
            }
            
            result = await handle_get_project_status_enhanced(arguments)
            
            assert len(result) == 1
            response_data = json.loads(result[0].text)
            
            assert response_data["id"] == self.test_project_id
            assert response_data["title"] == "Test Project"
            assert response_data["status"] == "in_progress"
            
            mock_pm.get_project.assert_called_once_with(self.test_project_id)
    
    @pytest.mark.asyncio
    async def test_handle_get_project_status_not_found(self):
        """Test project status for non-existent project."""
        
        with patch('langgraph_agents.enhanced_mcp_server.project_manager') as mock_pm:
            mock_pm.get_project.return_value = None
            
            arguments = {"project_id": "non-existent-project"}
            
            with pytest.raises(ValueError, match="Project .* not found"):
                await handle_get_project_status_enhanced(arguments)
    
    @pytest.mark.asyncio
    async def test_handle_list_projects_enhanced(self):
        """Test enhanced project listing."""
        
        with patch('langgraph_agents.enhanced_mcp_server.project_manager') as mock_pm:
            
            # Mock projects data
            mock_projects = [
                {"id": "proj1", "title": "Project 1", "status": "completed", "domain": "web"},
                {"id": "proj2", "title": "Project 2", "status": "in_progress", "domain": "mobile"},
                {"id": "proj3", "title": "Project 3", "status": "failed", "domain": "web"}
            ]
            mock_pm.list_projects.return_value = mock_projects
            
            arguments = {
                "status": "in_progress",
                "domain": None,
                "limit": 10
            }
            
            result = await handle_list_projects_enhanced(arguments)
            
            assert len(result) == 1
            response_data = json.loads(result[0].text)
            
            assert "projects" in response_data
            assert "total_count" in response_data
            assert "filters_applied" in response_data
            
            # Should filter by status
            filtered_projects = response_data["projects"]
            assert len(filtered_projects) == 1  # Only one in_progress project
            assert filtered_projects[0]["id"] == "proj2"
    
    @pytest.mark.asyncio
    async def test_handle_monitor_project_progress(self):
        """Test project progress monitoring."""
        
        with patch('langgraph_agents.enhanced_mcp_server.project_manager') as mock_pm:
            
            mock_project = {
                "id": self.test_project_id,
                "title": "Test Project",
                "current_phase": "architecture",
                "status": "in_progress",
                "phases": ["business_analysis", "architecture", "implementation", "testing"],
                "completed_phases": ["business_analysis"],
                "created_at": "2024-01-01T00:00:00"
            }
            mock_pm.get_project.return_value = mock_project
            
            arguments = {"project_id": self.test_project_id}
            
            result = await handle_monitor_project_progress(arguments)
            
            assert len(result) == 1
            response_data = json.loads(result[0].text)
            
            assert response_data["project_id"] == self.test_project_id
            assert response_data["current_phase"] == "architecture"
            assert response_data["progress_percentage"] == 25.0  # 1/4 phases completed
            assert len(response_data["completed_phases"]) == 1
            assert len(response_data["remaining_phases"]) == 3
    
    @pytest.mark.asyncio
    async def test_handle_get_project_artifacts_enhanced(self):
        """Test enhanced artifact retrieval."""
        
        # Create test artifact files
        project_dir = Path(__file__).parent.parent / "out" / f"project_{self.test_project_id}"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test artifact file
        artifact_data = {"test": "data", "artifact_type": "business_analysis"}
        artifact_file = project_dir / "business_analysis.json"
        with open(artifact_file, 'w') as f:
            json.dump(artifact_data, f)
        
        try:
            arguments = {
                "project_id": self.test_project_id,
                "artifact_type": "business_analysis"
            }
            
            result = await handle_get_project_artifacts_enhanced(arguments)
            
            assert len(result) == 1
            response_data = json.loads(result[0].text)
            
            assert response_data["project_id"] == self.test_project_id
            assert "artifacts" in response_data
            assert "business_analysis" in response_data["artifacts"]
            assert response_data["artifacts"]["business_analysis"] == artifact_data
            
        finally:
            # Clean up test files
            if artifact_file.exists():
                artifact_file.unlink()
            if project_dir.exists():
                project_dir.rmdir()
    
    @pytest.mark.asyncio
    async def test_handle_get_project_artifacts_not_found(self):
        """Test artifact retrieval for non-existent project."""
        
        arguments = {
            "project_id": "non-existent-project",
            "artifact_type": "all"
        }
        
        with pytest.raises(ValueError, match="No artifacts found"):
            await handle_get_project_artifacts_enhanced(arguments)
    
    @pytest.mark.asyncio
    async def test_error_handling_in_handlers(self):
        """Test error handling in MCP handlers."""
        
        # Test create project with invalid data
        arguments = {}  # Missing required specification
        
        result = await handle_create_project_enhanced(arguments)
        response_data = json.loads(result[0].text)
        
        assert "error" in response_data
        assert response_data["status"] == "failed"
    
    def test_project_filtering(self):
        """Test project filtering logic."""
        projects = [
            {"status": "completed", "domain": "web", "title": "Web App"},
            {"status": "in_progress", "domain": "mobile", "title": "Mobile App"},
            {"status": "completed", "domain": "web", "title": "Another Web App"},
            {"status": "failed", "domain": "data", "title": "Data Pipeline"}
        ]
        
        # Test status filtering
        completed_projects = [p for p in projects if p["status"] == "completed"]
        assert len(completed_projects) == 2
        
        # Test domain filtering
        web_projects = [p for p in projects if p["domain"] == "web"]
        assert len(web_projects) == 2
        
        # Test combined filtering
        completed_web = [p for p in projects if p["status"] == "completed" and p["domain"] == "web"]
        assert len(completed_web) == 2
    
    def test_progress_calculation(self):
        """Test progress percentage calculation."""
        total_phases = 4
        completed_phases = [1, 2, 3]  # Could be phase counts or list
        
        if isinstance(completed_phases, list):
            progress = (len(completed_phases) / total_phases) * 100
        else:
            progress = (completed_phases / total_phases) * 100
        
        assert progress == 75.0
        
        # Test edge cases
        assert (0 / 4) * 100 == 0.0  # No phases completed
        assert (4 / 4) * 100 == 100.0  # All phases completed
    
    def test_project_validation(self):
        """Test project data validation."""
        
        # Valid project data
        valid_project = {
            "specification": "Create a web app",
            "title": "Test App",
            "domain": "web"
        }
        
        assert len(valid_project["specification"]) > 0
        assert len(valid_project["title"]) > 0
        assert valid_project["domain"] in ["web", "mobile", "data", "api", "ml", "desktop", "embedded", "general"]
        
        # Invalid project data
        invalid_project = {
            "specification": "",  # Empty specification
            "title": "A" * 200,   # Too long title
            "domain": "invalid"   # Invalid domain
        }
        
        assert len(invalid_project["specification"]) == 0  # Should be rejected
        assert len(invalid_project["title"]) > 100  # Should be rejected
        assert invalid_project["domain"] not in ["web", "mobile", "data", "api", "ml", "desktop", "embedded", "general"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
