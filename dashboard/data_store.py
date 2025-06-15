import json
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from .models import DailyData, AppData
from .registry import registry
from pydantic import TypeAdapter

def load_data(filename: Path) -> List[DailyData]:
    """Load a list of DailyData from a JSON file using Pydantic's TypeAdapter."""
    if not filename.exists():
        return []
    with open(filename, 'r') as f:
        data = json.load(f)
    return TypeAdapter(List[DailyData]).validate_python(data)


def save_data(data: List[DailyData], filename: Path) -> None:
    """Save a list of DailyData to a JSON file using Pydantic's model_dump."""
    with open(filename, 'w') as f:
        json.dump([d.model_dump() for d in data], f, indent=2, default=str)


def update_data(old_data: List[DailyData], new_data: List[DailyData]) -> List[DailyData]:
    """Update old DailyData list with new DailyData, preserving non-None values."""
    data_by_date = {d.date: d for d in old_data}
    for new_entry in new_data:
        if new_entry.date in data_by_date:
            # Get existing entry
            existing = data_by_date[new_entry.date]
            # Update each source field if it's not None in the new entry
            for source in registry.get_sources():
                new_value = getattr(new_entry, source)
                if new_value is not None:
                    setattr(existing, source, new_value)
        else:
            # Add new entry if date doesn't exist
            data_by_date[new_entry.date] = new_entry
    return list(data_by_date.values())