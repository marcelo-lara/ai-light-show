"""
Chaser utilities for the AI Light Show backend.

Provides functionality for loading and expanding chaser templates
with proper type hints and improved error handling.
"""

import json
from typing import List, Dict, Any, Optional
from .config import CHASER_TEMPLATE_PATH
from .core.time_utils import beats_to_seconds
from .core.exceptions import ConfigurationError
from .types import ChaserTemplate, LightingCue

# Global cache for chaser templates
_chasers: Optional[List[ChaserTemplate]] = None


def get_chasers() -> List[ChaserTemplate]:
    """
    Get the list of chaser templates, loading from file if needed.
    
    Returns:
        List of chaser template configurations
        
    Raises:
        ConfigurationError: If chaser templates cannot be loaded
    """
    global _chasers
    if _chasers is None:
        _chasers = load_chaser_templates()
    return _chasers


def load_chaser_templates() -> List[ChaserTemplate]:
    """
    Load chaser templates from the JSON configuration file.
    
    Returns:
        List of chaser template configurations
        
    Raises:
        ConfigurationError: If file cannot be read or parsed
    """
    global _chasers
    
    try:
        with open(CHASER_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Validate that we got a list
        if not isinstance(data, list):
            raise ConfigurationError(f"Chaser templates file should contain a list, got {type(data)}")
            
        _chasers = data
        print(f"✅ Loaded {len(_chasers)} chaser templates from {CHASER_TEMPLATE_PATH}")
        return _chasers
        
    except FileNotFoundError:
        raise ConfigurationError(f"Chaser templates file not found: {CHASER_TEMPLATE_PATH}")
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON in chaser templates file: {e}")
    except Exception as e:
        raise ConfigurationError(f"Failed to load chaser templates: {e}")


def find_chaser_template(chaser_name: str) -> Optional[ChaserTemplate]:
    """
    Find a chaser template by name.
    
    Args:
        chaser_name: Name of the chaser template to find
        
    Returns:
        Chaser template if found, None otherwise
    """
    chasers = get_chasers()
    return next((c for c in chasers if c.get("name") == chaser_name), None)


def expand_chaser_template(
    chaser_name: str, 
    start_time: float, 
    bpm: float,
    fixture_ids: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Expand a chaser template into a list of lighting cues.
    
    Args:
        chaser_name: Name of the chaser template
        start_time: Start time in seconds
        bpm: Beats per minute for timing calculations
        fixture_ids: Optional override for fixture IDs (uses template default if None)
        
    Returns:
        List of expanded cue dictionaries
        
    Raises:
        ConfigurationError: If chaser template is not found or invalid
    """
    chaser = find_chaser_template(chaser_name)
    if not chaser:
        raise ConfigurationError(f"Chaser template '{chaser_name}' not found")

    # Extract chaser configuration
    preset = chaser.get("preset")
    if not preset:
        raise ConfigurationError(f"Chaser '{chaser_name}' missing required 'preset' field")
        
    # Use provided fixture_ids or fall back to template default
    target_fixtures = fixture_ids or chaser.get("fixture_ids", [])
    if not target_fixtures:
        raise ConfigurationError(f"Chaser '{chaser_name}' has no fixture IDs specified")
        
    parameters = chaser.get("parameters", {})
    spacing_beats = parameters.get("beat_spacing", 0.25)
    
    # Generate cues for each fixture
    cues = []
    for i, fixture_id in enumerate(target_fixtures):
        cue_time = round(start_time + beats_to_seconds(i * spacing_beats, bpm), 4)
        
        cue = {
            "time": cue_time,
            "fixture": fixture_id,
            "preset": preset,
            "parameters": {k: v for k, v in parameters.items() if k != "beat_spacing"},
            "chaser": chaser_name,
            "sequence_index": i
        }
        cues.append(cue)

    print(f"✅ Expanded chaser '{chaser_name}' into {len(cues)} cues starting at {start_time}s")
    return cues


def get_chaser_duration(chaser_name: str, bpm: float) -> float:
    """
    Calculate the total duration of a chaser template.
    
    Args:
        chaser_name: Name of the chaser template
        bpm: Beats per minute for timing calculations
        
    Returns:
        Duration in seconds
        
    Raises:
        ConfigurationError: If chaser template is not found
    """
    chaser = find_chaser_template(chaser_name)
    if not chaser:
        raise ConfigurationError(f"Chaser template '{chaser_name}' not found")
        
    fixture_ids = chaser.get("fixture_ids", [])
    parameters = chaser.get("parameters", {})
    spacing_beats = parameters.get("beat_spacing", 0.25)
    
    if not fixture_ids:
        return 0.0
        
    # Duration is the time to the last fixture plus any effect duration
    last_fixture_time = beats_to_seconds((len(fixture_ids) - 1) * spacing_beats, bpm)
    effect_duration = beats_to_seconds(parameters.get("duration_beats", 1.0), bpm)
    
    return last_fixture_time + effect_duration


def validate_chaser_template(chaser: Dict[str, Any]) -> bool:
    """
    Validate a chaser template configuration.
    
    Args:
        chaser: Chaser template dictionary
        
    Returns:
        True if valid
        
    Raises:
        ConfigurationError: If template is invalid
    """
    required_fields = ["name", "preset"]
    for field in required_fields:
        if field not in chaser:
            raise ConfigurationError(f"Chaser template missing required field: {field}")
    
    # Validate fixture_ids if present
    fixture_ids = chaser.get("fixture_ids", [])
    if fixture_ids and not isinstance(fixture_ids, list):
        raise ConfigurationError("Chaser template 'fixture_ids' must be a list")
    
    # Validate parameters if present
    parameters = chaser.get("parameters", {})
    if parameters and not isinstance(parameters, dict):
        raise ConfigurationError("Chaser template 'parameters' must be a dictionary")
    
    return True


def reload_chaser_templates() -> List[ChaserTemplate]:
    """
    Force reload of chaser templates from file.
    
    Returns:
        List of reloaded chaser templates
    """
    global _chasers
    _chasers = None
    return load_chaser_templates()
