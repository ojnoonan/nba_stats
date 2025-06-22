#!/usr/bin/env python3
"""
AI Agent Checklist Integration Helper
Automatically integrates checklist management into AI agent workflows
"""

import subprocess
import sys
import os
from pathlib import Path

def run_checklist_command(args):
    """Run a checklist command and return the output."""
    mcp_dir = Path(__file__).parent / "app" / "mcp"
    cmd = ["python3", "checklist_cli.py"] + args
    
    try:
        result = subprocess.run(
            cmd, 
            cwd=mcp_dir, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running checklist command: {e.stderr}"

def show_project_status():
    """Show current project checklist status."""
    print("🔍 CHECKING NBA STATS PROJECT STATUS...")
    print("=" * 50)
    
    # Show stats
    stats_output = run_checklist_command(["stats"])
    print(stats_output)
    
    print("\n🔥 HIGH PRIORITY ITEMS:")
    print("-" * 30)
    high_priority = run_checklist_command(["list", "--high-priority"])
    print(high_priority)
    
    print("\n🚀 READY TO WORK:")
    print("-" * 20)
    ready_items = run_checklist_command(["list", "--ready"])
    print(ready_items)

def suggest_related_items(task_description):
    """Suggest checklist items related to a task description."""
    print(f"\n🎯 ANALYZING TASK: {task_description}")
    print("=" * 50)
    
    # Simple keyword matching to suggest relevant items
    keywords_to_categories = {
        'auth': 'Security & Authentication',
        'security': 'Security & Authentication', 
        'login': 'Security & Authentication',
        'jwt': 'Security & Authentication',
        'database': 'Database Optimization',
        'db': 'Database Optimization',
        'sql': 'Database Optimization',
        'api': 'API Performance & Caching',
        'endpoint': 'API Performance & Caching',
        'test': 'Testing Infrastructure',
        'testing': 'Testing Infrastructure',
        'error': 'Error Handling & Monitoring',
        'logging': 'Error Handling & Monitoring',
        'frontend': 'Frontend Architecture',
        'ui': 'User Experience Enhancements',
        'deploy': 'DevOps & Deployment',
        'production': 'Production Environment Setup',
        'prod': 'Production Environment Setup'
    }
    
    task_lower = task_description.lower()
    suggested_categories = []
    
    for keyword, category in keywords_to_categories.items():
        if keyword in task_lower:
            suggested_categories.append(category)
    
    if suggested_categories:
        print("📋 SUGGESTED CHECKLIST CATEGORIES:")
        for category in set(suggested_categories):
            print(f"\n🔸 {category}:")
            category_items = run_checklist_command(["list", "--category", category])
            print(category_items)
    else:
        print("💡 No specific category matches found. Check all ready items:")
        ready_items = run_checklist_command(["list", "--ready"])
        print(ready_items)

def ai_agent_workflow():
    """Interactive workflow for AI agents."""
    print("🤖 NBA STATS AI AGENT CHECKLIST INTEGRATION")
    print("=" * 50)
    
    # Always show current status first
    show_project_status()
    
    # Ask for task description
    print("\n" + "="*50)
    task = input("📝 What task are you working on? (or 'skip' to just see status): ")
    
    if task.lower() != 'skip':
        suggest_related_items(task)
        
        print("\n" + "="*50)
        print("🔧 RECOMMENDED ACTIONS:")
        print("1. Update relevant checklist item status to 'In Progress'")
        print("2. Use checklist ID in your commit messages")
        print("3. Add progress notes as you work")
        print("4. Mark as 'Completed' when done")
        print("5. Suggest next ready items")
        
        # Offer to update an item
        item_id = input("\n📌 Enter checklist item ID to update (or press Enter to skip): ")
        if item_id.strip():
            update_item_interactive(item_id.strip())

def update_item_interactive(item_id):
    """Interactive item update."""
    print(f"\n🔄 UPDATING ITEM: {item_id}")
    
    # Show current item details
    item_details = run_checklist_command(["get", item_id])
    print(item_details)
    
    # Get updates
    status = input("\n📊 New status (Not Started/In Progress/Completed/Blocked/On Hold): ")
    assign = input("👤 Assign to (or press Enter to skip): ")
    notes = input("📝 Add notes (or press Enter to skip): ")
    
    # Build update command
    update_args = ["update", item_id]
    if status.strip():
        update_args.extend(["--status", status.strip()])
    if assign.strip():
        update_args.extend(["--assign", assign.strip()])
    if notes.strip():
        update_args.extend(["--notes", notes.strip()])
    
    if len(update_args) > 2:  # More than just "update item_id"
        result = run_checklist_command(update_args)
        print(f"\n✅ UPDATE RESULT:\n{result}")
    else:
        print("\n⏭️  No updates provided, skipping...")

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Direct command mode
        if sys.argv[1] == "status":
            show_project_status()
        elif sys.argv[1] == "suggest" and len(sys.argv) > 2:
            task = " ".join(sys.argv[2:])
            suggest_related_items(task)
        else:
            # Pass through to checklist CLI
            args = sys.argv[1:]
            result = run_checklist_command(args)
            print(result)
    else:
        # Interactive mode
        ai_agent_workflow()

if __name__ == "__main__":
    main()
