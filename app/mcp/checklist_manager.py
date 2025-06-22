from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import json
import re

class Priority(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM_HIGH = "Medium-High"
    MEDIUM = "Medium"
    MEDIUM_LOW = "Medium-Low"
    LOW = "Low"

class Status(Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    BLOCKED = "Blocked"
    ON_HOLD = "On Hold"

@dataclass
class ChecklistItem:
    id: str
    title: str
    priority: Priority
    status: Status
    category: str
    estimate: str
    description: Optional[str] = None
    notes: Optional[str] = None
    dependencies: Optional[List[str]] = None
    assigned_to: Optional[str] = None
    created_date: Optional[str] = None
    updated_date: Optional[str] = None
    completed_date: Optional[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.created_date is None:
            self.created_date = datetime.now().isoformat()

class ChecklistManager:
    def __init__(self, json_file_path: Optional[str] = None):
        if json_file_path is None:
            json_file_path = "/Users/olivernoonan/CopilotProjects/nba_stats/app/mcp/checklist_data.json"
        self.json_file_path = json_file_path
        self.items: Dict[str, ChecklistItem] = {}
        self._load_from_json()

    def _load_from_json(self):
        """Load checklist items from the JSON file."""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for item_id, item_data in data.items():
                item = ChecklistItem(
                    id=item_data['id'],
                    title=item_data['title'],
                    priority=Priority(item_data['priority']),
                    status=Status(item_data['status']),
                    category=item_data['category'],
                    estimate=item_data['estimate'],
                    description=item_data.get('description'),
                    notes=item_data.get('notes'),
                    dependencies=item_data.get('dependencies', []),
                    assigned_to=item_data.get('assigned_to'),
                    created_date=item_data.get('created_date'),
                    updated_date=item_data.get('updated_date'),
                    completed_date=item_data.get('completed_date')
                )
                self.items[item_id] = item
                
        except FileNotFoundError:
            print(f"Checklist JSON file not found: {self.json_file_path}")
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON file: {e}")

    def save_to_json(self):
        """Save the current state to JSON file."""
        data = {}
        for item_id, item in self.items.items():
            item_dict = asdict(item)
            # Convert enums to strings
            item_dict['priority'] = item.priority.value
            item_dict['status'] = item.status.value
            data[item_id] = item_dict
        
        try:
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving to JSON: {e}")
            return False

    def add_item(self, item: ChecklistItem) -> bool:
        """Add a new checklist item."""
        if item.id in self.items:
            return False
        
        item.created_date = datetime.now().isoformat()
        self.items[item.id] = item
        return True

    def update_item(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing checklist item."""
        if item_id not in self.items:
            return False
        
        item = self.items[item_id]
        
        # Update allowed fields
        for key, value in updates.items():
            if hasattr(item, key):
                if key == 'priority' and isinstance(value, str):
                    value = Priority(value)
                elif key == 'status' and isinstance(value, str):
                    value = Status(value)
                    if value == Status.COMPLETED and not item.completed_date:
                        item.completed_date = datetime.now().isoformat()
                
                setattr(item, key, value)
        
        item.updated_date = datetime.now().isoformat()
        
        # Auto-save to JSON
        self.save_to_json()
        return True

    def get_item(self, item_id: str) -> Optional[ChecklistItem]:
        """Get a specific checklist item."""
        return self.items.get(item_id)

    def get_items_by_status(self, status: Status) -> List[ChecklistItem]:
        """Get all items with a specific status."""
        return [item for item in self.items.values() if item.status == status]

    def get_items_by_priority(self, priority: Priority) -> List[ChecklistItem]:
        """Get all items with a specific priority."""
        return [item for item in self.items.values() if item.priority == priority]

    def get_items_by_category(self, category: str) -> List[ChecklistItem]:
        """Get all items in a specific category."""
        return [item for item in self.items.values() if item.category.lower() == category.lower()]

    def get_blocked_items(self) -> List[ChecklistItem]:
        """Get all items that are blocked by dependencies."""
        blocked = []
        for item in self.items.values():
            if item.dependencies:
                for dep_id in item.dependencies:
                    if dep_id in self.items and self.items[dep_id].status != Status.COMPLETED:
                        blocked.append(item)
                        break
        return blocked

    def get_ready_items(self) -> List[ChecklistItem]:
        """Get all items that are ready to work on (no blocking dependencies)."""
        ready = []
        for item in self.items.values():
            if item.status == Status.NOT_STARTED:
                if not item.dependencies:
                    ready.append(item)
                else:
                    # Check if all dependencies are completed
                    all_deps_completed = all(
                        dep_id in self.items and self.items[dep_id].status == Status.COMPLETED
                        for dep_id in item.dependencies
                    )
                    if all_deps_completed:
                        ready.append(item)
        return ready

    def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics about the checklist."""
        total_items = len(self.items)
        if total_items == 0:
            return {
                "total": 0,
                "completed": 0,
                "completion_percentage": 0,
                "status_counts": {},
                "priority_counts": {},
                "category_counts": {},
                "ready_to_work": 0,
                "blocked": 0
            }
        
        status_counts = {}
        priority_counts = {}
        category_counts = {}
        
        for item in self.items.values():
            # Count by status
            status_counts[item.status.value] = status_counts.get(item.status.value, 0) + 1
            
            # Count by priority
            priority_counts[item.priority.value] = priority_counts.get(item.priority.value, 0) + 1
            
            # Count by category
            category_counts[item.category] = category_counts.get(item.category, 0) + 1
        
        completed = status_counts.get(Status.COMPLETED.value, 0)
        completion_percentage = (completed / total_items) * 100 if total_items > 0 else 0
        
        return {
            "total": total_items,
            "completed": completed,
            "completion_percentage": round(completion_percentage, 1),
            "status_counts": status_counts,
            "priority_counts": priority_counts,
            "category_counts": category_counts,
            "ready_to_work": len(self.get_ready_items()),
            "blocked": len(self.get_blocked_items())
        }

    def export_to_json(self) -> str:
        """Export all checklist items to JSON."""
        items_dict = {}
        for item_id, item in self.items.items():
            item_dict = asdict(item)
            # Convert enums to strings
            item_dict['priority'] = item.priority.value
            item_dict['status'] = item.status.value
            items_dict[item_id] = item_dict
        
        return json.dumps(items_dict, indent=2)

    def save_to_markdown(self):
        """Save the current state back to the markdown file."""
        # This would regenerate the markdown file based on current state
        # Implementation would depend on desired markdown format
        pass
