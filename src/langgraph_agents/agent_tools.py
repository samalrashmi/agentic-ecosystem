import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize LLM with API key from environment
try:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    print("LLM initialized successfully")
except Exception as e:
    print(f"Failed to initialize LLM: {e}")
    llm = None

@tool
def analyze_business_requirements(specification: str, project_id: str) -> Dict[str, Any]:
    """
    Analyze project specification and generate user stories.
    
    Args:
        specification: Project specification text
        project_id: Unique identifier for the project
        
    Returns:
        Dictionary containing user stories, requirements, and acceptance criteria
    """
    try:
        prompt = f"""
        As a Business Analyst, analyze this project specification and create user stories:
        
        Specification: {specification}
        
        Generate 3-5 user stories in this format:
        As a [user type], I want [functionality] so that [benefit].
        
        Also provide:
        1. Functional requirements
        2. Non-functional requirements  
        3. Success criteria
        
        Format as JSON:
        {{
            "user_stories": ["story1", "story2", ...],
            "functional_requirements": ["req1", "req2", ...],
            "non_functional_requirements": ["req1", "req2", ...],
            "success_criteria": ["criteria1", "criteria2", ...]
        }}
        """
        
        if llm is None:
            raise Exception("LLM not initialized - check API key configuration")
            
        response = llm.invoke(prompt)
        
        try:
            result = json.loads(response.content)
        except json.JSONDecodeError:
            print("JSON parsing failed, using fallback")
            # Fallback if JSON parsing fails
            result = {
                "user_stories": [
                    "As a user, I want to access the application so that I can use its features",
                    "As a user, I want a responsive interface so that I can use it on any device",
                    "As a user, I want reliable performance so that I can complete tasks efficiently"
                ],
                "functional_requirements": [
                    "User interface for interaction",
                    "Core business logic implementation",
                    "Data processing capabilities"
                ],
                "non_functional_requirements": [
                    "Response time under 2 seconds",
                    "Mobile-responsive design",
                    "Cross-browser compatibility"
                ],
                "success_criteria": [
                    "All user stories implemented",
                    "Performance targets met",
                    "User acceptance testing passed"
                ]
            }
        
        # Add metadata
        result["project_id"] = project_id
        result["created_at"] = datetime.now().isoformat()
        result["created_by"] = "ba_agent"
        
        # Save to project folder
        _save_artifact(project_id, "business_analysis", result)
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to analyze requirements: {str(e)}",
            "project_id": project_id,
            "created_at": datetime.now().isoformat()
        }


