"""Song metadata models for the AI Light Show system.

This module provides backward compatibility imports for the refactored models.
All classes have been split into separate files for better organization.

For new code, prefer importing directly from the individual modules:
- from shared.models.key_moment import KeyMoment
- from shared.models.light_plan_item import LightPlanItem
- from shared.models.section import Section
- from shared.models.segment import Segment
- from shared.models.cluster import Cluster
- from shared.models.song_metadata_new import SongMetadata
- from shared.models.utils import ensure_json_serializable
"""

# Backward compatibility imports
from .key_moment import KeyMoment
from .light_plan_item import LightPlanItem
from .section import Section
from .segment import Segment
from .cluster import Cluster
from .song_metadata_new import SongMetadata
from .utils import ensure_json_serializable

__all__ = [
    'KeyMoment',
    'LightPlanItem', 
    'Section',
    'Segment',
    'Cluster',
    'SongMetadata',
    'ensure_json_serializable'
]

