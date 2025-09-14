#!/usr/bin/env python3
"""
Script to fix test files to match actual agent tool implementation
"""

import re
from pathlib import Path

def fix_test_file(file_path):
    """Fix a test file to use correct metadata structure."""
    print(f"Fixing {file_path}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace metadata checks
    content = re.sub(
        r'assert "metadata" in result',
        'assert "created_at" in result',
        content
    )
    
    # Replace metadata access patterns
    content = re.sub(
        r'metadata = result\["metadata"\]\s*\n\s*assert metadata\["project_id"\] == self\.test_project_id\s*\n\s*assert "timestamp" in metadata\s*\n\s*assert "agent_type" in metadata',
        'assert result["project_id"] == self.test_project_id\n            assert "created_at" in result\n            assert "created_by" in result',
        content
    )
    
    # Replace other metadata patterns
    content = re.sub(
        r'metadata\["project_id"\]',
        'result["project_id"]',
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"  ✅ Fixed {file_path}")

# Fix all test files
test_files = [
    "tests/test_architect_agent.py",
    "tests/test_developer_agent.py", 
    "tests/test_tester_agent.py"
]

for test_file in test_files:
    fix_test_file(test_file)

print("✅ All test files fixed!")
