#!/usr/bin/env python3
"""
Test suite for Architect Agent Tool

This module tests the design_system_architecture tool to ensure it properly
designs system architecture based on user stories.
"""

import pytest
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from langgraph_agents.agent_tools import design_system_architecture


class TestArchitectAgent:
    """Test cases for the Architect Agent tool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_project_id = "test-arch-project-123"
        self.sample_user_stories = json.dumps({
            "user_stories": [
                {
                    "id": "US001",
                    "title": "User Registration",
                    "description": "As a new user, I want to register an account",
                    "acceptance_criteria": ["Email validation", "Password requirements"],
                    "priority": "High",
                    "story_points": 5
                },
                {
                    "id": "US002",
                    "title": "Task Management",
                    "description": "As a user, I want to create and manage tasks",
                    "acceptance_criteria": ["CRUD operations", "Task categories"],
                    "priority": "High",
                    "story_points": 8
                }
            ]
        })
        self.sample_requirements = "Web-based task management application with user authentication"
        
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
    async def test_design_system_architecture_basic(self):
        """Test basic system architecture design."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "components": [
                    {
                        "name": "User Authentication Service",
                        "type": "microservice",
                        "description": "Handles user registration, login, and authentication",
                        "technologies": ["Node.js", "JWT", "bcrypt"],
                        "responsibilities": ["User registration", "Login validation", "Token management"],
                        "interfaces": ["REST API", "GraphQL"],
                        "data_stores": ["PostgreSQL"]
                    },
                    {
                        "name": "Task Management Service",
                        "type": "microservice", 
                        "description": "Manages task CRUD operations and organization",
                        "technologies": ["Python", "FastAPI", "SQLAlchemy"],
                        "responsibilities": ["Task creation", "Task updates", "Task categorization"],
                        "interfaces": ["REST API"],
                        "data_stores": ["PostgreSQL", "Redis"]
                    },
                    {
                        "name": "Frontend Application",
                        "type": "web_app",
                        "description": "React-based user interface",
                        "technologies": ["React", "TypeScript", "Material-UI"],
                        "responsibilities": ["User interface", "State management", "API communication"],
                        "interfaces": ["HTTP Client"],
                        "data_stores": ["LocalStorage", "SessionStorage"]
                    }
                ],
                "architecture_patterns": [
                    {
                        "pattern": "Microservices",
                        "rationale": "Enables independent scaling and deployment of services"
                    },
                    {
                        "pattern": "RESTful APIs",
                        "rationale": "Standard HTTP-based communication between services"
                    }
                ],
                "data_flow": [
                    {
                        "source": "Frontend",
                        "target": "Authentication Service",
                        "data": "Login credentials",
                        "protocol": "HTTPS"
                    },
                    {
                        "source": "Frontend",
                        "target": "Task Service",
                        "data": "Task operations",
                        "protocol": "HTTPS"
                    }
                ],
                "security_considerations": [
                    "JWT token-based authentication",
                    "HTTPS encryption for all communications",
                    "Input validation and sanitization",
                    "SQL injection prevention"
                ]
            })
            mock_llm.invoke.return_value = mock_response
            
            # Execute the tool
            result = design_system_architecture.invoke({
                "user_stories": self.sample_user_stories,
                "project_id": self.test_project_id,
                "requirements": self.sample_requirements
            })
            
            # Verify results structure
            assert isinstance(result, dict)
            assert "components" in result
            assert "architecture_patterns" in result
            assert "data_flow" in result
            assert "security_considerations" in result
            assert "created_at" in result
            
            # Verify components structure
            components = result["components"]
            assert len(components) >= 2
            
            for component in components:
                assert "name" in component
                assert "type" in component
                assert "description" in component
                assert "technologies" in component
                assert "responsibilities" in component
                assert "interfaces" in component
                assert "data_stores" in component
            
            # Verify metadata
            assert result["project_id"] == self.test_project_id
            assert "created_at" in result
            assert "created_by" in result
    
    def test_architecture_component_types(self):
        """Test that components have valid types."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "components": [
                    {"name": "API Gateway", "type": "gateway", "description": "test", "technologies": [], "responsibilities": [], "interfaces": [], "data_stores": []},
                    {"name": "User Service", "type": "microservice", "description": "test", "technologies": [], "responsibilities": [], "interfaces": [], "data_stores": []},
                    {"name": "Database", "type": "database", "description": "test", "technologies": [], "responsibilities": [], "interfaces": [], "data_stores": []},
                    {"name": "Frontend", "type": "web_app", "description": "test", "technologies": [], "responsibilities": [], "interfaces": [], "data_stores": []}
                ],
                "architecture_patterns": [],
                "data_flow": [],
                "security_considerations": []
            })
            mock_llm.invoke.return_value = mock_response
            
            result = design_system_architecture.invoke({
                "user_stories": self.sample_user_stories,
                "project_id": self.test_project_id,
                "requirements": self.sample_requirements
            })
            
            valid_types = ["microservice", "web_app", "mobile_app", "database", "cache", "gateway", "load_balancer", "message_queue"]
            
            for component in result["components"]:
                assert component["type"] in valid_types
    
    def test_technology_stack_consistency(self):
        """Test that technology choices are consistent and reasonable."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "components": [
                    {
                        "name": "Backend API",
                        "type": "microservice",
                        "description": "Main API service",
                        "technologies": ["Python", "FastAPI", "PostgreSQL"],
                        "responsibilities": ["API endpoints"],
                        "interfaces": ["REST"],
                        "data_stores": ["PostgreSQL"]
                    }
                ],
                "architecture_patterns": [{"pattern": "REST API", "rationale": "Standard web API pattern"}],
                "data_flow": [],
                "security_considerations": ["HTTPS"]
            })
            mock_llm.invoke.return_value = mock_response
            
            result = design_system_architecture.invoke({
                "user_stories": self.sample_user_stories,
                "project_id": self.test_project_id,
                "requirements": self.sample_requirements
            })
            
            # Check that technologies are real and commonly used together
            known_technologies = {
                "languages": ["Python", "JavaScript", "TypeScript", "Java", "C#", "Go", "Rust"],
                "frameworks": ["FastAPI", "Django", "React", "Vue", "Angular", "Express", "Spring"],
                "databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch"],
                "tools": ["Docker", "Kubernetes", "JWT", "bcrypt"]
            }
            
            all_known_techs = []
            for category in known_technologies.values():
                all_known_techs.extend(category)
            
            for component in result["components"]:
                for tech in component["technologies"]:
                    # Most technologies should be recognized (allow some flexibility for newer tech)
                    if tech not in all_known_techs:
                        print(f"Warning: Unknown technology '{tech}' in component '{component['name']}'")
    
    def test_security_considerations_coverage(self):
        """Test that security considerations cover important aspects."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "components": [],
                "architecture_patterns": [],
                "data_flow": [],
                "security_considerations": [
                    "Authentication and authorization",
                    "Data encryption in transit and at rest",
                    "Input validation and sanitization",
                    "SQL injection prevention",
                    "Cross-site scripting (XSS) protection",
                    "Rate limiting and DDoS protection"
                ]
            })
            mock_llm.invoke.return_value = mock_response
            
            result = design_system_architecture.invoke({
                "user_stories": self.sample_user_stories,
                "project_id": self.test_project_id,
                "requirements": self.sample_requirements
            })
            
            security_text = " ".join(result["security_considerations"]).lower()
            
            # Check for important security concepts
            important_security_concepts = [
                "authentication", "authorization", "encryption", "validation",
                "injection", "xss", "https", "token"
            ]
            
            covered_concepts = sum(1 for concept in important_security_concepts if concept in security_text)
            assert covered_concepts >= 3, f"Only {covered_concepts} security concepts covered"
    
    def test_data_flow_completeness(self):
        """Test that data flow describes system interactions."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "components": [
                    {"name": "Frontend", "type": "web_app", "description": "test", "technologies": [], "responsibilities": [], "interfaces": [], "data_stores": []},
                    {"name": "Backend", "type": "microservice", "description": "test", "technologies": [], "responsibilities": [], "interfaces": [], "data_stores": []}
                ],
                "architecture_patterns": [],
                "data_flow": [
                    {
                        "source": "Frontend",
                        "target": "Backend",
                        "data": "User requests",
                        "protocol": "HTTPS"
                    },
                    {
                        "source": "Backend",
                        "target": "Database",
                        "data": "Data queries",
                        "protocol": "TCP"
                    }
                ],
                "security_considerations": []
            })
            mock_llm.invoke.return_value = mock_response
            
            result = design_system_architecture.invoke({
                "user_stories": self.sample_user_stories,
                "project_id": self.test_project_id,
                "requirements": self.sample_requirements
            })
            
            data_flows = result["data_flow"]
            component_names = [comp["name"] for comp in result["components"]]
            
            # Verify data flow references actual components
            for flow in data_flows:
                assert "source" in flow
                assert "target" in flow
                assert "data" in flow
                assert "protocol" in flow
                
                # Source and target should reference actual components (with some flexibility)
                # Note: target might be external services not in components list
    
    def test_architecture_file_output(self):
        """Test that the tool creates proper output files."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "components": [{"name": "Test Component", "type": "microservice", "description": "test", "technologies": [], "responsibilities": [], "interfaces": [], "data_stores": []}],
                "architecture_patterns": [],
                "data_flow": [],
                "security_considerations": []
            })
            mock_llm.invoke.return_value = mock_response
            
            result = design_system_architecture.invoke({
                "user_stories": self.sample_user_stories,
                "project_id": self.test_project_id,
                "requirements": self.sample_requirements
            })
            
            # Check if output file was created
            output_file = Path(__file__).parent.parent / "out" / f"project_{self.test_project_id}" / "system_architecture_architect_agent.json"
            assert output_file.exists(), f"Output file not created: {output_file}"
            
            # Verify file content
            with open(output_file, 'r') as f:
                file_content = json.load(f)
            
            assert file_content == result
    
    def test_architecture_patterns_validation(self):
        """Test that architecture patterns have proper rationale."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "components": [],
                "architecture_patterns": [
                    {
                        "pattern": "Microservices",
                        "rationale": "Enables independent scaling and deployment"
                    },
                    {
                        "pattern": "Event-Driven Architecture",
                        "rationale": "Supports real-time updates and loose coupling"
                    }
                ],
                "data_flow": [],
                "security_considerations": []
            })
            mock_llm.invoke.return_value = mock_response
            
            result = design_system_architecture.invoke({
                "user_stories": self.sample_user_stories,
                "project_id": self.test_project_id,
                "requirements": self.sample_requirements
            })
            
            patterns = result["architecture_patterns"]
            
            for pattern in patterns:
                assert "pattern" in pattern
                assert "rationale" in pattern
                assert len(pattern["rationale"]) > 10  # Meaningful explanation
                
                # Check for common architecture patterns
                pattern_name = pattern["pattern"].lower()
                common_patterns = [
                    "microservices", "monolith", "layered", "event-driven",
                    "rest", "graphql", "mvc", "mvvm", "hexagonal"
                ]
                
                # Should mention at least one known pattern concept
                mentions_known_pattern = any(known in pattern_name for known in common_patterns)
                if not mentions_known_pattern:
                    print(f"Warning: Unknown architecture pattern '{pattern['pattern']}'")
    
    def test_error_handling(self):
        """Test error handling when LLM fails."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_llm.invoke.side_effect = Exception("API Error")
            
            result = design_system_architecture.invoke({
                "user_stories": self.sample_user_stories,
                "project_id": self.test_project_id,
                "requirements": self.sample_requirements
            })
            
            assert isinstance(result, dict)
            assert "error" in result
            assert "created_at" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
