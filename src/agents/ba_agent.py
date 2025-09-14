import uuid
from typing import Dict, List, Optional, Any
import json

from .base_agent import BaseAgent
from ..models import (
    AgentType, Message, MessageType, Priority, ProjectSpecification,
    UserStory, TechnicalRequirement, ProjectDomain
)


class BAAgent(BaseAgent):
    """Business Analyst Agent responsible for requirement gathering and user story creation."""
    
    def __init__(self, agent_id: str = None, **kwargs):
        super().__init__(
            agent_id=agent_id or "ba_agent_001",
            agent_type=AgentType.BA,
            **kwargs
        )
        
        # BA-specific attributes
        self.current_projects: Dict[str, ProjectSpecification] = {}
        self.pending_clarifications: Dict[str, List[str]] = {}
        self.user_stories: Dict[str, List[UserStory]] = {}
    
    def get_agent_persona_prompt(self) -> str:
        """Get the BA agent persona prompt."""
        return """You are an expert Business Analyst (BA) Agent in an enterprise software development ecosystem.

Your responsibilities include:
1. Analyzing user specifications and understanding functional requirements
2. Asking clarifying questions to gather complete requirements
3. Creating detailed user stories with acceptance criteria using Gherkin syntax
4. Coordinating with Architecture Agent for technical feasibility
5. Reviewing architecture designs to ensure they meet business requirements
6. Assigning appropriate personas to Developer and QA agents
7. Facilitating communication between stakeholders and technical teams

You have deep expertise in:
- Requirements analysis and documentation
- Business process modeling
- User story creation with proper acceptance criteria
- Gherkin syntax for behavior-driven development
- Stakeholder management
- Domain-specific business knowledge across various industries

Always be thorough, ask clarifying questions when requirements are unclear, and ensure all business needs are properly captured and addressed."""
    
    async def process_message(self, message: Message):
        """Process incoming messages based on type."""
        try:
            if message.message_type == MessageType.SPECIFICATION:
                await self._analyze_specification(message)
            elif message.message_type == MessageType.RESPONSE:
                await self._process_response(message)
            elif message.message_type == MessageType.ARTIFACT:
                await self._review_artifact(message)
            elif message.message_type == MessageType.QUERY:
                await self._handle_query(message)
            else:
                self.logger.warning(f"Unhandled message type: {message.message_type}")
        
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            await self.send_error_message(message, str(e))
    
    async def _analyze_specification(self, message: Message):
        """Analyze user specification and extract requirements."""
        try:
            # Parse the project specification
            project_spec = ProjectSpecification(
                id=message.project_id,
                title=f"Project from {message.project_id}",
                description=message.content,
                domain=self._determine_domain(message.content),
                requirements=[],
                constraints=[]
            )
            
            self.current_projects[message.project_id] = project_spec
            
            # Analyze the specification using LLM
            analysis_prompt = f"""
            Analyze the following project specification and extract:
            1. Functional requirements
            2. Non-functional requirements (if mentioned)
            3. Business constraints
            4. Any ambiguities or missing information that need clarification
            5. The primary business domain this project belongs to
            
            Project Specification:
            {message.content}
            
            Provide your analysis in JSON format with the following structure:
            {{
                "functional_requirements": ["req1", "req2", ...],
                "non_functional_requirements": ["nfr1", "nfr2", ...],
                "constraints": ["constraint1", "constraint2", ...],
                "clarifications_needed": ["question1", "question2", ...],
                "domain": "identified_domain",
                "complexity_assessment": "low|medium|high",
                "estimated_timeline": "estimated_duration"
            }}
            """
            
            system_message = self.get_agent_persona_prompt()
            analysis_result = await self.query_llm(analysis_prompt, system_message)
            
            # Parse the analysis result
            try:
                analysis_data = json.loads(analysis_result)
            except json.JSONDecodeError:
                # If LLM doesn't return valid JSON, extract information manually
                analysis_data = await self._extract_analysis_manually(analysis_result)
            
            # Update project specification
            project_spec.requirements = analysis_data.get("functional_requirements", [])
            project_spec.constraints = analysis_data.get("constraints", [])
            
            # Check if clarifications are needed
            clarifications = analysis_data.get("clarifications_needed", [])
            if clarifications:
                self.pending_clarifications[message.project_id] = clarifications
                await self._request_clarifications(message, clarifications)
            else:
                # Proceed to architect agent
                await self._send_to_architect(message, project_spec, analysis_data)
            
        except Exception as e:
            self.logger.error(f"Error analyzing specification: {str(e)}")
            raise
    
    async def _request_clarifications(self, original_message: Message, clarifications: List[str]):
        """Request clarifications from the user via orchestrator."""
        clarification_text = "I need some clarifications to better understand your requirements:\n\n"
        for i, question in enumerate(clarifications, 1):
            clarification_text += f"{i}. {question}\n"
        
        await self.send_message(
            to_agent=AgentType.ORCHESTRATOR,
            message_type=MessageType.QUERY,
            content=clarification_text,
            project_id=original_message.project_id,
            metadata={"awaiting_clarification": True, "original_message_id": original_message.id}
        )
    
    async def _send_to_architect(self, original_message: Message, project_spec: ProjectSpecification, analysis_data: Dict):
        """Send analyzed requirements to the Architect Agent."""
        architect_brief = f"""
        Project Analysis Complete. Please proceed with architecture design.
        
        Project: {project_spec.title}
        Domain: {project_spec.domain.value}
        
        Functional Requirements:
        {chr(10).join(f"- {req}" for req in project_spec.requirements)}
        
        Constraints:
        {chr(10).join(f"- {constraint}" for constraint in project_spec.constraints)}
        
        Complexity Assessment: {analysis_data.get('complexity_assessment', 'medium')}
        Estimated Timeline: {analysis_data.get('estimated_timeline', 'to be determined')}
        
        Please provide:
        1. Detailed technical architecture
        2. Technology stack recommendations
        3. System design with sequence diagrams
        4. Data model design
        5. API specifications (if applicable)
        6. Non-functional requirements specifications
        """
        
        await self.send_message(
            to_agent=AgentType.ARCHITECT,
            message_type=MessageType.SPECIFICATION,
            content=architect_brief,
            project_id=original_message.project_id,
            metadata={
                "analysis_data": analysis_data,
                "project_spec": project_spec.dict()
            }
        )
    
    async def _review_artifact(self, message: Message):
        """Review artifacts from Architect Agent."""
        try:
            # Parse the architecture artifact
            artifact_data = message.metadata.get("artifact_data", {})
            
            review_prompt = f"""
            Review the following architecture design and determine if it addresses all business requirements.
            
            Original Requirements:
            {self.current_projects.get(message.project_id, {}).requirements}
            
            Architecture Design:
            {message.content}
            
            Please provide:
            1. Approval status (APPROVED/NEEDS_REVISION)
            2. Any missing requirements or concerns
            3. Recommendations for improvement
            4. Confirmation that all business needs are addressed
            
            Format your response as JSON:
            {{
                "status": "APPROVED|NEEDS_REVISION",
                "concerns": ["concern1", "concern2", ...],
                "missing_requirements": ["missing1", "missing2", ...],
                "recommendations": ["rec1", "rec2", ...],
                "ready_for_development": true/false
            }}
            """
            
            system_message = self.get_agent_persona_prompt()
            review_result = await self.query_llm(review_prompt, system_message)
            
            try:
                review_data = json.loads(review_result)
            except json.JSONDecodeError:
                review_data = {"status": "NEEDS_REVISION", "concerns": ["Unable to parse review"], "ready_for_development": False}
            
            if review_data.get("status") == "APPROVED" and review_data.get("ready_for_development"):
                # Create user stories and proceed to development
                await self._create_user_stories(message)
            else:
                # Send feedback to architect
                await self._send_architecture_feedback(message, review_data)
            
        except Exception as e:
            self.logger.error(f"Error reviewing artifact: {str(e)}")
            raise
    
    async def _create_user_stories(self, message: Message):
        """Create detailed user stories from approved architecture."""
        try:
            project_spec = self.current_projects.get(message.project_id)
            if not project_spec:
                raise ValueError(f"Project specification not found for {message.project_id}")
            
            story_creation_prompt = f"""
            Create detailed user stories for the approved architecture design.
            
            Project Requirements:
            {chr(10).join(f"- {req}" for req in project_spec.requirements)}
            
            Architecture Design:
            {message.content}
            
            For each user story, provide:
            1. Title
            2. Description (As a [user], I want [goal] so that [benefit])
            3. Acceptance criteria
            4. Gherkin scenarios (Given, When, Then)
            5. Priority (High/Medium/Low)
            6. Story points estimate (1-13 Fibonacci scale)
            7. Dependencies on other stories
            
            Format as JSON array:
            [
                {{
                    "title": "Story Title",
                    "description": "As a [user], I want [goal] so that [benefit]",
                    "acceptance_criteria": ["criteria1", "criteria2"],
                    "gherkin_scenarios": ["Scenario 1: Given... When... Then...", "Scenario 2: ..."],
                    "priority": "High|Medium|Low",
                    "story_points": 5,
                    "dependencies": ["story_id1", "story_id2"],
                    "tags": ["frontend", "backend", "api"]
                }}
            ]
            """
            
            system_message = self.get_agent_persona_prompt()
            stories_result = await self.query_llm(story_creation_prompt, system_message)
            
            try:
                stories_data = json.loads(stories_result)
            except json.JSONDecodeError:
                # Fallback: create basic stories manually
                stories_data = await self._create_basic_stories(project_spec)
            
            # Create UserStory objects
            user_stories = []
            for story_data in stories_data:
                story = UserStory(
                    id=str(uuid.uuid4()),
                    title=story_data.get("title", "Generated Story"),
                    description=story_data.get("description", ""),
                    acceptance_criteria=story_data.get("acceptance_criteria", []),
                    gherkin_scenarios=story_data.get("gherkin_scenarios", []),
                    priority=Priority(story_data.get("priority", "medium").lower()),
                    story_points=story_data.get("story_points", 5),
                    dependencies=story_data.get("dependencies", []),
                    tags=story_data.get("tags", [])
                )
                user_stories.append(story)
            
            self.user_stories[message.project_id] = user_stories
            
            # Assign personas and send to Developer and QA agents
            await self._assign_personas_and_dispatch(message, user_stories)
            
        except Exception as e:
            self.logger.error(f"Error creating user stories: {str(e)}")
            raise
    
    async def _assign_personas_and_dispatch(self, message: Message, user_stories: List[UserStory]):
        """Assign appropriate personas to Developer and QA agents and dispatch work."""
        try:
            project_spec = self.current_projects.get(message.project_id)
            
            # Determine required developer persona based on technology stack
            persona_assignment_prompt = f"""
            Based on the project requirements and user stories, determine the appropriate developer persona.
            
            Project Domain: {project_spec.domain.value if project_spec else 'general'}
            User Stories Tags: {set(tag for story in user_stories for tag in story.tags)}
            
            Determine:
            1. Required technology expertise (frontend, backend, fullstack, devops)
            2. Specific technologies/frameworks needed
            3. Experience level required (junior, mid, senior)
            4. Specialization area
            
            Respond in JSON format:
            {{
                "expertise": ["React", "Node.js", "PostgreSQL", ...],
                "experience_level": "senior",
                "specialization": "fullstack",
                "persona_description": "Senior Full-Stack Developer with React/Node.js expertise"
            }}
            """
            
            system_message = self.get_agent_persona_prompt()
            persona_result = await self.query_llm(persona_assignment_prompt, system_message)
            
            try:
                persona_data = json.loads(persona_result)
            except json.JSONDecodeError:
                persona_data = {
                    "expertise": ["Python", "JavaScript"],
                    "experience_level": "senior",
                    "specialization": "fullstack",
                    "persona_description": "Senior Full-Stack Developer"
                }
            
            # Send user stories to Developer Agent
            developer_brief = f"""
            Project Assignment: {project_spec.title if project_spec else 'Development Project'}
            
            Assigned Persona: {persona_data['persona_description']}
            Required Expertise: {', '.join(persona_data['expertise'])}
            Experience Level: {persona_data['experience_level']}
            
            User Stories:
            {self._format_user_stories_for_agent(user_stories)}
            
            Please:
            1. Review all user stories and architecture design
            2. Ask any technical clarification questions
            3. Develop the application according to specifications
            4. Create unit tests for all components
            5. Set up the development environment
            6. Test the application end-to-end
            """
            
            await self.send_message(
                to_agent=AgentType.DEVELOPER,
                message_type=MessageType.SPECIFICATION,
                content=developer_brief,
                project_id=message.project_id,
                metadata={
                    "persona_data": persona_data,
                    "user_stories": [story.dict() for story in user_stories]
                }
            )
            
            # Send user stories to QA Agent
            qa_brief = f"""
            Project Testing Assignment: {project_spec.title if project_spec else 'Testing Project'}
            
            User Stories for Testing:
            {self._format_user_stories_for_agent(user_stories)}
            
            Please:
            1. Review all user stories and acceptance criteria
            2. Create comprehensive test cases based on Gherkin scenarios
            3. Prepare test data and test environment setup
            4. Ask any clarification questions about testing requirements
            5. Coordinate with Developer Agent for testing activities
            """
            
            await self.send_message(
                to_agent=AgentType.TESTER,
                message_type=MessageType.SPECIFICATION,
                content=qa_brief,
                project_id=message.project_id,
                metadata={
                    "user_stories": [story.dict() for story in user_stories]
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error assigning personas and dispatching: {str(e)}")
            raise
    
    def _format_user_stories_for_agent(self, user_stories: List[UserStory]) -> str:
        """Format user stories for sending to other agents."""
        formatted_stories = []
        for i, story in enumerate(user_stories, 1):
            formatted_story = f"""
Story {i}: {story.title}
Description: {story.description}
Priority: {story.priority.value}
Story Points: {story.story_points}

Acceptance Criteria:
{chr(10).join(f"- {criteria}" for criteria in story.acceptance_criteria)}

Gherkin Scenarios:
{chr(10).join(f"- {scenario}" for scenario in story.gherkin_scenarios)}

Tags: {', '.join(story.tags)}
"""
            formatted_stories.append(formatted_story)
        
        return "\n" + "="*50 + "\n".join(formatted_stories)
    
    def _determine_domain(self, specification: str) -> ProjectDomain:
        """Determine the project domain based on specification content."""
        spec_lower = specification.lower()
        
        if any(keyword in spec_lower for keyword in ["bank", "finance", "payment", "trading", "insurance"]):
            return ProjectDomain.FINANCIAL
        elif any(keyword in spec_lower for keyword in ["manufactur", "factory", "production", "supply chain"]):
            return ProjectDomain.MANUFACTURING
        elif any(keyword in spec_lower for keyword in ["health", "medical", "hospital", "patient"]):
            return ProjectDomain.HEALTHCARE
        elif any(keyword in spec_lower for keyword in ["ecommerce", "shop", "retail", "product", "cart"]):
            return ProjectDomain.ECOMMERCE
        elif any(keyword in spec_lower for keyword in ["education", "school", "student", "course", "learning"]):
            return ProjectDomain.EDUCATION
        elif any(keyword in spec_lower for keyword in ["logistics", "shipping", "delivery", "transport"]):
            return ProjectDomain.LOGISTICS
        else:
            return ProjectDomain.GENERAL
    
    async def _extract_analysis_manually(self, analysis_result: str) -> Dict[str, Any]:
        """Extract analysis information when LLM doesn't return valid JSON."""
        return {
            "functional_requirements": ["Extracted from free text"],
            "non_functional_requirements": [],
            "constraints": [],
            "clarifications_needed": [],
            "domain": "general",
            "complexity_assessment": "medium",
            "estimated_timeline": "to be determined"
        }
    
    async def _create_basic_stories(self, project_spec: ProjectSpecification) -> List[Dict[str, Any]]:
        """Create basic user stories when LLM output parsing fails."""
        return [
            {
                "title": "Basic User Story",
                "description": f"As a user, I want to use the {project_spec.title} system",
                "acceptance_criteria": ["System should be functional"],
                "gherkin_scenarios": ["Given the system is running, When I access it, Then it should respond"],
                "priority": "medium",
                "story_points": 5,
                "dependencies": [],
                "tags": ["general"]
            }
        ]
    
    async def _send_architecture_feedback(self, message: Message, review_data: Dict):
        """Send feedback to architect for design revisions."""
        feedback_content = f"""
        Architecture Review Feedback
        
        Status: {review_data.get('status', 'NEEDS_REVISION')}
        
        Concerns:
        {chr(10).join(f"- {concern}" for concern in review_data.get('concerns', []))}
        
        Missing Requirements:
        {chr(10).join(f"- {missing}" for missing in review_data.get('missing_requirements', []))}
        
        Recommendations:
        {chr(10).join(f"- {rec}" for rec in review_data.get('recommendations', []))}
        
        Please address these issues and provide a revised architecture design.
        """
        
        await self.send_message(
            to_agent=AgentType.ARCHITECT,
            message_type=MessageType.QUERY,
            content=feedback_content,
            project_id=message.project_id,
            metadata={"review_data": review_data, "revision_requested": True}
        )
    
    async def _process_response(self, message: Message):
        """Process responses from user or other agents."""
        # Handle clarification responses from user
        if message.project_id in self.pending_clarifications:
            project_spec = self.current_projects.get(message.project_id)
            if project_spec:
                # Update requirements based on clarifications
                clarification_prompt = f"""
                Based on the user's clarification response, update the project requirements.
                
                Original Requirements: {project_spec.requirements}
                User Response: {message.content}
                
                Provide updated requirements in JSON format:
                {{
                    "updated_requirements": ["req1", "req2", ...],
                    "additional_constraints": ["constraint1", ...],
                    "ready_for_architect": true/false
                }}
                """
                
                system_message = self.get_agent_persona_prompt()
                update_result = await self.query_llm(clarification_prompt, system_message)
                
                try:
                    update_data = json.loads(update_result)
                    project_spec.requirements = update_data.get("updated_requirements", project_spec.requirements)
                    project_spec.constraints.extend(update_data.get("additional_constraints", []))
                    
                    if update_data.get("ready_for_architect", True):
                        # Clear pending clarifications and proceed to architect
                        del self.pending_clarifications[message.project_id]
                        await self._send_to_architect(message, project_spec, {"complexity_assessment": "medium"})
                    
                except json.JSONDecodeError:
                    self.logger.warning("Failed to parse clarification update, proceeding with original requirements")
                    await self._send_to_architect(message, project_spec, {"complexity_assessment": "medium"})
    
    async def _handle_query(self, message: Message):
        """Handle queries from other agents."""
        # This could be questions from Developer or QA agents about requirements
        query_response_prompt = f"""
        Answer the following question about the project requirements:
        
        Question: {message.content}
        Project Requirements: {self.current_projects.get(message.project_id, {}).requirements if message.project_id in self.current_projects else 'No project found'}
        
        Provide a clear and detailed response.
        """
        
        system_message = self.get_agent_persona_prompt()
        response = await self.query_llm(query_response_prompt, system_message)
        
        await self.send_message(
            to_agent=message.from_agent,
            message_type=MessageType.RESPONSE,
            content=response,
            project_id=message.project_id,
            metadata={"query_response": True, "original_query_id": message.id}
        )
