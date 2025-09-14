from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class AgentType(str, Enum):
    BA = "ba"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    TESTER = "tester"
    ORCHESTRATOR = "orchestrator"


class MessageType(str, Enum):
    SPECIFICATION = "specification"
    QUERY = "query"
    RESPONSE = "response"
    APPROVAL = "approval"
    ARTIFACT = "artifact"
    ERROR = "error"
    STATUS = "status"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProjectDomain(str, Enum):
    FINANCIAL = "financial"
    MANUFACTURING = "manufacturing"
    HEALTHCARE = "healthcare"
    ECOMMERCE = "ecommerce"
    EDUCATION = "education"
    LOGISTICS = "logistics"
    GENERAL = "general"


class Message(BaseModel):
    id: str = Field(..., description="Unique message identifier")
    from_agent: AgentType = Field(..., description="Source agent")
    to_agent: AgentType = Field(..., description="Target agent")
    message_type: MessageType = Field(..., description="Type of message")
    content: str = Field(..., description="Message content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.now)
    project_id: str = Field(..., description="Associated project ID")
    priority: Priority = Field(default=Priority.MEDIUM)


class ProjectSpecification(BaseModel):
    id: str = Field(..., description="Project unique identifier")
    title: str = Field(..., description="Project title")
    description: str = Field(..., description="Detailed project description")
    domain: ProjectDomain = Field(..., description="Project domain")
    requirements: List[str] = Field(default_factory=list, description="Functional requirements")
    constraints: List[str] = Field(default_factory=list, description="Project constraints")
    deadline: Optional[datetime] = Field(None, description="Project deadline")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class TechnicalRequirement(BaseModel):
    id: str
    name: str
    description: str
    category: str  # NFR, Functional, Technical
    priority: Priority
    acceptance_criteria: List[str] = Field(default_factory=list)


class ArchitectureDesign(BaseModel):
    id: str
    project_id: str
    system_overview: str
    tech_stack: Dict[str, str]  # component: technology
    architecture_patterns: List[str]
    sequence_diagrams: List[str]  # URLs or base64 encoded diagrams
    data_models: Dict[str, Any]  # JSON or SQL schemas
    api_specifications: Optional[Dict[str, Any]] = None  # OpenAPI specs
    nfr_specifications: List[TechnicalRequirement] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class UserStory(BaseModel):
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    gherkin_scenarios: List[str]
    priority: Priority
    story_points: Optional[int] = None
    dependencies: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class TestCase(BaseModel):
    id: str
    user_story_id: str
    title: str
    description: str
    test_type: str  # unit, integration, e2e, performance
    gherkin_scenario: str
    expected_result: str
    test_data: Optional[Dict[str, Any]] = None
    automation_script: Optional[str] = None


class DeveloperPersona(BaseModel):
    id: str
    name: str
    expertise: List[str]  # technologies/frameworks
    experience_level: str  # junior, mid, senior
    specialization: str  # frontend, backend, fullstack, devops


class ProjectArtifact(BaseModel):
    id: str
    project_id: str
    artifact_type: str  # code, documentation, test_results, diagrams
    name: str
    content: str
    file_path: Optional[str] = None
    created_by: AgentType
    created_at: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"


class ProjectStatus(BaseModel):
    project_id: str
    current_phase: str
    completion_percentage: float
    active_agents: List[AgentType]
    last_updated: datetime = Field(default_factory=datetime.now)
    issues: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)


class AgentState(BaseModel):
    agent_id: str
    agent_type: AgentType
    status: str  # idle, working, waiting, error
    current_task: Optional[str] = None
    assigned_projects: List[str] = Field(default_factory=list)
    last_activity: datetime = Field(default_factory=datetime.now)
    persona: Optional[DeveloperPersona] = None  # Only for developer agents
