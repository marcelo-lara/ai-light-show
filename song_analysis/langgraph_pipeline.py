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
from langgraph.prebuilt import ToolNode

# Service imports
from services.audio.demucs_split import extract_stems
from services.audio.essentia_analysis import extract_with_essentia
from services.audio.pattern_finder import get_stem_clusters
from models.song_metadata import SongMetadata, ensure_json_serializable

# Import Ollama client for LLM interactions
from backend.services.ollama.ollama_api import query_ollama


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


def stem_split_node(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Split an audio file into stems using Demucs.
    
    Args:
        inputs: Dictionary containing mp3_path
        
    Returns:
        Dictionary with stem paths
    """
    mp3_path = inputs["mp3_path"]
    song_name = Path(mp3_path).stem
    temp_folder = str(Path(mp3_path).parent / "temp")
    
    # Extract stems using Demucs
    stems_result = extract_stems(
        input_file=mp3_path,
        songs_temp_folder=temp_folder,
        song_prefix=song_name
    )
    
    output = {
        "mp3_path": mp3_path,
        "stems": stems_result["stems"],
        "stems_folder": stems_result["output_folder"]
    }
    
    log_node_output("stem_split", output)
    return output


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
    # This is a simplified approach - in a real implementation,
    # you might use more sophisticated segmentation logic
    if patterns:
        # Use the first stem's patterns as a baseline for segmentation
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
                    "end": None  # Will be set in the next iteration
                }
        
        # Add the last segment
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


def segment_labeler_node(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Label segments using an LLM.
    
    Args:
        inputs: Dictionary containing segment information
        
    Returns:
        Dictionary with labeled segments
    """
    segments = inputs.get("segments", [])
    bpm = inputs.get("bpm", 0)
    song_name = Path(inputs["mp3_path"]).stem
    
    if not segments:
        labeled_segments = []
    else:
        # Prepare the prompt for the LLM
        segment_descriptions = []
        for i, segment in enumerate(segments):
            duration = segment["end"] - segment["start"]
            beats_in_segment = duration * bpm / 60
            segment_descriptions.append(
                f"Segment {i+1}: starts at {segment['start']:.2f}s, ends at {segment['end']:.2f}s, "
                f"duration: {duration:.2f}s, approximately {beats_in_segment:.1f} beats, "
                f"pattern label: {segment['label']}"
            )
        
        segments_text = "\n".join(segment_descriptions)
        
        prompt = f"""
You are an expert music producer analyzing the song "{song_name}".
Based on the following segments detected in the song, label each segment with an appropriate musical section name.

Song Information:
- BPM: {bpm}
- Total Segments: {len(segments)}

Detected Segments:
{segments_text}

Please label each segment with one of these common section types: Intro, Verse, Chorus, Bridge, Drop, Breakdown, Outro, Buildup, or any other appropriate label.

Return your answer as a JSON list of objects, each with:
1. "segment_number": the segment number from the input
2. "name": your assigned label (e.g., "Intro", "Chorus", etc.)
3. "start": the start time in seconds
4. "end": the end time in seconds

Format your response as valid JSON that I can parse programmatically.
"""
        
        # Query the LLM
        try:
            llm_response = query_ollama(prompt, model="mistral")
            
            # Extract JSON from the response
            json_start = llm_response.find("[")
            json_end = llm_response.rfind("]") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = llm_response[json_start:json_end]
                labeled_segments = json.loads(json_str)
            else:
                # Fallback if JSON parsing fails
                labeled_segments = []
                for i, segment in enumerate(segments):
                    labeled_segments.append({
                        "segment_number": i+1,
                        "name": f"Section {i+1}",
                        "start": segment["start"],
                        "end": segment["end"]
                    })
        except Exception as e:
            print(f"Error labeling segments: {str(e)}")
            # Fallback if LLM query fails
            labeled_segments = []
            for i, segment in enumerate(segments):
                labeled_segments.append({
                    "segment_number": i+1,
                    "name": f"Section {i+1}",
                    "start": segment["start"],
                    "end": segment["end"]
                })
    
    output = {
        "mp3_path": inputs["mp3_path"],
        "bpm": inputs.get("bpm", 0),
        "beats": inputs.get("beats", []),
        "segments": segments,
        "labeled_segments": labeled_segments
    }
    
    log_node_output("segment_labeler", output)
    return output


def lighting_hint_generator_node(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate lighting hints for each labeled segment using an LLM.
    
    Args:
        inputs: Dictionary containing labeled segments
        
    Returns:
        Dictionary with lighting hints for each segment
    """
    labeled_segments = inputs.get("labeled_segments", [])
    song_name = Path(inputs["mp3_path"]).stem
    bpm = inputs.get("bpm", 0)
    
    if not labeled_segments:
        lighting_hints = []
    else:
        # Prepare the prompt for the LLM
        segments_text = []
        for segment in labeled_segments:
            segments_text.append(
                f"{segment['name']}: starts at {segment['start']:.2f}s, ends at {segment['end']:.2f}s"
            )
        
        segments_description = "\n".join(segments_text)
        
        prompt = f"""
You are an expert lighting designer creating a light show for the song "{song_name}".
Based on the following song sections, suggest appropriate lighting effects for each section.

Song Information:
- BPM: {bpm}
- Total Sections: {len(labeled_segments)}

Song Sections:
{segments_description}

For each section, provide creative lighting suggestions that match the expected energy and mood of that section type.
For example:
- Intros might start with gentle blue washes that slowly build
- Drops might use intense strobes and color shifts
- Choruses might use bright, colorful patterns that pulse with the beat
- Verses might use softer, more focused lighting
- Outros might gradually fade or reduce in intensity

Return your answer as a JSON list of objects, each with:
1. "section_name": the name of the section (e.g., "Intro", "Chorus")
2. "start": the start time in seconds
3. "end": the end time in seconds
4. "suggestion": your lighting suggestion (1-2 sentences)

Format your response as valid JSON that I can parse programmatically.
"""
        
        # Query the LLM
        try:
            llm_response = query_ollama(prompt, model="mistral")
            
            # Extract JSON from the response
            json_start = llm_response.find("[")
            json_end = llm_response.rfind("]") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = llm_response[json_start:json_end]
                lighting_hints = json.loads(json_str)
            else:
                # Fallback if JSON parsing fails
                lighting_hints = []
                for segment in labeled_segments:
                    lighting_hints.append({
                        "section_name": segment["name"],
                        "start": segment["start"],
                        "end": segment["end"],
                        "suggestion": f"Default lighting for {segment['name']}"
                    })
        except Exception as e:
            print(f"Error generating lighting hints: {str(e)}")
            # Fallback if LLM query fails
            lighting_hints = []
            for segment in labeled_segments:
                lighting_hints.append({
                    "section_name": segment["name"],
                    "start": segment["start"],
                    "end": segment["end"],
                    "suggestion": f"Default lighting for {segment['name']}"
                })
    
    output = {
        "mp3_path": inputs["mp3_path"],
        "bpm": inputs.get("bpm", 0),
        "labeled_segments": inputs.get("labeled_segments", []),
        "lighting_hints": lighting_hints
    }
    
    # Create the final output that includes all the key information
    final_output = {
        "sections": inputs.get("labeled_segments", []),
        "lighting_hints": lighting_hints
    }
    
    log_node_output("lighting_hint_generator", output)
    log_node_output("final_output", final_output)
    
    return output


def create_pipeline() -> StateGraph:
    """
    Create the LangGraph pipeline for audio analysis.
    
    Returns:
        StateGraph: The configured pipeline
    """
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
    initial_state = {"mp3_path": mp3_path}
    
    # Run the pipeline
    result = None
    for event in pipeline.stream(initial_state):
        if event["type"] == "node":
            node_name = event["node"]
            print(f"Running node: {node_name}")
        elif event["type"] == "end":
            result = event["state"]
    
    # Extract the final output
    log_path = Path("logs") / "final_output.json"
    if log_path.exists():
        with open(log_path, "r") as f:
            final_output = json.load(f)
    else:
        final_output = {
            "sections": [] if result is None else result.get("labeled_segments", []),
            "lighting_hints": [] if result is None else result.get("lighting_hints", [])
        }
    
    return final_output
