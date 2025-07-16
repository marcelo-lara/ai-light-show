"""Re-export song metadata models from the shared module."""

# This file is a compatibility layer to allow existing code to continue working
# with the same import paths, but now using the shared implementation.

from shared.models.song_metadata import (
    SongMetadata,
    KeyMoment,
    Section,
    Segment,
    Cluster,
    ensure_json_serializable
)

__all__ = [
    "SongMetadata",
    "KeyMoment",
    "Section",
    "Segment",
    "Cluster",
    "ensure_json_serializable"
]
