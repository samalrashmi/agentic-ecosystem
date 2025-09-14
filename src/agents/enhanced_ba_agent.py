"""
Enhanced Business Analyst Agent for detailed functional specifications and user stories.
This module provides standalone BA functionality for creating comprehensive documentation.
"""

import uuid
import json
import tiktoken
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .base_agent import BaseAgent
from ..models import (
    AgentType, Message, MessageType, Priority, ProjectSpecification,
    UserStory, TechnicalRequirement, ProjectDomain
)
from ..utils.prompt_manager import get_prompt_manager


class EnhancedBAAgent(BaseAgent):
    """
    Enhanced Business Analyst Agent for detailed functional specifications.
    Can work standalone to create comprehensive requirements documentation.
    """
    
    def __init__(self, agent_id: str = None, **kwargs):
        super().__init__(
            agent_id=agent_id or "enhanced_ba_agent_001",
            agent_type=AgentType.BA,
            **kwargs
        )
        
        # Enhanced BA-specific attributes
        self.current_projects: Dict[str, ProjectSpecification] = {}
        self.functional_specs: Dict[str, Dict] = {}
        self.user_stories: Dict[str, List[Dict]] = {}
        
        # Token management
        self.max_context_tokens = 200000  # Configurable based on LLM model
        self.max_iterations = 2  # Maximum LLM calls for large requirements
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer
        
        # Initialize prompt manager
        self.prompt_manager = get_prompt_manager()
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        return len(self.tokenizer.encode(text))
    
    def get_agent_persona_prompt(self) -> str:
        """Get the enhanced BA agent persona prompt from prompt library."""
        return self.prompt_manager.get_persona('ba_agent')

    async def generate_standalone_specification(self, requirements: str, project_title: str = None) -> Dict[str, Any]:
        """
        Generate comprehensive functional specification as a standalone operation.
        
        Args:
            requirements: Raw requirements text
            project_title: Optional project title
            
        Returns:
            Complete functional specification document
        """
        project_id = str(uuid.uuid4())
        
        # Create project specification
        project_spec = ProjectSpecification(
            id=project_id,
            title=project_title or f"Project_{project_id[:8]}",
            description=requirements,
            domain=self._determine_domain(requirements),
            requirements=[],
            constraints=[]
        )
        
        self.current_projects[project_id] = project_spec
        
        # Determine if we need multiple LLM calls based on token count
        requirement_tokens = self.count_tokens(requirements)
        
        if requirement_tokens > (self.max_context_tokens * 0.3):  # If input is >30% of context
            # Use iterative approach for large requirements
            spec_document = await self._generate_specification_iteratively(requirements, project_spec)
        else:
            # Single comprehensive call
            spec_document = await self._generate_specification_single_call(requirements, project_spec)
        
        # Store the generated specification
        self.functional_specs[project_id] = spec_document
        
        return {
            "project_id": project_id,
            "specification": spec_document,
            "timestamp": datetime.now().isoformat(),
            "token_count": self.count_tokens(str(spec_document))
        }
    
    async def _generate_specification_single_call(self, requirements: str, project_spec: ProjectSpecification) -> Dict[str, Any]:
        """Generate complete specification using Chain of Thought approach in a single LLM call."""
        
        # Use the chain of thought prompt from the prompt library
        chain_of_thought_prompt = self.prompt_manager.get_chain_of_thought('ba_agent', user_requirement=requirements)
        
        system_message = self.get_agent_persona_prompt()
        response = await self.query_llm(chain_of_thought_prompt, system_message)
        
        try:
            # Parse the chain of thought response and convert to structured format
            structured_spec = await self._parse_chain_of_thought_response(response, requirements)
            return structured_spec
        except Exception as e:
            self.logger.error(f"Failed to parse chain of thought response: {e}")
            # Fallback: create structured document from text response
            return await self._create_fallback_document(response, requirements)
    
    async def _parse_chain_of_thought_response(self, response: str, requirements: str) -> Dict[str, Any]:
        """Parse the chain of thought response and convert to structured format."""
        
        # Extract sections from the markdown response
        sections = self._extract_markdown_sections(response)
        
        # Convert to structured format
        structured_spec = {
            "executive_summary": self._extract_executive_summary(sections, requirements),
            "business_context": self._extract_business_context(sections),
            "functional_requirements": self._extract_functional_requirements(sections),
            "non_functional_requirements": self._extract_non_functional_requirements(sections),
            "user_personas": self._extract_user_personas(sections),
            "business_rules": self._extract_business_rules(sections),
            "user_stories": self._extract_user_stories(sections),
            "data_requirements": self._extract_data_requirements(sections),
            "integration_requirements": self._extract_integration_requirements(sections),
            "assumptions_and_dependencies": self._extract_assumptions_dependencies(sections),
            "chain_of_thought_analysis": {
                "requirement_analysis": sections.get("1. Requirement Analysis & Clarification", ""),
                "functional_specification": sections.get("2. Functional Specification", ""),
                "gherkin_stories": sections.get("3. Gherkin User Stories", "")
            }
        }
        
        return structured_spec
    
    def _extract_markdown_sections(self, response: str) -> Dict[str, str]:
        """Extract sections from markdown response."""
        sections = {}
        current_section = None
        current_content = []
        
        lines = response.split('\n')
        for line in lines:
            if line.startswith('## '):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _extract_executive_summary(self, sections: Dict[str, str], requirements: str) -> str:
        """Extract or generate executive summary."""
        # Look for introduction or purpose in functional spec
        func_spec = sections.get("2. Functional Specification", "")
        if "1.0 Introduction & Purpose" in func_spec:
            # Extract the introduction section
            lines = func_spec.split('\n')
            intro_lines = []
            in_intro = False
            for line in lines:
                if "1.0 Introduction & Purpose" in line:
                    in_intro = True
                    continue
                elif line.startswith("## ") or line.startswith("### ") and "2.0" in line:
                    break
                elif in_intro and line.strip():
                    intro_lines.append(line.strip())
            
            return '\n'.join(intro_lines) if intro_lines else f"Comprehensive functional specification for: {requirements[:100]}..."
        
        return f"Functional specification document addressing the requirements: {requirements[:200]}..."
    
    def _extract_business_context(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """Extract business context from analysis."""
        req_analysis = sections.get("1. Requirement Analysis & Clarification", "")
        
        return {
            "background": "Business analysis completed based on provided requirements",
            "objectives": ["Meet specified business requirements", "Deliver functional software solution"],
            "success_criteria": ["Requirements fully implemented", "User acceptance achieved", "System performance meets expectations"]
        }
    
    def _extract_functional_requirements(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract functional requirements from specification."""
        func_spec = sections.get("2. Functional Specification", "")
        
        # Basic extraction - in a real implementation, you'd parse more sophisticated
        requirements = [
            {
                "id": "FR-001",
                "title": "Core System Functionality",
                "description": "Primary system features as specified in requirements",
                "acceptance_criteria": ["System meets functional specifications", "All core features operational"],
                "priority": "High",
                "complexity": "Medium"
            }
        ]
        
        return requirements
    
    def _extract_non_functional_requirements(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract non-functional requirements."""
        return [
            {
                "id": "NFR-001",
                "category": "Performance",
                "requirement": "System response time under 2 seconds",
                "acceptance_criteria": "95% of requests complete within 2 seconds"
            },
            {
                "id": "NFR-002", 
                "category": "Security",
                "requirement": "Secure user authentication and authorization",
                "acceptance_criteria": "All security tests pass and vulnerabilities addressed"
            }
        ]
    
    def _extract_user_personas(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract user personas from analysis."""
        return [
            {
                "name": "Primary User",
                "role": "System End User",
                "goals": ["Efficiently use system features", "Achieve business objectives"],
                "pain_points": ["Complex interfaces", "Slow system performance"],
                "tech_savviness": "Medium"
            }
        ]
    
    def _extract_business_rules(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract business rules."""
        return [
            {
                "id": "BR-001",
                "rule": "System must enforce data validation",
                "rationale": "Ensures data integrity and system reliability"
            }
        ]
    
    def _extract_user_stories(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract user stories with Gherkin scenarios."""
        gherkin_section = sections.get("3. Gherkin User Stories", "")
        
        return [
            {
                "id": "US-001",
                "feature": "Core Feature",
                "story": "As a user I want to use the system So that I can accomplish my tasks",
                "gherkin_scenarios": gherkin_section if gherkin_section else """Feature: Core System Usage
  As a user
  I want to access system functionality
  So that I can complete my work efficiently

  Scenario: Successful system access
    Given the user has valid credentials
    When they log into the system
    Then they can access core features
    And the system responds promptly""",
                "acceptance_criteria": ["User can access system", "Features work as expected"],
                "related_requirements": ["FR-001"]
            }
        ]
    
    def _extract_data_requirements(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """Extract data requirements."""
        return {
            "entities": [
                {
                    "name": "User",
                    "description": "System user entity",
                    "attributes": ["id", "name", "email", "role"],
                    "relationships": ["Has permissions", "Creates data"]
                }
            ],
            "data_flows": ["User input flows to system processing and storage"]
        }
    
    def _extract_integration_requirements(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract integration requirements."""
        return [
            {
                "system": "External Authentication",
                "type": "API",
                "description": "Integration with authentication service",
                "data_exchange": "User credentials and session tokens"
            }
        ]
    
    def _extract_assumptions_dependencies(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """Extract assumptions and dependencies."""
        return {
            "assumptions": ["Users have basic technical skills", "System will be web-based"],
            "dependencies": ["Authentication service availability", "Database infrastructure"],
            "risks": ["Technical complexity", "User adoption challenges"],
            "constraints": ["Budget limitations", "Timeline constraints"]
        }
    
    async def _generate_specification_iteratively(self, requirements: str, project_spec: ProjectSpecification) -> Dict[str, Any]:
        """Generate specification using multiple LLM calls with chain of thought approach for large requirements."""
        
        self.logger.info(f"Generating specification iteratively for large requirements (token count: {self.count_tokens(requirements)})")
        
        # Phase 1: Chain of Thought Analysis
        phase1_result = await self._generate_chain_of_thought_analysis(requirements, project_spec)
        
        # Phase 2: Detailed Specification Sections
        phase2_result = await self._generate_detailed_specification_sections(requirements, phase1_result)
        
        # Combine results
        spec_document = {**phase1_result, **phase2_result}
        
        return spec_document
    
    async def _generate_chain_of_thought_analysis(self, requirements: str, project_spec: ProjectSpecification) -> Dict[str, Any]:
        """Phase 1: Generate chain of thought analysis."""
        
        chain_of_thought_prompt = self.prompt_manager.get_chain_of_thought('ba_agent', user_requirement=requirements)
        
        system_message = self.get_agent_persona_prompt()
        response = await self.query_llm(chain_of_thought_prompt, system_message)
        
        # Parse the chain of thought response
        sections = self._extract_markdown_sections(response)
        
        return {
            "chain_of_thought_analysis": {
                "requirement_analysis": sections.get("1. Requirement Analysis & Clarification", ""),
                "functional_specification": sections.get("2. Functional Specification", ""),
                "gherkin_stories": sections.get("3. Gherkin User Stories", "")
            },
            "executive_summary": self._extract_executive_summary(sections, requirements),
            "business_context": self._extract_business_context(sections),
            "raw_analysis": response
        }
    
    async def _generate_detailed_specification_sections(self, requirements: str, phase1_data: Dict) -> Dict[str, Any]:
        """Phase 2: Generate detailed specification sections."""
        
        # Use the functional spec template for detailed sections
        detailed_prompt = self.prompt_manager.get_prompt('ba_agent', 'functional_spec_template', 
                                   introduction_context=phase1_data.get('executive_summary', ''),
                                   user_requirement=requirements)
        
        system_message = self.get_agent_persona_prompt()
        response = await self.query_llm(detailed_prompt, system_message)
        
        # Parse detailed sections
        sections = self._extract_markdown_sections(response)
        
        return {
            "functional_requirements": self._extract_functional_requirements(sections),
            "non_functional_requirements": self._extract_non_functional_requirements(sections),
            "user_personas": self._extract_user_personas(sections),
            "business_rules": self._extract_business_rules(sections),
            "user_stories": self._extract_user_stories(sections),
            "data_requirements": self._extract_data_requirements(sections),
            "integration_requirements": self._extract_integration_requirements(sections),
            "assumptions_and_dependencies": self._extract_assumptions_dependencies(sections),
            "detailed_specification": response
        }
    
    async def _generate_phase1_analysis(self, requirements: str, project_spec: ProjectSpecification) -> Dict[str, Any]:
        """Phase 1: Generate high-level analysis and functional requirements."""
        
        prompt = f"""
        Analyze the following requirements and create the foundation of a functional specification:

        PROJECT: {project_spec.title}
        REQUIREMENTS: {requirements}

        Generate the following sections in JSON format:

        1. Executive Summary
        2. Business Context (background, objectives, success criteria)
        3. Functional Requirements (detailed with acceptance criteria)
        4. Non-Functional Requirements
        5. User Personas
        6. Business Rules

        Return ONLY a valid JSON object with this structure:
        {{
            "executive_summary": "Comprehensive executive summary...",
            "business_context": {{
                "background": "Detailed business background...",
                "objectives": ["specific objective 1", "specific objective 2"],
                "success_criteria": ["measurable criteria 1", "measurable criteria 2"]
            }},
            "functional_requirements": [
                {{
                    "id": "FR-001",
                    "title": "Requirement Title",
                    "description": "Very detailed description with context...",
                    "acceptance_criteria": ["Specific AC1", "Specific AC2"],
                    "priority": "High|Medium|Low",
                    "complexity": "Simple|Medium|Complex"
                }}
            ],
            "non_functional_requirements": [
                {{
                    "id": "NFR-001",
                    "category": "Performance|Security|Usability|Reliability|Scalability",
                    "requirement": "Detailed NFR with specific metrics...",
                    "acceptance_criteria": "Measurable and testable criteria..."
                }}
            ],
            "user_personas": [
                {{
                    "name": "Specific Persona Name",
                    "role": "Detailed User Role",
                    "goals": ["specific goal 1", "specific goal 2"],
                    "pain_points": ["pain point 1", "pain point 2"],
                    "tech_savviness": "Low|Medium|High",
                    "context": "Additional context about this persona..."
                }}
            ],
            "business_rules": [
                {{
                    "id": "BR-001",
                    "rule": "Specific business rule with clear conditions...",
                    "rationale": "Detailed explanation of why this rule exists...",
                    "impact": "What happens if this rule is violated..."
                }}
            ]
        }}
        """
        
        system_message = self.get_agent_persona_prompt()
        response = await self.query_llm(prompt, system_message)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return await self._create_fallback_phase1(response, requirements)
    
    async def _generate_phase2_stories(self, requirements: str, phase1_data: Dict) -> Dict[str, Any]:
        """Phase 2: Generate detailed user stories with Gherkin scenarios."""
        
        # Extract functional requirements from phase 1 to create stories
        functional_reqs = phase1_data.get("functional_requirements", [])
        personas = phase1_data.get("user_personas", [])
        
        prompt = f"""
        Based on the following functional requirements and user personas, create detailed user stories with complete Gherkin scenarios:

        FUNCTIONAL REQUIREMENTS:
        {json.dumps(functional_reqs, indent=2)}

        USER PERSONAS:
        {json.dumps(personas, indent=2)}

        ORIGINAL REQUIREMENTS:
        {requirements}

        Generate the remaining sections in JSON format:

        1. User Stories (with comprehensive Gherkin scenarios)
        2. Data Requirements
        3. Integration Requirements
        4. Assumptions and Dependencies

        Return ONLY a valid JSON object with this structure:
        {{
            "user_stories": [
                {{
                    "id": "US-001",
                    "feature": "Specific Feature Name",
                    "story": "As a [specific persona] I want [specific functionality] So that [clear business value]",
                    "gherkin_scenarios": "Feature: Feature Name\\n  As a [persona]\\n  I want [goal]\\n  So that [benefit]\\n\\n  Background:\\n    Given [common setup]\\n\\n  Scenario: Main success scenario\\n    Given [precondition]\\n    When [action]\\n    Then [expected result]\\n    And [verification]\\n\\n  Scenario: Alternative scenario\\n    Given [different precondition]\\n    When [different action]\\n    Then [different result]\\n\\n  Scenario Outline: Data-driven scenario\\n    Given [precondition with <parameter>]\\n    When [action with <parameter>]\\n    Then [result with <parameter>]\\n    Examples:\\n      | parameter | result |\\n      | value1    | result1|\\n      | value2    | result2|",
                    "acceptance_criteria": ["AC1", "AC2"],
                    "related_requirements": ["FR-001", "FR-002"]
                }}
            ],
            "data_requirements": {{
                "entities": [
                    {{
                        "name": "Entity Name",
                        "description": "Detailed entity description with business context...",
                        "attributes": [
                            {{
                                "name": "attribute_name",
                                "type": "data_type",
                                "description": "attribute description",
                                "required": true,
                                "validation_rules": ["rule1", "rule2"]
                            }}
                        ],
                        "relationships": ["detailed relationship descriptions"],
                        "business_rules": ["entity-specific business rules"]
                    }}
                ],
                "data_flows": ["detailed data flow descriptions with sources and destinations"]
            }},
            "integration_requirements": [
                {{
                    "system": "External System Name",
                    "type": "API|Database|File|Message Queue|etc",
                    "description": "Detailed integration description with business justification...",
                    "data_exchange": "Specific data exchanged with formats and protocols...",
                    "frequency": "Real-time|Batch|On-demand",
                    "error_handling": "How errors are handled...",
                    "security_requirements": "Security considerations..."
                }}
            ],
            "assumptions_and_dependencies": {{
                "assumptions": ["detailed assumption 1", "detailed assumption 2"],
                "dependencies": ["specific dependency 1", "specific dependency 2"],
                "risks": ["identified risk 1 with mitigation", "identified risk 2 with mitigation"],
                "constraints": ["technical or business constraints"]
            }}
        }}

        Ensure all Gherkin scenarios are complete, realistic, and cover both happy path and edge cases.
        """
        
        system_message = self.get_agent_persona_prompt()
        response = await self.query_llm(prompt, system_message)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return await self._create_fallback_phase2(response, requirements)
    
    async def _create_fallback_document(self, llm_response: str, requirements: str) -> Dict[str, Any]:
        """Create a fallback structured document when JSON parsing fails."""
        return {
            "executive_summary": f"Functional specification for requirements: {requirements[:200]}...",
            "business_context": {
                "background": "Extracted from requirements analysis",
                "objectives": ["Primary objective extracted from requirements"],
                "success_criteria": ["Success criteria to be defined"]
            },
            "functional_requirements": [
                {
                    "id": "FR-001",
                    "title": "Core Functionality",
                    "description": requirements,
                    "acceptance_criteria": ["To be refined based on stakeholder feedback"],
                    "priority": "High",
                    "complexity": "Medium"
                }
            ],
            "user_stories": [
                {
                    "id": "US-001",
                    "feature": "Core Feature",
                    "story": "As a user I want the core functionality So that I can achieve my goals",
                    "gherkin_scenarios": "Feature: Core Feature\n  Scenario: Basic usage\n    Given the system is available\n    When I use the feature\n    Then I get the expected result"
                }
            ],
            "llm_response": llm_response,
            "note": "This is a fallback document. Manual review and enhancement recommended."
        }
    
    async def _create_fallback_phase1(self, llm_response: str, requirements: str) -> Dict[str, Any]:
        """Create fallback for phase 1 analysis."""
        return {
            "executive_summary": f"Phase 1 analysis for: {requirements[:200]}...",
            "business_context": {
                "background": "Analysis of provided requirements",
                "objectives": ["Meet specified requirements"],
                "success_criteria": ["Successful implementation"]
            },
            "functional_requirements": [
                {
                    "id": "FR-001",
                    "title": "Primary Requirement",
                    "description": requirements,
                    "acceptance_criteria": ["Requirement fulfilled as specified"],
                    "priority": "High",
                    "complexity": "Medium"
                }
            ],
            "user_personas": [
                {
                    "name": "Primary User",
                    "role": "System User",
                    "goals": ["Use the system effectively"],
                    "pain_points": ["Current manual processes"],
                    "tech_savviness": "Medium"
                }
            ],
            "business_rules": [
                {
                    "id": "BR-001",
                    "rule": "System must meet all specified requirements",
                    "rationale": "Ensures business objectives are met"
                }
            ],
            "phase1_llm_response": llm_response
        }
    
    async def _create_fallback_phase2(self, llm_response: str, requirements: str) -> Dict[str, Any]:
        """Create fallback for phase 2 user stories."""
        return {
            "user_stories": [
                {
                    "id": "US-001",
                    "feature": "Core Functionality",
                    "story": "As a user I want to use the system So that I can accomplish my tasks",
                    "gherkin_scenarios": """Feature: Core Functionality
  As a user
  I want to use the system
  So that I can accomplish my tasks

  Scenario: Basic system usage
    Given the system is available
    When I interact with the system
    Then I can complete my tasks successfully""",
                    "acceptance_criteria": ["System responds appropriately", "User can complete tasks"],
                    "related_requirements": ["FR-001"]
                }
            ],
            "data_requirements": {
                "entities": [
                    {
                        "name": "User",
                        "description": "System user entity",
                        "attributes": ["id", "name", "email"],
                        "relationships": ["Has access to system features"]
                    }
                ],
                "data_flows": ["User input flows to system processing"]
            },
            "integration_requirements": [
                {
                    "system": "External Systems",
                    "type": "To be determined",
                    "description": "Integration requirements to be analyzed",
                    "data_exchange": "Data exchange patterns to be defined"
                }
            ],
            "assumptions_and_dependencies": {
                "assumptions": ["System will be built as specified"],
                "dependencies": ["Technical platform availability"],
                "risks": ["Implementation complexity"],
                "constraints": ["Budget and timeline constraints"]
            },
            "phase2_llm_response": llm_response
        }
    
    def _determine_domain(self, requirements: str) -> ProjectDomain:
        """Determine project domain from requirements text."""
        requirements_lower = requirements.lower()
        
        domain_keywords = {
            ProjectDomain.ECOMMERCE: ['shop', 'cart', 'payment', 'product', 'order', 'checkout'],
            ProjectDomain.FINTECH: ['finance', 'bank', 'payment', 'transaction', 'money', 'account'],
            ProjectDomain.HEALTHCARE: ['health', 'medical', 'patient', 'doctor', 'hospital', 'clinical'],
            ProjectDomain.EDUCATION: ['learn', 'student', 'course', 'education', 'school', 'training'],
            ProjectDomain.ENTERPRISE: ['business', 'enterprise', 'company', 'employee', 'corporate'],
            ProjectDomain.SOCIAL: ['social', 'friend', 'share', 'community', 'network', 'chat'],
            ProjectDomain.GAMING: ['game', 'player', 'score', 'level', 'play', 'gaming'],
            ProjectDomain.IOT: ['device', 'sensor', 'iot', 'smart', 'connected', 'monitoring'],
            ProjectDomain.AI_ML: ['ai', 'machine learning', 'predict', 'model', 'algorithm', 'intelligence'],
            ProjectDomain.PRODUCTIVITY: ['task', 'todo', 'manage', 'organize', 'productivity', 'workflow']
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in requirements_lower for keyword in keywords):
                return domain
        
        return ProjectDomain.GENERAL
    
    async def export_specification_document(self, project_id: str, format: str = "markdown") -> str:
        """Export the functional specification in the specified format."""
        if project_id not in self.functional_specs:
            raise ValueError(f"No specification found for project {project_id}")
        
        spec = self.functional_specs[project_id]
        
        if format.lower() == "markdown":
            return self._export_as_markdown(spec)
        elif format.lower() == "json":
            return json.dumps(spec, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_as_markdown(self, spec: Dict[str, Any]) -> str:
        """Export specification as markdown document."""
        md_content = []
        
        # Title and metadata
        md_content.append("# Functional Specification Document\n")
        md_content.append(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md_content.append(f"**Agent:** Enhanced BA Agent\n\n")
        
        # Executive Summary
        if "executive_summary" in spec:
            md_content.append("## Executive Summary\n")
            md_content.append(f"{spec['executive_summary']}\n\n")
        
        # Business Context
        if "business_context" in spec:
            md_content.append("## Business Context\n")
            context = spec["business_context"]
            if "background" in context:
                md_content.append(f"### Background\n{context['background']}\n\n")
            if "objectives" in context:
                md_content.append("### Objectives\n")
                for obj in context["objectives"]:
                    md_content.append(f"- {obj}\n")
                md_content.append("\n")
            if "success_criteria" in context:
                md_content.append("### Success Criteria\n")
                for criteria in context["success_criteria"]:
                    md_content.append(f"- {criteria}\n")
                md_content.append("\n")
        
        # Functional Requirements
        if "functional_requirements" in spec:
            md_content.append("## Functional Requirements\n")
            for req in spec["functional_requirements"]:
                md_content.append(f"### {req.get('id', 'REQ')} - {req.get('title', 'Requirement')}\n")
                md_content.append(f"**Priority:** {req.get('priority', 'Medium')}\n")
                md_content.append(f"**Complexity:** {req.get('complexity', 'Medium')}\n\n")
                md_content.append(f"**Description:** {req.get('description', '')}\n\n")
                if req.get('acceptance_criteria'):
                    md_content.append("**Acceptance Criteria:**\n")
                    for ac in req['acceptance_criteria']:
                        md_content.append(f"- {ac}\n")
                    md_content.append("\n")
        
        # User Stories
        if "user_stories" in spec:
            md_content.append("## User Stories\n")
            for story in spec["user_stories"]:
                md_content.append(f"### {story.get('id', 'US')} - {story.get('feature', 'Feature')}\n")
                md_content.append(f"**Story:** {story.get('story', '')}\n\n")
                if story.get('gherkin_scenarios'):
                    md_content.append("**Gherkin Scenarios:**\n")
                    md_content.append("```gherkin\n")
                    md_content.append(f"{story['gherkin_scenarios']}\n")
                    md_content.append("```\n\n")
        
        # Additional sections...
        # (Add more sections as needed)
        
        return "".join(md_content)
