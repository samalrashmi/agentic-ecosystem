#!/usr/bin/env python3
"""
Test suite for Business Analyst Agent Tool (Legacy)

This module tests the analyze_business_requirements tool for backward compatibility.
For testing the Enhanced BA Agent, see test_enhanced_ba_agent.py
"""

import pytest
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import the enhanced BA agent instead
from agents.enhanced_ba_agent import EnhancedBAAgent


#!/usr/bin/env python3
"""
Test suite for Business Analyst Agent (Legacy Compatibility)

This module provides backward compatibility tests for the BA agent functionality.
For comprehensive testing of the Enhanced BA Agent, see test_enhanced_ba_agent.py
"""

import pytest
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.enhanced_ba_agent import EnhancedBAAgent
from models import Message, AgentType


class TestBAAgentCompatibility:
    """Test cases for BA Agent backward compatibility."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = EnhancedBAAgent()
        self.test_project_id = "test-ba-project-123"
        self.sample_specification = """
        Create a web-based task management application with the following features:
        - User authentication and authorization
        - Create, edit, and delete tasks
        - Organize tasks into projects
        - Real-time collaboration with team members
        - Mobile-responsive design
        - Notification system for deadlines
        - File attachments for tasks
        - Search and filter functionality
        """
    
    def test_ba_agent_initialization(self):
        """Test that BA agent initializes correctly."""
        assert isinstance(self.agent, EnhancedBAAgent)
        assert self.agent.agent_type == AgentType.BUSINESS_ANALYST
    
    @patch('agents.enhanced_ba_agent.EnhancedBAAgent._call_llm')
    def test_specification_generation_compatibility(self, mock_llm):
        """Test specification generation for backward compatibility."""
        mock_response = """
        ## Business Analysis Results

        ### User Stories
        1. **US001: User Registration**
           - As a new user, I want to register an account so that I can access the task management system
           - Acceptance Criteria: User can enter email and password, System validates email format
           - Priority: High, Story Points: 5

        2. **US002: Create Task**  
           - As a user, I want to create tasks so that I can organize my work
           - Acceptance Criteria: User can enter task title and description, User can set due date
           - Priority: High, Story Points: 3

        ### Requirements Analysis
        **Functional Requirements:**
        - User authentication system
        - Task CRUD operations
        - Project organization

        **Non-Functional Requirements:**
        - Mobile responsiveness
        - Real-time updates
        - Security and data protection

        ### Business Rules
        - Users can only access their own tasks
        - Project owners can invite team members
        - Tasks must have at least a title

        ### Gherkin Scenarios

        Feature: Task Management
        
        Scenario: Create a new task
        Given I am logged into the system
        When I click "New Task" button
        And I enter "Complete project proposal" as the task title
        And I click "Save Task"
        Then I should see the task in my task list
        And the task should have a status of "Open"
        """
        
        mock_llm.return_value = mock_response
        
        # Test specification generation
        result = self.agent.generate_specification(self.sample_specification)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "User Stories" in result
        assert "Requirements Analysis" in result
        assert "Business Rules" in result
        assert "Gherkin" in result or "Scenario:" in result
    
    @patch('agents.enhanced_ba_agent.EnhancedBAAgent._call_llm')
    def test_empty_specification_handling(self, mock_llm):
        """Test handling of empty specification."""
        mock_llm.return_value = "No specific requirements provided. Please provide more details."
        
        result = self.agent.generate_specification("")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    @patch('agents.enhanced_ba_agent.EnhancedBAAgent._call_llm')
    def test_error_handling(self, mock_llm):
        """Test error handling when processing fails."""
        mock_llm.side_effect = Exception("Processing error")
        
        result = self.agent.generate_specification(self.sample_specification)
        
        # Should return error information instead of crashing
        assert isinstance(result, str)
        assert "error" in result.lower() or "failed" in result.lower()
    
    def test_user_story_format_validation(self):
        """Test that user stories follow proper format."""
        with patch.object(self.agent, '_call_llm') as mock_llm:
            mock_llm.return_value = """
            ### User Stories
            
            **US001: User Authentication**
            As a user, I want to log in so that I can access my tasks
            
            **US002: Task Creation**  
            As a user, I want to create tasks so that I can organize my work
            """
            
            result = self.agent.generate_specification(self.sample_specification)
            
            # Validate user story format
            assert "As a" in result or "As an" in result
            assert "I want" in result
            assert "so that" in result or "in order to" in result
    
    def test_requirements_structure(self):
        """Test that requirements are properly structured."""
        with patch.object(self.agent, '_call_llm') as mock_llm:
            mock_llm.return_value = """
            ### Requirements Analysis
            
            **Functional Requirements:**
            - User authentication
            - Task creation and management
            - Project organization
            
            **Non-Functional Requirements:**
            - Mobile responsiveness
            - Real-time updates
            - Security compliance
            """
            
            result = self.agent.generate_specification(self.sample_specification)
            
            assert "Functional Requirements" in result
            assert "Non-Functional Requirements" in result
    
    def test_business_rules_inclusion(self):
        """Test that business rules are included in output."""
        with patch.object(self.agent, '_call_llm') as mock_llm:
            mock_llm.return_value = """
            ### Business Rules
            - Users can only access their own data
            - Admin users can manage all projects
            - Tasks must have a title and description
            """
            
            result = self.agent.generate_specification(self.sample_specification)
            
            assert "Business Rules" in result or "business rules" in result.lower()
    
    def test_gherkin_scenario_structure(self):
        """Test that Gherkin scenarios are properly formatted."""
        with patch.object(self.agent, '_call_llm') as mock_llm:
            mock_llm.return_value = """
            ### Gherkin Scenarios
            
            Feature: User Authentication
            
            Scenario: Successful login
            Given I am on the login page
            When I enter valid credentials
            And I click the login button
            Then I should be redirected to the dashboard
            And I should see my username displayed
            
            Scenario: Failed login attempt
            Given I am on the login page
            When I enter invalid credentials
            And I click the login button
            Then I should see an error message
            And I should remain on the login page
            """
            
            result = self.agent.generate_specification(self.sample_specification)
            
            # Validate Gherkin structure
            assert "Feature:" in result
            assert "Scenario:" in result
            assert "Given" in result
            assert "When" in result
            assert "Then" in result
    
    def test_token_management(self):
        """Test that token management works correctly."""
        # Test token counting
        tokens = self.agent.count_tokens(self.sample_specification)
        assert isinstance(tokens, int)
        assert tokens > 0
        
        # Test that token limits are respected
        assert self.agent.max_tokens > 0
        assert self.agent.current_tokens >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
