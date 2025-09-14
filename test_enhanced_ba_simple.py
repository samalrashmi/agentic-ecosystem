#!/usr/bin/env python3
"""
Test script for the Enhanced BA Agent with Chain of Thought prompts
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_enhanced_ba_agent():
    """Test the Enhanced BA Agent with the new prompt system."""
    try:
        from agents.enhanced_ba_agent import EnhancedBAAgent
        
        print('🧪 Testing Enhanced BA Agent with Chain of Thought')
        print('=' * 60)
        
        # Create BA agent instance
        ba_agent = EnhancedBAAgent()
        print('✓ Enhanced BA Agent created successfully')
        
        # Simple test requirement
        test_requirement = '''Create a user authentication system for a web application that allows users to register, login, and manage their profiles. The system should support email verification, password reset, and role-based access control.'''
        
        # Generate specification
        result = await ba_agent.generate_standalone_specification(
            requirements=test_requirement,
            project_title='User Authentication System'
        )
        
        print('✓ Specification generated successfully')
        print(f'  - Project ID: {result["project_id"][:8]}...')
        print(f'  - Token count: {result["token_count"]:,}')
        
        spec = result['specification']
        print(f'  - Has executive summary: {"executive_summary" in spec}')
        print(f'  - Functional requirements: {len(spec.get("functional_requirements", []))}')
        print(f'  - User stories: {len(spec.get("user_stories", []))}')
        
        print('\n🎉 Enhanced BA Agent test completed successfully!')
        
    except Exception as e:
        print(f'✗ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enhanced_ba_agent())
