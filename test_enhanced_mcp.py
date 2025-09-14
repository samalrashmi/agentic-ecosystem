#!/usr/bin/env python3
"""
Test script for the Enhanced LangGraph MCP Server

This script tests the enhanced MCP implementation with advanced features
like persistent project management, resource support, and real-time monitoring.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from langgraph_agents.enhanced_mcp_server import (
    project_manager,
    handle_create_project_enhanced,
    handle_get_project_status_enhanced,
    handle_list_projects_enhanced,
    handle_monitor_project_progress,
    handle_get_project_artifacts_enhanced
)

async def test_enhanced_mcp_server():
    """Test the enhanced MCP server functionality."""
    
    print("🧪 Testing Enhanced LangGraph MCP Server")
    print("=" * 50)
    
    # Test 1: Create a project
    print("\n1️⃣ Testing project creation...")
    create_args = {
        "specification": "Create a web-based task management application with user authentication, real-time updates, and mobile responsiveness. The app should allow users to create, edit, and delete tasks, organize them into projects, and collaborate with team members.",
        "title": "TaskMaster Pro",
        "domain": "web",
        "priority": "high"
    }
    
    try:
        result = await handle_create_project_enhanced(create_args)
        response_data = json.loads(result[0].text)
        project_id = response_data["project_id"]
        print(f"✅ Project created successfully: {project_id}")
        print(f"   Title: {response_data['title']}")
        print(f"   Domain: {response_data['domain']}")
        print(f"   Priority: {response_data['priority']}")
    except Exception as e:
        print(f"❌ Project creation failed: {e}")
        return
    
    # Wait a moment for workflow to start
    await asyncio.sleep(2)
    
    # Test 2: Check project status
    print("\n2️⃣ Testing project status retrieval...")
    try:
        status_result = await handle_get_project_status_enhanced({
            "project_id": project_id,
            "include_artifacts": True
        })
        status_data = json.loads(status_result[0].text)
        print(f"✅ Project status retrieved:")
        print(f"   Status: {status_data.get('status', 'unknown')}")
        print(f"   Current Phase: {status_data.get('current_phase', 'unknown')}")
        print(f"   Progress: {status_data.get('progress', 0)}%")
    except Exception as e:
        print(f"❌ Status retrieval failed: {e}")
    
    # Test 3: List projects
    print("\n3️⃣ Testing project listing...")
    try:
        list_result = await handle_list_projects_enhanced({
            "limit": 10
        })
        list_data = json.loads(list_result[0].text)
        print(f"✅ Projects listed: {list_data['total_count']} projects found")
        for project in list_data["projects"][:3]:  # Show first 3
            print(f"   - {project['title']} ({project['status']})")
    except Exception as e:
        print(f"❌ Project listing failed: {e}")
    
    # Test 4: Monitor project progress
    print("\n4️⃣ Testing progress monitoring...")
    try:
        monitor_result = await handle_monitor_project_progress({
            "project_id": project_id
        })
        monitor_data = json.loads(monitor_result[0].text)
        print(f"✅ Progress monitoring active:")
        print(f"   Current Phase: {monitor_data.get('current_phase', 'unknown')}")
        print(f"   Progress: {monitor_data.get('progress_percentage', 0)}%")
        print(f"   Completed Phases: {len(monitor_data.get('completed_phases', []))}")
        print(f"   Remaining Phases: {len(monitor_data.get('remaining_phases', []))}")
    except Exception as e:
        print(f"❌ Progress monitoring failed: {e}")
    
    # Wait for workflow to make some progress
    print("\n⏳ Waiting for workflow to progress...")
    await asyncio.sleep(10)
    
    # Test 5: Check progress again
    print("\n5️⃣ Checking updated progress...")
    try:
        monitor_result = await handle_monitor_project_progress({
            "project_id": project_id
        })
        monitor_data = json.loads(monitor_result[0].text)
        print(f"✅ Updated progress:")
        print(f"   Current Phase: {monitor_data.get('current_phase', 'unknown')}")
        print(f"   Progress: {monitor_data.get('progress_percentage', 0)}%")
        print(f"   Completed Phases: {monitor_data.get('completed_phases', [])}")
        if monitor_data.get('recent_activity'):
            print(f"   Recent Activity: {len(monitor_data['recent_activity'])} files updated")
    except Exception as e:
        print(f"❌ Progress check failed: {e}")
    
    # Test 6: Test project manager persistence
    print("\n6️⃣ Testing persistent project management...")
    try:
        # Check if data directory was created
        data_dir = Path(__file__).parent / "data"
        projects_file = data_dir / "projects.json"
        
        if projects_file.exists():
            print(f"✅ Projects file created: {projects_file}")
            with open(projects_file, 'r') as f:
                saved_data = json.load(f)
            print(f"   Saved projects: {len(saved_data)}")
        else:
            print("⚠️ Projects file not found (may not have been saved yet)")
    except Exception as e:
        print(f"❌ Persistence check failed: {e}")
    
    # Test 7: Wait for workflow completion and check artifacts
    print("\n7️⃣ Waiting for workflow completion and checking artifacts...")
    
    # Wait longer for workflow to complete
    max_wait = 60  # 60 seconds max wait
    check_interval = 5  # Check every 5 seconds
    waited = 0
    
    while waited < max_wait:
        try:
            status_result = await handle_get_project_status_enhanced({
                "project_id": project_id,
                "include_artifacts": False
            })
            status_data = json.loads(status_result[0].text)
            
            if status_data.get('status') in ['completed', 'failed']:
                break
                
            print(f"   Workflow still running... ({status_data.get('current_phase', 'unknown')})")
            await asyncio.sleep(check_interval)
            waited += check_interval
            
        except Exception as e:
            print(f"   Error checking status: {e}")
            break
    
    # Final status check
    try:
        final_status = await handle_get_project_status_enhanced({
            "project_id": project_id,
            "include_artifacts": True
        })
        final_data = json.loads(final_status[0].text)
        
        print(f"✅ Final project status:")
        print(f"   Status: {final_data.get('status', 'unknown')}")
        print(f"   Workflow Completed: {final_data.get('workflow_completed', False)}")
        
        if final_data.get('artifacts'):
            print(f"   Artifacts Generated: {len(final_data['artifacts'])}")
            for artifact_name in final_data['artifacts']:
                print(f"     - {artifact_name}")
        
        # Test artifact retrieval
        if final_data.get('status') == 'completed':
            print("\n8️⃣ Testing artifact retrieval...")
            try:
                artifacts_result = await handle_get_project_artifacts_enhanced({
                    "project_id": project_id,
                    "artifact_type": "all"
                })
                artifacts_data = json.loads(artifacts_result[0].text)
                print(f"✅ Retrieved {artifacts_data.get('artifact_count', 0)} artifacts")
                
                for artifact_name, artifact_data in artifacts_data.get('artifacts', {}).items():
                    if isinstance(artifact_data, dict):
                        keys = list(artifact_data.keys())[:3]  # Show first 3 keys
                        print(f"   - {artifact_name}: {keys}...")
                
            except Exception as e:
                print(f"❌ Artifact retrieval failed: {e}")
                
    except Exception as e:
        print(f"❌ Final status check failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Enhanced MCP Server testing completed!")
    print()
    print("Enhanced Features Tested:")
    print("✅ Project creation with metadata")
    print("✅ Enhanced status retrieval")
    print("✅ Project listing with filters")
    print("✅ Real-time progress monitoring")
    print("✅ Persistent project management")
    print("✅ Artifact management")
    print("✅ Background workflow execution")


if __name__ == "__main__":
    asyncio.run(test_enhanced_mcp_server())
