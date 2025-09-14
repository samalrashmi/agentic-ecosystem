#!/usr/bin/env python3
"""
BA Agent Test Runner

Simple script to run all BA agent related tests with proper environment setup.
"""

import sys
import pytest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def run_ba_tests():
    """Run all BA agent tests."""
    print("🧪 Running Enhanced BA Agent Test Suite")
    print("=" * 50)
    
    # Test files to run
    test_files = [
        "tests/test_enhanced_ba_agent.py",
        "tests/test_ba_agent.py"
    ]
    
    # Run each test file
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"\n📋 Running {test_file}")
            print("-" * 30)
            
            # Run pytest with verbose output
            result = pytest.main([
                test_file,
                "-v",
                "--tb=short",
                "--no-header",
                "--disable-warnings"
            ])
            
            if result == 0:
                print(f"✅ {test_file} passed")
            else:
                print(f"❌ {test_file} failed")
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    print("\n🎉 BA Agent test suite completed!")

if __name__ == "__main__":
    run_ba_tests()
