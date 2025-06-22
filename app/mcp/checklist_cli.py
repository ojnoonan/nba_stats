#!/usr/bin/env python3
"""
Simple Checklist Manager CLI for NBA Stats Application Improvements
Run with: python3 checklist_cli.py [command] [args]
"""

import argparse
import json
import sys
from pathlib import Path
from checklist_manager import ChecklistManager, Priority, Status

def main():
    parser = argparse.ArgumentParser(description='NBA Stats Checklist Manager')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show checklist statistics')
    
    # Get item command
    get_parser = subparsers.add_parser('get', help='Get item details')
    get_parser.add_argument('item_id', help='Item ID (e.g., AUTH-001)')
    
    # List commands
    list_parser = subparsers.add_parser('list', help='List items by criteria')
    list_parser.add_argument('--status', choices=['Not Started', 'In Progress', 'Completed', 'Blocked', 'On Hold'])
    list_parser.add_argument('--priority', choices=['Critical', 'High', 'Medium-High', 'Medium', 'Medium-Low', 'Low'])
    list_parser.add_argument('--category', help='Category name')
    list_parser.add_argument('--ready', action='store_true', help='Show items ready to work on')
    list_parser.add_argument('--blocked', action='store_true', help='Show blocked items')
    list_parser.add_argument('--high-priority', action='store_true', help='Show high priority items')
    
    # Update commands
    update_parser = subparsers.add_parser('update', help='Update item')
    update_parser.add_argument('item_id', help='Item ID')
    update_parser.add_argument('--status', choices=['Not Started', 'In Progress', 'Completed', 'Blocked', 'On Hold'])
    update_parser.add_argument('--assign', help='Assign to person')
    update_parser.add_argument('--notes', help='Add notes')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export checklist to JSON')
    export_parser.add_argument('--output', '-o', help='Output file (default: stdout)')

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return

    # Initialize checklist manager
    try:
        checklist = ChecklistManager()
    except Exception as e:
        print(f"Error initializing checklist: {e}")
        return

    # Handle commands
    if args.command == 'stats':
        show_stats(checklist)
    elif args.command == 'get':
        show_item(checklist, args.item_id)
    elif args.command == 'list':
        list_items(checklist, args)
    elif args.command == 'update':
        update_item(checklist, args)
    elif args.command == 'export':
        export_checklist(checklist, args.output)

def show_stats(checklist):
    """Show checklist statistics."""
    stats = checklist.get_stats()
    
    print("📊 NBA Stats App Improvement Checklist Statistics")
    print("=" * 50)
    print(f"Total Items: {stats['total']}")
    print(f"Completed: {stats['completed']}")
    print(f"Completion Rate: {stats['completion_percentage']}%")
    print(f"Ready to Work: {stats['ready_to_work']}")
    print(f"Blocked: {stats['blocked']}")
    print()
    
    print("By Status:")
    for status, count in stats['status_counts'].items():
        print(f"  • {status}: {count}")
    print()
    
    print("By Priority:")
    for priority, count in stats['priority_counts'].items():
        print(f"  • {priority}: {count}")
    print()
    
    print("By Category:")
    for category, count in stats['category_counts'].items():
        print(f"  • {category}: {count}")

def show_item(checklist, item_id):
    """Show details of a specific item."""
    item = checklist.get_item(item_id)
    if not item:
        print(f"❌ Item '{item_id}' not found")
        return
    
    print(f"📋 {item.id}: {item.title}")
    print("=" * 50)
    print(f"Status: {item.status.value}")
    print(f"Priority: {item.priority.value}")
    print(f"Category: {item.category}")
    print(f"Estimate: {item.estimate}")
    print(f"Assigned to: {item.assigned_to or 'Unassigned'}")
    print(f"Dependencies: {', '.join(item.dependencies) if item.dependencies else 'None'}")
    print(f"Notes: {item.notes or 'None'}")
    print(f"Created: {item.created_date}")
    print(f"Updated: {item.updated_date or 'Never'}")

def list_items(checklist, args):
    """List items based on criteria."""
    items = []
    title = ""
    
    if args.status:
        items = checklist.get_items_by_status(Status(args.status))
        title = f"Items with status '{args.status}'"
    elif args.priority:
        items = checklist.get_items_by_priority(Priority(args.priority))
        title = f"{args.priority} priority items"
    elif args.category:
        items = checklist.get_items_by_category(args.category)
        title = f"Items in '{args.category}'"
    elif args.ready:
        items = checklist.get_ready_items()
        title = "Items ready to work on"
    elif args.blocked:
        items = checklist.get_blocked_items()
        title = "Blocked items"
    elif args.high_priority:
        critical_items = checklist.get_items_by_priority(Priority.CRITICAL)
        high_items = checklist.get_items_by_priority(Priority.HIGH)
        items = [item for item in critical_items + high_items if item.status != Status.COMPLETED]
        title = "High priority items needing attention"
    
    if not items:
        print(f"No items found for criteria")
        return
    
    print(f"📝 {title} ({len(items)} items):")
    print("=" * 50)
    
    for item in sorted(items, key=lambda x: x.id):
        status_icon = get_status_icon(item.status)
        priority_icon = get_priority_icon(item.priority)
        assigned = f" [{item.assigned_to}]" if item.assigned_to else ""
        print(f"{status_icon}{priority_icon} {item.id}: {item.title}{assigned}")

def update_item(checklist, args):
    """Update an item."""
    updates = {}
    
    if args.status:
        updates['status'] = args.status
    if args.assign:
        updates['assigned_to'] = args.assign
    if args.notes:
        updates['notes'] = args.notes
    
    if not updates:
        print("No updates specified")
        return
    
    success = checklist.update_item(args.item_id, updates)
    if success:
        print(f"✅ Updated {args.item_id}")
        if args.status:
            print(f"  Status: {args.status}")
        if args.assign:
            print(f"  Assigned to: {args.assign}")
        if args.notes:
            print(f"  Notes: {args.notes}")
    else:
        print(f"❌ Failed to update item '{args.item_id}'")

def export_checklist(checklist, output_file):
    """Export checklist to JSON."""
    json_data = checklist.export_to_json()
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(json_data)
        print(f"✅ Exported checklist to {output_file}")
    else:
        print(json_data)

def get_status_icon(status):
    """Get icon for status."""
    icons = {
        Status.NOT_STARTED: "⭕",
        Status.IN_PROGRESS: "🔄",
        Status.COMPLETED: "✅",
        Status.BLOCKED: "🚫",
        Status.ON_HOLD: "⏸️"
    }
    return icons.get(status, "❓")

def get_priority_icon(priority):
    """Get icon for priority."""
    icons = {
        Priority.CRITICAL: "🔥",
        Priority.HIGH: "🔴",
        Priority.MEDIUM_HIGH: "🟠",
        Priority.MEDIUM: "🟡",
        Priority.MEDIUM_LOW: "🟢",
        Priority.LOW: "🔵"
    }
    return icons.get(priority, "❓")

if __name__ == "__main__":
    main()