@tool
def design_system_architecture(user_stories: str, project_id: str, requirements: str = "") -> Dict[str, Any]:
    """
    Design system architecture based on user stories and requirements.
    
    Args:
        user_stories: JSON string of user stories
        project_id: Unique identifier for the project
        requirements: Additional requirements context
        
    Returns:
        Dictionary containing system architecture, components, and technology stack
    """
    try:
        # Analyze project complexity and recommend optimal solution
        context = (user_stories + " " + requirements).lower()
        
        # Enhanced system prompt for intelligent technology selection
        system_prompt = f"""
        You are an expert Software Architect. Analyze the following project requirements and provide architectural recommendations.

        Project Context: {context}
        User Stories: {user_stories}
        Requirements: {requirements}

        CRITICAL GUIDELINES:
        - For calculators, converters, timers, counters, or any basic interactive tools → classify as "simple"
        - For simple projects, ALWAYS recommend "HTML/CSS/JavaScript" (vanilla web technologies)
        - Only suggest React/Vue/frameworks for truly complex applications with multiple pages, user auth, databases, etc.

        Follow these steps:

        1. EVALUATE PROJECT COMPLEXITY:
        Classify this project as Simple, Medium, or Complex based on:
        - **Simple**: Calculators, converters, timers, counters, portfolios, landing pages, simple games, basic forms
        - **Medium**: Multi-page apps, user authentication, CRUD operations, API integrations
        - **Complex**: Real-time features, microservices, scalability requirements, complex business logic

        2. PROVIDE TOP 3 RECOMMENDED TECHNOLOGY SOLUTIONS:
        Based on your complexity analysis:

        FOR SIMPLE PROJECTS - Always include these options:
        Option 1: HTML/CSS/JavaScript (vanilla web technologies)
        Option 2: HTML/CSS/JavaScript with a simple framework like Bootstrap
        Option 3: Static site generator if needed

        FOR MEDIUM/COMPLEX PROJECTS - Then consider:
        React, Vue, Angular, Node.js, databases, etc.

        3. CHOOSE THE MOST OPTIMAL SOLUTION:
        For simple projects like calculators → ALWAYS choose HTML/CSS/JavaScript

        Respond with JSON in this exact format (no markdown, no additional text):
        {{
            "complexity_analysis": "simple|medium|complex",
            "top_3_options": [
                {{
                    "option": 1,
                    "technology": "Technology name",
                    "pros": ["advantage1", "advantage2"],
                    "cons": ["disadvantage1", "disadvantage2"],
                    "best_for": "Use case description"
                }},
                {{
                    "option": 2,
                    "technology": "Technology name", 
                    "pros": ["advantage1", "advantage2"],
                    "cons": ["disadvantage1", "disadvantage2"],
                    "best_for": "Use case description"
                }},
                {{
                    "option": 3,
                    "technology": "Technology name",
                    "pros": ["advantage1", "advantage2"], 
                    "cons": ["disadvantage1", "disadvantage2"],
                    "best_for": "Use case description"
                }}
            ],
            "optimal_choice": {{
                "selected_option": 1,
                "reasoning": "Why this option is optimal for this specific project"
            }},
            "overview": "Brief system description",
            "technology_stack": {{
                "frontend": "Selected frontend technology",
                "backend": "Selected backend technology or 'Static files'",
                "database": "Selected database or 'None required'",
                "deployment": "Deployment strategy"
            }},
            "components": [
                {{
                    "name": "Component name",
                    "responsibility": "What it does",
                    "technology": "Technology used"
                }}
            ],
            "deployment_strategy": "How to deploy this solution"
        }}
        """
        
        try:
            if llm is None:
                raise Exception("LLM not initialized - check API key configuration")
                
            response = llm.invoke(system_prompt)
            print(f"LLM Response received: {len(response.content)} characters")
            
            # Clean the response content more thoroughly
            content = response.content.strip()
            
            # Remove markdown code blocks
            if content.startswith('```json'):
                content = content[7:]
            elif content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            
            # Remove any leading/trailing whitespace
            content = content.strip()
            
            # Try to find JSON within the response if it's wrapped in text
            if not content.startswith('{'):
                # Look for JSON object in the response
                start_idx = content.find('{')
                if start_idx != -1:
                    end_idx = content.rfind('}')
                    if end_idx != -1:
                        content = content[start_idx:end_idx+1]
            
            print(f"Cleaned content preview: {content[:200]}...")
            
            result = json.loads(content)
            
            # Validate that we got a proper response
            if "technology_stack" not in result:
                raise ValueError("Invalid LLM response format - missing technology_stack")
            if "complexity_analysis" not in result:
                raise ValueError("Invalid LLM response format - missing complexity_analysis")
                
            print(f"LLM analysis successful: {result.get('complexity_analysis', 'unknown')} complexity")
                
        except Exception as llm_error:
            print(f"LLM call failed: {llm_error}")
            print(f"LLM error type: {type(llm_error).__name__}")
            
            # Check if it's an API key issue
            if "api" in str(llm_error).lower() or "unauthorized" in str(llm_error).lower():
                print("API key issue detected - check OPENAI_API_KEY environment variable")
            
            # Check if it's a JSON parsing issue
            if hasattr(llm_error, 'response') and hasattr(llm_error.response, 'content'):
                print(f"Raw LLM response: {llm_error.response.content[:500]}...")
            elif "json" in str(llm_error).lower():
                print("JSON parsing failed - LLM response might not be valid JSON")
            
            # Intelligent fallback - analyze project complexity locally
            simple_indicators = ["calculator", "hello world", "basic", "simple", "static", "landing page", "portfolio"]
            complex_indicators = ["real-time", "database", "user authentication", "api", "microservice", "scalable"]
            
            is_simple = any(indicator in context for indicator in simple_indicators)
            is_complex = any(indicator in context for indicator in complex_indicators)
            
            if is_simple and not is_complex:
                result = {
                    "complexity_analysis": "simple",
                    "optimal_choice": {
                        "selected_option": 1,
                        "reasoning": "Simple project requiring minimal overhead and fast development"
                    },
                    "overview": "A simple web application using vanilla HTML, CSS, and JavaScript",
                    "technology_stack": {
                        "frontend": "HTML/CSS/JavaScript",
                        "backend": "Static files (no backend needed)",
                        "database": "None required",
                        "deployment": "Static hosting (GitHub Pages, Netlify, etc.)"
                    },
                    "components": [
                        {
                            "name": "User Interface",
                            "responsibility": "Handle user interactions and display results",
                            "technology": "HTML/CSS/JavaScript"
                        }
                    ],
                    "deployment_strategy": "Deploy as static files to web hosting service"
                }
            elif is_complex:
                result = {
                    "complexity_analysis": "complex",
                    "optimal_choice": {
                        "selected_option": 1,
                        "reasoning": "Complex project requiring scalable architecture and modern tooling"
                    },
                    "overview": "Modern full-stack web application with robust architecture",
                    "technology_stack": {
                        "frontend": "React.js",
                        "backend": "Node.js with Express",
                        "database": "PostgreSQL",
                        "deployment": "Docker containers on cloud platform"
                    },
                    "components": [
                        {
                            "name": "Frontend Application",
                            "responsibility": "User interface and client-side logic",
                            "technology": "React.js"
                        },
                        {
                            "name": "Backend API",
                            "responsibility": "Business logic and data processing",
                            "technology": "Node.js"
                        },
                        {
                            "name": "Database",
                            "responsibility": "Data storage and retrieval",
                            "technology": "PostgreSQL"
                        }
                    ],
                    "deployment_strategy": "Containerized deployment with CI/CD pipeline"
                }
            else:
                # Medium complexity
                result = {
                    "complexity_analysis": "medium",
                    "optimal_choice": {
                        "selected_option": 1,
                        "reasoning": "Medium complexity project requiring balance of features and simplicity"
                    },
                    "overview": "Interactive web application with modern frontend framework",
                    "technology_stack": {
                        "frontend": "Vue.js",
                        "backend": "Node.js",
                        "database": "MongoDB",
                        "deployment": "Cloud hosting platform"
                    },
                    "components": [
                        {
                            "name": "Frontend Application",
                            "responsibility": "Interactive user interface",
                            "technology": "Vue.js"
                        },
                        {
                            "name": "Backend Service",
                            "responsibility": "API and business logic",
                            "technology": "Node.js"
                        }
                    ],
                    "deployment_strategy": "Cloud platform deployment with managed database"
                }
        
        # Add metadata
        result["project_id"] = project_id
        result["created_at"] = datetime.now().isoformat()
        result["created_by"] = "architect_agent"
        
        # Extract technology_used from the technology_stack
        tech_stack = result.get("technology_stack", {})
        frontend_tech = tech_stack.get("frontend", "")
        
        if frontend_tech:
            result["technology_used"] = frontend_tech
        else:
            # Fallback based on complexity
            complexity = result.get("complexity_analysis", "medium")
            if complexity == "simple":
                result["technology_used"] = "HTML/CSS/JavaScript"
            elif complexity == "complex":
                result["technology_used"] = "React.js"
            else:
                result["technology_used"] = "Vue.js"
        
        # Save to project folder
        _save_artifact(project_id, "system_architecture", result)
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to design architecture: {str(e)}",
            "project_id": project_id,
            "created_at": datetime.now().isoformat()
        }


