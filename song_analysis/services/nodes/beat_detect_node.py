from pathlib import Path
from typing import Dict, Any
from services.audio.essentia_analysis import extract_with_essentia
from models.song_metadata import ensure_json_serializable
import json

def log_node_output(node_name: str, data: dict):
    """
    Log the output of a node to a JSON file.
    
    Args:
        node_name: The name of the node
        data: The data to log
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Ensure data is JSON serializable
    data = ensure_json_serializable(data)
    
    with open(log_dir / f"{node_name}.json", "w") as f:
        json.dump(data, f, indent=2)

def beat_detect_node(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect beats and extract basic audio features using Essentia.
    
    Args:
        inputs: Dictionary containing mp3_path and stems
        
    Returns:
        Dictionary with beat timestamps and audio features
    """
    mp3_path = inputs["mp3_path"]
    stems = inputs.get("stems", {})
    
    # Use the drums stem if available, otherwise use the full track
    audio_path = stems.get("drums") if "drums" in stems else mp3_path
    
    # Extract beats and audio features using Essentia
    essentia_results = extract_with_essentia(audio_path)
    
    output = {
        "mp3_path": mp3_path,
        "stems": inputs.get("stems", {}),
        "stems_folder": inputs.get("stems_folder", ""),
        "beats": essentia_results["beats"],
        "bpm": essentia_results["bpm"],
        "song_duration": essentia_results["song_duration"],
        "volume_profile": essentia_results.get("volume_profile", [])
    }
    
    log_node_output("beat_detect", output)
    return output
