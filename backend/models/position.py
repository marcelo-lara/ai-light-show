from dataclasses import dataclass
from typing import Optional

@dataclass
class Position:
    x: float
    y: float
    z: Optional[float] = None
    label: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert the position to a dictionary."""
        return {
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'label': self.label
        }