@tool
def generate_implementation_plan(architecture: str, project_id: str) -> Dict[str, Any]:
    """
    Generate implementation plan and create actual source code.
    
    Args:
        architecture: JSON string of system architecture
        project_id: Unique identifier for the project
        
    Returns:
        Dictionary containing implementation plan and generated source files
    """
    try:
        # Parse architecture to understand the technology choice
        try:
            arch_data = json.loads(architecture)
            tech_stack = arch_data.get("technology_stack", {})
            frontend_tech = tech_stack.get("frontend", "")
            complexity = arch_data.get("complexity_analysis", "medium")
            overview = arch_data.get("overview", "")
        except:
            frontend_tech = ""
            complexity = "medium"
            overview = ""
            tech_stack = {}

        # Use LLM to generate implementation plan
        implementation_prompt = f"""
        You are a Senior Developer. Create a detailed implementation plan based on this architecture:

        Architecture: {architecture}
        
        Technology Stack: {tech_stack}
        Project Complexity: {complexity}
        Overview: {overview}

        Provide a comprehensive implementation plan including:
        1. Project structure and folder organization
        2. Implementation phases with realistic timelines
        3. Key development tasks and priorities
        4. Setup and configuration steps
        5. Dependencies and tools needed
        6. Development workflow recommendations

        Respond with JSON in this exact format (no markdown):
        {{
            "project_structure": {{
                "folders": ["folder1", "folder2", ...],
                "key_files": ["file1.ext", "file2.ext", ...],
                "description": "Overview of project organization"
            }},
            "implementation_phases": [
                {{
                    "phase": "Phase 1: Setup",
                    "description": "What this phase accomplishes",
                    "tasks": ["task1", "task2", ...],
                    "duration": "time estimate",
                    "deliverables": ["deliverable1", "deliverable2"]
                }},
                {{
                    "phase": "Phase 2: Development",
                    "description": "Core development work",
                    "tasks": ["task1", "task2", ...],
                    "duration": "time estimate", 
                    "deliverables": ["deliverable1", "deliverable2"]
                }},
                {{
                    "phase": "Phase 3: Testing & Deployment",
                    "description": "Testing and deployment",
                    "tasks": ["task1", "task2", ...],
                    "duration": "time estimate",
                    "deliverables": ["deliverable1", "deliverable2"]
                }}
            ],
            "setup_steps": [
                "Step 1: Install dependencies",
                "Step 2: Configure environment",
                "Step 3: Initialize project"
            ],
            "development_workflow": {{
                "version_control": "Git workflow recommendation",
                "testing_approach": "How to test during development",
                "deployment_strategy": "How to deploy changes"
            }},
            "dependencies": {{
                "runtime": ["dependency1", "dependency2"],
                "development": ["dev-dependency1", "dev-dependency2"],
                "tools": ["tool1", "tool2"]
            }},
            "estimated_timeline": "Overall project timeline",
            "risk_considerations": ["risk1", "risk2", ...],
            "success_criteria": ["criteria1", "criteria2", ...]
        }}
        """

        try:
            if llm is None:
                raise Exception("LLM not initialized")
                
            response = llm.invoke(implementation_prompt)
            print(f"Implementation plan LLM response: {len(response.content)} characters")
            
            # Clean response
            content = response.content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            result = json.loads(content)
            
            # Validate response
            if "implementation_phases" not in result:
                raise ValueError("Invalid implementation plan format")
                
            print("LLM implementation plan generated successfully")
            
        except Exception as llm_error:
            print(f"LLM implementation planning failed: {llm_error}")
            
            # Intelligent fallback based on technology
            if "HTML/CSS/JavaScript" in frontend_tech or complexity == "simple":
                result = {
                    "project_structure": {
                        "folders": ["src", "assets", "docs"],
                        "key_files": ["index.html", "styles.css", "script.js", "README.md"],
                        "description": "Simple static web application structure"
                    },
                    "implementation_phases": [
                        {
                            "phase": "Phase 1: Setup & Structure",
                            "description": "Create basic project structure and HTML framework",
                            "tasks": ["Create HTML structure", "Set up CSS framework", "Initialize JavaScript"],
                            "duration": "1-2 days",
                            "deliverables": ["Basic HTML layout", "CSS grid/flexbox structure"]
                        },
                        {
                            "phase": "Phase 2: Core Functionality",
                            "description": "Implement main application logic",
                            "tasks": ["Add interactive features", "Implement calculations", "Add error handling"],
                            "duration": "3-5 days",
                            "deliverables": ["Working calculator", "Input validation", "Error handling"]
                        },
                        {
                            "phase": "Phase 3: Enhancement & Testing",
                            "description": "Polish UI and test thoroughly",
                            "tasks": ["Responsive design", "Keyboard shortcuts", "Cross-browser testing"],
                            "duration": "2-3 days",
                            "deliverables": ["Responsive design", "Accessibility features", "Browser compatibility"]
                        }
                    ],
                    "setup_steps": [
                        "Create project folder",
                        "Set up basic HTML, CSS, JS files",
                        "Open in browser for development"
                    ],
                    "estimated_timeline": "1 week"
                }
            else:
                result = {
                    "project_structure": {
                        "folders": ["src", "public", "tests", "docs", "config"],
                        "key_files": ["package.json", "src/App.js", "src/index.js", "README.md"],
                        "description": "Modern React application structure"
                    },
                    "implementation_phases": [
                        {
                            "phase": "Phase 1: Project Setup",
                            "description": "Initialize React project and dependencies",
                            "tasks": ["Create React app", "Install dependencies", "Configure build tools"],
                            "duration": "1-2 days",
                            "deliverables": ["Working React environment", "Build configuration"]
                        },
                        {
                            "phase": "Phase 2: Component Development",
                            "description": "Build React components and logic",
                            "tasks": ["Create components", "Implement state management", "Add styling"],
                            "duration": "1-2 weeks",
                            "deliverables": ["React components", "Application logic", "Styling"]
                        },
                        {
                            "phase": "Phase 3: Testing & Deployment",
                            "description": "Test components and deploy application",
                            "tasks": ["Unit testing", "Integration testing", "Build for production"],
                            "duration": "3-5 days",
                            "deliverables": ["Test suite", "Production build", "Deployment"]
                        }
                    ],
                    "setup_steps": [
                        "Run npm install",
                        "Start development server with npm start",
                        "Configure environment variables"
                    ],
                    "estimated_timeline": "2-3 weeks"
                }

        # Generate appropriate source code based on complexity and technology
        # Check complexity first, then technology preference
        complexity_level = complexity.lower() if complexity else "medium"
        
        # For simple projects, always use HTML/CSS/JavaScript regardless of what LLM suggested
        if (complexity_level == "simple" or 
            "calculator" in overview.lower() or 
            "basic" in overview.lower() or
            "simple" in overview.lower() or
            frontend_tech == "HTML/CSS/JavaScript" or
            "static" in frontend_tech.lower()):
            
            source_files = _generate_simple_web_app(project_id, overview, arch_data)
            tech_used = "HTML/CSS/JavaScript"
            print(f"✅ Generated simple web app for complexity: {complexity}, frontend: {frontend_tech}")
        else:
            source_files = _generate_react_app(project_id, overview, arch_data)
            tech_used = "React.js" 
            print(f"✅ Generated React app for complexity: {complexity}, frontend: {frontend_tech}")
        
        # Add generated source files to the result
        result["technology_used"] = tech_used
        result["source_files"] = source_files
        
        # Add metadata
        result["project_id"] = project_id
        result["created_at"] = datetime.now().isoformat()
        result["created_by"] = "developer_agent"
        
        # Save source files as individual artifacts
        for filename, content in source_files.items():
            _save_source_file(project_id, filename, content)
        
        # Create a README.md file for the project
        readme_content = f"""# {project_id.replace('-', ' ').title()} Project

## Overview
{result.get('project_structure', {}).get('description', 'Generated web application')}

## Technology Stack
- **Frontend**: {tech_used}
- **Files Generated**: {', '.join(source_files.keys())}

## Project Structure
```
project_{project_id}/
├── src/                    # Source code files
│   ├── index.html         # Main HTML file
│   ├── styles.css         # Stylesheet
│   ├── script.js          # JavaScript logic
│   └── ...                # Other source files
├── docs/                  # Documentation
│   └── README.md          # This file
└── ...                    # Other project files
```

## How to Run
1. Navigate to the `src/` folder
2. Open `index.html` in a web browser
3. Or use a local server:
   ```bash
   cd src
   python -m http.server 8080
   ```
   Then open http://localhost:8080

## Files Description
{chr(10).join('- **' + f + '**: ' + ('Main application file' if f.endswith('.html') else 'Stylesheet' if f.endswith('.css') else 'JavaScript logic' if f.endswith('.js') else 'Project file') for f in source_files.keys() if not f.endswith('.md'))}

## Created
- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Agent**: Developer Agent
- **Technology**: {tech_used}
"""
        _save_source_file(project_id, "README.md", readme_content)
        
        # Update the result to include the README
        result["source_files"]["README.md"] = readme_content
        
        # Save implementation plan
        _save_artifact(project_id, "implementation_plan", result)
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to generate implementation plan: {str(e)}",
            "project_id": project_id,
            "created_at": datetime.now().isoformat()
        }


