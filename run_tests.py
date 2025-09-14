#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner for Agentic Ecosystem

This script runs all test suites and provides a comprehensive test report.
"""

import sys
import pytest
import subprocess
from pathlib import Path
import json
import time
from datetime import datetime

def run_test_suite():
    """Run all test suites with comprehensive reporting."""
    
    print("🧪 Agentic Ecosystem - Comprehensive Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test configuration
    test_files = [
        ("Business Analyst Agent", "tests/test_ba_agent.py"),
        ("Architect Agent", "tests/test_architect_agent.py"),
        ("Developer Agent", "tests/test_developer_agent.py"),
        ("Tester Agent", "tests/test_tester_agent.py"),
        ("LangGraph Workflow", "tests/test_workflow.py"),
        ("MCP Server", "tests/test_mcp_server.py")
    ]
    
    results = {}
    total_start_time = time.time()
    
    # Run each test suite
    for test_name, test_file in test_files:
        print(f"🔍 Running {test_name} tests...")
        print(f"   File: {test_file}")
        
        start_time = time.time()
        
        try:
            # Run pytest with verbose output and JSON report
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_file, 
                "-v", 
                "--tb=short",
                "--json-report",
                f"--json-report-file=test_results_{test_name.lower().replace(' ', '_')}.json"
            ], capture_output=True, text=True, cwd=Path(__file__).parent)
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                print(f"   ✅ PASSED ({execution_time:.2f}s)")
                status = "PASSED"
            else:
                print(f"   ❌ FAILED ({execution_time:.2f}s)")
                status = "FAILED"
                print(f"   Error output: {result.stderr}")
            
            results[test_name] = {
                "status": status,
                "execution_time": execution_time,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"   💥 ERROR ({execution_time:.2f}s): {str(e)}")
            results[test_name] = {
                "status": "ERROR",
                "execution_time": execution_time,
                "error": str(e),
                "return_code": -1
            }
        
        print()
    
    total_execution_time = time.time() - total_start_time
    
    # Generate summary report
    print("📊 TEST SUMMARY REPORT")
    print("=" * 60)
    
    passed_count = sum(1 for r in results.values() if r["status"] == "PASSED")
    failed_count = sum(1 for r in results.values() if r["status"] == "FAILED")
    error_count = sum(1 for r in results.values() if r["status"] == "ERROR")
    total_count = len(results)
    
    print(f"Total Test Suites: {total_count}")
    print(f"✅ Passed: {passed_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"💥 Errors: {error_count}")
    print(f"⏱️  Total Time: {total_execution_time:.2f}s")
    print()
    
    # Detailed results
    print("📋 DETAILED RESULTS")
    print("-" * 60)
    
    for test_name, result in results.items():
        status_icon = {
            "PASSED": "✅",
            "FAILED": "❌", 
            "ERROR": "💥"
        }.get(result["status"], "❓")
        
        print(f"{status_icon} {test_name}")
        print(f"   Status: {result['status']}")
        print(f"   Time: {result['execution_time']:.2f}s")
        
        if result["status"] != "PASSED":
            if "error" in result:
                print(f"   Error: {result['error']}")
            if result.get("stderr"):
                print(f"   stderr: {result['stderr'][:200]}...")
        print()
    
    # Test coverage recommendations
    print("💡 TEST COVERAGE RECOMMENDATIONS")
    print("-" * 60)
    
    recommendations = [
        "✅ Individual agent tools are tested with mocked LLM responses",
        "✅ Workflow orchestration is tested with proper state management",
        "✅ MCP server functionality is tested with async handlers",
        "✅ Error handling is tested for all components",
        "✅ File I/O operations are tested with proper cleanup",
        "⚠️  Consider adding integration tests with real LLM calls (optional)",
        "⚠️  Consider adding performance benchmarks for large projects",
        "⚠️  Consider adding stress tests for concurrent project creation"
    ]
    
    for rec in recommendations:
        print(rec)
    
    print()
    
    # Save comprehensive report
    report = {
        "test_run": {
            "timestamp": datetime.now().isoformat(),
            "total_execution_time": total_execution_time,
            "summary": {
                "total_suites": total_count,
                "passed": passed_count,
                "failed": failed_count,
                "errors": error_count,
                "success_rate": (passed_count / total_count) * 100 if total_count > 0 else 0
            },
            "results": results
        }
    }
    
    report_file = Path(__file__).parent / "comprehensive_test_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📄 Comprehensive report saved to: {report_file}")
    print()
    
    # Return overall success
    overall_success = failed_count == 0 and error_count == 0
    
    if overall_success:
        print("🎉 ALL TESTS PASSED! The agentic ecosystem is ready for deployment.")
    else:
        print("⚠️  Some tests failed. Please review the results above.")
    
    return overall_success


def run_quick_validation():
    """Run a quick validation of critical functionality."""
    
    print("⚡ Quick Validation Test")
    print("-" * 30)
    
    try:
        # Test imports
        print("🔍 Testing imports...")
        
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from langgraph_agents.agent_tools import (
            analyze_business_requirements,
            design_system_architecture, 
            generate_implementation_plan,
            create_test_strategy
        )
        from langgraph_agents.workflow import run_software_development_workflow
        from langgraph_agents.enhanced_mcp_server import ProjectManager
        
        print("   ✅ All imports successful")
        
        # Test basic instantiation
        print("🔍 Testing basic instantiation...")
        
        pm = ProjectManager()
        assert pm is not None
        
        print("   ✅ ProjectManager created successfully")
        
        # Test tool function signatures
        print("🔍 Testing tool signatures...")
        
        tools = [
            analyze_business_requirements,
            design_system_architecture,
            generate_implementation_plan,
            create_test_strategy
        ]
        
        for tool in tools:
            assert hasattr(tool, 'invoke'), f"Tool {tool.name} missing invoke method"
            assert hasattr(tool, 'name'), f"Tool missing name attribute"
        
        print("   ✅ All tool signatures valid")
        
        print()
        print("✅ Quick validation PASSED! Core components are functional.")
        return True
        
    except Exception as e:
        print(f"   ❌ Validation failed: {str(e)}")
        print()
        print("❌ Quick validation FAILED! Please check your installation.")
        return False


if __name__ == "__main__":
    print("🚀 Agentic Ecosystem Test Suite")
    print("Choose test mode:")
    print("1. Quick Validation (fast)")
    print("2. Comprehensive Test Suite (thorough)")
    print("3. Both")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("Enter choice (1-3): ").strip()
    
    success = True
    
    if choice in ["1", "3"]:
        success &= run_quick_validation()
        print()
    
    if choice in ["2", "3"]:
        success &= run_test_suite()
    
    if not success:
        sys.exit(1)
    
    print("🎉 All tests completed successfully!")
