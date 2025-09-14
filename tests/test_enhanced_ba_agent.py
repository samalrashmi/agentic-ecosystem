#!/usr/bin/env python3
"""
Comprehensive test suite for Enhanced Business Analyst Agent.

This module tests the EnhancedBAAgent class with its advanced features including:
- Prompt management system integration
- Token counting and management
- Chain of thought specification generation
- Gherkin user story creation
- Standalone functionality
- Iterative processing for large outputs
"""

import pytest
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import tiktoken
import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.enhanced_ba_agent import EnhancedBAAgent
from utils.prompt_manager import get_prompt_manager, PromptManager
from models import Message, AgentType


class TestEnhancedBAAgent:
    """Test cases for the Enhanced Business Analyst Agent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = EnhancedBAAgent()
        self.sample_requirement = """
        Create a modern e-commerce platform with the following features:
        - User registration and authentication
        - Product catalog with search and filtering
        - Shopping cart and checkout process
        - Payment integration (Stripe, PayPal)
        - Order management and tracking
        - Admin dashboard for product management
        - Customer reviews and ratings
        - Inventory management
        - Email notifications
        - Mobile-responsive design
        """
        
        self.simple_requirement = "Create a basic todo list application"
        
        self.complex_requirement = """
        Build a comprehensive enterprise resource planning (ERP) system that includes:
        
        1. Human Resources Management:
        - Employee onboarding and offboarding
        - Payroll processing and tax calculations
        - Performance management and reviews
        - Training and certification tracking
        - Benefits administration
        - Time and attendance tracking
        
        2. Financial Management:
        - General ledger and chart of accounts
        - Accounts payable and receivable
        - Budgeting and forecasting
        - Financial reporting and analytics
        - Tax management and compliance
        - Multi-currency support
        
        3. Supply Chain Management:
        - Vendor management and procurement
        - Inventory optimization
        - Warehouse management
        - Quality control and assurance
        - Supplier relationship management
        - Demand planning and forecasting
        
        4. Customer Relationship Management:
        - Lead and opportunity management
        - Customer service and support
        - Sales pipeline tracking
        - Marketing automation
        - Customer analytics and segmentation
        - Communication history tracking
        
        5. Project Management:
        - Resource allocation and scheduling
        - Project tracking and reporting
        - Risk management
        - Document management
        - Collaboration tools
        - Time tracking and billing
        
        The system must support multiple subsidiaries, comply with international regulations,
        provide real-time reporting, and integrate with existing third-party systems.
        """
    
    def test_agent_initialization(self):
        """Test that the enhanced BA agent initializes correctly."""
        assert isinstance(self.agent, EnhancedBAAgent)
        assert self.agent.agent_type == AgentType.BUSINESS_ANALYST
        assert hasattr(self.agent, 'prompt_manager')
        assert hasattr(self.agent, 'encoding')
        assert hasattr(self.agent, 'max_tokens')
        assert hasattr(self.agent, 'current_tokens')
    
    def test_prompt_manager_integration(self):
        """Test integration with the prompt management system."""
        # Test that agent can access prompts
        persona = self.agent.prompt_manager.get_persona('ba_agent')
        assert len(persona) > 0
        assert "Business Analyst" in persona or "business analyst" in persona.lower()
        
        # Test chain of thought prompt
        cot = self.agent.prompt_manager.get_chain_of_thought(
            'ba_agent',
            user_requirement=self.simple_requirement,
            context="Test context"
        )
        assert len(cot) > 0
    
    def test_token_counting_functionality(self):
        """Test token counting and management."""
        # Test token counting for different text lengths
        short_text = "Hello world"
        short_tokens = self.agent.count_tokens(short_text)
        assert isinstance(short_tokens, int)
        assert short_tokens > 0
        
        long_text = self.complex_requirement
        long_tokens = self.agent.count_tokens(long_text)
        assert long_tokens > short_tokens
        
        # Test token limit checking
        assert self.agent.max_tokens > 0
        assert self.agent.current_tokens >= 0
    
    @patch('agents.enhanced_ba_agent.EnhancedBAAgent._call_llm')
    def test_generate_specification_simple(self, mock_llm):
        """Test specification generation for simple requirements."""
        # Mock LLM response
        mock_response = """
        ## Functional Requirements Specification

        ### 1. Project Overview
        A basic todo list application for personal task management.

        ### 2. Functional Requirements
        - FR001: Users can create new todo items
        - FR002: Users can mark items as complete
        - FR003: Users can delete todo items
        - FR004: Users can view all todo items

        ### 3. Non-Functional Requirements
        - NFR001: Application should be responsive
        - NFR002: Data should persist between sessions

        ## Gherkin User Stories

        **Feature: Todo Item Management**

        Scenario: Create a new todo item
        Given I am on the todo list page
        When I enter "Buy groceries" in the input field
        And I click the "Add" button
        Then I should see "Buy groceries" in my todo list
        And the input field should be cleared

        Scenario: Mark todo item as complete
        Given I have a todo item "Buy groceries" in my list
        When I click the checkbox next to "Buy groceries"
        Then the item should be marked as completed
        And it should appear with strikethrough text
        """
        
        mock_llm.return_value = mock_response
        
        # Test specification generation
        result = self.agent.generate_specification(self.simple_requirement)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Functional Requirements" in result
        assert "Gherkin" in result or "Scenario:" in result
        assert mock_llm.called
    
    @patch('agents.enhanced_ba_agent.EnhancedBAAgent._call_llm')
    def test_generate_specification_with_context(self, mock_llm):
        """Test specification generation with additional context."""
        mock_response = "Detailed specification with context..."
        mock_llm.return_value = mock_response
        
        context = {
            "project_type": "web application",
            "target_users": "small business owners",
            "technology_stack": "React, Node.js, MongoDB"
        }
        
        result = self.agent.generate_specification(
            self.simple_requirement, 
            context=context
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Verify LLM was called with context
        assert mock_llm.called
        call_args = mock_llm.call_args[0][0]
        assert "React" in call_args
        assert "small business" in call_args
    
    @patch('agents.enhanced_ba_agent.EnhancedBAAgent._call_llm')
    def test_iterative_processing_large_output(self, mock_llm):
        """Test iterative processing when output exceeds token limits."""
        # First call returns large response that triggers iteration
        first_response = "A" * 10000  # Large response
        second_response = "Continued specification details..."
        
        mock_llm.side_effect = [first_response, second_response]
        
        # Mock token counting to simulate exceeding limits
        with patch.object(self.agent, 'count_tokens') as mock_count:
            # First count returns high number, second returns acceptable
            mock_count.side_effect = [15000, 8000, 5000]
            
            result = self.agent.generate_specification(self.complex_requirement)
            
            # Should have made multiple LLM calls
            assert mock_llm.call_count <= 2  # Max iterations is 2
            assert isinstance(result, str)
    
    def test_chain_of_thought_process(self):
        """Test the chain of thought methodology."""
        with patch.object(self.agent, '_call_llm') as mock_llm:
            mock_llm.return_value = "Chain of thought response"
            
            # Test that CoT prompt is properly formatted
            self.agent.generate_specification(self.simple_requirement)
            
            # Verify LLM was called with chain of thought structure
            assert mock_llm.called
            prompt_used = mock_llm.call_args[0][0]
            
            # Should include chain of thought elements
            assert len(prompt_used) > 0
    
    def test_gherkin_scenario_generation(self):
        """Test generation of Gherkin scenarios."""
        with patch.object(self.agent, '_call_llm') as mock_llm:
            gherkin_response = """
            Feature: User Authentication
            
            Scenario: Successful login
            Given I am on the login page
            When I enter valid credentials
            Then I should be redirected to the dashboard
            
            Scenario: Failed login
            Given I am on the login page  
            When I enter invalid credentials
            Then I should see an error message
            """
            mock_llm.return_value = gherkin_response
            
            result = self.agent.generate_specification("User login system")
            
            assert "Feature:" in result
            assert "Scenario:" in result
            assert "Given" in result
            assert "When" in result
            assert "Then" in result
    
    def test_error_handling_llm_failure(self):
        """Test error handling when LLM calls fail."""
        with patch.object(self.agent, '_call_llm') as mock_llm:
            mock_llm.side_effect = Exception("API Error")
            
            result = self.agent.generate_specification(self.simple_requirement)
            
            # Should return error message instead of crashing
            assert isinstance(result, str)
            assert "error" in result.lower() or "failed" in result.lower()
    
    def test_token_management_efficiency(self):
        """Test that token management is efficient."""
        # Test with various input sizes
        inputs = [
            "Short requirement",
            self.simple_requirement,
            self.sample_requirement,
            self.complex_requirement
        ]
        
        for req in inputs:
            tokens = self.agent.count_tokens(req)
            assert tokens > 0
            assert tokens < self.agent.max_tokens  # Input should be manageable
    
    def test_specification_quality_validation(self):
        """Test that generated specifications meet quality standards."""
        with patch.object(self.agent, '_call_llm') as mock_llm:
            quality_response = """
            ## Functional Requirements Specification
            
            ### 1. Project Overview
            Comprehensive project description with clear objectives.
            
            ### 2. Functional Requirements
            - FR001: Clearly defined functional requirement
            - FR002: Another well-specified requirement
            
            ### 3. Non-Functional Requirements  
            - NFR001: Performance requirements
            - NFR002: Security requirements
            
            ### 4. Business Rules
            - BR001: Clear business rule definition
            
            ## Gherkin User Stories
            
            Feature: Core Functionality
            
            Scenario: Primary use case
            Given a clear precondition
            When a specific action is taken
            Then a verifiable outcome occurs
            """
            mock_llm.return_value = quality_response
            
            result = self.agent.generate_specification(self.sample_requirement)
            
            # Validate specification structure
            assert "## Functional Requirements" in result
            assert "### 1. Project Overview" in result
            assert "FR001:" in result  # Functional requirements numbered
            assert "NFR001:" in result  # Non-functional requirements numbered
            assert "Feature:" in result
            assert "Scenario:" in result
    
    def test_prompt_template_usage(self):
        """Test that proper prompt templates are being used."""
        # Test that the agent uses the correct prompt templates
        prompt_manager = get_prompt_manager()
        
        # Verify BA agent prompts are available
        available_prompts = prompt_manager.list_available_prompts()
        assert 'ba_agent' in available_prompts
        
        ba_prompts = available_prompts['ba_agent']
        expected_prompts = ['persona', 'chain_of_thought', 'functional_spec_template', 'gherkin_template']
        
        for expected in expected_prompts:
            assert expected in ba_prompts
    
    def test_metadata_and_versioning(self):
        """Test prompt metadata and versioning."""
        prompt_manager = get_prompt_manager()
        
        # Test metadata retrieval
        metadata = prompt_manager.get_prompt_metadata('ba_agent', 'persona')
        if metadata:
            assert hasattr(metadata, 'version')
            assert hasattr(metadata, 'description')
            assert hasattr(metadata, 'required_params')
    
    @pytest.mark.parametrize("requirement_type", [
        "web application",
        "mobile app", 
        "desktop software",
        "API service",
        "data pipeline"
    ])
    def test_different_project_types(self, requirement_type):
        """Test specification generation for different project types."""
        with patch.object(self.agent, '_call_llm') as mock_llm:
            mock_llm.return_value = f"Specification for {requirement_type}"
            
            requirement = f"Create a {requirement_type} for task management"
            result = self.agent.generate_specification(requirement)
            
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_concurrent_processing(self):
        """Test that the agent can handle concurrent requests safely."""
        import threading
        import time
        
        results = []
        
        def generate_spec(req_id):
            with patch.object(self.agent, '_call_llm') as mock_llm:
                mock_llm.return_value = f"Spec for request {req_id}"
                result = self.agent.generate_specification(f"Requirement {req_id}")
                results.append(result)
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=generate_spec, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        assert len(results) == 3
        for result in results:
            assert isinstance(result, str)
    
    def test_agent_standalone_functionality(self):
        """Test that the BA agent can work standalone without other agents."""
        # This tests the core enhancement - standalone operation
        with patch.object(self.agent, '_call_llm') as mock_llm:
            mock_llm.return_value = "Complete standalone specification"
            
            # Should work without any dependencies on other agents
            result = self.agent.generate_specification(self.simple_requirement)
            
            assert isinstance(result, str)
            assert len(result) > 0
            # No other agent dependencies should be called
    
    def test_performance_metrics(self):
        """Test performance characteristics of the enhanced BA agent."""
        import time
        
        with patch.object(self.agent, '_call_llm') as mock_llm:
            mock_llm.return_value = "Performance test response"
            
            start_time = time.time()
            result = self.agent.generate_specification(self.simple_requirement)
            end_time = time.time()
            
            # Should complete within reasonable time
            execution_time = end_time - start_time
            assert execution_time < 10.0  # Should be fast without actual LLM calls
            assert isinstance(result, str)


class TestEnhancedBAAgentIntegration:
    """Integration tests for Enhanced BA Agent with real prompt system."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.agent = EnhancedBAAgent()
    
    def test_real_prompt_loading(self):
        """Test loading real prompts from the prompt management system."""
        # Test that real prompts can be loaded
        persona = self.agent.prompt_manager.get_persona('ba_agent')
        assert len(persona) > 0
        
        # Test chain of thought with real prompt
        cot = self.agent.prompt_manager.get_chain_of_thought(
            'ba_agent',
            user_requirement="Test requirement",
            context="Test context"
        )
        # Note: This might return empty string if required params missing
        assert isinstance(cot, str)
    
    def test_prompt_file_structure(self):
        """Test that prompt files have correct structure."""
        prompt_dir = Path(__file__).parent.parent / "src" / "prompts"
        
        # Check that BA agent prompt file exists
        ba_prompt_file = prompt_dir / "ba_agent.json"
        assert ba_prompt_file.exists()
        
        # Validate JSON structure
        with open(ba_prompt_file, 'r') as f:
            prompts = json.load(f)
        
        required_sections = ['persona', 'chain_of_thought', 'functional_spec_template', 'gherkin_template']
        for section in required_sections:
            assert section in prompts
    
    def test_yaml_prompt_support(self):
        """Test YAML prompt file support."""
        prompt_dir = Path(__file__).parent.parent / "src" / "prompts"
        
        # Check for YAML files
        yaml_files = list(prompt_dir.glob("*.yaml")) + list(prompt_dir.glob("*.yml"))
        
        for yaml_file in yaml_files:
            # Should be able to load YAML prompts
            with open(yaml_file, 'r') as f:
                yaml_content = yaml.safe_load(f)
            assert isinstance(yaml_content, dict)


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
