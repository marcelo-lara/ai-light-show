"""Section model for the AI Light Show system."""

from typing import Dict, Any


class Section:
    """Represents a section of a song (verse, chorus, bridge, etc.)."""
    
    def __init__(self, name: str, start: float, end: float, prompt: str):
        self.name = name
        self.start = start
        self.end = end
        self.prompt = prompt
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "start": float(self.start),
            "end": float(self.end),
            "prompt": self.prompt,
        }