@tool
def create_test_strategy(implementation_plan: str, project_id: str) -> Dict[str, Any]:
    """
    Create test strategy and run actual tests on generated source code.
    
    Args:
        implementation_plan: JSON string of implementation plan
        project_id: Unique identifier for the project
        
    Returns:
        Dictionary containing test strategy and test results
    """
    try:
        # Parse implementation plan
        try:
            plan_data = json.loads(implementation_plan)
            source_files = plan_data.get("source_files", {})
            tech_used = plan_data.get("technology_used", "HTML/CSS/JavaScript")
            project_structure = plan_data.get("project_structure", {})
            implementation_phases = plan_data.get("implementation_phases", [])
        except:
            source_files = {}
            tech_used = "HTML/CSS/JavaScript"
            project_structure = {}
            implementation_phases = []

        # Use LLM to create intelligent test strategy
        test_strategy_prompt = f"""
        You are a QA Engineer. Create a comprehensive testing strategy based on this implementation plan:

        Technology Used: {tech_used}
        Source Files: {list(source_files.keys()) if source_files else 'Not available'}
        Project Structure: {project_structure}
        Implementation Phases: {[phase.get('phase', '') for phase in implementation_phases]}

        Implementation Plan: {implementation_plan}

        Create a testing strategy that includes:
        1. Testing approach methodology 
        2. Test categories with priorities
        3. Specific test cases for this technology
        4. Automation recommendations
        5. Quality metrics and success criteria
        6. Risk-based testing priorities

        Respond with JSON in this exact format (no markdown):
        {{
            "testing_approach": "Overall testing methodology description",
            "test_categories": [
                {{
                    "category": "Category Name",
                    "description": "What this category tests",
                    "priority": "High|Medium|Low",
                    "automation": true/false,
                    "tools_recommended": ["tool1", "tool2"]
                }}
            ],
            "specific_test_cases": [
                {{
                    "test_id": "TC001",
                    "title": "Test case name",
                    "description": "What to test",
                    "steps": ["step 1", "step 2", "step 3"],
                    "expected_result": "Expected outcome",
                    "priority": "High|Medium|Low",
                    "type": "Unit|Integration|E2E|Performance|Security"
                }}
            ],
            "automation_strategy": {{
                "framework_recommendation": "Recommended testing framework",
                "automation_percentage": "Target % of automated tests",
                "ci_cd_integration": "How to integrate with CI/CD",
                "tools": ["tool1", "tool2", "tool3"]
            }},
            "quality_metrics": {{
                "code_coverage_target": "percentage",
                "performance_benchmarks": ["benchmark1", "benchmark2"],
                "security_requirements": ["requirement1", "requirement2"]
            }},
            "risk_areas": [
                {{
                    "risk": "Risk description",
                    "impact": "High|Medium|Low",
                    "mitigation": "How to mitigate this risk"
                }}
            ],
            "testing_timeline": [
                {{
                    "phase": "Testing phase name",
                    "duration": "time estimate",
                    "activities": ["activity1", "activity2"]
                }}
            ],
            "success_criteria": ["criteria1", "criteria2", ...],
            "deliverables": ["deliverable1", "deliverable2", ...]
        }}
        """

        try:
            if llm is None:
                raise Exception("LLM not initialized")
                
            response = llm.invoke(test_strategy_prompt)
            print(f"Test strategy LLM response: {len(response.content)} characters")
            
            # Clean response
            content = response.content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            strategy_result = json.loads(content)
            
            # Validate response
            if "testing_approach" not in strategy_result:
                raise ValueError("Invalid test strategy format")
                
            print("LLM test strategy generated successfully")
            
        except Exception as llm_error:
            print(f"LLM test strategy generation failed: {llm_error}")
            
            # Intelligent fallback based on technology
            if tech_used == "HTML/CSS/JavaScript":
                strategy_result = {
                    "testing_approach": "Static web application testing with focus on functionality, compatibility, and user experience",
                    "test_categories": [
                        {
                            "category": "HTML Validation",
                            "description": "Validate HTML structure, semantics, and accessibility",
                            "priority": "High",
                            "automation": True,
                            "tools_recommended": ["HTML Validator", "axe-core", "WAVE"]
                        },
                        {
                            "category": "CSS Testing",
                            "description": "Test styling, responsiveness, and cross-browser compatibility",
                            "priority": "Medium",
                            "automation": True,
                            "tools_recommended": ["CSS Validator", "BackstopJS", "Percy"]
                        },
                        {
                            "category": "JavaScript Functionality",
                            "description": "Test interactive features and calculations",
                            "priority": "High",
                            "automation": True,
                            "tools_recommended": ["Jest", "Cypress", "Playwright"]
                        },
                        {
                            "category": "Cross-Browser Testing",
                            "description": "Ensure compatibility across different browsers",
                            "priority": "High",
                            "automation": False,
                            "tools_recommended": ["BrowserStack", "Sauce Labs"]
                        }
                    ],
                    "specific_test_cases": [
                        {
                            "test_id": "TC001",
                            "title": "Basic Calculation Test",
                            "description": "Verify basic arithmetic operations work correctly",
                            "steps": ["Enter first number", "Select operation", "Enter second number", "Press equals"],
                            "expected_result": "Correct calculation result displayed",
                            "priority": "High",
                            "type": "Functional"
                        },
                        {
                            "test_id": "TC002", 
                            "title": "Keyboard Input Test",
                            "description": "Verify keyboard shortcuts work properly",
                            "steps": ["Use keyboard to input numbers", "Use keyboard shortcuts for operations"],
                            "expected_result": "All keyboard inputs function correctly",
                            "priority": "Medium",
                            "type": "Usability"
                        }
                    ],
                    "automation_strategy": {
                        "framework_recommendation": "Cypress for E2E testing",
                        "automation_percentage": "80%",
                        "ci_cd_integration": "GitHub Actions workflow",
                        "tools": ["Cypress", "Jest", "HTML Validator"]
                    }
                }
            else:
                strategy_result = {
                    "testing_approach": "React component testing with unit tests, integration tests, and E2E testing",
                    "test_categories": [
                        {
                            "category": "Unit Tests",
                            "description": "Test individual React components in isolation",
                            "priority": "High",
                            "automation": True,
                            "tools_recommended": ["Jest", "React Testing Library"]
                        },
                        {
                            "category": "Integration Tests",
                            "description": "Test component interactions and state management",
                            "priority": "High",
                            "automation": True,
                            "tools_recommended": ["Jest", "React Testing Library", "MSW"]
                        },
                        {
                            "category": "E2E Tests",
                            "description": "Test complete user workflows",
                            "priority": "Medium",
                            "automation": True,
                            "tools_recommended": ["Cypress", "Playwright", "Puppeteer"]
                        }
                    ],
                    "automation_strategy": {
                        "framework_recommendation": "Jest + React Testing Library",
                        "automation_percentage": "90%",
                        "ci_cd_integration": "GitHub Actions with test coverage reporting",
                        "tools": ["Jest", "React Testing Library", "Cypress"]
                    }
                }

        # Run actual tests on the source files
        test_execution_results = _test_source_files(source_files, tech_used)
        
        # Combine strategy with execution results
        result = {
            "testing_approach": strategy_result.get("testing_approach", "Comprehensive testing approach"),
            "test_categories": strategy_result.get("test_categories", []),
            "specific_test_cases": strategy_result.get("specific_test_cases", []),
            "automation_strategy": strategy_result.get("automation_strategy", {}),
            "test_execution_results": test_execution_results,
            "quality_score": test_execution_results.get("quality_score", 85),
            "recommendations": test_execution_results.get("recommendations", []),
            "quality_metrics": strategy_result.get("quality_metrics", {}),
            "risk_areas": strategy_result.get("risk_areas", []),
            "success_criteria": strategy_result.get("success_criteria", []),
            "project_id": project_id,
            "created_at": datetime.now().isoformat(),
            "created_by": "tester_agent"
        }
        
        # Save test strategy
        _save_artifact(project_id, "test_strategy", result)
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to create test strategy: {str(e)}",
            "project_id": project_id,
            "created_at": datetime.now().isoformat()
        }


