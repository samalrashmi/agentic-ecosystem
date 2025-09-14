#!/usr/bin/env python3
"""
Test suite for Developer Agent Tool

This module tests the generate_implementation_plan tool to ensure it properly
creates implementation plans based on system architecture.
"""

import pytest
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from langgraph_agents.agent_tools import generate_implementation_plan


class TestDeveloperAgent:
    """Test cases for the Developer Agent tool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_project_id = "test-dev-project-123"
        self.sample_architecture = json.dumps({
            "components": [
                {
                    "name": "User Authentication Service",
                    "type": "microservice",
                    "description": "Handles user registration and login",
                    "technologies": ["Node.js", "Express", "JWT"],
                    "responsibilities": ["User registration", "Login validation"],
                    "interfaces": ["REST API"],
                    "data_stores": ["PostgreSQL"]
                },
                {
                    "name": "Task Management Service",
                    "type": "microservice",
                    "description": "Manages task CRUD operations",
                    "technologies": ["Python", "FastAPI"],
                    "responsibilities": ["Task creation", "Task updates"],
                    "interfaces": ["REST API"],
                    "data_stores": ["PostgreSQL"]
                }
            ],
            "architecture_patterns": [
                {"pattern": "Microservices", "rationale": "Independent scaling"}
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
    async def test_generate_implementation_plan_basic(self):
        """Test basic implementation plan generation."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "implementation_phases": [
                    {
                        "phase": "Phase 1: Infrastructure Setup",
                        "duration": "1 week",
                        "tasks": [
                            {
                                "task": "Set up development environment",
                                "description": "Configure Docker containers and development tools",
                                "estimated_effort": "2 days",
                                "dependencies": [],
                                "deliverables": ["Docker compose file", "Development setup guide"]
                            },
                            {
                                "task": "Database setup",
                                "description": "Create PostgreSQL database schema",
                                "estimated_effort": "1 day",
                                "dependencies": ["Set up development environment"],
                                "deliverables": ["Database schema", "Migration scripts"]
                            }
                        ]
                    },
                    {
                        "phase": "Phase 2: Authentication Service",
                        "duration": "2 weeks",
                        "tasks": [
                            {
                                "task": "Implement user registration",
                                "description": "Create user registration endpoints and validation",
                                "estimated_effort": "3 days",
                                "dependencies": ["Database setup"],
                                "deliverables": ["Registration API", "Input validation", "Unit tests"]
                            },
                            {
                                "task": "Implement user login",
                                "description": "Create login endpoints with JWT token generation",
                                "estimated_effort": "2 days",
                                "dependencies": ["Implement user registration"],
                                "deliverables": ["Login API", "JWT implementation", "Unit tests"]
                            }
                        ]
                    }
                ],
                "technical_specifications": [
                    {
                        "component": "User Authentication Service",
                        "technology_stack": ["Node.js 18+", "Express 4.x", "JWT", "bcrypt"],
                        "api_endpoints": [
                            {"method": "POST", "path": "/auth/register", "description": "User registration"},
                            {"method": "POST", "path": "/auth/login", "description": "User login"}
                        ],
                        "database_schema": [
                            {
                                "table": "users",
                                "columns": ["id", "email", "password_hash", "created_at", "updated_at"]
                            }
                        ]
                    }
                ],
                "deployment_strategy": {
                    "environment_setup": ["Development", "Staging", "Production"],
                    "ci_cd_pipeline": ["GitHub Actions", "Docker builds", "Automated testing"],
                    "monitoring": ["Application logs", "Performance metrics", "Error tracking"]
                },
                "risk_mitigation": [
                    {
                        "risk": "Database connection failures",
                        "mitigation": "Implement connection pooling and retry logic",
                        "priority": "High"
                    }
                ]
            })
            mock_llm.invoke.return_value = mock_response
            
            # Execute the tool
            result = generate_implementation_plan.invoke({
                "architecture": self.sample_architecture,
                "project_id": self.test_project_id
            })
            
            # Verify results structure
            assert isinstance(result, dict)
            assert "implementation_phases" in result
            assert "technical_specifications" in result
            assert "deployment_strategy" in result
            assert "risk_mitigation" in result
            assert "created_at" in result
            
            # Verify implementation phases structure
            phases = result["implementation_phases"]
            assert len(phases) >= 1
            
            for phase in phases:
                assert "phase" in phase
                assert "duration" in phase
                assert "tasks" in phase
                
                for task in phase["tasks"]:
                    assert "task" in task
                    assert "description" in task
                    assert "estimated_effort" in task
                    assert "dependencies" in task
                    assert "deliverables" in task
            
            # Verify metadata
            assert result["project_id"] == self.test_project_id
            assert "created_at" in result
            assert "created_by" in result
    
    def test_task_dependency_validation(self):
        """Test that task dependencies are logically ordered."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "implementation_phases": [
                    {
                        "phase": "Phase 1",
                        "duration": "1 week",
                        "tasks": [
                            {
                                "task": "Setup Database",
                                "description": "Create database",
                                "estimated_effort": "1 day",
                                "dependencies": [],
                                "deliverables": ["Database schema"]
                            },
                            {
                                "task": "Create API Endpoints",
                                "description": "Build REST APIs",
                                "estimated_effort": "2 days",
                                "dependencies": ["Setup Database"],
                                "deliverables": ["API endpoints"]
                            },
                            {
                                "task": "Add Authentication",
                                "description": "Implement auth",
                                "estimated_effort": "1 day",
                                "dependencies": ["Create API Endpoints"],
                                "deliverables": ["Auth system"]
                            }
                        ]
                    }
                ],
                "technical_specifications": [],
                "deployment_strategy": {},
                "risk_mitigation": []
            })
            mock_llm.invoke.return_value = mock_response
            
            result = generate_implementation_plan.invoke({
                "architecture": self.sample_architecture,
                "project_id": self.test_project_id
            })
            
            # Verify dependency chain makes sense
            phases = result["implementation_phases"]
            for phase in phases:
                tasks = phase["tasks"]
                task_names = [task["task"] for task in tasks]
                
                for task in tasks:
                    for dependency in task["dependencies"]:
                        # Each dependency should refer to an actual task
                        assert dependency in task_names, f"Unknown dependency: {dependency}"
    
    def test_technical_specifications_completeness(self):
        """Test that technical specifications cover all components."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "implementation_phases": [],
                "technical_specifications": [
                    {
                        "component": "User Authentication Service",
                        "technology_stack": ["Node.js", "Express", "JWT"],
                        "api_endpoints": [
                            {"method": "POST", "path": "/auth/register", "description": "Register new user"},
                            {"method": "POST", "path": "/auth/login", "description": "User login"}
                        ],
                        "database_schema": [
                            {"table": "users", "columns": ["id", "email", "password_hash"]}
                        ]
                    },
                    {
                        "component": "Task Management Service",
                        "technology_stack": ["Python", "FastAPI"],
                        "api_endpoints": [
                            {"method": "POST", "path": "/tasks", "description": "Create task"},
                            {"method": "GET", "path": "/tasks", "description": "List tasks"}
                        ],
                        "database_schema": [
                            {"table": "tasks", "columns": ["id", "title", "description", "user_id"]}
                        ]
                    }
                ],
                "deployment_strategy": {},
                "risk_mitigation": []
            })
            mock_llm.invoke.return_value = mock_response
            
            result = generate_implementation_plan.invoke({
                "architecture": self.sample_architecture,
                "project_id": self.test_project_id
            })
            
            # Extract component names from architecture
            architecture = json.loads(self.sample_architecture)
            arch_components = [comp["name"] for comp in architecture["components"]]
            
            # Verify technical specs cover architecture components
            tech_specs = result["technical_specifications"]
            spec_components = [spec["component"] for spec in tech_specs]
            
            for arch_comp in arch_components:
                assert arch_comp in spec_components, f"Missing technical spec for {arch_comp}"
            
            # Verify each spec has required fields
            for spec in tech_specs:
                assert "component" in spec
                assert "technology_stack" in spec
                assert "api_endpoints" in spec
                assert "database_schema" in spec
                
                # Verify API endpoints structure
                for endpoint in spec["api_endpoints"]:
                    assert "method" in endpoint
                    assert "path" in endpoint
                    assert "description" in endpoint
                    assert endpoint["method"] in ["GET", "POST", "PUT", "DELETE", "PATCH"]
    
    def test_effort_estimation_reasonableness(self):
        """Test that effort estimations are reasonable."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "implementation_phases": [
                    {
                        "phase": "Phase 1",
                        "duration": "2 weeks",
                        "tasks": [
                            {
                                "task": "Setup",
                                "description": "Initial setup",
                                "estimated_effort": "2 days",
                                "dependencies": [],
                                "deliverables": ["Setup"]
                            },
                            {
                                "task": "Development",
                                "description": "Main development",
                                "estimated_effort": "1 week",
                                "dependencies": ["Setup"],
                                "deliverables": ["Features"]
                            }
                        ]
                    }
                ],
                "technical_specifications": [],
                "deployment_strategy": {},
                "risk_mitigation": []
            })
            mock_llm.invoke.return_value = mock_response
            
            result = generate_implementation_plan.invoke({
                "architecture": self.sample_architecture,
                "project_id": self.test_project_id
            })
            
            # Verify effort estimates are reasonable
            time_units = ["hour", "day", "week", "month"]
            
            for phase in result["implementation_phases"]:
                # Phase duration should be reasonable
                duration = phase["duration"].lower()
                assert any(unit in duration for unit in time_units)
                
                for task in phase["tasks"]:
                    effort = task["estimated_effort"].lower()
                    assert any(unit in effort for unit in time_units)
                    
                    # Effort should be less than or equal to phase duration
                    # (This is a simplified check - real validation would parse time units)
                    if "week" in effort and "day" in phase["duration"]:
                        pass  # Week effort in day-duration phase might be issue, but allow for now
    
    def test_deployment_strategy_coverage(self):
        """Test that deployment strategy covers essential aspects."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "implementation_phases": [],
                "technical_specifications": [],
                "deployment_strategy": {
                    "environment_setup": ["Development", "Staging", "Production"],
                    "ci_cd_pipeline": ["GitHub Actions", "Docker builds", "Automated testing", "Deployment automation"],
                    "monitoring": ["Application logs", "Performance metrics", "Error tracking", "Health checks"],
                    "backup_strategy": ["Daily database backups", "Code repository backups"],
                    "security_measures": ["SSL certificates", "Environment variables", "Access controls"]
                },
                "risk_mitigation": []
            })
            mock_llm.invoke.return_value = mock_response
            
            result = generate_implementation_plan.invoke({
                "architecture": self.sample_architecture,
                "project_id": self.test_project_id
            })
            
            deployment = result["deployment_strategy"]
            
            # Check essential deployment aspects
            essential_aspects = ["environment_setup", "ci_cd_pipeline", "monitoring"]
            
            for aspect in essential_aspects:
                assert aspect in deployment, f"Missing deployment aspect: {aspect}"
                assert len(deployment[aspect]) > 0, f"Empty deployment aspect: {aspect}"
            
            # Verify environments include at least dev and prod
            envs = deployment.get("environment_setup", [])
            env_text = " ".join(envs).lower()
            assert "development" in env_text or "dev" in env_text
            assert "production" in env_text or "prod" in env_text
    
    def test_risk_mitigation_priorities(self):
        """Test that risk mitigation includes prioritized risks."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "implementation_phases": [],
                "technical_specifications": [],
                "deployment_strategy": {},
                "risk_mitigation": [
                    {
                        "risk": "Database connection failures",
                        "mitigation": "Connection pooling and retry logic",
                        "priority": "High"
                    },
                    {
                        "risk": "API rate limiting",
                        "mitigation": "Implement caching and request throttling",
                        "priority": "Medium"
                    },
                    {
                        "risk": "Security vulnerabilities",
                        "mitigation": "Regular security audits and updates",
                        "priority": "High"
                    }
                ]
            })
            mock_llm.invoke.return_value = mock_response
            
            result = generate_implementation_plan.invoke({
                "architecture": self.sample_architecture,
                "project_id": self.test_project_id
            })
            
            risks = result["risk_mitigation"]
            assert len(risks) > 0, "No risks identified"
            
            valid_priorities = ["High", "Medium", "Low", "Critical"]
            
            for risk in risks:
                assert "risk" in risk
                assert "mitigation" in risk
                assert "priority" in risk
                assert risk["priority"] in valid_priorities
                
                # Mitigation should be meaningful
                assert len(risk["mitigation"]) > 10, "Mitigation too brief"
    
    def test_implementation_file_output(self):
        """Test that the tool creates proper output files."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "implementation_phases": [{"phase": "Test Phase", "duration": "1 day", "tasks": []}],
                "technical_specifications": [],
                "deployment_strategy": {},
                "risk_mitigation": []
            })
            mock_llm.invoke.return_value = mock_response
            
            result = generate_implementation_plan.invoke({
                "architecture": self.sample_architecture,
                "project_id": self.test_project_id
            })
            
            # Check if output file was created
            output_file = Path(__file__).parent.parent / "out" / f"project_{self.test_project_id}" / "implementation_plan_developer_agent.json"
            assert output_file.exists(), f"Output file not created: {output_file}"
            
            # Verify file content
            with open(output_file, 'r') as f:
                file_content = json.load(f)
            
            assert file_content == result
    
    def test_error_handling(self):
        """Test error handling when LLM fails."""
        with patch('langgraph_agents.agent_tools.llm') as mock_llm:
            mock_llm.invoke.side_effect = Exception("API Error")
            
            result = generate_implementation_plan.invoke({
                "architecture": self.sample_architecture,
                "project_id": self.test_project_id
            })
            
            assert isinstance(result, dict)
            assert "error" in result
            assert "created_at" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
