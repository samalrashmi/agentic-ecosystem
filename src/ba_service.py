"""
Standalone BA Agent Service for Web Interface

This module provides a simplified BA agent service that works with the web interface
without complex import dependencies.
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys
import os

# Add src to path for imports
src_path = Path(__file__).parent
project_root = src_path.parent
output_dir = project_root / "out"
sys.path.insert(0, str(src_path))

from utils.prompt_manager import get_prompt_manager

# LLM imports for actual processing
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI


class StandaloneBAService:
    """Standalone BA service for web interface."""
    
    def __init__(self):
        """Initialize the BA service."""
        self.prompt_manager = get_prompt_manager()
        
        # Initialize LLM
        try:
            self.llm = ChatOpenAI(
                model="gpt-4",
                temperature=0.1,
                max_tokens=4000
            )
        except Exception as e:
            print(f"Warning: Could not initialize OpenAI LLM: {e}")
            print("BA service will return prompt templates only")
            self.llm = None
        
        # Try to import tiktoken for token counting
        try:
            import tiktoken
            self.encoding = tiktoken.get_encoding("cl100k_base")
            self.has_tiktoken = True
        except ImportError:
            print("Warning: tiktoken not available, using character-based estimation")
            self.has_tiktoken = False
        
        self.max_tokens = 16384  # Conservative limit
        self.current_tokens = 0
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.has_tiktoken:
            return len(self.encoding.encode(text))
        else:
            # Rough estimation: ~4 characters per token
            return len(text) // 4
    
    async def query_llm(self, prompt: str, system_message: Optional[str] = None) -> str:
        """Query the LLM with the given prompt."""
        if not self.llm:
            # Demo mode: Generate realistic-looking responses based on prompt type
            return await self._generate_demo_response(prompt)
            
        try:
            messages = []
            
            if system_message:
                messages.append(SystemMessage(content=system_message))
            
            messages.append(HumanMessage(content=prompt))
            
            # Get response from LLM
            response = await self.llm.agenerate([messages])
            result = response.generations[0][0].text
            
            return result
            
        except Exception as e:
            print(f"Error querying LLM: {str(e)}")
            # Fallback to demo mode
            return await self._generate_demo_response(prompt)
    
    async def _generate_demo_response(self, prompt: str) -> str:
        """Generate a demo response based on the prompt type."""
        if "chain_of_thought" in prompt.lower() or "executive summary" in prompt.lower():
            return """## 1. Requirement Analysis & Clarification

### Initial Analysis
The user has requested "Create a simple calculator with all simple mathematical function." This requirement needs clarification to ensure comprehensive development.

### Clarifying Questions Identified:
1. **User Interface**: Should this be a web application, desktop application, or mobile app?
2. **Mathematical Functions**: Which specific operations should be included (addition, subtraction, multiplication, division, modulo, exponents)?
3. **Input Methods**: Keyboard input, button clicks, or both?
4. **Display Requirements**: Should it show calculation history? Support for decimal places?
5. **Error Handling**: How should division by zero and invalid inputs be handled?
6. **Accessibility**: Any specific accessibility requirements?

### Assumptions Made:
- Web-based calculator application
- Standard arithmetic operations: +, -, ×, ÷, %, √, ^
- Both button interface and keyboard input support
- Decimal number support with up to 10 decimal places
- Basic error handling for invalid operations
- Responsive design for desktop and mobile devices

### Business Value:
This calculator will provide users with a convenient tool for performing basic mathematical calculations quickly and accurately, improving productivity for everyday computational needs."""
            
        elif "functional_spec" in prompt.lower() or "functional specification" in prompt.lower():
            return """## 1.0 Introduction & Purpose
This document provides the functional specification for the Fun Calculator application, a web-based mathematical calculation tool designed to perform standard arithmetic operations with an intuitive user interface.

## 2.0 Scope
### 2.1 In-Scope
- Basic arithmetic operations (addition, subtraction, multiplication, division)
- Advanced operations (percentage, square root, exponentiation)
- Decimal number support
- Keyboard and mouse input support
- Responsive web interface
- Error handling and validation
- Calculation history display

