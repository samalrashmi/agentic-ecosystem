"""
Test Script for LangGraph Multi-Agent Workflow

This script tests the new LangGraph-based implementation
to ensure it works properly before replacing the old system.
"""

import asyncio
import json
from pathlib import Path

from src.langgraph_agents.workflow import run_software_development_workflow

def test_langgraph_workflow():
    """Test the LangGraph workflow with a sample specification."""
    
    print("🧪 Testing LangGraph Multi-Agent Workflow")
    print("=" * 50)
    
    # Sample specification similar to what was working before
    test_specification = """
    Create a text extraction application that extracts and analyzes information from user-provided text.
    
    Key Requirements:
    - Text Extraction Engine for data extraction
    - Text Analysis Engine for processing extracted data  
    - User Management Service for user operations
    - Frontend UI for user interaction
    - RESTful APIs for component communication
    - Centralized database for data persistence
    
    The system should be scalable, secure, and provide real-time text analysis capabilities.
    """
    
    try:
        # Run the workflow
        print("🚀 Starting LangGraph workflow...")
        result = run_software_development_workflow(test_specification)
        
        print("\n📋 Workflow Results:")
        print(f"Project ID: {result.get('project_id', 'N/A')}")
        print(f"Status: {result.get('status', 'N/A')}")
        print(f"Current Phase: {result.get('current_phase', 'N/A')}")
        print(f"Errors: {len(result.get('errors', []))}")
        
        # Check artifacts
        artifacts = {
            "Business Analysis": result.get('business_analysis') is not None,
            "System Architecture": result.get('system_architecture') is not None,
            "Implementation Plan": result.get('implementation_plan') is not None,
            "Test Strategy": result.get('test_strategy') is not None
        }
        
        print("\n📁 Generated Artifacts:")
        for artifact, generated in artifacts.items():
            status = "✅" if generated else "❌"
            print(f"  {status} {artifact}")
        
        # Show some details if available
        if result.get('business_analysis'):
            ba = result['business_analysis']
            user_stories = ba.get('user_stories', [])
            print(f"\n👤 User Stories Generated: {len(user_stories)}")
            for story in user_stories[:2]:  # Show first 2
                print(f"  - {story.get('title', 'Untitled')}")
        
        if result.get('system_architecture'):
            arch = result['system_architecture']
            components = arch.get('components', [])
            print(f"\n🏗️ System Components: {len(components)}")
            for comp in components[:3]:  # Show first 3
                print(f"  - {comp.get('name', 'Unnamed')}: {comp.get('responsibility', 'No description')}")
        
        # Check if files were saved
        project_id = result.get('project_id')
        if project_id:
            project_dir = Path(__file__).parent / "out" / f"project_{project_id}"
            if project_dir.exists():
                files = list(project_dir.glob("*"))
                print(f"\n📂 Files Saved: {len(files)}")
                for file in files:
                    print(f"  - {file.name}")
        
        if result.get('errors'):
            print("\n⚠️ Errors encountered:")
            for error in result['errors']:
                print(f"  - {error}")
        
        print("\n" + "=" * 50)
        
        if result.get('status') == 'completed':
            print("✅ LangGraph workflow test PASSED!")
            return True
        else:
            print("❌ LangGraph workflow test FAILED!")
            return False
            
    except Exception as e:
        print(f"💥 Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_langgraph_workflow()
    exit(0 if success else 1)
