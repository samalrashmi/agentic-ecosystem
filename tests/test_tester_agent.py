#!/usr/bin/env python3
"""
Test suite for Tester Agent Tool

This module tests the create_test_strategy tool to ensure it properly
creates comprehensive test strategies based on implementation plans.
"""

import pytest
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from langgraph_agents.agent_tools import create_test_strategy


class TestTesterAgent:
    """Test cases for the Tester Agent tool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_project_id = "test-tester-project-123"
        self.sample_implementation_plan = json.dumps({
            "implementation_phases": [
                {
                    "phase": "Phase 1: Authentication Service",
                    "tasks": [
                        {
                            "task": "Implement user registration",
                            "description": "Create registration endpoints",
                            "deliverables": ["Registration API", "Input validation"]
                        },
                        {
                            "task": "Implement user login",
                            "description": "Create login with JWT",
                            "deliverables": ["Login API", "JWT implementation"]
                        }
                    ]
                }
            ],
            "technical_specifications": [
                {
                    "component": "User Authentication Service",
                    "api_endpoints": [
                        {"method": "POST", "path": "/auth/register", "description": "User registration"},
                        {"method": "POST", "path": "/auth/login", "description": "User login"}
                    ]
                }
            ]
        })
        
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
    
    @pytest.mark.asyncio
    async def test_create_test_strategy_basic(self):
        """Test basic test strategy creation."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "test_cases": [
                    {
                        "test_id": "TC001",
                        "test_name": "User Registration - Valid Data",
                        "test_type": "functional",
                        "priority": "High",
                        "description": "Test user registration with valid email and password",
                        "preconditions": ["Database is accessible", "Registration endpoint is available"],
                        "test_steps": [
                            "Send POST request to /auth/register with valid email and password",
                            "Verify response status is 201",
                            "Verify user is created in database",
                            "Verify confirmation email is sent"
                        ],
                        "expected_results": [
                            "Response status: 201 Created",
                            "Response contains user ID",
                            "User record exists in database",
                            "Confirmation email sent"
                        ],
                        "test_data": {
                            "valid_email": "test@example.com",
                            "valid_password": "SecurePass123!"
                        }
                    },
                    {
                        "test_id": "TC002",
                        "test_name": "User Login - Valid Credentials",
                        "test_type": "functional",
                        "priority": "High",
                        "description": "Test user login with valid credentials",
                        "preconditions": ["User account exists", "Login endpoint is available"],
                        "test_steps": [
                            "Send POST request to /auth/login with valid credentials",
                            "Verify response status is 200",
                            "Verify JWT token is returned",
                            "Verify token is valid"
                        ],
                        "expected_results": [
                            "Response status: 200 OK",
                            "Response contains JWT token",
                            "Token can be validated",
                            "Token contains user information"
                        ],
                        "test_data": {
                            "email": "test@example.com",
                            "password": "SecurePass123!"
                        }
                    }
                ],
                "test_strategy": {
                    "testing_approach": "Risk-based testing focusing on critical user authentication flows",
                    "test_levels": ["Unit Testing", "Integration Testing", "API Testing", "End-to-End Testing"],
                    "test_types": ["Functional", "Security", "Performance", "Usability"],
                    "automation_strategy": "Automate API tests and critical user flows, manual testing for usability",
                    "test_environment": "Dedicated testing environment with test database"
                },
                "test_coverage": {
                    "functional_coverage": [
                        "User registration flows",
                        "User authentication flows",
                        "Input validation",
                        "Error handling"
                    ],
                    "security_coverage": [
                        "SQL injection prevention",
                        "Password security",
                        "JWT token security",
                        "Input sanitization"
                    ],
                    "performance_coverage": [
                        "API response times",
                        "Concurrent user load",
                        "Database performance"
                    ]
                },
                "automation_framework": {
                    "api_testing": "pytest + requests",
                    "ui_testing": "Selenium WebDriver",
                    "performance_testing": "Apache JMeter",
                    "security_testing": "OWASP ZAP"
                }
            })
            mock_llm.invoke.return_value = mock_response
            
            # Execute the tool
            result = create_test_strategy.invoke({
                "implementation_plan": self.sample_implementation_plan,
                "project_id": self.test_project_id
            })
            
            # Verify results structure
            assert isinstance(result, dict)
            assert "test_cases" in result
            assert "test_strategy" in result
            assert "test_coverage" in result
            assert "automation_framework" in result
            assert "created_at" in result
            
            # Verify test cases structure
            test_cases = result["test_cases"]
            assert len(test_cases) >= 2
            
            for test_case in test_cases:
                assert "test_id" in test_case
                assert "test_name" in test_case
                assert "test_type" in test_case
                assert "priority" in test_case
                assert "description" in test_case
                assert "preconditions" in test_case
                assert "test_steps" in test_case
                assert "expected_results" in test_case
                assert "test_data" in test_case
            
            # Verify metadata
            assert result["project_id"] == self.test_project_id
            assert "created_at" in result
            assert "created_by" in result
    
    def test_test_case_completeness(self):
        """Test that test cases cover all important scenarios."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "test_cases": [
                    {
                        "test_id": "TC001",
                        "test_name": "Registration - Valid Data",
                        "test_type": "functional",
                        "priority": "High",
                        "description": "Test valid registration",
                        "preconditions": ["System available"],
                        "test_steps": ["Register user"],
                        "expected_results": ["User created"],
                        "test_data": {"email": "test@test.com"}
                    },
                    {
                        "test_id": "TC002",
                        "test_name": "Registration - Invalid Email",
                        "test_type": "functional",
                        "priority": "Medium",
                        "description": "Test invalid email format",
                        "preconditions": ["System available"],
                        "test_steps": ["Register with invalid email"],
                        "expected_results": ["Error returned"],
                        "test_data": {"email": "invalid-email"}
                    },
                    {
                        "test_id": "TC003",
                        "test_name": "Login - SQL Injection",
                        "test_type": "security",
                        "priority": "High",
                        "description": "Test SQL injection protection",
                        "preconditions": ["System available"],
                        "test_steps": ["Login with SQL injection payload"],
                        "expected_results": ["Attack blocked"],
                        "test_data": {"email": "'; DROP TABLE users; --"}
                    }
                ],
                "test_strategy": {},
                "test_coverage": {},
                "automation_framework": {}
            })
            mock_llm.invoke.return_value = mock_response
            
            result = create_test_strategy.invoke({
                "implementation_plan": self.sample_implementation_plan,
                "project_id": self.test_project_id
            })
            
            test_cases = result["test_cases"]
            
            # Check for different test types
            test_types = [tc["test_type"] for tc in test_cases]
            assert "functional" in test_types
            assert "security" in test_types or any("security" in tc["description"].lower() for tc in test_cases)
            
            # Check for positive and negative test cases
            descriptions = [tc["description"].lower() for tc in test_cases]
            has_positive = any("valid" in desc for desc in descriptions)
            has_negative = any("invalid" in desc or "error" in desc for desc in descriptions)
            
            assert has_positive, "No positive test cases found"
            assert has_negative, "No negative test cases found"
    
    def test_test_priorities_distribution(self):
        """Test that test cases have appropriate priority distribution."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "test_cases": [
                    {"test_id": "TC001", "test_name": "Critical Test", "test_type": "functional", "priority": "High", "description": "test", "preconditions": [], "test_steps": [], "expected_results": [], "test_data": {}},
                    {"test_id": "TC002", "test_name": "Important Test", "test_type": "functional", "priority": "Medium", "description": "test", "preconditions": [], "test_steps": [], "expected_results": [], "test_data": {}},
                    {"test_id": "TC003", "test_name": "Nice to Have", "test_type": "functional", "priority": "Low", "description": "test", "preconditions": [], "test_steps": [], "expected_results": [], "test_data": {}},
                    {"test_id": "TC004", "test_name": "Security Test", "test_type": "security", "priority": "High", "description": "test", "preconditions": [], "test_steps": [], "expected_results": [], "test_data": {}}
                ],
                "test_strategy": {},
                "test_coverage": {},
                "automation_framework": {}
            })
            mock_llm.invoke.return_value = mock_response
            
            result = create_test_strategy.invoke({
                "implementation_plan": self.sample_implementation_plan,
                "project_id": self.test_project_id
            })
            
            test_cases = result["test_cases"]
            priorities = [tc["priority"] for tc in test_cases]
            
            valid_priorities = ["High", "Medium", "Low", "Critical"]
            
            for priority in priorities:
                assert priority in valid_priorities
            
            # Should have some high priority tests
            assert "High" in priorities, "No high priority test cases"
            
            # Should have distribution across priorities (not all same priority)
            unique_priorities = set(priorities)
            assert len(unique_priorities) > 1, "All test cases have same priority"
    
    def test_test_coverage_areas(self):
        """Test that test coverage includes all important areas."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "test_cases": [],
                "test_strategy": {},
                "test_coverage": {
                    "functional_coverage": [
                        "User registration",
                        "User authentication",
                        "Input validation",
                        "Error handling",
                        "Data persistence"
                    ],
                    "security_coverage": [
                        "Authentication bypass",
                        "SQL injection",
                        "Cross-site scripting (XSS)",
                        "Input sanitization",
                        "Password security"
                    ],
                    "performance_coverage": [
                        "API response times",
                        "Concurrent users",
                        "Database performance",
                        "Memory usage"
                    ],
                    "compatibility_coverage": [
                        "Browser compatibility",
                        "Mobile devices",
                        "Different operating systems"
                    ]
                },
                "automation_framework": {}
            })
            mock_llm.invoke.return_value = mock_response
            
            result = create_test_strategy.invoke({
                "implementation_plan": self.sample_implementation_plan,
                "project_id": self.test_project_id
            })
            
            coverage = result["test_coverage"]
            
            # Check for essential coverage areas
            essential_areas = ["functional_coverage", "security_coverage"]
            
            for area in essential_areas:
                assert area in coverage, f"Missing coverage area: {area}"
                assert len(coverage[area]) > 0, f"Empty coverage area: {area}"
            
            # Check functional coverage includes basic operations
            functional = coverage.get("functional_coverage", [])
            functional_text = " ".join(functional).lower()
            
            assert any(keyword in functional_text for keyword in ["registration", "login", "authentication"])
            assert any(keyword in functional_text for keyword in ["validation", "error"])
    
    def test_automation_framework_selection(self):
        """Test that automation framework choices are appropriate."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "test_cases": [],
                "test_strategy": {
                    "automation_strategy": "Focus on API automation with selective UI automation"
                },
                "test_coverage": {},
                "automation_framework": {
                    "api_testing": "pytest + requests",
                    "ui_testing": "Selenium WebDriver",
                    "performance_testing": "Apache JMeter",
                    "security_testing": "OWASP ZAP",
                    "load_testing": "Locust",
                    "test_reporting": "Allure Reports"
                }
            })
            mock_llm.invoke.return_value = mock_response
            
            result = create_test_strategy.invoke({
                "implementation_plan": self.sample_implementation_plan,
                "project_id": self.test_project_id
            })
            
            automation = result["automation_framework"]
            
            # Common testing frameworks
            known_frameworks = {
                "api": ["pytest", "postman", "rest-assured", "supertest", "requests"],
                "ui": ["selenium", "cypress", "playwright", "webdriver"],
                "performance": ["jmeter", "locust", "k6", "gatling"],
                "security": ["owasp", "zap", "burp", "nessus"]
            }
            
            # Check that suggested frameworks are recognized
            for test_type, framework in automation.items():
                if isinstance(framework, str):
                    framework_lower = framework.lower()
                    
                    # At least one known framework should be mentioned
                    all_known = []
                    for known_list in known_frameworks.values():
                        all_known.extend(known_list)
                    
                    mentions_known = any(known in framework_lower for known in all_known)
                    if not mentions_known:
                        print(f"Warning: Unknown framework '{framework}' for {test_type}")
    
    def test_test_strategy_comprehensiveness(self):
        """Test that test strategy covers all essential aspects."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "test_cases": [],
                "test_strategy": {
                    "testing_approach": "Risk-based testing with focus on critical paths",
                    "test_levels": ["Unit Testing", "Integration Testing", "System Testing", "Acceptance Testing"],
                    "test_types": ["Functional", "Security", "Performance", "Usability", "Compatibility"],
                    "automation_strategy": "80% automation for regression, manual for exploratory",
                    "test_environment": "Isolated test environment with production-like data",
                    "entry_criteria": ["Code complete", "Unit tests passing", "Environment ready"],
                    "exit_criteria": ["All high priority tests pass", "No critical defects", "Performance benchmarks met"]
                },
                "test_coverage": {},
                "automation_framework": {}
            })
            mock_llm.invoke.return_value = mock_response
            
            result = create_test_strategy.invoke({
                "implementation_plan": self.sample_implementation_plan,
                "project_id": self.test_project_id
            })
            
            strategy = result["test_strategy"]
            
            # Essential strategy elements
            essential_elements = ["testing_approach", "test_levels", "test_types"]
            
            for element in essential_elements:
                assert element in strategy, f"Missing strategy element: {element}"
            
            # Test levels should include standard levels
            test_levels = strategy.get("test_levels", [])
            levels_text = " ".join(test_levels).lower()
            
            standard_levels = ["unit", "integration", "system", "acceptance"]
            mentioned_levels = sum(1 for level in standard_levels if level in levels_text)
            assert mentioned_levels >= 2, f"Only {mentioned_levels} standard test levels mentioned"
            
            # Test types should include functional and at least one other type
            test_types = strategy.get("test_types", [])
            types_text = " ".join(test_types).lower()
            
            assert "functional" in types_text, "Functional testing not mentioned"
            
            other_types = ["security", "performance", "usability", "compatibility"]
            mentioned_other = sum(1 for type_name in other_types if type_name in types_text)
            assert mentioned_other >= 1, "No non-functional test types mentioned"
    
    def test_test_data_appropriateness(self):
        """Test that test data is appropriate for test scenarios."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "test_cases": [
                    {
                        "test_id": "TC001",
                        "test_name": "Valid Registration",
                        "test_type": "functional",
                        "priority": "High",
                        "description": "Test user registration with valid data",
                        "preconditions": [],
                        "test_steps": [],
                        "expected_results": [],
                        "test_data": {
                            "valid_email": "user@example.com",
                            "valid_password": "SecurePassword123!",
                            "confirm_password": "SecurePassword123!"
                        }
                    },
                    {
                        "test_id": "TC002",
                        "test_name": "Invalid Email Format",
                        "test_type": "functional",
                        "priority": "Medium",
                        "description": "Test registration with invalid email",
                        "preconditions": [],
                        "test_steps": [],
                        "expected_results": [],
                        "test_data": {
                            "invalid_emails": ["invalid-email", "@example.com", "user@", "user.example.com"]
                        }
                    }
                ],
                "test_strategy": {},
                "test_coverage": {},
                "automation_framework": {}
            })
            mock_llm.invoke.return_value = mock_response
            
            result = create_test_strategy.invoke({
                "implementation_plan": self.sample_implementation_plan,
                "project_id": self.test_project_id
            })
            
            test_cases = result["test_cases"]
            
            for test_case in test_cases:
                test_data = test_case.get("test_data", {})
                test_name = test_case.get("test_name", "").lower()
                
                # Test data should be relevant to test name/description
                if "email" in test_name:
                    data_text = str(test_data).lower()
                    assert "email" in data_text, f"Email test case missing email data: {test_case['test_id']}"
                
                if "password" in test_name:
                    data_text = str(test_data).lower()
                    assert "password" in data_text, f"Password test case missing password data: {test_case['test_id']}"
    
    def test_test_strategy_file_output(self):
        """Test that the tool creates proper output files."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "test_cases": [{"test_id": "TC001", "test_name": "Test", "test_type": "functional", "priority": "Medium", "description": "test", "preconditions": [], "test_steps": [], "expected_results": [], "test_data": {}}],
                "test_strategy": {},
                "test_coverage": {},
                "automation_framework": {}
            })
            mock_llm.invoke.return_value = mock_response
            
            result = create_test_strategy.invoke({
                "implementation_plan": self.sample_implementation_plan,
                "project_id": self.test_project_id
            })
            
            # Check if output file was created
            output_file = Path(__file__).parent.parent / "out" / f"project_{self.test_project_id}" / "test_strategy_tester_agent.json"
            assert output_file.exists(), f"Output file not created: {output_file}"
            
            # Verify file content
            with open(output_file, 'r') as f:
                file_content = json.load(f)
            
            assert file_content == result
    
    def test_error_handling(self):
        """Test error handling when LLM fails."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_llm.invoke.side_effect = Exception("API Error")
            
            result = create_test_strategy.invoke({
                "implementation_plan": self.sample_implementation_plan,
                "project_id": self.test_project_id
            })
            
            assert isinstance(result, dict)
            assert "error" in result
            assert "created_at" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