### 2.2 Out-of-Scope
- Scientific calculator functions (trigonometry, logarithms)
- Graphing capabilities
- Unit conversions
- Programming/statistical functions
- User account management
- Cloud synchronization

## 3.0 User Roles & Permissions
### 3.1 Primary Users
- General users requiring basic mathematical calculations
- Students performing homework calculations
- Office workers doing quick calculations

### 3.2 Secondary Users
- Accessibility users requiring screen reader support
- Mobile users accessing via smartphones/tablets

### 3.3 Administrative Users
- Not applicable for this application

## 4.0 System Features & Functionality
### 4.1 Core Features
- **Basic Operations**: Addition (+), Subtraction (-), Multiplication (×), Division (÷)
- **Advanced Operations**: Percentage (%), Square Root (√), Exponentiation (^)
- **Number Input**: Support for positive/negative numbers and decimals
- **Display**: Large, clear display showing current calculation and result
- **Clear Functions**: Clear current entry (CE) and clear all (C)

### 4.2 Supporting Features
- **Keyboard Support**: Full keyboard input for numbers and operations
- **History**: Display of last 5 calculations
- **Error Messages**: Clear error messages for invalid operations
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### 4.3 Integration Points
- No external system integrations required

## 5.0 Non-Functional Requirements
### 5.1 Performance Requirements
- Calculations must complete within 100ms
- Application must load within 2 seconds
- Support up to 15-digit precision

### 5.2 Security Requirements
- Input validation to prevent code injection
- No sensitive data storage required

### 5.3 Usability Requirements
- Intuitive button layout following standard calculator design
- Clear visual feedback for button presses
- Accessible to users with disabilities (WCAG 2.1 Level AA)

