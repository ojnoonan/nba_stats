#!/usr/bin/env python3
"""
Generate AI Agent Prompt with Current Checklist Status
Creates a ready-to-use prompt that includes current project status
"""

import subprocess
import sys
from pathlib import Path

def get_checklist_status():
    """Get current checklist status."""
    try:
        result = subprocess.run(
            ["python3", "app/mcp/checklist_cli.py", "stats"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except Exception as e:
        return f"Error getting status: {e}"

def get_ready_items():
    """Get items ready to work on."""
    try:
        result = subprocess.run(
            ["python3", "app/mcp/checklist_cli.py", "list", "--ready"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except Exception as e:
        return f"Error getting ready items: {e}"

def get_high_priority_items():
    """Get high priority items."""
    try:
        result = subprocess.run(
            ["python3", "app/mcp/checklist_cli.py", "list", "--high-priority"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except Exception as e:
        return f"Error getting high priority items: {e}"

def generate_prompt():
    """Generate a current status-based prompt for AI agents."""
    
    print("🤖 GENERATING AI AGENT PROMPT FOR NBA STATS PROJECT")
    print("=" * 60)
    
    # Get current status
    status = get_checklist_status()
    ready_items = get_ready_items()
    high_priority = get_high_priority_items()
    
    # Generate the prompt
    prompt = f"""
You are working on the NBA Stats application project. This project uses a systematic improvement checklist.

**CURRENT PROJECT STATUS:**
{status}

**READY TO WORK ON:**
{ready_items}

**HIGH PRIORITY ITEMS:**
{high_priority}

**YOUR TASK:**
1. ✅ Review the status above - this is the current state of the project
2. ✅ Choose ONE item from the "Ready to Work" list, prioritizing Critical/High priority items
3. ✅ Update the item status BEFORE starting work:
   ```bash
   python3 app/mcp/checklist_cli.py update [ITEM-ID] --status "In Progress" --assign "AI Agent"
   ```
4. ✅ Implement the improvement following best practices
5. ✅ Reference the checklist item ID in ALL commits (e.g., "AUTH-001: Added JWT middleware")
6. ✅ Add progress notes during work:
   ```bash
   python3 app/mcp/checklist_cli.py update [ITEM-ID] --notes "Your progress update"
   ```
7. ✅ Mark as completed when done:
   ```bash
   python3 app/mcp/checklist_cli.py update [ITEM-ID] --status "Completed"
   ```
8. ✅ Run final status check and suggest next items to work on

**IMPORTANT REMINDERS:**
- Focus on Critical (🔥) and High (🔴) priority items first
- Only work on items that show as "Ready to Work" (no blocking dependencies)
- Always update the checklist before, during, and after your work
- Include checklist item IDs in commit messages for traceability

Choose your item and begin the systematic improvement process!
"""

    return prompt

def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--copy":
        # Generate prompt and copy to clipboard (if available)
        prompt = generate_prompt()
        try:
            subprocess.run(["pbcopy"], input=prompt, text=True, check=True)
            print("✅ Prompt copied to clipboard!")
        except:
            print("📋 Prompt generated (clipboard not available):")
            print(prompt)
    else:
        # Just print the prompt
        prompt = generate_prompt()
        print("📋 READY-TO-USE AI AGENT PROMPT:")
        print("=" * 60)
        print(prompt)
        print("=" * 60)
        print("\n💡 Use --copy flag to copy to clipboard")

if __name__ == "__main__":
    main()
