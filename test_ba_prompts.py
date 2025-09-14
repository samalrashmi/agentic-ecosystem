#!/usr/bin/env python3
"""
Direct test of the Enhanced BA Agent functionality without complex imports
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_ba_prompt_system():
    """Test the BA prompt system directly."""
    try:
        from prompts.utils import PromptManager
        
        print('🧪 Testing BA Prompt System')
        print('=' * 50)
        
        # Initialize prompt manager
        manager = PromptManager()
        
        # Test persona formatting
        formatted_persona = manager.get_prompt('ba_agent', 'persona',
            project_title='User Authentication System',
            additional_context='Web application with role-based access'
        )
        
        print('✓ Formatted persona successfully')
        print(f'  - Formatted length: {len(formatted_persona)} characters')
        
        # Test CoT formatting
        formatted_cot = manager.get_prompt('ba_agent', 'chain_of_thought',
            user_requirement='Create authentication system with login, registration, and password reset',
            project_title='User Auth System'
        )
        
        print('✓ Formatted Chain of Thought successfully')
        print(f'  - Formatted length: {len(formatted_cot)} characters')
        
        # Show first 200 characters of CoT
        print('\n📋 Chain of Thought Preview:')
        print('-' * 40)
        print(formatted_cot[:200] + '...')
        
        print('\n🎉 BA Prompt System test completed successfully!')
        return True
        
    except Exception as e:
        print(f'✗ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ba_prompt_system())
    sys.exit(0 if success else 1)
