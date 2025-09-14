#!/usr/bin/env python3
"""
Test script for the enhanced prompt management system
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.prompt_manager import (
    PromptManager, 
    get_prompt_manager, 
    get_prompt, 
    get_persona, 
    get_chain_of_thought,
    list_available_prompts
)
import logging

logging.basicConfig(level=logging.INFO)

def test_prompt_system():
    """Test the prompt management system."""
    print("🧪 Testing Enhanced Prompt Management System")
    print("=" * 50)
    
    # Get prompt manager instance
    pm = get_prompt_manager()
    
    # List available prompts
    print("\n📚 Available Prompts:")
    prompts = pm.list_available_prompts()
    for agent, prompt_list in prompts.items():
        print(f"  {agent}:")
        for prompt_name in prompt_list:
            metadata = pm.get_prompt_metadata(agent, prompt_name)
            if metadata:
                print(f"    - {prompt_name} (v{metadata.version}) - {metadata.description}")
            else:
                print(f"    - {prompt_name}")
    
    # Test BA agent persona
    print("\n🎭 Testing BA Agent Persona:")
    persona = pm.get_persona('ba_agent')
    print(f"Length: {len(persona)} characters")
    print(f"Preview: {persona[:100]}...")
    
    # Test chain of thought with parameters
    print("\n🧠 Testing Chain of Thought:")
    requirement = "Create a simple task management system for small teams"
    cot_prompt = pm.get_chain_of_thought('ba_agent', user_requirement=requirement)
    print(f"Length: {len(cot_prompt)} characters")
    print(f"Preview: {cot_prompt[:200]}...")
    
    # Test parameter validation
    print("\n✅ Testing Parameter Validation:")
    try:
        # This should work
        pm.get_prompt('ba_agent', 'functional_spec_template', user_requirement="test")
        print("✓ Valid parameters accepted")
    except Exception as e:
        print(f"✗ Error with valid parameters: {e}")
    
    try:
        # This should fail (missing required parameter)
        pm.get_prompt('ba_agent', 'functional_spec_template')
        print("✗ Missing parameter validation failed")
    except Exception as e:
        print(f"✓ Missing parameter correctly caught: {e}")
    
    # Test caching
    print("\n⚡ Testing Caching:")
    import time
    
    start_time = time.time()
    pm.get_prompt('ba_agent', 'persona')
    first_call = time.time() - start_time
    
    start_time = time.time()
    pm.get_prompt('ba_agent', 'persona')
    second_call = time.time() - start_time
    
    print(f"First call: {first_call:.4f}s")
    print(f"Second call (cached): {second_call:.4f}s")
    print(f"Cache speedup: {first_call/second_call:.1f}x")
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    test_prompt_system()
