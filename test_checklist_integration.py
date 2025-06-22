#!/usr/bin/env python3
"""
Test script to verify AI agent checklist integration is working
"""

import subprocess
import sys
from pathlib import Path

def test_checklist_integration():
    """Test all checklist integration components."""
    print("🧪 TESTING NBA STATS CHECKLIST INTEGRATION")
    print("=" * 50)
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Basic checklist CLI
    total_tests += 1
    try:
        result = subprocess.run(
            ["python3", "app/mcp/checklist_cli.py", "stats"],
            capture_output=True,
            text=True,
            check=True
        )
        if "Total Items:" in result.stdout:
            print("✅ Test 1: Basic checklist CLI - PASSED")
            success_count += 1
        else:
            print("❌ Test 1: Basic checklist CLI - FAILED (no stats output)")
    except Exception as e:
        print(f"❌ Test 1: Basic checklist CLI - FAILED ({e})")
    
    # Test 2: AI integration helper
    total_tests += 1
    try:
        result = subprocess.run(
            ["python3", "ai_checklist.py", "status"],
            capture_output=True,
            text=True,
            check=True
        )
        if "CHECKING NBA STATS PROJECT STATUS" in result.stdout:
            print("✅ Test 2: AI integration helper - PASSED")
            success_count += 1
        else:
            print("❌ Test 2: AI integration helper - FAILED (no status output)")
    except Exception as e:
        print(f"❌ Test 2: AI integration helper - FAILED ({e})")
    
    # Test 3: Task suggestion
    total_tests += 1
    try:
        result = subprocess.run(
            ["python3", "ai_checklist.py", "suggest", "authentication"],
            capture_output=True,
            text=True,
            check=True
        )
        if "ANALYZING TASK:" in result.stdout:
            print("✅ Test 3: Task suggestion - PASSED")
            success_count += 1
        else:
            print("❌ Test 3: Task suggestion - FAILED (no analysis output)")
    except Exception as e:
        print(f"❌ Test 3: Task suggestion - FAILED ({e})")
    
    # Test 4: Check required files exist
    total_tests += 1
    required_files = [
        "AI_AGENT_CHECKLIST_INTEGRATION.md",
        "IMPROVEMENT_CHECKLIST.md",
        "ai_checklist.py",
        "app/mcp/checklist_cli.py",
        "app/mcp/checklist_manager.py",
        "app/mcp/checklist_data.json",
        "README.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if not missing_files:
        print("✅ Test 4: Required files exist - PASSED")
        success_count += 1
    else:
        print(f"❌ Test 4: Required files exist - FAILED (missing: {missing_files})")
    
    # Test 5: VS Code workspace file
    total_tests += 1
    if Path("nba-stats.code-workspace").exists():
        print("✅ Test 5: VS Code workspace - PASSED")
        success_count += 1
    else:
        print("❌ Test 5: VS Code workspace - FAILED (file missing)")
    
    # Final results
    print("\n" + "=" * 50)
    print(f"🎯 INTEGRATION TEST RESULTS: {success_count}/{total_tests} PASSED")
    
    if success_count == total_tests:
        print("🎉 ALL TESTS PASSED! Checklist integration is ready.")
        print("\n📋 AI agents can now use:")
        print("  - python3 ai_checklist.py (interactive)")
        print("  - python3 ai_checklist.py status (quick status)")
        print("  - python3 app/mcp/checklist_cli.py [commands]")
        print("  - VS Code tasks for checklist management")
        return True
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    success = test_checklist_integration()
    sys.exit(0 if success else 1)
