from typing import Dict, Any
from services.audio.pattern_finder import get_stem_clusters
from models.song_metadata import ensure_json_serializable
from pathlib import Path
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

def pattern_analysis_node(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze patterns and segments in the audio.
    
    Args:
        inputs: Dictionary containing beats and stems information
        
    Returns:
        Dictionary with pattern analysis results
    """
    mp3_path = inputs["mp3_path"]
    stems = inputs.get("stems", {})
    beats = inputs.get("beats", [])
    
    patterns = {}
    segments = []
    
    # Analyze patterns for each stem
    for stem_name, stem_path in stems.items():
        try:
            stem_clusters = get_stem_clusters(beats, stem_path)
            if stem_clusters and "clusters_timeline" in stem_clusters:
                patterns[stem_name] = stem_clusters["clusters_timeline"]
        except Exception as e:
            print(f"Error analyzing patterns for {stem_name}: {str(e)}")
    
    # Derive segments from patterns
    if patterns:
        first_stem = list(patterns.keys())[0]
        current_segment = None
        
        for cluster_item in patterns[first_stem]:
            start_time = cluster_item.get("start_time", 0)
            label = cluster_item.get("label", 0)
            
            if current_segment is None or current_segment["label"] != label:
                if current_segment:
                    current_segment["end"] = start_time
                    segments.append(current_segment)
                
                current_segment = {
                    "start": start_time,
                    "label": label,
                    "end": None
                }
        
        if current_segment:
            current_segment["end"] = inputs.get("song_duration", 0)
            segments.append(current_segment)
    
    output = {
        "mp3_path": mp3_path,
        "stems": inputs.get("stems", {}),
        "beats": inputs.get("beats", []),
        "bpm": inputs.get("bpm", 0),
        "patterns": patterns,
        "segments": segments
    }
    
    log_node_output("pattern_analysis", output)
    return output