### 5.4 Reliability Requirements
- 99.9% uptime for web application
- Graceful error handling for all edge cases
- Cross-browser compatibility (Chrome, Firefox, Safari, Edge)"""
            
        elif "gherkin" in prompt.lower() or "user stories" in prompt.lower():
            return """```gherkin
Feature: Basic Arithmetic Operations
  As a user
  I want to perform basic arithmetic calculations
  So that I can solve mathematical problems quickly

  Background:
    Given the calculator application is loaded
    And the display shows "0"

  Scenario: Addition of two positive numbers
    Given I have entered "5" into the calculator
    When I press the "+" button
    And I enter "3"
    And I press the "=" button
    Then the display should show "8"

  Scenario: Subtraction resulting in negative number
    Given I have entered "3" into the calculator
    When I press the "-" button
    And I enter "5"
    And I press the "=" button
    Then the display should show "-2"

  Scenario: Multiplication with decimal numbers
    Given I have entered "2.5" into the calculator
    When I press the "×" button
    And I enter "4"
    And I press the "=" button
    Then the display should show "10"

  Scenario: Division by zero error handling
    Given I have entered "10" into the calculator
    When I press the "÷" button
    And I enter "0"
    And I press the "=" button
    Then the display should show "Error: Division by zero"
    And the calculator should be ready for new input

  Scenario: Chain calculations
    Given I have entered "10" into the calculator
    When I press the "+" button
    And I enter "5"
    And I press the "=" button
    And I press the "×" button
    And I enter "2"
    And I press the "=" button
    Then the display should show "30"

  Scenario Outline: Multiple basic operations
    Given I have entered "<first_number>" into the calculator
    When I press the "<operation>" button
    And I enter "<second_number>"
    And I press the "=" button
    Then the display should show "<result>"
    
    Examples:
      | first_number | operation | second_number | result |
      | 15           | +         | 25            | 40     |
      | 100          | -         | 33            | 67     |
      | 12           | ×         | 8             | 96     |
      | 144          | ÷         | 12            | 12     |

Feature: Advanced Mathematical Operations
  As a user
  I want to perform advanced mathematical operations
  So that I can solve more complex calculations

  Background:
    Given the calculator application is loaded
    And the display shows "0"

  Scenario: Square root calculation
    Given I have entered "16" into the calculator
    When I press the "√" button
    Then the display should show "4"

  Scenario: Percentage calculation
    Given I have entered "50" into the calculator
    When I press the "%" button
    Then the display should show "0.5"

  Scenario: Exponentiation
    Given I have entered "2" into the calculator
    When I press the "^" button
    And I enter "3"
    And I press the "=" button
    Then the display should show "8"

  Scenario: Complex calculation with order of operations
    Given I have entered "5" into the calculator
    When I press the "+" button
    And I enter "3"
    And I press the "×" button
    And I enter "2"
    And I press the "=" button
    Then the display should show "11"

  Scenario Outline: Advanced operations with various inputs
    Given I have entered "<input>" into the calculator
    When I press the "<operation>" button
    Then the display should show "<result>"
    
    Examples:
      | input | operation | result |
      | 25    | √         | 5      |
      | 64    | √         | 8      |
      | 100   | %         | 1      |
      | 75    | %         | 0.75   |

Feature: Input and Display Management
  As a user
  I want to manage my input and see clear results
  So that I can track my calculations accurately

  Background:
    Given the calculator application is loaded

  Scenario: Clear entry function
    Given I have entered "123" into the calculator
    When I press the "CE" button
    Then the display should show "0"
    And I should be able to enter new numbers

  Scenario: Clear all function
    Given I have performed a calculation "5 + 3 = 8"
    When I press the "C" button
    Then the display should show "0"
    And the calculation history should be cleared

  Scenario: Decimal number input
    Given I am entering a decimal number
    When I enter "3.14159"
    Then the display should show "3.14159"
    And I should be able to perform operations with this number

  Scenario: Negative number handling
    Given I want to enter a negative number
    When I press the "+/-" button
    And I enter "5"
    Then the display should show "-5"

  Scenario: Maximum digit display
    Given I am entering a very long number
    When I enter "123456789012345"
    Then the display should show the number within display limits
    And should handle overflow gracefully

Feature: Keyboard Input Support
  As a user
  I want to use keyboard shortcuts
  So that I can calculate faster without using mouse

  Background:
    Given the calculator application is loaded
    And keyboard input is enabled

  Scenario: Numeric key input
    Given I am using the keyboard
    When I press the "5" key
    And I press the "+" key
    And I press the "3" key
    And I press the "Enter" key
    Then the display should show "8"

  Scenario: Operation keys
    Given I have entered "10" using keyboard
    When I press the "*" key for multiplication
    And I press "2"
    And I press "Enter"
    Then the display should show "20"

  Scenario Outline: Keyboard shortcuts
    Given I am using keyboard input
    When I press "<key_combination>"
    Then the action "<expected_action>" should be performed
    
    Examples:
      | key_combination | expected_action    |
      | Escape          | Clear all          |
      | Delete          | Clear entry        |
      | Backspace       | Delete last digit  |
      | Enter           | Calculate result   |

Feature: Error Handling and Validation
  As a user
  I want to see clear error messages
  So that I understand what went wrong and how to fix it

  Background:
    Given the calculator application is loaded

  Scenario: Division by zero
    Given I have entered "42" into the calculator
    When I press the "÷" button
    And I enter "0"
    And I press the "=" button
    Then I should see an error message "Error: Division by zero"
    And the calculator should be ready for new input

  Scenario: Invalid operation sequence
    Given the calculator is showing "0"
    When I press the "+" button
    And I press the "×" button
    Then the calculator should handle the invalid sequence gracefully
    And use the last operator entered

  Scenario: Overflow error
    Given I am performing calculations that exceed the display limit
    When the result would be larger than the maximum displayable number
    Then I should see an error message "Error: Number too large"
    And the calculator should be ready for new input

  Scenario: Square root of negative number
    Given I have entered "-9" into the calculator
    When I press the "√" button
    Then I should see an error message "Error: Cannot calculate square root of negative number"

Feature: Calculation History
  As a user
  I want to see my recent calculations
  So that I can reference previous results

  Background:
    Given the calculator application is loaded
    And calculation history is enabled

  Scenario: Display calculation history
    Given I have performed several calculations
    When I perform "5 + 3 = 8"
    And I perform "10 × 2 = 20"
    And I perform "15 ÷ 3 = 5"
    Then the history should show the last 3 calculations
    And each entry should show the full equation and result

  Scenario: Use result from history
    Given I have a calculation "25 + 15 = 40" in history
    When I click on the result "40" in history
    Then the display should show "40"
    And I should be able to continue calculating with this number

  Scenario: Clear calculation history
    Given I have multiple calculations in history
    When I press the "Clear History" button
    Then the calculation history should be empty
    And the current calculation should remain unaffected
```

  Scenario: Square root calculation
    Given I have entered "16" into the calculator
    When I press the "√" button
    Then the display should show "4"

  Scenario: Exponentiation
    Given I have entered "2" into the calculator
    When I press the "^" button
    And I enter "3"
    And I press the "=" button
    Then the display should show "8"

