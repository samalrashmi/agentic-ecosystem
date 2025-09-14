#!/usr/bin/env python3
"""
BA Agent Test Configuration and Utilities

This module provides test utilities and configuration specifically for BA agent testing.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

class BATestConfig:
    """Configuration for BA agent tests."""
    
    # Test data directory
    TEST_DATA_DIR = Path(__file__).parent / "test_data"
    
    # Sample requirements for testing
    SAMPLE_REQUIREMENTS = {
        "simple": "Create a basic todo list application",
        
        "medium": """
        Create a task management web application with:
        - User authentication
        - Create, edit, delete tasks
        - Task categories and priorities
        - Due date tracking
        - Basic reporting
        """,
        
        "complex": """
        Build a comprehensive project management platform that includes:
        
        1. User Management:
        - Multi-role authentication (Admin, Manager, Developer, Client)
        - User profiles and permissions
        - Team and organization management
        
        2. Project Management:
        - Project creation and configuration
        - Milestone and phase tracking
        - Resource allocation and scheduling
        - Budget tracking and reporting
        
        3. Task Management:
        - Hierarchical task structures
        - Task dependencies and relationships
        - Time tracking and logging
        - Custom fields and metadata
        
        4. Collaboration:
        - Real-time comments and discussions
        - File sharing and version control
        - Notification and alert system
        - Activity feeds and history
        
        5. Reporting and Analytics:
        - Project progress dashboards
        - Time and cost analysis
        - Performance metrics
        - Custom report generation
        
        The system must support multiple projects, integrate with third-party tools,
        provide mobile access, and ensure data security and compliance.
        """
    }
    
    # Expected output patterns for validation
    EXPECTED_PATTERNS = {
        "functional_requirements": [
            "Functional Requirements",
            "FR001:",
            "FR002:"
        ],
        "non_functional_requirements": [
            "Non-Functional Requirements",
            "NFR001:",
            "Performance",
            "Security",
            "Usability"
        ],
        "user_stories": [
            "User Stories",
            "As a",
            "I want",
            "so that"
        ],
        "gherkin_scenarios": [
            "Feature:",
            "Scenario:",
            "Given",
            "When", 
            "Then"
        ],
        "business_rules": [
            "Business Rules",
            "BR001:"
        ]
    }
    
    # Mock LLM responses for different scenarios
    MOCK_RESPONSES = {
        "complete_specification": """
        ## Functional Requirements Specification
        
        ### 1. Project Overview
        A comprehensive task management application for personal and team productivity.
        
        ### 2. Functional Requirements
        - FR001: User registration and authentication
        - FR002: Task creation and management
        - FR003: Project organization and categorization
        - FR004: Team collaboration features
        - FR005: Notification and reminder system
        
        ### 3. Non-Functional Requirements
        - NFR001: System must support 1000+ concurrent users
        - NFR002: Response time must be under 2 seconds
        - NFR003: 99.9% uptime availability
        - NFR004: Mobile-responsive design
        - NFR005: GDPR compliance for data protection
        
        ### 4. Business Rules
        - BR001: Users can only access projects they are assigned to
        - BR002: Only project owners can delete projects
        - BR003: Tasks must have at least a title and description
        - BR004: Due dates cannot be set in the past
        
        ## Gherkin User Stories
        
        Feature: Task Management
        
        Scenario: Create a new task
        Given I am logged into the system
        And I am on the project dashboard
        When I click the "New Task" button
        And I enter "Complete user research" as the task title
        And I enter "Conduct interviews with 10 users" as the description
        And I set the due date to "2024-12-31"
        And I click "Save Task"
        Then I should see the task in my task list
        And the task should have a status of "Open"
        And I should receive a confirmation message
        
        Scenario: Mark task as complete
        Given I have an open task "Complete user research"
        When I click the checkbox next to the task
        Then the task status should change to "Complete"
        And the task should be visually marked as completed
        And the completion date should be recorded
        
        Feature: User Authentication
        
        Scenario: Successful login
        Given I am on the login page
        When I enter valid email "user@example.com"
        And I enter valid password "SecurePass123"
        And I click the "Login" button
        Then I should be redirected to the dashboard
        And I should see my username in the navigation bar
        
        Scenario: Failed login attempt
        Given I am on the login page
        When I enter invalid email "wrong@example.com"
        And I enter invalid password "wrongpass"
        And I click the "Login" button
        Then I should see an error message "Invalid credentials"
        And I should remain on the login page
        """,
        
        "simple_specification": """
        ## Todo List Application Specification
        
        ### Functional Requirements
        - FR001: Add new todo items
        - FR002: Mark items as complete
        - FR003: Delete todo items
        - FR004: View all todo items
        
        ### Gherkin Scenarios
        
        Feature: Todo Management
        
        Scenario: Add new todo item
        Given I am on the todo list page
        When I enter "Buy groceries" in the input field
        And I click "Add"
        Then I should see "Buy groceries" in my list
        """,
        
        "error_response": "Error: Unable to process the specification. Please provide more detailed requirements."
    }


class BATestUtils:
    """Utility functions for BA agent testing."""
    
    @staticmethod
    def validate_specification_structure(specification: str) -> Dict[str, bool]:
        """Validate that a specification contains required sections."""
        validation_results = {}
        
        # Check for main sections
        sections = {
            "functional_requirements": ["Functional Requirements", "FR001"],
            "non_functional_requirements": ["Non-Functional Requirements", "NFR001"],
            "user_stories": ["User Stories", "As a", "I want"],
            "gherkin_scenarios": ["Feature:", "Scenario:", "Given", "When", "Then"],
            "business_rules": ["Business Rules", "BR001"]
        }
        
        for section_name, patterns in sections.items():
            validation_results[section_name] = any(
                pattern in specification for pattern in patterns
            )
        
        return validation_results
    
    @staticmethod
    def count_user_stories(specification: str) -> int:
        """Count the number of user stories in a specification."""
        # Simple count based on "As a" pattern
        return specification.lower().count("as a")
    
    @staticmethod
    def count_gherkin_scenarios(specification: str) -> int:
        """Count the number of Gherkin scenarios."""
        return specification.count("Scenario:")
    
    @staticmethod
    def extract_functional_requirements(specification: str) -> List[str]:
        """Extract functional requirements from specification."""
        requirements = []
        lines = specification.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('- FR') or line.startswith('FR'):
                requirements.append(line)
        
        return requirements
    
    @staticmethod
    def validate_gherkin_format(specification: str) -> Dict[str, bool]:
        """Validate Gherkin scenario format."""
        validation = {
            "has_features": "Feature:" in specification,
            "has_scenarios": "Scenario:" in specification,
            "has_given": "Given" in specification,
            "has_when": "When" in specification,
            "has_then": "Then" in specification,
            "has_and": "And" in specification
        }
        
        return validation
    
    @staticmethod
    def save_test_output(test_name: str, specification: str, metadata: Dict[str, Any] = None):
        """Save test output for manual inspection."""
        output_dir = Path(__file__).parent / "test_output"
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"{test_name}_output.md"
        
        with open(output_file, 'w') as f:
            f.write(f"# Test Output: {test_name}\n\n")
            if metadata:
                f.write("## Test Metadata\n")
                f.write(f"```json\n{json.dumps(metadata, indent=2)}\n```\n\n")
            f.write("## Generated Specification\n\n")
            f.write(specification)
        
        return output_file


# Test data for parameterized tests
TEST_SCENARIOS = [
    {
        "name": "simple_todo",
        "requirement": BATestConfig.SAMPLE_REQUIREMENTS["simple"],
        "expected_sections": ["functional_requirements", "gherkin_scenarios"],
        "min_user_stories": 2,
        "min_scenarios": 1
    },
    {
        "name": "medium_task_manager", 
        "requirement": BATestConfig.SAMPLE_REQUIREMENTS["medium"],
        "expected_sections": ["functional_requirements", "non_functional_requirements", "user_stories", "gherkin_scenarios"],
        "min_user_stories": 5,
        "min_scenarios": 3
    },
    {
        "name": "complex_project_platform",
        "requirement": BATestConfig.SAMPLE_REQUIREMENTS["complex"],
        "expected_sections": ["functional_requirements", "non_functional_requirements", "user_stories", "gherkin_scenarios", "business_rules"],
        "min_user_stories": 10,
        "min_scenarios": 8
    }
]
