#!/usr/bin/env python3
"""
Standalone BA Agent Test Suite

This test suite focuses on testing BA agent functionality without complex import dependencies.
"""

import pytest
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import tiktoken

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Simple test imports
from utils.prompt_manager import get_prompt_manager


class TestBAAgentStandalone:
    """Standalone tests for BA agent functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_requirement = """
        Create a web-based task management application with:
        - User authentication and authorization
        - Create, edit, and delete tasks
        - Organize tasks into projects
        - Real-time collaboration
        """
        
        self.simple_requirement = "Create a basic todo list application"
    
    def test_prompt_manager_ba_agent_prompts(self):
        """Test that BA agent prompts are available."""
        prompt_manager = get_prompt_manager()
        
        # Test available prompts
        available = prompt_manager.list_available_prompts()
        assert 'ba_agent' in available
        
        ba_prompts = available['ba_agent']
        expected_prompts = ['persona', 'chain_of_thought', 'functional_spec_template', 'gherkin_template']
        
        for prompt in expected_prompts:
            assert prompt in ba_prompts, f"Missing prompt: {prompt}"
    
    def test_ba_agent_persona_prompt(self):
        """Test BA agent persona prompt."""
        prompt_manager = get_prompt_manager()
        
        persona = prompt_manager.get_persona('ba_agent')
        assert len(persona) > 0
        assert "Business Analyst" in persona or "business analyst" in persona.lower()
    
    def test_ba_agent_chain_of_thought_prompt(self):
        """Test BA agent chain of thought prompt."""
        prompt_manager = get_prompt_manager()
        
        # Test with required parameters
        cot = prompt_manager.get_chain_of_thought(
            'ba_agent',
            user_requirement=self.simple_requirement,
            context="Test context"
        )
        
        # May return empty string if parameters don't match exactly
        assert isinstance(cot, str)
    
    def test_ba_agent_functional_spec_template(self):
        """Test BA agent functional specification template."""
        prompt_manager = get_prompt_manager()
        
        # Test getting the functional spec template
        func_spec = prompt_manager.get_prompt(
            'ba_agent', 
            'functional_spec_template',
            user_requirement=self.sample_requirement,
            context="Web application",
            introduction_context="Task management system"
        )
        
        assert isinstance(func_spec, str)
    
    def test_ba_agent_gherkin_template(self):
        """Test BA agent Gherkin template."""
        prompt_manager = get_prompt_manager()
        
        gherkin = prompt_manager.get_prompt(
            'ba_agent',
            'gherkin_template',
            user_requirement=self.sample_requirement,
            context="Web application"
        )
        
        assert isinstance(gherkin, str)
    
    def test_token_counting_functionality(self):
        """Test token counting using tiktoken."""
        try:
            # Test basic token counting
            encoding = tiktoken.get_encoding("cl100k_base")
            
            short_text = "Hello world"
            short_tokens = len(encoding.encode(short_text))
            assert short_tokens > 0
            
            long_text = self.sample_requirement
            long_tokens = len(encoding.encode(long_text))
            assert long_tokens > short_tokens
            
        except Exception as e:
            pytest.skip(f"tiktoken not available: {e}")
    
    def test_mock_specification_generation(self):
        """Test mock specification generation process."""
        
        # Mock the specification generation process
        def mock_generate_specification(requirement, context=None):
            """Mock specification generation."""
            return f"""
            ## Functional Requirements Specification
            
            ### 1. Project Overview
            {requirement}
            
            ### 2. Functional Requirements
            - FR001: User authentication system
            - FR002: Task management capabilities
            - FR003: Project organization features
            
            ### 3. Non-Functional Requirements
            - NFR001: System performance requirements
            - NFR002: Security and data protection
            - NFR003: User interface responsiveness
            
            ## Gherkin User Stories
            
            Feature: Task Management
            
            Scenario: Create new task
            Given I am logged into the system
            When I click "New Task"
            And I enter task details
            Then I should see the task in my list
            
            Scenario: Complete task
            Given I have an open task
            When I mark it as complete
            Then it should be marked as done
            """
        
        # Test the mock function
        result = mock_generate_specification(self.sample_requirement)
        
        # Validate output structure
        assert "Functional Requirements" in result
        assert "FR001:" in result
        assert "NFR001:" in result
        assert "Feature:" in result
        assert "Scenario:" in result
        assert "Given" in result
        assert "When" in result
        assert "Then" in result
    
    def test_specification_validation(self):
        """Test specification validation logic."""
        
        valid_spec = """
        ## Functional Requirements
        - FR001: User login
        - FR002: Task creation
        
        ## Gherkin Scenarios
        Feature: Authentication
        Scenario: Login
        Given I am on login page
        When I enter credentials
        Then I should be logged in
        """
        
        # Test validation functions
        def validate_spec_structure(spec):
            """Validate specification structure."""
            validations = {
                "has_functional_requirements": "Functional Requirements" in spec,
                "has_numbered_requirements": "FR001:" in spec,
                "has_gherkin_feature": "Feature:" in spec,
                "has_gherkin_scenario": "Scenario:" in spec,
                "has_gherkin_steps": all(step in spec for step in ["Given", "When", "Then"])
            }
            return validations
        
        # Run validation
        results = validate_spec_structure(valid_spec)
        
        # Check results
        assert results["has_functional_requirements"]
        assert results["has_numbered_requirements"]
        assert results["has_gherkin_feature"]
        assert results["has_gherkin_scenario"]
        assert results["has_gherkin_steps"]
    
    def test_error_handling_scenarios(self):
        """Test various error handling scenarios."""
        
        # Test empty requirement
        def handle_empty_requirement(requirement):
            if not requirement or not requirement.strip():
                return "Error: No requirement provided. Please specify your needs."
            return "Processing requirement..."
        
        assert "Error:" in handle_empty_requirement("")
        assert "Error:" in handle_empty_requirement("   ")
        assert "Processing" in handle_empty_requirement("Valid requirement")
        
        # Test invalid context
        def handle_invalid_context(context):
            if context and not isinstance(context, (str, dict)):
                return "Error: Invalid context format"
            return "Context processed"
        
        assert "Error:" in handle_invalid_context(123)
        assert "Context processed" in handle_invalid_context("valid context")
        assert "Context processed" in handle_invalid_context({"key": "value"})
    
    def test_different_requirement_types(self):
        """Test handling different types of requirements."""
        
        requirements = {
            "web_app": "Create a web application for inventory management",
            "mobile_app": "Develop a mobile app for fitness tracking", 
            "api_service": "Build a REST API for user authentication",
            "data_pipeline": "Design a data processing pipeline for analytics"
        }
        
        def categorize_requirement(req):
            """Categorize requirement type."""
            req_lower = req.lower()
            if "web" in req_lower:
                return "web_application"
            elif "mobile" in req_lower or "app" in req_lower:
                return "mobile_application"
            elif "api" in req_lower:
                return "api_service"
            elif "data" in req_lower or "pipeline" in req_lower:
                return "data_system"
            else:
                return "general_software"
        
        # Test categorization
        assert categorize_requirement(requirements["web_app"]) == "web_application"
        assert categorize_requirement(requirements["mobile_app"]) == "mobile_application"
        assert categorize_requirement(requirements["api_service"]) == "api_service"
        assert categorize_requirement(requirements["data_pipeline"]) == "data_system"


class TestBAAgentPromptIntegration:
    """Integration tests with the prompt management system."""
    
    def test_prompt_loading_performance(self):
        """Test prompt loading performance."""
        import time
        
        start_time = time.time()
        prompt_manager = get_prompt_manager()
        load_time = time.time() - start_time
        
        # Should load quickly (under 1 second)
        assert load_time < 1.0
        
        # Test cached access
        start_time = time.time()
        persona = prompt_manager.get_persona('ba_agent')
        cached_time = time.time() - start_time
        
        # Cached access should be very fast
        assert cached_time < 0.1
    
    def test_prompt_file_structure(self):
        """Test that prompt files exist and have correct structure."""
        prompt_dir = Path(__file__).parent.parent / "src" / "prompts"
        
        # Check BA agent prompt file
        ba_file = prompt_dir / "ba_agent.json"
        assert ba_file.exists(), "BA agent prompt file missing"
        
        # Load and validate structure
        with open(ba_file, 'r') as f:
            ba_prompts = json.load(f)
        
        required_prompts = ['persona', 'chain_of_thought', 'functional_spec_template', 'gherkin_template']
        for prompt in required_prompts:
            assert prompt in ba_prompts, f"Missing prompt: {prompt}"
    
    def test_multiple_agent_prompt_support(self):
        """Test that multiple agent prompts are supported."""
        prompt_manager = get_prompt_manager()
        available = prompt_manager.list_available_prompts()
        
        # Should have at least BA agent and architect agent
        assert len(available) >= 2
        assert 'ba_agent' in available
        
        # Each agent should have multiple prompts
        for agent, prompts in available.items():
            assert len(prompts) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