def _generate_simple_web_app(project_id: str, overview: str, architecture_data: Dict[str, Any]) -> Dict[str, str]:
    """Generate HTML/CSS/JS application based on project requirements using LLM."""
    
    # Extract project details
    components = architecture_data.get("components", [])
    tech_stack = architecture_data.get("technology_stack", {})
    
    # Use LLM to generate project-specific code
    code_generation_prompt = f"""
    You are a Senior Frontend Developer. Generate complete, working HTML, CSS, and JavaScript code for this project:

    Project Overview: {overview}
    Architecture Components: {components}
    Technology Stack: {tech_stack}

    Requirements:
    1. Generate COMPLETE, WORKING code (not snippets or placeholders)
    2. Create a modern, responsive design
    3. Include proper functionality based on the project description
    4. Use semantic HTML, modern CSS (flexbox/grid), and vanilla JavaScript
    5. Make it visually appealing with gradients, shadows, and smooth animations

    Project Types and Expected Outputs:
    - Calculator: Number pad, display, arithmetic operations
    - To-Do List: Add/remove tasks, mark complete, local storage
    - Weather App: Mock weather display, search by city
    - Timer/Stopwatch: Start/stop/reset functionality
    - Quiz App: Multiple choice questions, scoring
    - Portfolio: About, projects, contact sections
    - Landing Page: Hero section, features, call-to-action

    Respond with JSON containing the exact file contents (no markdown formatting):
    {{
        "index.html": "complete HTML code",
        "styles.css": "complete CSS code", 
        "script.js": "complete JavaScript code"
    }}
    """

    try:
        if llm is None:
            raise Exception("LLM not initialized")
            
        response = llm.invoke(code_generation_prompt)
        print(f"Code generation LLM response: {len(response.content)} characters")
        
        # Clean response
        content = response.content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # Try to find JSON within the response
        if not content.startswith('{'):
            start_idx = content.find('{')
            if start_idx != -1:
                end_idx = content.rfind('}')
                if end_idx != -1:
                    content = content[start_idx:end_idx+1]
        
        generated_code = json.loads(content)
        
        # Validate that we got the required files
        if "index.html" not in generated_code or "styles.css" not in generated_code or "script.js" not in generated_code:
            raise ValueError("LLM didn't generate all required files")
            
        print("✅ LLM generated project-specific code successfully")
        
        # Add a README for the generated project
        generated_code["README.md"] = f"""# {project_id.replace('-', ' ').title().replace('_', ' ')} Project

## Overview
{overview}

## Features
- Modern, responsive design
- Vanilla HTML, CSS, and JavaScript
- Cross-browser compatibility

## How to Run
1. Open index.html in your web browser
2. Or serve with a local server for best results

## Technology Stack
- HTML5 for structure
- CSS3 with modern features (flexbox/grid)
- Vanilla JavaScript for functionality

## Generated by AI Agent
This project was automatically generated by the Agentic Ecosystem.
"""
        
        return generated_code
        
    except Exception as llm_error:
        print(f"LLM code generation failed: {llm_error}")
        print("Falling back to template-based generation...")
        
        # Intelligent fallback based on project description
        overview_lower = overview.lower()
        
        if "calculator" in overview_lower or "arithmetic" in overview_lower:
            return _generate_calculator_template()
        elif "todo" in overview_lower or "task" in overview_lower:
            return _generate_todo_template()
        elif "timer" in overview_lower or "stopwatch" in overview_lower:
            return _generate_timer_template()
        elif "weather" in overview_lower:
            return _generate_weather_template()
        elif "portfolio" in overview_lower:
            return _generate_portfolio_template()
        elif "quiz" in overview_lower or "trivia" in overview_lower:
            return _generate_quiz_template()
        else:
            # Generic landing page template
            return _generate_generic_template(overview)


