"""Cluster model for the AI Light Show system."""

from typing import Dict, Any, List
from .segment import Segment


class Cluster:
    """Represents a cluster of segments in a song."""
    
    def __init__(self, part: str, segments: List[Segment]):
        self.part = part
        self.segments = segments if isinstance(segments, list) else [Segment(*seg) for seg in segments]

    def __iter__(self):
        return iter(self.segments)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "part": self.part,
            "segments": [seg.to_dict() for seg in self.segments]
        }
    
    def __str__(self) -> str:
        return f"Cluster(part={self.part}, segments={self.segments})"
