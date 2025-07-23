from dataclasses import dataclass
from typing import Optional

@dataclass
class Position:
    x: float
    y: float
    z: Optional[float] = None
    label: Optional[str] = None