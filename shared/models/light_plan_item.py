"""LightPlanItem model for the AI Light Show system."""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class LightPlanItem:
    """Represents a lighting plan to be executed at a specific time."""
    id: int
    start: float
    end: Optional[float] = None
    name: str = ''
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "start": float(self.start),
            "end": float(self.end) if self.end is not None else None,
            "name": self.name,
            "description": self.description,
        }

    def __str__(self) -> str:
        return f"LightPlanItem(id={self.id}, start={self.start}, end={self.end}, name='{self.name}', description='{self.description}')"
