#!/usr/bin/env python3
"""
Simplified Enhanced BA Agent for testing without complex dependencies
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

class SimplifiedEnhancedBAAgent:
    """Simplified version of Enhanced BA Agent for testing."""
    
    def __init__(self):
        """Initialize the BA Agent with prompt manager."""
        from prompts.utils import PromptManager
        
        self.prompt_manager = PromptManager()
        self.agent_name = "ba_agent"
        
        # Try to import tiktoken for token counting
        try:
            import tiktoken
            self.encoding = tiktoken.get_encoding("cl100k_base")
            self.has_tiktoken = True
        except ImportError:
            print("Warning: tiktoken not available, using character-based estimation")
            self.has_tiktoken = False
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.has_tiktoken:
            return len(self.encoding.encode(text))
        else:
            # Rough estimation: ~4 characters per token
            return len(text) // 4
    
    async def generate_standalone_specification(
        self, 
        requirements: str, 
        project_title: str = "Software Project",
        additional_context: str = ""
    ) -> Dict[str, Any]:
        """Generate a complete specification using Chain of Thought process."""
        
        project_id = str(uuid.uuid4())
        
        print(f"🔄 Generating specification for: {project_title}")
        
        # Step 1: Generate persona and CoT response
        cot_response = self.prompt_manager.get_prompt(
            self.agent_name, 
            'chain_of_thought',
            user_requirement=requirements,
            project_title=project_title,
            additional_context=additional_context
        )
        
        print("✓ Chain of Thought analysis completed")
        
        # Step 2: Generate functional specification
        func_spec = self.prompt_manager.get_prompt(
            self.agent_name,
            'functional_spec_template',
            user_requirement=requirements,
            introduction_context=f"This functional specification covers the {project_title} requirements."
        )
        
        print("✓ Functional specification generated")
        
        # Step 3: Generate Gherkin user stories
        user_stories = self.prompt_manager.get_prompt(
            self.agent_name,
            'gherkin_template',
            functional_requirements=func_spec[:500],  # First 500 chars as context
            user_personas="Primary: End Users, Secondary: Administrators",
            business_rules="Standard web application security and usability rules"
        )
        
        print("✓ Gherkin user stories created")
        
        # Combine all parts into structured specification
        specification = {
            "project_id": project_id,
            "project_title": project_title,
            "timestamp": datetime.now().isoformat(),
            "executive_summary": cot_response,
            "functional_requirements": func_spec,
            "user_stories": user_stories,
            "original_requirements": requirements
        }
        
        # Calculate total token count
        total_text = json.dumps(specification, indent=2)
        token_count = self.count_tokens(total_text)
        
        return {
            "project_id": project_id,
            "specification": specification,
            "token_count": token_count,
            "generated_at": datetime.now().isoformat()
        }

async def test_simplified_ba():
    """Test the simplified BA agent."""
    try:
        print('🧪 Testing Simplified Enhanced BA Agent')
        print('=' * 60)
        
        # Create agent
        ba_agent = SimplifiedEnhancedBAAgent()
        print('✓ Simplified BA Agent created')
        
        # Test requirement
        test_requirement = '''
        Create a user authentication system for a web application that allows users to:
        - Register with email and password
        - Login with email/password
        - Reset forgotten passwords via email
        - Verify email addresses
        - Manage user profiles
        - Support role-based access control (admin, user, moderator)
        - Enable two-factor authentication
        '''
        
        print('🔄 Generating specification...')
        
        # Generate specification
        result = await ba_agent.generate_standalone_specification(
            requirements=test_requirement.strip(),
            project_title='User Authentication System',
            additional_context='Web application with security focus'
        )
        
        print('\n📊 Results:')
        print(f'  - Project ID: {result["project_id"][:8]}...')
        print(f'  - Token count: {result["token_count"]:,}')
        print(f'  - Generated at: {result["generated_at"]}')
        
        spec = result['specification']
        
        print('\n📝 Specification Components:')
        print(f'  - Executive Summary: {len(spec["executive_summary"])} chars')
        print(f'  - Functional Requirements: {len(spec["functional_requirements"])} chars')
        print(f'  - User Stories: {len(spec["user_stories"])} chars')
        
        print('\n🔍 Preview of Executive Summary:')
        print('-' * 50)
        print(spec["executive_summary"][:300] + '...')
        
        print('\n🎉 Simplified Enhanced BA Agent test completed successfully!')
        return True
        
    except Exception as e:
        print(f'✗ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simplified_ba())
    sys.exit(0 if success else 1)