def _generate_calculator_template() -> Dict[str, str]:
    """Generate calculator template."""
    return {
        "index.html": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calculator</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="calculator">
        <div class="display">
            <input type="text" id="display" readonly>
        </div>
        <div class="buttons">
            <button onclick="clearDisplay()">C</button>
            <button onclick="deleteLast()">←</button>
            <button onclick="appendToDisplay('/')" class="operator">÷</button>
            <button onclick="appendToDisplay('*')" class="operator">×</button>
            
            <button onclick="appendToDisplay('7')">7</button>
            <button onclick="appendToDisplay('8')">8</button>
            <button onclick="appendToDisplay('9')">9</button>
            <button onclick="appendToDisplay('-')" class="operator">-</button>
            
            <button onclick="appendToDisplay('4')">4</button>
            <button onclick="appendToDisplay('5')">5</button>
            <button onclick="appendToDisplay('6')">6</button>
            <button onclick="appendToDisplay('+')" class="operator">+</button>
            
            <button onclick="appendToDisplay('1')">1</button>
            <button onclick="appendToDisplay('2')">2</button>
            <button onclick="appendToDisplay('3')">3</button>
            <button onclick="calculate()" class="equals">=</button>
            
            <button onclick="appendToDisplay('0')" class="zero">0</button>
            <button onclick="appendToDisplay('.')">.</button>
        </div>
    </div>
    <script src="script.js"></script>
</body>
</html>''',

        "styles.css": '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Arial', sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
}

.calculator {
    background: #2c3e50;
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    max-width: 300px;
    width: 100%;
}

.display {
    margin-bottom: 20px;
}

#display {
    width: 100%;
    height: 60px;
    background: #34495e;
    border: none;
    border-radius: 8px;
    color: white;
    font-size: 24px;
    text-align: right;
    padding: 0 15px;
    outline: none;
}

.buttons {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
}

button {
    height: 60px;
    border: none;
    border-radius: 8px;
    font-size: 18px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.2s ease;
    background: #7f8c8d;
    color: white;
}

button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
}

.operator {
    background: #e67e22 !important;
}

.equals {
    background: #27ae60 !important;
    grid-column: span 2;
}

.zero {
    grid-column: span 2;
}''',

        "script.js": '''let display = document.getElementById('display');

function appendToDisplay(value) {
    if (display.value === '0' && value !== '.') {
        display.value = value;
    } else {
        display.value += value;
    }
}

function clearDisplay() {
    display.value = '';
}

function deleteLast() {
    display.value = display.value.slice(0, -1);
}

function calculate() {
    try {
        let expression = display.value
            .replace(/×/g, '*')
            .replace(/÷/g, '/');
        
        if (expression === '' || /[+\\-*/.]$/.test(expression)) {
            return;
        }
        
        let result = eval(expression);
        
        if (!isFinite(result)) {
            display.value = 'Error';
            return;
        }
        
        display.value = Number.isInteger(result) ? result : parseFloat(result.toFixed(8));
        
    } catch (error) {
        display.value = 'Error';
    }
}

// Keyboard support
document.addEventListener('keydown', function(event) {
    const key = event.key;
    
    if (key >= '0' && key <= '9' || key === '.') {
        appendToDisplay(key);
    } else if (key === '+' || key === '-') {
        appendToDisplay(key);
    } else if (key === '*') {
        appendToDisplay('×');
    } else if (key === '/') {
        event.preventDefault();
        appendToDisplay('÷');
    } else if (key === 'Enter' || key === '=') {
        event.preventDefault();
        calculate();
    } else if (key === 'Escape' || key === 'c' || key === 'C') {
        clearDisplay();
    } else if (key === 'Backspace') {
        deleteLast();
    }
});'''
    }


def _generate_todo_template() -> Dict[str, str]:
    """Generate todo list template."""
    return {
        "index.html": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Todo List</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <h1>My Todo List</h1>
        <div class="input-container">
            <input type="text" id="taskInput" placeholder="Add a new task...">
            <button onclick="addTask()">Add</button>
        </div>
        <ul id="taskList"></ul>
    </div>
    <script src="script.js"></script>
</body>
</html>''',

        "styles.css": '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Arial', sans-serif;
    background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
    min-height: 100vh;
    padding: 20px;
}

.container {
    max-width: 500px;
    margin: 50px auto;
    background: white;
    border-radius: 15px;
    padding: 30px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

h1 {
    text-align: center;
    color: #2d3436;
    margin-bottom: 30px;
}

.input-container {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

#taskInput {
    flex: 1;
    padding: 12px;
    border: 2px solid #ddd;
    border-radius: 8px;
    font-size: 16px;
}

button {
    padding: 12px 20px;
    background: #00b894;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    transition: background 0.3s;
}

button:hover {
    background: #00a085;
}

#taskList {
    list-style: none;
}

.task-item {
    background: #f8f9fa;
    margin: 10px 0;
    padding: 15px;
    border-radius: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.3s;
}

.task-item.completed {
    opacity: 0.6;
    text-decoration: line-through;
}

.task-actions {
    display: flex;
    gap: 10px;
}

.complete-btn {
    background: #fdcb6e;
    padding: 5px 10px;
    font-size: 14px;
}

.delete-btn {
    background: #e17055;
    padding: 5px 10px;
    font-size: 14px;
}''',

        "script.js": '''let tasks = JSON.parse(localStorage.getItem('tasks')) || [];

function saveTasks() {
    localStorage.setItem('tasks', JSON.stringify(tasks));
}

function renderTasks() {
    const taskList = document.getElementById('taskList');
    taskList.innerHTML = '';
    
    tasks.forEach((task, index) => {
        const li = document.createElement('li');
        li.className = `task-item ${task.completed ? 'completed' : ''}`;
        li.innerHTML = `
            <span>${task.text}</span>
            <div class="task-actions">
                <button class="complete-btn" onclick="toggleTask(${index})">
                    ${task.completed ? 'Undo' : 'Complete'}
                </button>
                <button class="delete-btn" onclick="deleteTask(${index})">Delete</button>
            </div>
        `;
        taskList.appendChild(li);
    });
}

function addTask() {
    const input = document.getElementById('taskInput');
    const text = input.value.trim();
    
    if (text) {
        tasks.push({ text, completed: false });
        input.value = '';
        saveTasks();
        renderTasks();
    }
}

function toggleTask(index) {
    tasks[index].completed = !tasks[index].completed;
    saveTasks();
    renderTasks();
}

function deleteTask(index) {
    tasks.splice(index, 1);
    saveTasks();
    renderTasks();
}

// Enter key support
document.getElementById('taskInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        addTask();
    }
});

// Initial render
renderTasks();'''
    }


