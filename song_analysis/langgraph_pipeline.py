"""
LangGraph-based audio analysis pipeline.

This module implements a modular, step-by-step pipeline for audio analysis
using LangGraph. It enables easier debugging, customization, and reasoning
over each analysis step.

The pipeline includes:
1. Stem splitting (using Demucs)
2. Beat detection (using Essentia)
3. Pattern analysis
4. Segment labeling (using LLMs)
5. Lighting hint generation (using LLMs)
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# LangGraph imports
from langgraph.graph import StateGraph
from langgraph.schema import Schema

# Service imports
from services.audio.demucs_split import extract_stems
from services.audio.essentia_analysis import extract_with_essentia
from services.audio.pattern_finder import get_stem_clusters
from models.song_metadata import SongMetadata, ensure_json_serializable

# Define a state schema for the pipeline
state_schema = Schema({
    "mp3_path": str,
    "stems": dict,
    "beats": list,
    "bpm": int,
    "segments": list,
    "labeled_segments": list,
    "lighting_hints": list
})


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


def create_pipeline() -> StateGraph:
    """
    Create the LangGraph pipeline for audio analysis.
    
    Returns:
        StateGraph: The configured pipeline
    """
    # Create the graph with the state schema
    builder = StateGraph(state_schema=state_schema)
    
    # Add nodes
    from .services.nodes.extract_stems import stem_split_node
    from .services.nodes.beat_detect_node import beat_detect_node
    from .services.nodes.pattern_analysis_node import pattern_analysis_node
    from .services.nodes.segment_labeler_node import segment_labeler_node
    from .services.nodes.lighting_hint_generator_node import lighting_hint_generator_node

    def wrap_node(node_function):
        return lambda state: node_function(state)

    builder.add_node("stem_split", wrap_node(stem_split_node))
    builder.add_node("beat_detect", wrap_node(beat_detect_node))
    builder.add_node("pattern_analysis", wrap_node(pattern_analysis_node))
    builder.add_node("segment_labeler", wrap_node(segment_labeler_node))
    builder.add_node("lighting_hint_generator", wrap_node(lighting_hint_generator_node))
    
    # Connect nodes in sequence
    builder.add_edge("stem_split", "beat_detect")
    builder.add_edge("beat_detect", "pattern_analysis")
    builder.add_edge("pattern_analysis", "segment_labeler")
    builder.add_edge("segment_labeler", "lighting_hint_generator")
    
    # Set the entry point
    builder.set_entry_point("stem_split")
    
    # Compile the graph
    return builder.compile()


def run_pipeline(mp3_path: str) -> Dict[str, Any]:
    """
    Run the audio analysis pipeline on a song file.
    
    Args:
        mp3_path: Path to the MP3 file to analyze
        
    Returns:
        Dictionary with analysis results
    """
    # Create the pipeline
    pipeline = create_pipeline()
    
    # Set up the initial state
    state = {"mp3_path": mp3_path}
    
    # Execute the pipeline manually
    node_functions = {
        "stem_split": stem_split_node,
        "beat_detect": beat_detect_node,
        # "pattern_analysis": pattern_analysis_node,
        # "segment_labeler": segment_labeler_node,
        # "lighting_hint_generator": lighting_hint_generator_node
    }

    for node_name in node_functions.keys():
        node_function = node_functions[node_name]
        state = node_function(state)
    
    # Extract the final output
    log_path = Path("logs") / "final_output.json"
    if log_path.exists():
        with open(log_path, "r") as f:
            final_output = json.load(f)
    else:
        final_output = {
            "sections": [] if state is None else state.get("labeled_segments", []),
            "lighting_hints": [] if state is None else state.get("lighting_hints", [])
        }
    
    return final_output
