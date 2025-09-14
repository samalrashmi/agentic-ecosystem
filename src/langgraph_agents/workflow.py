"""
LangGraph Multi-Agent Workflow for Software Development

This module implements a state machine-based multi-agent workflow using LangGraph
for coordinating business analysis, architecture design, development, and testing.

Based on LangChain best practices and the Agent-Experiments repository:
https://github.com/kabir12345/Agent-Experiments
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, TypedDict, Annotated
from pathlib import Path

from langchain import hub
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages

from dotenv import load_dotenv

from .agent_tools import (
    analyze_business_requirements,
    design_system_architecture,
    generate_implementation_plan,
    create_test_strategy
)

# Load environment variables
load_dotenv()

# Define the state structure for the workflow
class ProjectState(TypedDict):
    """State structure for the software development workflow."""
    project_id: str
    original_specification: str
    current_phase: str
    business_analysis: Optional[Dict[str, Any]]
    system_architecture: Optional[Dict[str, Any]]
    implementation_plan: Optional[Dict[str, Any]]
    test_strategy: Optional[Dict[str, Any]]
    messages: Annotated[List[Dict[str, Any]], add_messages]
    errors: List[str]
    status: str  # "in_progress", "completed", "failed"

class SoftwareDevelopmentWorkflow:
    """
    LangGraph-based multi-agent workflow for software development.
    
    This workflow coordinates multiple specialized agents:
    - Business Analyst: Analyzes requirements and creates user stories
    - System Architect: Designs system architecture
    - Developer: Creates implementation plans
    - Tester: Develops testing strategies
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name=os.getenv("OPENAI_MODEL", "gpt-4"),
            temperature=0.7
        )
        
        # Create memory saver for checkpointing
        self.memory = MemorySaver()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow state machine."""
        
        # Create the state graph
        workflow = StateGraph(ProjectState)
        
        # Add nodes for each agent/phase
        workflow.add_node("business_analysis", self._business_analysis_node)
        workflow.add_node("architecture_design", self._architecture_design_node)
        workflow.add_node("implementation_planning", self._implementation_planning_node)
        workflow.add_node("test_strategy_creation", self._test_strategy_node)
        workflow.add_node("completion", self._completion_node)
        
        # Define the workflow edges
        workflow.add_edge(START, "business_analysis")
        workflow.add_edge("business_analysis", "architecture_design")
        workflow.add_edge("architecture_design", "implementation_planning")
        workflow.add_edge("implementation_planning", "test_strategy_creation")
        workflow.add_edge("test_strategy_creation", "completion")
        workflow.add_edge("completion", END)
        
        # Compile the workflow with checkpointing
        return workflow.compile(checkpointer=self.memory)
    
    def _business_analysis_node(self, state: ProjectState) -> ProjectState:
        """Business Analysis phase - analyze requirements and create user stories."""
        try:
            print(f"🔍 Starting Business Analysis for project {state['project_id']}")
            
            # Call the business analysis tool
            result = analyze_business_requirements.invoke({
                "specification": state["original_specification"],
                "project_id": state["project_id"]
            })
            
            # Update state
            state["business_analysis"] = result
            state["current_phase"] = "business_analysis_completed"
            state["messages"].append({
                "role": "assistant",
                "content": f"Business analysis completed. Generated {len(result.get('user_stories', []))} user stories.",
                "timestamp": datetime.now().isoformat()
            })
            
            print(f"✅ Business Analysis completed with {len(result.get('user_stories', []))} user stories")
            
            # Call phase completion callback if provided
            if hasattr(self, 'phase_callback') and self.phase_callback:
                self.phase_callback("business_analysis")
            
        except Exception as e:
            error_msg = f"Business analysis failed: {str(e)}"
            state["errors"].append(error_msg)
            state["status"] = "failed"
            print(f"❌ {error_msg}")
            
        return state
    
    def _architecture_design_node(self, state: ProjectState) -> ProjectState:
        """Architecture Design phase - design system architecture."""
        try:
            print(f"🏗️ Starting Architecture Design for project {state['project_id']}")
            
            # Prepare user stories data for architect
            user_stories_json = json.dumps(state.get("business_analysis", {}))
            
            # Call the architecture design tool
            result = design_system_architecture.invoke({
                "user_stories": user_stories_json,
                "project_id": state["project_id"],
                "requirements": state["original_specification"]
            })
            
            # Update state
            state["system_architecture"] = result
            state["current_phase"] = "architecture_design_completed"
            state["messages"].append({
                "role": "assistant",
                "content": f"System architecture designed with {len(result.get('components', []))} components.",
                "timestamp": datetime.now().isoformat()
            })
            
            print(f"✅ Architecture Design completed with {len(result.get('components', []))} components")
            
            # Call phase completion callback if provided
            if hasattr(self, 'phase_callback') and self.phase_callback:
                self.phase_callback("architecture")
            
        except Exception as e:
            error_msg = f"Architecture design failed: {str(e)}"
            state["errors"].append(error_msg)
            state["status"] = "failed"
            print(f"❌ {error_msg}")
            
        return state
    
    def _implementation_planning_node(self, state: ProjectState) -> ProjectState:
        """Implementation Planning phase - create development plan."""
        try:
            print(f"💻 Starting Implementation Planning for project {state['project_id']}")
            
            # Prepare architecture data for developer
            architecture_json = json.dumps(state.get("system_architecture", {}))
            
            # Call the implementation planning tool
            result = generate_implementation_plan.invoke({
                "architecture": architecture_json,
                "project_id": state["project_id"]
            })
            
            # Update state
            state["implementation_plan"] = result
            state["current_phase"] = "implementation_planning_completed"
            state["messages"].append({
                "role": "assistant",
                "content": f"Implementation plan created with {len(result.get('implementation_phases', []))} phases.",
                "timestamp": datetime.now().isoformat()
            })
            
            print(f"✅ Implementation Planning completed with {len(result.get('implementation_phases', []))} phases")
            
            # Call phase completion callback if provided
            if hasattr(self, 'phase_callback') and self.phase_callback:
                self.phase_callback("implementation")
            
        except Exception as e:
            error_msg = f"Implementation planning failed: {str(e)}"
            state["errors"].append(error_msg)
            state["status"] = "failed"
            print(f"❌ {error_msg}")
            
        return state
    
    def _test_strategy_node(self, state: ProjectState) -> ProjectState:
        """Test Strategy phase - create testing strategy."""
        try:
            print(f"🧪 Starting Test Strategy Creation for project {state['project_id']}")
            
            # Prepare implementation plan data for tester
            implementation_json = json.dumps(state.get("implementation_plan", {}))
            
            # Call the test strategy tool
            result = create_test_strategy.invoke({
                "implementation_plan": implementation_json,
                "project_id": state["project_id"]
            })
            
            # Update state
            state["test_strategy"] = result
            state["current_phase"] = "test_strategy_completed"
            state["messages"].append({
                "role": "assistant",
                "content": f"Test strategy created with {len(result.get('test_cases', []))} test cases.",
                "timestamp": datetime.now().isoformat()
            })
            
            print(f"✅ Test Strategy completed with {len(result.get('test_cases', []))} test cases")
            
            # Call phase completion callback if provided
            if hasattr(self, 'phase_callback') and self.phase_callback:
                self.phase_callback("testing")
            
        except Exception as e:
            error_msg = f"Test strategy creation failed: {str(e)}"
            state["errors"].append(error_msg)
            state["status"] = "failed"
            print(f"❌ {error_msg}")
            
        return state
    
    def _completion_node(self, state: ProjectState) -> ProjectState:
        """Completion phase - finalize the project."""
        print(f"🎉 Completing project {state['project_id']}")
        
        state["current_phase"] = "completed"
        state["status"] = "completed" if not state["errors"] else "completed_with_errors"
        state["messages"].append({
            "role": "assistant",
            "content": "Software development workflow completed successfully!",
            "timestamp": datetime.now().isoformat()
        })
        
        # Generate summary report
        self._generate_summary_report(state)
        
        print(f"✅ Project {state['project_id']} completed!")
        return state
    
    def _generate_summary_report(self, state: ProjectState) -> None:
        """Generate a comprehensive summary report."""
        try:
            report = {
                "project_id": state["project_id"],
                "specification": state["original_specification"],
                "status": state["status"],
                "completed_at": datetime.now().isoformat(),
                "phases_completed": state["current_phase"],
                "artifacts_generated": {
                    "business_analysis": state.get("business_analysis") is not None,
                    "system_architecture": state.get("system_architecture") is not None,
                    "implementation_plan": state.get("implementation_plan") is not None,
                    "test_strategy": state.get("test_strategy") is not None
                },
                "errors": state["errors"],
                "summary": {
                    "user_stories_count": len(state.get("business_analysis", {}).get("user_stories", [])),
                    "components_count": len(state.get("system_architecture", {}).get("components", [])),
                    "implementation_phases": len(state.get("implementation_plan", {}).get("implementation_phases", [])),
                    "test_cases_count": len(state.get("test_strategy", {}).get("test_cases", []))
                }
            }
            
            # Save summary report
            base_dir = Path(__file__).parent.parent.parent / "out" / f"project_{state['project_id']}"
            base_dir.mkdir(parents=True, exist_ok=True)
            
            with open(base_dir / "project_summary.json", 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
                
            # Generate markdown summary
            md_content = self._generate_markdown_summary(report)
            with open(base_dir / "project_summary.md", 'w', encoding='utf-8') as f:
                f.write(md_content)
                
        except Exception as e:
            print(f"Error generating summary report: {e}")
    
    def _generate_markdown_summary(self, report: Dict[str, Any]) -> str:
        """Generate markdown summary report."""
        md = f"""# Project Summary