def _generate_generic_template(overview: str) -> Dict[str, str]:
    """Generate generic landing page template."""
    return {
        "index.html": f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Application</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <nav>
            <h1>My App</h1>
            <ul>
                <li><a href="#home">Home</a></li>
                <li><a href="#features">Features</a></li>
                <li><a href="#about">About</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <section id="home" class="hero">
            <div class="hero-content">
                <h2>Welcome to Our Application</h2>
                <p>{overview}</p>
                <button class="cta-button">Get Started</button>
            </div>
        </section>
        
        <section id="features" class="features">
            <h2>Features</h2>
            <div class="feature-grid">
                <div class="feature-card">
                    <h3>Feature 1</h3>
                    <p>Description of feature 1</p>
                </div>
                <div class="feature-card">
                    <h3>Feature 2</h3>
                    <p>Description of feature 2</p>
                </div>
                <div class="feature-card">
                    <h3>Feature 3</h3>
                    <p>Description of feature 3</p>
                </div>
            </div>
        </section>
    </main>
    
    <footer>
        <p>&copy; 2025 Web Application. All rights reserved.</p>
    </footer>
    
    <script src="script.js"></script>
</body>
</html>''',

        "styles.css": '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Arial', sans-serif;
    line-height: 1.6;
    color: #333;
}

header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem 0;
    position: fixed;
    width: 100%;
    top: 0;
    z-index: 1000;
}

nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
}

nav ul {
    display: flex;
    list-style: none;
    gap: 2rem;
}

nav a {
    color: white;
    text-decoration: none;
    transition: opacity 0.3s;
}

nav a:hover {
    opacity: 0.8;
}

main {
    margin-top: 80px;
}

.hero {
    background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
    color: white;
    padding: 100px 0;
    text-align: center;
}

.hero-content {
    max-width: 800px;
    margin: 0 auto;
    padding: 0 2rem;
}

.hero h2 {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.hero p {
    font-size: 1.2rem;
    margin-bottom: 2rem;
}

.cta-button {
    background: #00b894;
    color: white;
    padding: 15px 30px;
    border: none;
    border-radius: 8px;
    font-size: 1.1rem;
    cursor: pointer;
    transition: background 0.3s;
}

.cta-button:hover {
    background: #00a085;
}

.features {
    padding: 80px 0;
    background: #f8f9fa;
}

.features h2 {
    text-align: center;
    margin-bottom: 3rem;
    font-size: 2.5rem;
}

.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
}

.feature-card {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    text-align: center;
    transition: transform 0.3s;
}

.feature-card:hover {
    transform: translateY(-5px);
}

footer {
    background: #2d3436;
    color: white;
    text-align: center;
    padding: 2rem 0;
}

@media (max-width: 768px) {
    nav {
        flex-direction: column;
        gap: 1rem;
    }
    
    .hero h2 {
        font-size: 2rem;
    }
    
    .feature-grid {
        grid-template-columns: 1fr;
    }
}''',

        "script.js": '''// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// CTA button functionality
document.querySelector('.cta-button').addEventListener('click', function() {
    alert('Welcome! This is where your application functionality would begin.');
});

// Add some interactivity to feature cards
document.querySelectorAll('.feature-card').forEach(card => {
    card.addEventListener('click', function() {
        this.style.background = this.style.background === 'rgb(116, 185, 255)' ? 'white' : '#74b9ff';
        this.style.color = this.style.color === 'white' ? '#333' : 'white';
    });
});'''
    }


# Add minimal templates for other types
def _generate_timer_template() -> Dict[str, str]:
    return _generate_generic_template("A simple timer application for tracking time")

def _generate_weather_template() -> Dict[str, str]:
    return _generate_generic_template("A weather application for checking weather conditions")

def _generate_portfolio_template() -> Dict[str, str]:
    return _generate_generic_template("A personal portfolio website")

def _generate_quiz_template() -> Dict[str, str]:
    return _generate_generic_template("An interactive quiz application")


def _generate_react_app(project_id: str, overview: str = "", architecture_data: Dict[str, Any] = None) -> Dict[str, str]:
    """Generate React calculator application."""
    return {
        "package.json": '''{
  "name": "calculator-app",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }
}''',

        "src/App.js": '''import React, { useState } from 'react';
import './App.css';

function App() {
  const [display, setDisplay] = useState('');

  const appendToDisplay = (value) => {
    setDisplay(prev => prev === '0' && value !== '.' ? value : prev + value);
  };

  const clearDisplay = () => {
    setDisplay('');
  };

  const deleteLast = () => {
    setDisplay(prev => prev.slice(0, -1));
  };

  const calculate = () => {
    try {
      const expression = display.replace(/×/g, '*').replace(/÷/g, '/');
      if (expression === '' || /[+\\-*/.]$/.test(expression)) return;
      
      const result = eval(expression);
      if (!isFinite(result)) {
        setDisplay('Error');
        return;
      }
      
      setDisplay(Number.isInteger(result) ? String(result) : String(parseFloat(result.toFixed(8))));
    } catch (error) {
      setDisplay('Error');
    }
  };

  return (
    <div className="App">
      <div className="calculator">
        <div className="display">
          <input type="text" value={display} readOnly />
        </div>
        <div className="buttons">
          <button onClick={clearDisplay}>C</button>
          <button onClick={deleteLast}>←</button>
          <button onClick={() => appendToDisplay('÷')} className="operator">÷</button>
          <button onClick={() => appendToDisplay('×')} className="operator">×</button>
          
          <button onClick={() => appendToDisplay('7')}>7</button>
          <button onClick={() => appendToDisplay('8')}>8</button>
          <button onClick={() => appendToDisplay('9')}>9</button>
          <button onClick={() => appendToDisplay('-')} className="operator">-</button>
          
          <button onClick={() => appendToDisplay('4')}>4</button>
          <button onClick={() => appendToDisplay('5')}>5</button>
          <button onClick={() => appendToDisplay('6')}>6</button>
          <button onClick={() => appendToDisplay('+')} className="operator">+</button>
          
          <button onClick={() => appendToDisplay('1')}>1</button>
          <button onClick={() => appendToDisplay('2')}>2</button>
          <button onClick={() => appendToDisplay('3')}>3</button>
          <button onClick={calculate} className="equals">=</button>
          
          <button onClick={() => appendToDisplay('0')} className="zero">0</button>
          <button onClick={() => appendToDisplay('.')}>.</button>
        </div>
      </div>
    </div>
  );
}

export default App;''',

        "README.md": '''# React Calculator App

A calculator application built with React.js.

## Setup
1. npm install
2. npm start

## Features
- Basic arithmetic operations
- Modern React component structure
- Responsive design
'''
    }


