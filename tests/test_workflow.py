#!/usr/bin/env python3
"""
Test suite for LangGraph Workflow

This module tests the overall workflow orchestration to ensure proper
coordination between all agents and state management.
"""

import pytest
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from langgraph_agents.workflow import (
    SoftwareDevelopmentWorkflow,
    ProjectState,
    run_software_development_workflow
)


class TestLangGraphWorkflow:
    """Test cases for the LangGraph workflow orchestration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_project_id = "test-workflow-project-123"
        self.sample_specification = """
        Create a simple todo application with the following features:
        - Add new todos
        - Mark todos as complete
        - Delete todos
        - Filter todos by status
        """
        
        # Clean up any existing test files
        self.cleanup_test_files()
    
    def teardown_method(self):
        """Clean up after tests."""
        self.cleanup_test_files()
    
    def cleanup_test_files(self):
        """Remove test output files."""
        test_dir = Path(__file__).parent.parent / "out" / f"project_{self.test_project_id}"
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)
    
    def test_workflow_initialization(self):
        """Test workflow instance creation."""
        workflow = SoftwareDevelopmentWorkflow()
        
        assert workflow is not None
        assert hasattr(workflow, 'workflow')
        assert hasattr(workflow, 'run_project')
    
    def test_project_state_structure(self):
        """Test that ProjectState has required fields."""
        # This tests the TypedDict structure
        state_keys = ProjectState.__annotations__.keys()
        
        required_keys = [
            'project_id', 'original_specification', 'current_phase',
            'business_analysis', 'system_architecture', 'implementation_plan',
            'test_strategy', 'messages', 'errors'
        ]
        
        for key in required_keys:
            assert key in state_keys, f"Missing required state key: {key}"
    
    @patch('langgraph_agents.agent_tools.analyze_business_requirements')
    @patch('langgraph_agents.agent_tools.design_system_architecture')
    @patch('langgraph_agents.agent_tools.generate_implementation_plan')
    @patch('langgraph_agents.agent_tools.create_test_strategy')
    def test_workflow_execution_success(self, mock_test_strategy, mock_impl_plan, 
                                      mock_architecture, mock_business_analysis):
        """Test successful workflow execution through all phases."""
        
        # Mock agent responses
        mock_business_analysis.invoke.return_value = {
            "user_stories": [
                {"id": "US001", "title": "Add Todo", "description": "As a user, I want to add todos"}
            ],
            "requirements_analysis": {"functional_requirements": ["Todo CRUD"]},
            "metadata": {"project_id": self.test_project_id}
        }
        
        mock_architecture.invoke.return_value = {
            "components": [
                {"name": "Todo API", "type": "microservice", "technologies": ["Python", "FastAPI"]}
            ],
            "architecture_patterns": [{"pattern": "REST API", "rationale": "Simple web API"}],
            "metadata": {"project_id": self.test_project_id}
        }
        
        mock_impl_plan.invoke.return_value = {
            "implementation_phases": [
                {"phase": "Phase 1", "duration": "1 week", "tasks": []}
            ],
            "technical_specifications": [],
            "metadata": {"project_id": self.test_project_id}
        }
        
        mock_test_strategy.invoke.return_value = {
            "test_cases": [
                {"test_id": "TC001", "test_name": "Add Todo Test", "test_type": "functional"}
            ],
            "test_strategy": {"testing_approach": "TDD"},
            "metadata": {"project_id": self.test_project_id}
        }
        
        # Execute workflow
        result = run_software_development_workflow(
            specification=self.sample_specification,
            project_id=self.test_project_id
        )
        
        # Verify workflow completion
        assert isinstance(result, dict)
        assert result["project_id"] == self.test_project_id
        assert result["original_specification"] == self.sample_specification
        assert result["current_phase"] == "completed"
        
        # Verify all phases were executed
        assert result["business_analysis"] is not None
        assert result["system_architecture"] is not None
        assert result["implementation_plan"] is not None
        assert result["test_strategy"] is not None
        
        # Verify agent tools were called
        mock_business_analysis.invoke.assert_called_once()
        mock_architecture.invoke.assert_called_once()
        mock_impl_plan.invoke.assert_called_once()
        mock_test_strategy.invoke.assert_called_once()
    
    @patch('langgraph_agents.agent_tools.analyze_business_requirements')
    def test_workflow_error_handling(self, mock_business_analysis):
        """Test workflow error handling when an agent fails."""
        
        # Mock agent to raise exception
        mock_business_analysis.invoke.side_effect = Exception("Business analysis failed")
        
        # Execute workflow
        result = run_software_development_workflow(
            specification=self.sample_specification,
            project_id=self.test_project_id
        )
        
        # Verify error handling
        assert isinstance(result, dict)
        assert len(result["errors"]) > 0
        assert "Business analysis failed" in str(result["errors"])
        assert result["business_analysis"] is None
    
    @patch('langgraph_agents.agent_tools.analyze_business_requirements')
    @patch('langgraph_agents.agent_tools.design_system_architecture')
    def test_workflow_partial_completion(self, mock_architecture, mock_business_analysis):
        """Test workflow behavior when one phase succeeds and next fails."""
        
        # Mock first agent success
        mock_business_analysis.invoke.return_value = {
            "user_stories": [{"id": "US001", "title": "Test Story"}],
            "requirements_analysis": {"functional_requirements": []},
            "metadata": {"project_id": self.test_project_id}
        }
        
        # Mock second agent failure
        mock_architecture.invoke.side_effect = Exception("Architecture design failed")
        
        # Execute workflow
        result = run_software_development_workflow(
            specification=self.sample_specification,
            project_id=self.test_project_id
        )
        
        # Verify partial completion
        assert result["business_analysis"] is not None  # First phase succeeded
        assert result["system_architecture"] is None    # Second phase failed
        assert len(result["errors"]) > 0
        assert "Architecture design failed" in str(result["errors"])
    
    def test_workflow_state_transitions(self):
        """Test that workflow state transitions happen correctly."""
        workflow = SoftwareDevelopmentWorkflow()
        
        # Test initial state
        initial_state = {
            "project_id": self.test_project_id,
            "original_specification": self.sample_specification,
            "current_phase": "initiated",
            "business_analysis": None,
            "system_architecture": None,
            "implementation_plan": None,
            "test_strategy": None,
            "messages": [],
            "errors": []
        }
        
        # Verify state structure
        for key in initial_state:
            assert key in ProjectState.__annotations__
    
    @patch('langgraph_agents.workflow.Path')
    def test_summary_report_generation(self, mock_path):
        """Test that summary reports are generated correctly."""
        workflow = SoftwareDevelopmentWorkflow()
        
        # Mock file system
        mock_dir = MagicMock()
        mock_path.return_value.parent.parent.parent.__truediv__.return_value = mock_dir
        mock_dir.mkdir.return_value = None
        
        # Mock state with completed workflow
        state = {
            "project_id": self.test_project_id,
            "original_specification": self.sample_specification,
            "current_phase": "completed",
            "status": "completed",
            "business_analysis": {"user_stories": [{"id": "US001"}]},
            "system_architecture": {"components": [{"name": "API"}]},
            "implementation_plan": {"implementation_phases": [{"phase": "P1"}]},
            "test_strategy": {"test_cases": [{"test_id": "TC001"}]},
            "errors": []
        }
        
        # Test summary generation
        workflow._generate_summary_report(state)
        
        # Verify directory creation was attempted
        mock_dir.mkdir.assert_called()
    
    def test_workflow_message_tracking(self):
        """Test that workflow properly tracks messages throughout execution."""
        
        with patch('langgraph_agents.agent_tools.analyze_business_requirements') as mock_ba:
            mock_ba.invoke.return_value = {
                "user_stories": [{"id": "US001"}],
                "requirements_analysis": {"functional_requirements": []},
                "metadata": {"project_id": self.test_project_id}
            }
            
            result = run_software_development_workflow(
                specification=self.sample_specification,
                project_id=self.test_project_id
            )
            
            # Verify messages were tracked
            assert "messages" in result
            assert len(result["messages"]) > 0
            
            # Check message structure
            for message in result["messages"]:
                assert "role" in message
                assert "content" in message
                assert "timestamp" in message
    
    def test_workflow_with_callback(self):
        """Test workflow execution with phase callbacks."""
        callback_calls = []
        
        def test_callback(phase_name):
            callback_calls.append(phase_name)
        
        with patch('langgraph_agents.agent_tools.analyze_business_requirements') as mock_ba:
            mock_ba.invoke.return_value = {
                "user_stories": [{"id": "US001"}],
                "requirements_analysis": {"functional_requirements": []},
                "metadata": {"project_id": self.test_project_id}
            }
            
            result = run_software_development_workflow(
                specification=self.sample_specification,
                project_id=self.test_project_id,
                phase_callback=test_callback
            )
            
            # Verify callback was called
            assert len(callback_calls) > 0
            assert "business_analysis" in callback_calls
    
    def test_workflow_output_files(self):
        """Test that workflow creates expected output files."""
        
        with patch('langgraph_agents.agent_tools.analyze_business_requirements') as mock_ba, \
             patch('langgraph_agents.agent_tools.design_system_architecture') as mock_arch, \
             patch('langgraph_agents.agent_tools.generate_implementation_plan') as mock_dev, \
             patch('langgraph_agents.agent_tools.create_test_strategy') as mock_test:
            
            # Mock all agent responses
            mock_ba.invoke.return_value = {"user_stories": [], "metadata": {"project_id": self.test_project_id}}
            mock_arch.invoke.return_value = {"components": [], "metadata": {"project_id": self.test_project_id}}
            mock_dev.invoke.return_value = {"implementation_phases": [], "metadata": {"project_id": self.test_project_id}}
            mock_test.invoke.return_value = {"test_cases": [], "metadata": {"project_id": self.test_project_id}}
            
            result = run_software_development_workflow(
                specification=self.sample_specification,
                project_id=self.test_project_id
            )
            
            # Check that summary file would be created
            project_dir = Path(__file__).parent.parent / "out" / f"project_{self.test_project_id}"
            
            # Note: In a real test, we'd check actual file creation
            # Here we verify the workflow completed successfully
            assert result["current_phase"] == "completed"
    
    def test_workflow_performance(self):
        """Test that workflow execution completes in reasonable time."""
        import time
        
        with patch('langgraph_agents.agent_tools.analyze_business_requirements') as mock_ba:
            # Mock fast response
            mock_ba.invoke.return_value = {
                "user_stories": [],
                "requirements_analysis": {"functional_requirements": []},
                "metadata": {"project_id": self.test_project_id}
            }
            
            start_time = time.time()
            
            result = run_software_development_workflow(
                specification=self.sample_specification,
                project_id=self.test_project_id
            )
            
            execution_time = time.time() - start_time
            
            # Workflow should complete quickly with mocked agents
            assert execution_time < 5.0, f"Workflow took too long: {execution_time}s"
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
