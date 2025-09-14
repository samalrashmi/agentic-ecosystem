import uuid
import json
from typing import Dict, List, Optional, Any

from .base_agent import BaseAgent
from ..models import (
    AgentType, Message, MessageType, Priority, ProjectSpecification,
    ArchitectureDesign, TechnicalRequirement, ProjectDomain
)


class ArchitectAgent(BaseAgent):
    """Architecture Agent responsible for system design and technical specifications."""
    
    def __init__(self, agent_id: str = None, **kwargs):
        super().__init__(
            agent_id=agent_id or "architect_agent_001",
            agent_type=AgentType.ARCHITECT,
            **kwargs
        )
        
        # Architecture-specific attributes
        self.architecture_designs: Dict[str, ArchitectureDesign] = {}
        self.domain_tech_stacks = self._initialize_domain_tech_stacks()
        self.architecture_patterns = self._initialize_architecture_patterns()
    
    def get_agent_persona_prompt(self) -> str:
        """Get the Architecture agent persona prompt."""
        return """You are an expert Software Architect Agent in an enterprise software development ecosystem.

Your responsibilities include:
1. Designing scalable and maintainable software architectures
2. Selecting appropriate technology stacks based on project domain and requirements
3. Creating detailed system designs with sequence diagrams
4. Defining data models and API specifications
5. Establishing non-functional requirements (NFRs)
6. Ensuring industry-standard architecture patterns are followed
7. Recommending open-source technologies with no licensing restrictions

You have deep expertise in:
- Enterprise architecture patterns (microservices, event-driven, layered, etc.)
- Domain-specific technology stacks (Financial, Manufacturing, Healthcare, etc.)
- System design and scalability principles
- Database design (SQL and NoSQL)
- API design and OpenAPI specifications
- Non-functional requirements (performance, security, reliability)
- Cloud-native architectures
- DevOps and deployment strategies

Always recommend open-source, free-to-use technologies. Consider scalability, maintainability, security, and performance in all designs. Follow industry best practices for the specific domain."""
    
    def _initialize_domain_tech_stacks(self) -> Dict[ProjectDomain, Dict[str, List[str]]]:
        """Initialize recommended technology stacks for different domains."""
        return {
            ProjectDomain.FINANCIAL: {
                "backend": ["Java Spring Boot", "Python Django", "Node.js Express"],
                "frontend": ["React", "Angular", "Vue.js"],
                "database": ["PostgreSQL", "MongoDB", "Redis"],
                "messaging": ["Apache Kafka", "RabbitMQ", "Apache Pulsar"],
                "security": ["OAuth 2.0", "JWT", "Spring Security"],
                "monitoring": ["Prometheus", "Grafana", "ELK Stack"],
                "deployment": ["Docker", "Kubernetes", "Jenkins"]
            },
            ProjectDomain.MANUFACTURING: {
                "backend": ["Python Django", "Java Spring Boot", "C# .NET Core"],
                "frontend": ["React", "Angular", "Vue.js"],
                "database": ["PostgreSQL", "TimescaleDB", "InfluxDB"],
                "iot": ["MQTT", "Apache IoT", "Node-RED"],
                "analytics": ["Apache Spark", "Pandas", "Apache Airflow"],
                "monitoring": ["Prometheus", "Grafana", "Elasticsearch"],
                "deployment": ["Docker", "Kubernetes", "GitLab CI"]
            },
            ProjectDomain.HEALTHCARE: {
                "backend": ["Python Django", "Java Spring Boot", "Node.js"],
                "frontend": ["React", "Angular", "Vue.js"],
                "database": ["PostgreSQL", "MongoDB", "Neo4j"],
                "security": ["HIPAA Compliance", "Encryption", "Audit Logging"],
                "integration": ["HL7 FHIR", "DICOM", "REST APIs"],
                "monitoring": ["Prometheus", "Grafana", "ELK Stack"],
                "deployment": ["Docker", "Kubernetes", "Terraform"]
            },
            ProjectDomain.ECOMMERCE: {
                "backend": ["Node.js Express", "Python Django", "Java Spring Boot"],
                "frontend": ["React", "Next.js", "Vue.js"],
                "database": ["PostgreSQL", "MongoDB", "Redis"],
                "search": ["Elasticsearch", "Apache Solr", "Algolia"],
                "payments": ["Stripe", "PayPal", "Square"],
                "cdn": ["Cloudflare", "AWS CloudFront", "KeyCDN"],
                "deployment": ["Docker", "Kubernetes", "Vercel"]
            },
            ProjectDomain.EDUCATION: {
                "backend": ["Python Django", "Node.js Express", "Ruby on Rails"],
                "frontend": ["React", "Vue.js", "Angular"],
                "database": ["PostgreSQL", "MongoDB", "SQLite"],
                "lms": ["Moodle", "Open edX", "Canvas"],
                "video": ["Jitsi Meet", "BigBlueButton", "WebRTC"],
                "collaboration": ["Matrix", "Rocket.Chat", "Discourse"],
                "deployment": ["Docker", "Kubernetes", "Heroku"]
            },
            ProjectDomain.LOGISTICS: {
                "backend": ["Java Spring Boot", "Python Django", "Go"],
                "frontend": ["React", "Angular", "Vue.js"],
                "database": ["PostgreSQL", "MongoDB", "Redis"],
                "mapping": ["OpenStreetMap", "Leaflet", "PostGIS"],
                "optimization": ["OR-Tools", "OptaPlanner", "SUMO"],
                "tracking": ["GPS APIs", "WebSockets", "Real-time DBs"],
                "deployment": ["Docker", "Kubernetes", "AWS ECS"]
            },
            ProjectDomain.GENERAL: {
                "backend": ["Python FastAPI", "Node.js Express", "Java Spring Boot"],
                "frontend": ["React", "Vue.js", "Angular"],
                "database": ["PostgreSQL", "MongoDB", "SQLite"],
                "api": ["REST", "GraphQL", "OpenAPI"],
                "testing": ["Jest", "PyTest", "JUnit"],
                "monitoring": ["Prometheus", "Grafana", "Loki"],
                "deployment": ["Docker", "Docker Compose", "GitHub Actions"]
            }
        }
    
    def _initialize_architecture_patterns(self) -> Dict[str, Dict[str, str]]:
        """Initialize architecture patterns for different use cases."""
        return {
            "microservices": {
                "description": "Distributed architecture with independently deployable services",
                "use_case": "Large, complex applications with multiple teams",
                "benefits": "Scalability, technology diversity, fault isolation",
                "challenges": "Network complexity, data consistency, operational overhead"
            },
            "monolithic": {
                "description": "Single deployable unit containing all functionality",
                "use_case": "Small to medium applications, rapid prototyping",
                "benefits": "Simple deployment, easy debugging, strong consistency",
                "challenges": "Scaling limitations, technology lock-in"
            },
            "layered": {
                "description": "Organized into horizontal layers (presentation, business, data)",
                "use_case": "Traditional enterprise applications",
                "benefits": "Clear separation of concerns, well understood",
                "challenges": "Can become monolithic, performance bottlenecks"
            },
            "event_driven": {
                "description": "Components communicate through events",
                "use_case": "Real-time processing, IoT, financial trading",
                "benefits": "Loose coupling, scalability, real-time processing",
                "challenges": "Event ordering, debugging complexity"
            },
            "hexagonal": {
                "description": "Domain-centric with adapters for external concerns",
                "use_case": "Domain-rich applications, testing-focused",
                "benefits": "Testability, technology independence",
                "challenges": "Initial complexity, over-engineering risk"
            }
        }
    
    async def process_message(self, message: Message):
        """Process incoming messages based on type."""
        try:
            if message.message_type == MessageType.SPECIFICATION:
                await self._design_architecture(message)
            elif message.message_type == MessageType.QUERY:
                await self._handle_revision_request(message)
            elif message.message_type == MessageType.RESPONSE:
                await self._process_feedback(message)
            else:
                self.logger.warning(f"Unhandled message type: {message.message_type}")
        
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            await self.send_error_message(message, str(e))
    
    async def _design_architecture(self, message: Message):
        """Design system architecture based on requirements."""
        try:
            # Parse project requirements from message
            metadata = message.metadata
            analysis_data = metadata.get("analysis_data", {})
            project_spec_data = metadata.get("project_spec", {})
            
            # Determine project domain
            domain = ProjectDomain(project_spec_data.get("domain", "general"))
            requirements = project_spec_data.get("requirements", [])
            constraints = project_spec_data.get("constraints", [])
            
            # Design architecture using LLM
            architecture_prompt = f"""
            Design a comprehensive software architecture for the following project:
            
            Domain: {domain.value}
            Requirements: {chr(10).join(f"- {req}" for req in requirements)}
            Constraints: {chr(10).join(f"- {constraint}" for constraint in constraints)}
            Complexity: {analysis_data.get('complexity_assessment', 'medium')}
            
            Provide a detailed architecture design including:
            
            1. SYSTEM OVERVIEW
            - High-level architecture description
            - Key components and their responsibilities
            - Communication patterns between components
            
            2. TECHNOLOGY STACK
            - Backend framework and language
            - Frontend framework
            - Database(s) selection and justification
            - Additional technologies (caching, messaging, etc.)
            
            3. ARCHITECTURE PATTERNS
            - Primary architectural pattern (microservices, monolithic, etc.)
            - Justification for pattern selection
            - How the pattern addresses the requirements
            
            4. SEQUENCE DIAGRAMS
            - Key user workflows as sequence diagrams (in PlantUML format)
            - System interaction flows
            
            5. DATA MODEL
            - Database schema design
            - Entity relationships
            - Data flow patterns
            
            6. API SPECIFICATIONS
            - REST API endpoints (if applicable)
            - Request/response examples
            - Authentication and authorization approach
            
            7. NON-FUNCTIONAL REQUIREMENTS
            - Performance requirements
            - Security requirements
            - Scalability considerations
            - Reliability and availability
            
            8. DEPLOYMENT STRATEGY
            - Containerization approach
            - CI/CD pipeline recommendations
            - Environment setup
            
            Use only open-source, free technologies. Follow industry best practices for {domain.value} domain.
            
            Format your response in JSON:
            {{
                "system_overview": "...",
                "tech_stack": {{
                    "backend": "...",
                    "frontend": "...",
                    "database": "...",
                    "additional": ["..."]
                }},
                "architecture_patterns": ["pattern1", "pattern2"],
                "sequence_diagrams": ["PlantUML diagram 1", "PlantUML diagram 2"],
                "data_models": {{
                    "entities": [{{ "name": "User", "attributes": ["id", "name"], "relationships": ["has_many orders"] }}],
                    "database_schema": "SQL DDL or JSON schema"
                }},
                "api_specifications": {{
                    "endpoints": [{{ "method": "GET", "path": "/api/users", "description": "..." }}],
                    "authentication": "JWT tokens",
                    "examples": {{"request": {{}}, "response": {{}}}}
                }},
                "nfr_specifications": [
                    {{ "category": "Performance", "requirement": "API response time < 200ms", "priority": "high" }},
                    {{ "category": "Security", "requirement": "Data encryption at rest", "priority": "high" }}
                ],
                "deployment_strategy": {{
                    "containerization": "Docker",
                    "orchestration": "Kubernetes",
                    "ci_cd": "GitHub Actions"
                }}
            }}
            """
            
            system_message = self.get_agent_persona_prompt()
            architecture_result = await self.query_llm(architecture_prompt, system_message)
            
            try:
                architecture_data = json.loads(architecture_result)
            except json.JSONDecodeError:
                # Fallback to manual extraction
                architecture_data = await self._create_fallback_architecture(domain, requirements)
            
            # Create ArchitectureDesign object
            tech_stack = architecture_data.get("tech_stack", {})
            nfr_specs = []
            for nfr in architecture_data.get("nfr_specifications", []):
                nfr_req = TechnicalRequirement(
                    id=str(uuid.uuid4()),
                    name=nfr.get("category", "General"),
                    description=nfr.get("requirement", ""),
                    category=nfr.get("category", "NFR"),
                    priority=Priority(nfr.get("priority", "medium").lower())
                )
                nfr_specs.append(nfr_req)
            
            architecture_design = ArchitectureDesign(
                id=str(uuid.uuid4()),
                project_id=message.project_id,
                system_overview=architecture_data.get("system_overview", ""),
                tech_stack=tech_stack,
                architecture_patterns=architecture_data.get("architecture_patterns", []),
                sequence_diagrams=architecture_data.get("sequence_diagrams", []),
                data_models=architecture_data.get("data_models", {}),
                api_specifications=architecture_data.get("api_specifications", {}),
                nfr_specifications=nfr_specs
            )
            
            self.architecture_designs[message.project_id] = architecture_design
            
            # Create detailed documentation
            documentation = await self._create_architecture_documentation(architecture_design, architecture_data)
            
            # Send architecture to BA agent for review
            await self.send_message(
                to_agent=AgentType.BA,
                message_type=MessageType.ARTIFACT,
                content=documentation,
                project_id=message.project_id,
                metadata={
                    "artifact_type": "architecture_design",
                    "artifact_data": architecture_data,
                    "architecture_id": architecture_design.id
                }
            )
            
            # Create architecture artifact
            await self.create_artifact(
                project_id=message.project_id,
                artifact_type="architecture_design",
                name="System Architecture Design",
                content=documentation
            )
            
        except Exception as e:
            self.logger.error(f"Error designing architecture: {str(e)}")
            raise
    
    async def _create_architecture_documentation(self, design: ArchitectureDesign, raw_data: Dict) -> str:
        """Create comprehensive architecture documentation."""
        doc = f"""# System Architecture Design
        
## Project Overview
{design.system_overview}

## Technology Stack

### Backend
- **Framework**: {design.tech_stack.get('backend', 'Not specified')}
- **Language**: {self._extract_language_from_framework(design.tech_stack.get('backend', ''))}

### Frontend
- **Framework**: {design.tech_stack.get('frontend', 'Not specified')}

### Database
- **Primary**: {design.tech_stack.get('database', 'Not specified')}

### Additional Technologies
{chr(10).join(f"- {tech}" for tech in design.tech_stack.get('additional', []))}

## Architecture Patterns
{chr(10).join(f"- {pattern}" for pattern in design.architecture_patterns)}

## System Components

### Data Model
```json
{json.dumps(design.data_models, indent=2)}
```

### API Specifications
{json.dumps(design.api_specifications, indent=2)}

## Non-Functional Requirements

{chr(10).join(f"### {nfr.name} ({nfr.priority.value} priority){chr(10)}{nfr.description}{chr(10)}" for nfr in design.nfr_specifications)}

## Sequence Diagrams

{chr(10).join(f"### Workflow {i+1}{chr(10)}```plantuml{chr(10)}{diagram}{chr(10)}```{chr(10)}" for i, diagram in enumerate(design.sequence_diagrams))}

## Deployment Strategy
{json.dumps(raw_data.get('deployment_strategy', {}), indent=2)}

## Implementation Recommendations

1. **Phase 1: Core Infrastructure**
   - Set up development environment
   - Implement basic authentication
   - Create database schema

2. **Phase 2: Core Features**
   - Implement main business logic
   - Create API endpoints
   - Develop frontend components

3. **Phase 3: Advanced Features**
   - Add advanced functionality
   - Implement optimization
   - Add monitoring and logging

4. **Phase 4: Production Readiness**
   - Security hardening
   - Performance optimization
   - Deployment automation

---
*Generated by Architecture Agent on {design.created_at.isoformat()}*
"""
        return doc
    
    def _extract_language_from_framework(self, framework: str) -> str:
        """Extract programming language from framework name."""
        framework_lower = framework.lower()
        if any(keyword in framework_lower for keyword in ["spring", "java"]):
            return "Java"
        elif any(keyword in framework_lower for keyword in ["django", "fastapi", "flask", "python"]):
            return "Python"
        elif any(keyword in framework_lower for keyword in ["express", "node", "nest"]):
            return "JavaScript/TypeScript"
        elif any(keyword in framework_lower for keyword in ["rails", "ruby"]):
            return "Ruby"
        elif any(keyword in framework_lower for keyword in ["laravel", "php"]):
            return "PHP"
        elif any(keyword in framework_lower for keyword in [".net", "core"]):
            return "C#"
        elif "go" in framework_lower:
            return "Go"
        else:
            return "Not specified"
    
    async def _create_fallback_architecture(self, domain: ProjectDomain, requirements: List[str]) -> Dict[str, Any]:
        """Create a fallback architecture when LLM parsing fails."""
        tech_stack = self.domain_tech_stacks.get(domain, self.domain_tech_stacks[ProjectDomain.GENERAL])
        
        return {
            "system_overview": f"A {domain.value} application built with modern, scalable architecture",
            "tech_stack": {
                "backend": tech_stack["backend"][0],
                "frontend": tech_stack["frontend"][0],
                "database": tech_stack["database"][0],
                "additional": tech_stack.get("monitoring", ["Prometheus", "Grafana"])
            },
            "architecture_patterns": ["layered", "rest_api"],
            "sequence_diagrams": [
                "@startuml\nUser -> Frontend: Request\nFrontend -> Backend: API Call\nBackend -> Database: Query\nDatabase -> Backend: Data\nBackend -> Frontend: Response\nFrontend -> User: Display\n@enduml"
            ],
            "data_models": {
                "entities": [{"name": "User", "attributes": ["id", "name", "email"]}],
                "database_schema": "CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(100), email VARCHAR(100));"
            },
            "api_specifications": {
                "endpoints": [{"method": "GET", "path": "/api/users", "description": "Get all users"}],
                "authentication": "JWT tokens"
            },
            "nfr_specifications": [
                {"category": "Performance", "requirement": "API response time < 500ms", "priority": "medium"},
                {"category": "Security", "requirement": "HTTPS encryption", "priority": "high"}
            ],
            "deployment_strategy": {
                "containerization": "Docker",
                "orchestration": "Docker Compose",
                "ci_cd": "GitHub Actions"
            }
        }
    
    async def _handle_revision_request(self, message: Message):
        """Handle architecture revision requests from BA agent."""
        try:
            revision_data = message.metadata.get("review_data", {})
            concerns = revision_data.get("concerns", [])
            missing_requirements = revision_data.get("missing_requirements", [])
            recommendations = revision_data.get("recommendations", [])
            
            # Get original architecture
            original_design = self.architecture_designs.get(message.project_id)
            if not original_design:
                raise ValueError(f"No architecture design found for project {message.project_id}")
            
            # Create revision prompt
            revision_prompt = f"""
            Revise the architecture design based on the following feedback:
            
            Original Architecture:
            {original_design.system_overview}
            Tech Stack: {original_design.tech_stack}
            
            Feedback to Address:
            
            Concerns:
            {chr(10).join(f"- {concern}" for concern in concerns)}
            
            Missing Requirements:
            {chr(10).join(f"- {missing}" for missing in missing_requirements)}
            
            Recommendations:
            {chr(10).join(f"- {rec}" for rec in recommendations)}
            
            Provide a revised architecture that addresses all the feedback points.
            Keep the same JSON format as before but with improvements and additions.
            """
            
            system_message = self.get_agent_persona_prompt()
            revision_result = await self.query_llm(revision_prompt, system_message)
            
            try:
                revised_data = json.loads(revision_result)
            except json.JSONDecodeError:
                # If parsing fails, create incremental improvements
                revised_data = await self._create_incremental_revision(original_design, concerns, missing_requirements)
            
            # Update architecture design
            updated_design = await self._update_architecture_design(original_design, revised_data)
            self.architecture_designs[message.project_id] = updated_design
            
            # Create updated documentation
            updated_documentation = await self._create_architecture_documentation(updated_design, revised_data)
            
            # Send revised architecture back to BA agent
            await self.send_message(
                to_agent=AgentType.BA,
                message_type=MessageType.ARTIFACT,
                content=updated_documentation,
                project_id=message.project_id,
                metadata={
                    "artifact_type": "architecture_design_revision",
                    "artifact_data": revised_data,
                    "architecture_id": updated_design.id,
                    "revision_number": 2
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error handling revision request: {str(e)}")
            raise
    
    async def _update_architecture_design(self, original: ArchitectureDesign, revised_data: Dict) -> ArchitectureDesign:
        """Update architecture design with revised data."""
        # Create new NFR specifications
        nfr_specs = []
        for nfr in revised_data.get("nfr_specifications", []):
            nfr_req = TechnicalRequirement(
                id=str(uuid.uuid4()),
                name=nfr.get("category", "General"),
                description=nfr.get("requirement", ""),
                category=nfr.get("category", "NFR"),
                priority=Priority(nfr.get("priority", "medium").lower())
            )
            nfr_specs.append(nfr_req)
        
        # Create updated design
        updated_design = ArchitectureDesign(
            id=str(uuid.uuid4()),
            project_id=original.project_id,
            system_overview=revised_data.get("system_overview", original.system_overview),
            tech_stack=revised_data.get("tech_stack", original.tech_stack),
            architecture_patterns=revised_data.get("architecture_patterns", original.architecture_patterns),
            sequence_diagrams=revised_data.get("sequence_diagrams", original.sequence_diagrams),
            data_models=revised_data.get("data_models", original.data_models),
            api_specifications=revised_data.get("api_specifications", original.api_specifications),
            nfr_specifications=nfr_specs
        )
        
        return updated_design
    
    async def _create_incremental_revision(self, original: ArchitectureDesign, concerns: List[str], missing_reqs: List[str]) -> Dict[str, Any]:
        """Create incremental revisions when LLM parsing fails."""
        # Basic fallback revision
        revised_data = {
            "system_overview": f"{original.system_overview}\n\nRevised to address concerns: {'; '.join(concerns[:3])}",
            "tech_stack": original.tech_stack,
            "architecture_patterns": original.architecture_patterns,
            "sequence_diagrams": original.sequence_diagrams,
            "data_models": original.data_models,
            "api_specifications": original.api_specifications,
            "nfr_specifications": [
                {"category": "Performance", "requirement": "Enhanced performance monitoring", "priority": "high"},
                {"category": "Security", "requirement": "Additional security measures", "priority": "high"}
            ],
            "deployment_strategy": {
                "containerization": "Docker",
                "orchestration": "Kubernetes", 
                "ci_cd": "GitHub Actions"
            }
        }
        
        return revised_data
    
    async def _process_feedback(self, message: Message):
        """Process feedback from other agents."""
        # Handle responses and feedback from BA or other agents
        feedback_prompt = f"""
        Process the following feedback about the architecture:
        
        Feedback: {message.content}
        
        Determine if any architectural changes are needed and respond appropriately.
        """
        
        system_message = self.get_agent_persona_prompt()
        response = await self.query_llm(feedback_prompt, system_message)
        
        # Send acknowledgment
        await self.send_message(
            to_agent=message.from_agent,
            message_type=MessageType.RESPONSE,
            content=f"Architecture feedback processed: {response}",
            project_id=message.project_id,
            metadata={"feedback_processed": True}
        )
