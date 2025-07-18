"""
A minimal implementation of the LangGraph-based pipeline for testing purposes.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# LangGraph imports
try:
    from langgraph.graph import StateGraph
except ImportError:
    print("LangGraph not installed. Please install with 'pip install langgraph'")
    StateGraph = object  # Mock class

# Logging function
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
    for key, value in list(data.items()):
        if isinstance(value, Path):
            data[key] = str(value)
    
    with open(log_dir / f"{node_name}.json", "w") as f:
        json.dump(data, f, indent=2)


# Simplified node implementations
def stem_split_node(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simplified stem split node that logs the input and simulates splitting a song into stems.
    """
    mp3_path = inputs["mp3_path"]
    print(f"Splitting stems for {mp3_path}")
    
    # In a real implementation, this would call the Demucs library
    stems = {
        "vocals": f"{mp3_path}_vocals.wav",
        "drums": f"{mp3_path}_drums.wav",
        "bass": f"{mp3_path}_bass.wav",
        "other": f"{mp3_path}_other.wav"
    }
    
    output = {
        "mp3_path": mp3_path,
        "stems": stems,
        "stems_folder": str(Path(mp3_path).parent / "temp")
    }
    
    log_node_output("stem_split", output)
    return output


def beat_detect_node(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simplified beat detection node that logs the input and simulates detecting beats.
    """
    mp3_path = inputs["mp3_path"]
    print(f"Detecting beats for {mp3_path}")
    
    # In a real implementation, this would use Essentia
    beats = [i for i in range(0, 200, 1)]  # Simulate beats every 1 second
    
    output = {
        "mp3_path": mp3_path,
        "stems": inputs.get("stems", {}),
        "stems_folder": inputs.get("stems_folder", ""),
        "beats": beats,
        "bpm": 120,
        "song_duration": 200
    }
    
    log_node_output("beat_detect", output)
    return output


def pattern_analysis_node(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simplified pattern analysis node that logs the input and simulates pattern detection.
    """
    mp3_path = inputs["mp3_path"]
    print(f"Analyzing patterns for {mp3_path}")
    
    # In a real implementation, this would analyze the audio and identify patterns
    segments = [
        {"start": 0, "end": 20, "label": 1},
        {"start": 20, "end": 60, "label": 2},
        {"start": 60, "end": 80, "label": 3},
        {"start": 80, "end": 120, "label": 2},
        {"start": 120, "end": 140, "label": 3},
        {"start": 140, "end": 180, "label": 4},
        {"start": 180, "end": 200, "label": 5}
    ]
    
    output = {
        "mp3_path": mp3_path,
        "stems": inputs.get("stems", {}),
        "beats": inputs.get("beats", []),
        "bpm": inputs.get("bpm", 120),
        "segments": segments
    }
    
    log_node_output("pattern_analysis", output)
    return output


def segment_labeler_node(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simplified segment labeler node that logs the input and simulates segment labeling.
    """
    mp3_path = inputs["mp3_path"]
    segments = inputs.get("segments", [])
    print(f"Labeling segments for {mp3_path}")
    
    # In a real implementation, this would use an LLM to label segments
    labeled_segments = []
    section_types = ["Intro", "Verse", "Chorus", "Bridge", "Drop", "Outro"]
    
    for i, segment in enumerate(segments):
        section_index = min(i, len(section_types) - 1)
        labeled_segments.append({
            "segment_number": i+1,
            "name": section_types[section_index],
            "start": segment["start"],
            "end": segment["end"]
        })
    
    output = {
        "mp3_path": mp3_path,
        "bpm": inputs.get("bpm", 120),
        "segments": segments,
        "labeled_segments": labeled_segments
    }
    
    log_node_output("segment_labeler", output)
    return output


def lighting_hint_generator_node(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simplified lighting hint generator node that logs the input and simulates lighting hint generation.
    """
    mp3_path = inputs["mp3_path"]
    labeled_segments = inputs.get("labeled_segments", [])
    print(f"Generating lighting hints for {mp3_path}")
    
    # In a real implementation, this would use an LLM to generate lighting hints
    lighting_hints = []
    
    hint_templates = {
        "Intro": "Start with soft blue washes that gradually build in intensity",
        "Verse": "Use focused white spots with occasional color accents on beat",
        "Chorus": "Bright, colorful patterns that pulse with the beat, alternating between warm and cool tones",
        "Bridge": "Dramatic contrast with deep purples and slow color shifts",
        "Drop": "Intense strobes and rapid color shifts between red and blue",
        "Outro": "Gradually fade intensity, using cool colors that slowly reduce to a single spotlight"
    }
    
    for segment in labeled_segments:
        lighting_hints.append({
            "section_name": segment["name"],
            "start": segment["start"],
            "end": segment["end"],
            "suggestion": hint_templates.get(segment["name"], f"Default lighting for {segment['name']}")
        })
    
    output = {
        "mp3_path": mp3_path,
        "bpm": inputs.get("bpm", 120),
        "labeled_segments": labeled_segments,
        "lighting_hints": lighting_hints
    }
    
    # Create the final output that includes all the key information
    final_output = {
        "sections": labeled_segments,
        "lighting_hints": lighting_hints
    }
    
    log_node_output("lighting_hint_generator", output)
    log_node_output("final_output", final_output)
    
    return output


def create_pipeline() -> StateGraph:
    """
    Create a simple LangGraph pipeline for demonstration purposes.
    """
    try:
        # Create the graph
        builder = StateGraph()
        
        # Add nodes
        builder.add_node("stem_split", stem_split_node)
        builder.add_node("beat_detect", beat_detect_node)
        builder.add_node("pattern_analysis", pattern_analysis_node)
        builder.add_node("segment_labeler", segment_labeler_node)
        builder.add_node("lighting_hint_generator", lighting_hint_generator_node)
        
        # Connect nodes in sequence
        builder.add_edge("stem_split", "beat_detect")
        builder.add_edge("beat_detect", "pattern_analysis")
        builder.add_edge("pattern_analysis", "segment_labeler")
        builder.add_edge("segment_labeler", "lighting_hint_generator")
        
        # Set the entry point
        builder.set_entry_point("stem_split")
        
        # Compile the graph
        return builder.compile()
    except Exception as e:
        print(f"Error creating pipeline: {str(e)}")
        # Return a dummy object that will be handled in run_pipeline
        return None


def run_pipeline(mp3_path: str) -> Dict[str, Any]:
    """
    Run the pipeline in sequence, even if LangGraph is not available.
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    print(f"Running pipeline on {mp3_path}")
    
    # Try to use LangGraph if available
    pipeline = create_pipeline()
    
    if pipeline is not None:
        # Use LangGraph pipeline
        initial_state = {"mp3_path": mp3_path}
        
        result = None
        try:
            for event in pipeline.stream(initial_state):
                if event["type"] == "node":
                    node_name = event["node"]
                    print(f"Running node (LangGraph): {node_name}")
                elif event["type"] == "end":
                    result = event["state"]
        except Exception as e:
            print(f"Error running LangGraph pipeline: {str(e)}")
    else:
        # Fall back to sequential execution
        print("Falling back to sequential execution")
        state = {"mp3_path": mp3_path}
        state = stem_split_node(state)
        state = beat_detect_node(state)
        state = pattern_analysis_node(state)
        state = segment_labeler_node(state)
        state = lighting_hint_generator_node(state)
        result = state
    
    # Extract the final output
    log_path = log_dir / "final_output.json"
    if log_path.exists():
        with open(log_path, "r") as f:
            try:
                final_output = json.load(f)
            except json.JSONDecodeError:
                print("Error decoding final output JSON, using fallback")
                final_output = {
                    "sections": [] if result is None else result.get("labeled_segments", []),
                    "lighting_hints": [] if result is None else result.get("lighting_hints", [])
                }
    else:
        final_output = {
            "sections": [] if result is None else result.get("labeled_segments", []),
            "lighting_hints": [] if result is None else result.get("lighting_hints", [])
        }
    
    return final_output
