#!/usr/bin/env python3
"""
Comprehensive test showing the full output of the Enhanced BA Agent
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

class EnhancedBAAgentDemo:
    """Enhanced BA Agent demonstration with full output."""
    
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
    
    async def demonstrate_chain_of_thought(
        self, 
        requirements: str, 
        project_title: str = "Software Project"
    ) -> Dict[str, Any]:
        """Demonstrate the full Chain of Thought process."""
        
        print(f"🎯 Demonstrating Chain of Thought for: {project_title}")
        print("=" * 70)
        
        # Generate the complete Chain of Thought analysis
        cot_response = self.prompt_manager.get_prompt(
            self.agent_name, 
            'chain_of_thought',
            user_requirement=requirements
        )
        
        print("📋 COMPLETE CHAIN OF THOUGHT ANALYSIS:")
        print("-" * 70)
        print(cot_response)
        print("-" * 70)
        
        # Also generate functional specification template
        print("\n📄 FUNCTIONAL SPECIFICATION TEMPLATE:")
        print("-" * 50)
        func_spec = self.prompt_manager.get_prompt(
            self.agent_name,
            'functional_spec_template',
            user_requirement=requirements,
            introduction_context=f"Functional specification for {project_title}"
        )
        print(func_spec)
        print("-" * 50)
        
        # Generate Gherkin user stories template
        print("\n📝 GHERKIN USER STORIES TEMPLATE:")
        print("-" * 50)
        user_stories = self.prompt_manager.get_prompt(
            self.agent_name,
            'gherkin_template',
            functional_requirements=requirements,
            user_personas="End Users, Administrators, Moderators"
        )
        print(user_stories)
        print("-" * 50)
        
        # Calculate tokens
        total_content = cot_response + func_spec + user_stories
        token_count = self.count_tokens(total_content)
        
        return {
            "project_title": project_title,
            "chain_of_thought": cot_response,
            "functional_spec": func_spec,
            "user_stories": user_stories,
            "token_count": token_count,
            "character_count": len(total_content)
        }

async def demo_full_ba_capabilities():
    """Demonstrate the full capabilities of the Enhanced BA Agent."""
    
    print("🚀 Enhanced BA Agent - Chain of Thought Demonstration")
    print("=" * 70)
    
    # Create the demo agent
    demo_agent = EnhancedBAAgentDemo()
    
    # Example requirement
    requirement = """
    Create a comprehensive e-commerce platform that allows customers to browse products, 
    add items to their cart, process payments, and track orders. The system should support 
    multiple vendors, product reviews, inventory management, and promotional campaigns. 
    It needs to integrate with payment gateways, shipping providers, and provide analytics 
    for business owners.
    """
    
    # Run the demonstration
    result = await demo_agent.demonstrate_chain_of_thought(
        requirements=requirement.strip(),
        project_title="E-Commerce Platform"
    )
    
    print(f"\n📊 SUMMARY METRICS:")
    print(f"  • Project: {result['project_title']}")
    print(f"  • Total Characters: {result['character_count']:,}")
    print(f"  • Estimated Tokens: {result['token_count']:,}")
    print(f"  • Chain of Thought Length: {len(result['chain_of_thought'])} chars")
    print(f"  • Functional Spec Length: {len(result['functional_spec'])} chars")
    print(f"  • User Stories Length: {len(result['user_stories'])} chars")
    
    print("\n🎉 Demonstration completed successfully!")
    return True

if __name__ == "__main__":
    success = asyncio.run(demo_full_ba_capabilities())
    sys.exit(0 if success else 1)
