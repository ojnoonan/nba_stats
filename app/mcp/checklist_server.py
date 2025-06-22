import asyncio
import json
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
import logging

from checklist_manager import ChecklistManager, ChecklistItem, Priority, Status

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the server
app = Server("nba-checklist-manager")

# Initialize checklist manager
checklist_manager = ChecklistManager()

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools for checklist management."""
    return [
        Tool(
            name="get_checklist_stats",
            description="Get overall statistics about the improvement checklist",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_item_by_id",
            description="Get details of a specific checklist item by its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "string",
                        "description": "The ID of the checklist item (e.g., 'AUTH-001')"
                    }
                },
                "required": ["item_id"]
            }
        ),
        Tool(
            name="get_items_by_status",
            description="Get all checklist items with a specific status",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["Not Started", "In Progress", "Completed", "Blocked", "On Hold"],
                        "description": "The status to filter by"
                    }
                },
                "required": ["status"]
            }
        ),
        Tool(
            name="get_items_by_priority",
            description="Get all checklist items with a specific priority",
            inputSchema={
                "type": "object",
                "properties": {
                    "priority": {
                        "type": "string",
                        "enum": ["Critical", "High", "Medium-High", "Medium", "Medium-Low", "Low"],
                        "description": "The priority level to filter by"
                    }
                },
                "required": ["priority"]
            }
        ),
        Tool(
            name="get_items_by_category",
            description="Get all checklist items in a specific category",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "The category name (e.g., 'Security & Authentication', 'Database Optimization')"
                    }
                },
                "required": ["category"]
            }
        ),
        Tool(
            name="update_item_status",
            description="Update the status of a checklist item",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "string",
                        "description": "The ID of the checklist item"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["Not Started", "In Progress", "Completed", "Blocked", "On Hold"],
                        "description": "The new status"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes about the status change"
                    }
                },
                "required": ["item_id", "status"]
            }
        ),
        Tool(
            name="assign_item",
            description="Assign a checklist item to someone",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "string",
                        "description": "The ID of the checklist item"
                    },
                    "assigned_to": {
                        "type": "string",
                        "description": "The person to assign the item to"
                    }
                },
                "required": ["item_id", "assigned_to"]
            }
        ),
        Tool(
            name="get_ready_items",
            description="Get all items that are ready to work on (no blocking dependencies)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_blocked_items",
            description="Get all items that are blocked by dependencies",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_high_priority_items",
            description="Get all high priority (Critical/High) items that need attention",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="add_notes",
            description="Add or update notes for a checklist item",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "string",
                        "description": "The ID of the checklist item"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Notes to add or update"
                    }
                },
                "required": ["item_id", "notes"]
            }
        ),
        Tool(
            name="export_checklist",
            description="Export the entire checklist to JSON format",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls for checklist management."""
    
    if name == "get_checklist_stats":
        stats = checklist_manager.get_stats()
        return [TextContent(
            type="text",
            text=f"📊 **NBA Stats App Improvement Checklist Statistics**\n\n"
                 f"**Total Items:** {stats['total']}\n"
                 f"**Completed:** {stats['completed']}\n"
                 f"**Completion Rate:** {stats['completion_percentage']}%\n"
                 f"**Ready to Work:** {stats['ready_to_work']}\n"
                 f"**Blocked:** {stats['blocked']}\n\n"
                 f"**By Status:**\n" + 
                 "\n".join([f"  • {status}: {count}" for status, count in stats['status_counts'].items()]) +
                 f"\n\n**By Priority:**\n" +
                 "\n".join([f"  • {priority}: {count}" for priority, count in stats['priority_counts'].items()])
        )]
    
    elif name == "get_item_by_id":
        item_id = arguments["item_id"]
        item = checklist_manager.get_item(item_id)
        if not item:
            return [TextContent(type="text", text=f"❌ Item '{item_id}' not found")]
        
        deps_text = ", ".join(item.dependencies) if item.dependencies else "None"
        assigned_text = item.assigned_to if item.assigned_to else "Unassigned"
        
        return [TextContent(
            type="text",
            text=f"📋 **{item.id}: {item.title}**\n\n"
                 f"**Status:** {item.status.value}\n"
                 f"**Priority:** {item.priority.value}\n"
                 f"**Category:** {item.category}\n"
                 f"**Estimate:** {item.estimate}\n"
                 f"**Assigned to:** {assigned_text}\n"
                 f"**Dependencies:** {deps_text}\n"
                 f"**Notes:** {item.notes or 'None'}\n"
                 f"**Created:** {item.created_date}\n"
                 f"**Updated:** {item.updated_date or 'Never'}"
        )]
    
    elif name == "get_items_by_status":
        status = Status(arguments["status"])
        items = checklist_manager.get_items_by_status(status)
        
        if not items:
            return [TextContent(type="text", text=f"No items found with status '{status.value}'")]
        
        items_text = "\n".join([
            f"• **{item.id}**: {item.title} ({item.priority.value})"
            for item in sorted(items, key=lambda x: x.priority.value)
        ])
        
        return [TextContent(
            type="text",
            text=f"📝 **Items with status '{status.value}' ({len(items)} items):**\n\n{items_text}"
        )]
    
    elif name == "get_items_by_priority":
        priority = Priority(arguments["priority"])
        items = checklist_manager.get_items_by_priority(priority)
        
        if not items:
            return [TextContent(type="text", text=f"No items found with priority '{priority.value}'")]
        
        items_text = "\n".join([
            f"• **{item.id}**: {item.title} ({item.status.value})"
            for item in sorted(items, key=lambda x: x.id)
        ])
        
        return [TextContent(
            type="text",
            text=f"🔥 **{priority.value} Priority Items ({len(items)} items):**\n\n{items_text}"
        )]
    
    elif name == "get_items_by_category":
        category = arguments["category"]
        items = checklist_manager.get_items_by_category(category)
        
        if not items:
            return [TextContent(type="text", text=f"No items found in category '{category}'")]
        
        items_text = "\n".join([
            f"• **{item.id}**: {item.title} ({item.status.value}, {item.priority.value})"
            for item in sorted(items, key=lambda x: x.id)
        ])
        
        return [TextContent(
            type="text",
            text=f"📂 **Items in '{category}' ({len(items)} items):**\n\n{items_text}"
        )]
    
    elif name == "update_item_status":
        item_id = arguments["item_id"]
        new_status = arguments["status"]
        notes = arguments.get("notes")
        
        updates = {"status": new_status}
        if notes:
            updates["notes"] = notes
        
        success = checklist_manager.update_item(item_id, updates)
        if success:
            return [TextContent(
                type="text",
                text=f"✅ Updated {item_id} status to '{new_status}'" + 
                     (f" with notes: {notes}" if notes else "")
            )]
        else:
            return [TextContent(type="text", text=f"❌ Failed to update item '{item_id}'")]
    
    elif name == "assign_item":
        item_id = arguments["item_id"]
        assigned_to = arguments["assigned_to"]
        
        success = checklist_manager.update_item(item_id, {"assigned_to": assigned_to})
        if success:
            return [TextContent(
                type="text",
                text=f"👤 Assigned {item_id} to {assigned_to}"
            )]
        else:
            return [TextContent(type="text", text=f"❌ Failed to assign item '{item_id}'")]
    
    elif name == "get_ready_items":
        items = checklist_manager.get_ready_items()
        
        if not items:
            return [TextContent(type="text", text="No items are ready to work on")]
        
        # Sort by priority
        priority_order = [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM_HIGH, Priority.MEDIUM, Priority.MEDIUM_LOW, Priority.LOW]
        items_sorted = sorted(items, key=lambda x: priority_order.index(x.priority))
        
        items_text = "\n".join([
            f"• **{item.id}**: {item.title} ({item.priority.value})"
            for item in items_sorted
        ])
        
        return [TextContent(
            type="text",
            text=f"🚀 **Ready to Work ({len(items)} items):**\n\n{items_text}"
        )]
    
    elif name == "get_blocked_items":
        items = checklist_manager.get_blocked_items()
        
        if not items:
            return [TextContent(type="text", text="No items are currently blocked")]
        
        items_text = "\n".join([
            f"• **{item.id}**: {item.title} (depends on: {', '.join(item.dependencies or [])})"
            for item in items
        ])
        
        return [TextContent(
            type="text",
            text=f"🚫 **Blocked Items ({len(items)} items):**\n\n{items_text}"
        )]
    
    elif name == "get_high_priority_items":
        critical_items = checklist_manager.get_items_by_priority(Priority.CRITICAL)
        high_items = checklist_manager.get_items_by_priority(Priority.HIGH)
        
        all_high_priority = critical_items + high_items
        incomplete_items = [item for item in all_high_priority if item.status != Status.COMPLETED]
        
        if not incomplete_items:
            return [TextContent(type="text", text="🎉 All high priority items are completed!")]
        
        items_text = "\n".join([
            f"• **{item.id}**: {item.title} ({item.priority.value}, {item.status.value})"
            for item in sorted(incomplete_items, key=lambda x: (x.priority.value, x.id))
        ])
        
        return [TextContent(
            type="text",
            text=f"⚠️ **High Priority Items Needing Attention ({len(incomplete_items)} items):**\n\n{items_text}"
        )]
    
    elif name == "add_notes":
        item_id = arguments["item_id"]
        notes = arguments["notes"]
        
        success = checklist_manager.update_item(item_id, {"notes": notes})
        if success:
            return [TextContent(
                type="text",
                text=f"📝 Added notes to {item_id}: {notes}"
            )]
        else:
            return [TextContent(type="text", text=f"❌ Failed to add notes to item '{item_id}'")]
    
    elif name == "export_checklist":
        json_data = checklist_manager.export_to_json()
        return [TextContent(
            type="text",
            text=f"📄 **Checklist Export (JSON):**\n\n```json\n{json_data}\n```"
        )]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

if __name__ == "__main__":
    import mcp.server.stdio
    mcp.server.stdio.run_server(app)
