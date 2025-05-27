from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Convert a datetime to ISO-8601 format string with UTC timezone"""
    if not dt:
        return None
    return dt.isoformat() if dt.tzinfo else dt.replace(tzinfo=timezone.utc).isoformat()


def serialize_value(value: Any) -> Any:
    """Serialize a value to JSON-compatible format"""
    if isinstance(value, datetime):
        return serialize_datetime(value)
    if isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [serialize_value(v) for v in value]
    return value


def normalize_components(components: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure component dictionary has consistent structure and all values are properly serialized"""
    if not isinstance(components, dict):
        components = {}

    for component in ["teams", "players", "games"]:
        if component not in components:
            components[component] = {}

        current = components[component]
        if not isinstance(current, dict):
            current = {}

        # Ensure required fields exist
        defaults = {
            "updated": False,
            "percent_complete": 0,
            "last_update": None,
            "last_error": None,
        }

        # Create normalized component dict with defaults and serialized values
        normalized = {}
        for key, default in defaults.items():
            value = current.get(key, default)
            normalized[key] = serialize_value(value)

        components[component] = normalized

    return components