**Project ID:** {report['project_id']}
**Status:** {report['status']}
**Completed:** {report['completed_at']}

## Original Specification
{report['specification']}

## Artifacts Generated
- **Business Analysis:** {'✅' if report['artifacts_generated']['business_analysis'] else '❌'}
- **System Architecture:** {'✅' if report['artifacts_generated']['system_architecture'] else '❌'}
- **Implementation Plan:** {'✅' if report['artifacts_generated']['implementation_plan'] else '❌'}
- **Test Strategy:** {'✅' if report['artifacts_generated']['test_strategy'] else '❌'}

## Summary Statistics
- **User Stories:** {report['summary']['user_stories_count']}
- **System Components:** {report['summary']['components_count']}
- **Implementation Phases:** {report['summary']['implementation_phases']}
- **Test Cases:** {report['summary']['test_cases_count']}

"""
        
        if report['errors']:
            md += "## Errors Encountered\n"
            for error in report['errors']:
                md += f"- {error}\n"
            md += "\n"
        
        md += "---\n*Generated by LangGraph Multi-Agent Workflow*\n"
        
        return md
    
    async def arun_project(self, specification: str, project_id: Optional[str] = None, phase_callback=None) -> Dict[str, Any]:
        """
        Async version - Run the complete software development workflow.
        
        Args:
            specification: The business specification/requirements
            project_id: Optional project ID (will generate if not provided)
            phase_callback: Optional callback function called when each phase completes
            
        Returns:
            Dictionary containing the final project state
        """
        if not project_id:
            project_id = str(uuid.uuid4())
        
        # Store callback for use in nodes
        self.phase_callback = phase_callback
        
        print(f"🚀 Starting software development workflow for project: {project_id}")
        print(f"📝 Specification: {specification[:100]}...")
        
        # Initialize state
        initial_state = ProjectState(
            project_id=project_id,
            original_specification=specification,
            current_phase="initiated",
            business_analysis=None,
            system_architecture=None,
            implementation_plan=None,
            test_strategy=None,
            messages=[{
                "role": "system",
                "content": "Starting software development workflow",
                "timestamp": datetime.now().isoformat()
            }],
            errors=[],
            status="in_progress"
        )
        
        # Run the workflow with proper configuration
        try:
            config = {
                "configurable": {
                    "thread_id": project_id,
                    "checkpoint_ns": "software_development",
                    "checkpoint_id": str(uuid.uuid4())
                },
                "recursion_limit": 10
            }
            final_state = await self.workflow.ainvoke(initial_state, config=config)
            
            print(f"🎯 Workflow completed for project {project_id}")
            return final_state
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            print(f"💥 {error_msg}")
            initial_state["errors"].append(error_msg)
            initial_state["status"] = "failed"
            return initial_state

    def run_project(self, specification: str, project_id: Optional[str] = None, phase_callback=None) -> Dict[str, Any]:
        """
        Run the complete software development workflow.
        
        Args:
            specification: The business specification/requirements
            project_id: Optional project ID (will generate if not provided)
            phase_callback: Optional callback function called when each phase completes
            
        Returns:
            Dictionary containing the final project state
        """
        if not project_id:
            project_id = str(uuid.uuid4())
        
        # Store callback for use in nodes
        self.phase_callback = phase_callback
        
        print(f"🚀 Starting software development workflow for project: {project_id}")
        print(f"📝 Specification: {specification[:100]}...")
        
        # Initialize state
        initial_state = ProjectState(
            project_id=project_id,
            original_specification=specification,
            current_phase="initiated",
            business_analysis=None,
            system_architecture=None,
            implementation_plan=None,
            test_strategy=None,
            messages=[{
                "role": "system",
                "content": "Starting software development workflow",
                "timestamp": datetime.now().isoformat()
            }],
            errors=[],
            status="in_progress"
        )
        
        # Run the workflow
        try:
            config = {"configurable": {"thread_id": project_id}}
            final_state = self.workflow.invoke(initial_state, config=config)
            
            print(f"🎯 Workflow completed for project {project_id}")
            return final_state
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            print(f"💥 {error_msg}")
            initial_state["errors"].append(error_msg)
            initial_state["status"] = "failed"
            return initial_state

# Create a global instance for easy access
workflow_instance = SoftwareDevelopmentWorkflow()

def run_software_development_workflow(specification: str, project_id: Optional[str] = None, phase_callback=None) -> Dict[str, Any]:
    """
    Convenience function to run the software development workflow.
    
    Args:
        specification: Business requirements specification
        project_id: Optional project identifier
        phase_callback: Optional callback function called when each phase completes
        
    Returns:
        Final project state dictionary
    """
    return workflow_instance.run_project(specification, project_id, phase_callback)

# Export main functions
__all__ = [
    'SoftwareDevelopmentWorkflow',
    'ProjectState',
    'run_software_development_workflow',
    'workflow_instance'
]