def _test_source_files(source_files: Dict[str, str], tech_used: str) -> Dict[str, Any]:
    """Test the generated source files for quality and correctness."""
    results = {
        "files_tested": list(source_files.keys()),
        "test_results": {},
        "issues_found": [],
        "quality_score": 0,
        "recommendations": []
    }
    
    total_score = 0
    file_count = 0
    
    for filename, content in source_files.items():
        file_score = 100
        file_issues = []
        
        # Basic tests for all files
        if not content.strip():
            file_issues.append("File is empty")
            file_score -= 50
            
        # HTML-specific tests
        if filename.endswith('.html'):
            if '<!DOCTYPE html>' not in content:
                file_issues.append("Missing DOCTYPE declaration")
                file_score -= 10
            if '<title>' not in content:
                file_issues.append("Missing title tag")
                file_score -= 5
            if content.count('<') != content.count('>'):
                file_issues.append("Unmatched HTML tags")
                file_score -= 15
                
        # CSS-specific tests
        elif filename.endswith('.css'):
            if content.count('{') != content.count('}'):
                file_issues.append("Unmatched CSS braces")
                file_score -= 15
            if len(content.strip()) < 50:
                file_issues.append("CSS file seems too simple")
                file_score -= 5
                
        # JavaScript-specific tests  
        elif filename.endswith('.js'):
            if content.count('(') != content.count(')'):
                file_issues.append("Unmatched parentheses")
                file_score -= 15
            if content.count('{') != content.count('}'):
                file_issues.append("Unmatched braces")
                file_score -= 15
            if 'function' not in content and '=>' not in content:
                file_issues.append("No functions found")
                file_score -= 10
        
        file_score = max(0, file_score)
        total_score += file_score
        file_count += 1
        
        results["test_results"][filename] = {
            "score": file_score,
            "issues": file_issues,
            "status": "pass" if file_score > 80 else "warning" if file_score > 60 else "fail"
        }
        
        results["issues_found"].extend([f"{filename}: {issue}" for issue in file_issues])
    
    # Calculate overall quality score
    if file_count > 0:
        results["quality_score"] = round(total_score / file_count, 1)
        
        # Generate recommendations
        if results["quality_score"] < 70:
            results["recommendations"].append("Code quality needs improvement")
        if len(results["issues_found"]) > 3:
            results["recommendations"].append("Multiple issues found - consider review")
        if results["quality_score"] > 85:
            results["recommendations"].append("Good code quality - ready for deployment")
    
    return results


def _save_source_file(project_id: str, filename: str, content: str) -> None:
    """Save individual source code file with proper project structure."""
    try:
        # Create project directory with proper structure
        base_dir = Path(__file__).parent.parent.parent / "out" / f"project_{project_id}"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        src_dir = base_dir / "src"
        docs_dir = base_dir / "docs"
        src_dir.mkdir(exist_ok=True)
        docs_dir.mkdir(exist_ok=True)
        
        # Determine where to save the file based on its type
        if filename.endswith('.md'):
            # Documentation goes in docs folder
            file_path = docs_dir / filename
        elif filename in ['package.json', 'package-lock.json', '.gitignore']:
            # Root configuration files go in project root
            file_path = base_dir / filename
        else:
            # Source code goes in src folder
            file_path = src_dir / filename
        
        # Save the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Saved source file: {file_path}")
        
        # Also save metadata as JSON for tracking
        file_result = {
            "filename": filename,
            "file_path": str(file_path),
            "relative_path": str(file_path.relative_to(base_dir)),
            "content_length": len(content),
            "project_id": project_id,
            "created_at": datetime.now().isoformat(),
            "created_by": "developer_agent"
        }
        safe_filename = filename.replace('/', '_').replace('.', '_')
        _save_artifact(project_id, f"source_code_metadata_{safe_filename}", file_result)
        
    except Exception as e:
        print(f"Error saving source file {filename}: {e}")
        # Fallback to old method if there's an error
        file_result = {
            "filename": filename,
            "content": content,
            "project_id": project_id,
            "created_at": datetime.now().isoformat(),
            "created_by": "developer_agent",
            "error": str(e)
        }
        safe_filename = filename.replace('/', '_').replace('.', '_')
        _save_artifact(project_id, f"source_code_{safe_filename}", file_result)


def _save_artifact(project_id: str, artifact_type: str, data: Dict[str, Any]) -> None:
    """Save artifact data to project folder."""
    try:
        # Create project directory
        base_dir = Path(__file__).parent.parent.parent / "out" / f"project_{project_id}"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON
        file_path = base_dir / f"{artifact_type}_{data.get('created_by', 'agent')}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        # Also save as markdown for readability
        md_content = _convert_to_markdown(artifact_type, data)
        md_path = base_dir / f"{artifact_type}_{data.get('created_by', 'agent')}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
    except Exception as e:
        print(f"Error saving artifact: {e}")


def _convert_to_markdown(artifact_type: str, data: Dict[str, Any]) -> str:
    """Convert artifact data to markdown format."""
    md_content = f"# {artifact_type.replace('_', ' ').title()}\n\n"
    
    # Add metadata
    if "created_at" in data:
        md_content += f"**Created:** {data['created_at']}\n"
    if "created_by" in data:
        md_content += f"**Created by:** {data['created_by']}\n"
    if "project_id" in data:
        md_content += f"**Project ID:** {data['project_id']}\n\n"
    
    # Convert main content
    for key, value in data.items():
        if key in ["created_at", "created_by", "project_id"]:
            continue
            
        md_content += f"## {key.replace('_', ' ').title()}\n\n"
        
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    md_content += f"- **{item.get('name', 'Item')}**: {item.get('description', str(item))}\n"
                else:
                    md_content += f"- {item}\n"
        elif isinstance(value, dict):
            for subkey, subvalue in value.items():
                md_content += f"- **{subkey}**: {subvalue}\n"
        else:
            md_content += f"{value}\n"
        
        md_content += "\n"
    
    return md_content