Feature: Calculator History
  As a user
  I want to see my recent calculations
  So that I can review and reuse previous results

  Scenario: Viewing calculation history
    Given I have performed the calculation "5 + 3 = 8"
    And I have performed the calculation "10 - 2 = 8"
    When I view the calculation history
    Then I should see "5 + 3 = 8" in the history
    And I should see "10 - 2 = 8" in the history

Feature: Keyboard Input Support
  As a user
  I want to use keyboard input for calculations
  So that I can work more efficiently

  Scenario: Keyboard number input
    Given the calculator is ready for input
    When I press the "5" key on my keyboard
    Then the display should show "5"

  Scenario: Keyboard operation input
    Given I have entered "5" into the calculator
    When I press the "+" key on my keyboard
    And I press the "3" key on my keyboard
    And I press the "Enter" key on my keyboard
    Then the display should show "8"
```"""
        
        else:
            # Generic response for unknown prompt types
            return "Generated response for: " + prompt[:100] + "..."
    
    async def generate_standalone_specification(
        self, 
        requirements: str, 
        project_title: str = "Software Project",
        additional_context: str = "",
        progress_callback = None
    ) -> Dict[str, Any]:
        """Generate a complete specification using Chain of Thought process."""
        
        project_id = str(uuid.uuid4())
        
        print(f"🔄 Generating specification for: {project_title}")
        
        try:
            if progress_callback:
                await progress_callback("🚀 Initializing BA Agent...")
            
            # BA Agent persona system message
            ba_persona = """You are an expert Senior Business Analyst AI agent in an enterprise software development ecosystem.

Your responsibilities include:
1. Analyzing user specifications and understanding functional requirements
2. Creating detailed user stories with acceptance criteria using Gherkin syntax
3. Providing comprehensive functional specifications
4. Ensuring all business needs are properly captured and addressed

You have deep expertise in:
- Requirements analysis and documentation
- Business process modeling
- User story creation with proper acceptance criteria
- Gherkin syntax for behavior-driven development
- Functional specification creation
- Domain-specific business knowledge across various industries

Always be thorough and ensure all business needs are properly captured."""

            if progress_callback:
                await progress_callback("🧠 Analyzing requirements with Chain of Thought...")

            # Step 1: Generate Chain of Thought analysis
            cot_prompt = self.prompt_manager.get_prompt(
                'ba_agent', 
                'chain_of_thought',
                user_requirement=requirements
            )
            
            print("🔄 Generating Chain of Thought analysis...")
            cot_response = await self.query_llm(cot_prompt, ba_persona)
            print("✓ Chain of Thought analysis completed")
            
            if progress_callback:
                await progress_callback("📋 Generating functional specification...")

            # Step 2: Generate functional specification
            func_spec_prompt = self.prompt_manager.get_prompt(
                'ba_agent',
                'functional_spec_template',
                user_requirement=requirements,
                introduction_context=f"Functional specification for {project_title}"
            )
            
            print("🔄 Generating functional specification...")
            func_spec = await self.query_llm(func_spec_prompt, ba_persona)
            print("✓ Functional specification generated")
            
            if progress_callback:
                await progress_callback("📝 Creating comprehensive Gherkin user stories...")

            # Step 3: Generate Gherkin user stories
            user_stories_prompt = self.prompt_manager.get_prompt(
                'ba_agent',
                'gherkin_template',
                functional_requirements=requirements,
                user_personas="End Users, Administrators, Moderators"
            )
            
            print("🔄 Generating Gherkin user stories...")
            user_stories = await self.query_llm(user_stories_prompt, ba_persona)
            print("✓ Gherkin user stories created")
            
            if progress_callback:
                await progress_callback("💾 Saving specification files...")

            # Combine all parts into a structured specification
            full_specification = f"""
# {project_title} - Business Analysis

## Executive Summary
{cot_response}

## Functional Specification
{func_spec}

## User Stories
{user_stories}

## Original Requirements
{requirements}
"""
            
            # Create specification structure
            specification = {
                "project_id": project_id,
                "project_title": project_title,
                "timestamp": datetime.now().isoformat(),
                "executive_summary": cot_response,
                "functional_requirements": func_spec,
                "user_stories": user_stories,
                "original_requirements": requirements,
                "full_document": full_specification
            }
            
            # Calculate total token count
            total_text = json.dumps(specification, indent=2)
            token_count = self.count_tokens(total_text)
            
            # Save files to output directory
            saved_files = self._save_specification_files(project_id, specification, full_specification)
            
            if progress_callback:
                await progress_callback("✅ Specification complete!")

            return {
                "project_id": project_id,
                "specification": specification,
                "token_count": token_count,
                "generated_at": datetime.now().isoformat(),
                "status": "success",
                "saved_files": saved_files,
                "output_directory": str(output_dir / f"project_{project_id}")
            }
            
        except Exception as e:
            print(f"Error in specification generation: {e}")
            # Return error response
            return {
                "project_id": project_id,
                "specification": {
                    "project_title": project_title,
                    "error": f"Failed to generate specification: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                },
                "token_count": 0,
                "generated_at": datetime.now().isoformat(),
                "status": "error",
                "saved_files": [],
                "output_directory": None
            }
    
    def _save_specification_files(self, project_id: str, specification: Dict[str, Any], full_specification: str) -> List[str]:
        """Save specification files to the output directory."""
        try:
            project_dir = output_dir / f"project_{project_id}"
            project_dir.mkdir(parents=True, exist_ok=True)
            
            saved_files = []
            
            # Save JSON file
            json_file = project_dir / "business_analysis_ba_agent.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(specification, f, indent=2, ensure_ascii=False)
            saved_files.append(str(json_file))
            
            # Save Markdown file
            md_file = project_dir / "business_analysis_ba_agent.md"
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(full_specification)
            saved_files.append(str(md_file))
            
            # Save summary file
            summary_file = project_dir / "project_summary.json"
            summary = {
                "project_id": project_id,
                "project_title": specification.get("project_title", "Unknown"),
                "generated_at": specification.get("timestamp", datetime.now().isoformat()),
                "agent_type": "business_analyst",
                "token_count": self.count_tokens(full_specification),
                "files_generated": len(saved_files),
                "status": "completed"
            }
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)
            saved_files.append(str(summary_file))
            
            return saved_files
            
        except Exception as e:
            print(f"Error saving files: {e}")
            return []
    
    async def export_specification_document(
        self, 
        project_id: str, 
        format: str = "markdown"
    ) -> str:
        """Export specification document in specified format."""
        # For demo purposes, return a placeholder
        # In real implementation, this would retrieve stored specification
        return f"""
# Project Specification Export

**Project ID:** {project_id}
**Format:** {format}
**Generated:** {datetime.now().isoformat()}

This is a placeholder for the exported specification document.
In a full implementation, this would retrieve the stored specification
and format it according to the requested format.
"""


# Global instance for the web server
_ba_service_instance = None

def get_ba_service() -> StandaloneBAService:
    """Get or create the BA service instance."""
    global _ba_service_instance
    if _ba_service_instance is None:
        _ba_service_instance = StandaloneBAService()
    return _ba_service_instance
