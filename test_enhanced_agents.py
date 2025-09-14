#!/usr/bin/env python3
"""Test script for enhanced LLM-powered agents."""

import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from langgraph_agents.agent_tools import (
    analyze_business_requirements,
    design_system_architecture,
    generate_implementation_plan,
    create_test_strategy
)

def test_calculator_project():
    """Test the complete workflow with a calculator project."""
    print("🧪 Testing enhanced agents with calculator project...")
    
    # Step 1: Business Requirements Analysis
    print("\n1️⃣ Analyzing business requirements...")
    requirements = analyze_business_requirements.invoke({
        "specification": "Create a simple calculator app that can perform basic arithmetic operations like addition, subtraction, multiplication, and division. It should have a clean interface and be easy to use.",
        "project_id": "test_calc_001"
    })
    print(f"✅ Requirements analyzed - {len(requirements.get('functional_requirements', []))} functional requirements found")
    
    # Step 2: System Architecture Design  
    print("\n2️⃣ Designing system architecture...")
    architecture = design_system_architecture.invoke({
        "user_stories": str(requirements),
        "project_id": "test_calc_001",
        "requirements": ""
    })
    print(f"✅ Architecture designed - Technology: {architecture.get('technology_used', 'Unknown')}")
    
    # Step 3: Implementation Planning
    print("\n3️⃣ Generating implementation plan...")
    plan = generate_implementation_plan.invoke({
        "architecture": str(architecture),
        "project_id": "test_calc_001"
    })
    print(f"✅ Implementation plan created - {len(plan.get('implementation_phases', []))} phases planned")
    
    # Step 4: Test Strategy Creation
    print("\n4️⃣ Creating test strategy...")
    test_strategy = create_test_strategy.invoke({
        "implementation_plan": str(plan),
        "project_id": "test_calc_001"
    })
    print(f"✅ Test strategy created - {len(test_strategy.get('test_categories', []))} test categories defined")
    
    # Print summary
    print("\n📊 WORKFLOW SUMMARY:")
    print(f"   • Technology Selected: {architecture.get('technology_used', 'N/A')}")
    print(f"   • Implementation Phases: {len(plan.get('implementation_phases', []))}")
    print(f"   • Test Categories: {len(test_strategy.get('test_categories', []))}")
    print(f"   • Quality Score: {test_strategy.get('quality_score', 'N/A')}")
    
    # Check if we have LLM-generated content vs fallbacks
    has_llm_content = (
        isinstance(architecture.get('technology_rationale'), str) and 
        len(architecture.get('technology_rationale', '')) > 100
    )
    
    if has_llm_content:
        print("   • ✅ LLM-powered responses detected")
    else:
        print("   • ⚠️  Using fallback responses (check API key)")
    
    return {
        "requirements": requirements,
        "architecture": architecture, 
        "plan": plan,
        "test_strategy": test_strategy
    }

if __name__ == "__main__":
    try:
        results = test_calculator_project()
        print("\n🎉 All agents tested successfully!")
        
        # Check for errors
        errors = []
        for step_name, step_result in results.items():
            if "error" in step_result:
                errors.append(f"{step_name}: {step_result['error']}")
        
        if errors:
            print(f"\n❌ Found {len(errors)} errors:")
            for error in errors:
                print(f"   • {error}")
        else:
            print("✅ No errors found - all agents working properly!")
            
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)
