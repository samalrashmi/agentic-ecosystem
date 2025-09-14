#!/usr/bin/env python3
"""
Complete Agentic Ecosystem Startup Script
Starts both the MCP server and Web server for full functionality.
"""

import asyncio
import subprocess
import time
import sys
import os
from pathlib import Path

def start_mcp_server():
    """Start the enhanced MCP server."""
    print("🚀 Starting Enhanced MCP Server...")
    cmd = [sys.executable, "main.py", "server"]
    return subprocess.Popen(cmd, cwd=Path.cwd())

def start_web_server():
    """Start the web server."""
    print("🌐 Starting Web Server...")
    cmd = [sys.executable, "src/web_server.py"]
    return subprocess.Popen(cmd, cwd=Path.cwd())

def start_test_server():
    """Start the test server as fallback."""
    print("🧪 Starting Test Server...")
    cmd = [sys.executable, "test_server.py"]
    return subprocess.Popen(cmd, cwd=Path.cwd())

def main():
    """Start the complete agentic ecosystem."""
    print("🎯 STARTING COMPLETE ENHANCED AGENTIC ECOSYSTEM")
    print("=" * 60)
    print()
    
    processes = []
    
    try:
        # Option 1: Try to start the MCP server
        print("📡 Attempting to start MCP Server...")
        try:
            mcp_process = start_mcp_server()
            time.sleep(2)  # Give it time to start
            
            # Check if MCP server started successfully
            if mcp_process.poll() is None:
                print("✅ MCP Server started successfully!")
                processes.append(("MCP Server", mcp_process))
            else:
                print("❌ MCP Server failed to start, trying web server...")
                raise Exception("MCP Server failed")
                
        except Exception as e:
            print(f"⚠️  MCP Server issue: {e}")
            print("🔄 Falling back to Web Server...")
            
            # Option 2: Try to start the web server
            try:
                web_process = start_web_server()
                time.sleep(2)  # Give it time to start
                
                # Check if web server started successfully
                if web_process.poll() is None:
                    print("✅ Web Server started successfully!")
                    processes.append(("Web Server", web_process))
                else:
                    print("❌ Web Server failed to start, trying test server...")
                    raise Exception("Web Server failed")
                    
            except Exception as e2:
                print(f"⚠️  Web Server issue: {e2}")
                print("🔄 Falling back to Test Server...")
                
                # Option 3: Start the test server
                test_process = start_test_server()
                time.sleep(2)  # Give it time to start
                
                if test_process.poll() is None:
                    print("✅ Test Server started successfully!")
                    processes.append(("Test Server", test_process))
                else:
                    print("❌ All servers failed to start!")
                    return
        
        # Display success information
        print()
        print("🎉 AGENTIC ECOSYSTEM RUNNING!")
        print("-" * 40)
        for name, process in processes:
            print(f"✅ {name}: PID {process.pid}")
        
        print()
        print("🌐 Access Points:")
        print("   • Main UI: http://localhost:8000")
        print("   • Status: http://localhost:8000/agents/health")
        print()
        print("🤖 Enhanced Features:")
        print("   ✅ LLM-powered intelligent agents")
        print("   ✅ Real-time status tracking")
        print("   ✅ Complete project generation")
        print("   ✅ Persistent artifact storage")
        print()
        print("⌨️  Press Ctrl+C to stop all servers...")
        
        # Keep running until interrupted
        try:
            while True:
                # Check if processes are still running
                for name, process in processes:
                    if process.poll() is not None:
                        print(f"⚠️  {name} stopped unexpectedly!")
                        return
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down servers...")
            
    except Exception as e:
        print(f"💥 Startup error: {e}")
        
    finally:
        # Clean up processes
        for name, process in processes:
            try:
                print(f"🔄 Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except Exception as e:
                print(f"⚠️  Error stopping {name}: {e}")
                try:
                    process.kill()
                except:
                    pass
        
        print("\n👋 Agentic Ecosystem shutdown complete!")

if __name__ == "__main__":
    main()
