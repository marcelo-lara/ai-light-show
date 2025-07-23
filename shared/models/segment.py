"""Segment model for the AI Light Show system."""

from typing import Dict, Any


class Segment:
    """Represents a segment within a song cluster."""
    
    def __init__(self, start: float, end: float, segment_id: str = ''):
        self.segment_id = segment_id
        self.start = start
        self.end = end

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": float(self.start),
            "end": float(self.end),
            "cluster": self.segment_id,
        }

    def __str__(self) -> str:
        return f"Segment(start={self.start}, end={self.end}, segment_id={self.segment_id})"

    def __iter__(self):
        return iter((self.start, self.end, self.segment_id))
