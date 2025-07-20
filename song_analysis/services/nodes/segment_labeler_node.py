from typing import Dict, Any
from pathlib import Path
from backend.services.ollama.ollama_api import query_ollama
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
        
        try:
            llm_response = query_ollama(prompt, model="mistral")
            json_start = llm_response.find("[")
            json_end = llm_response.rfind("]") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = llm_response[json_start:json_end]
                labeled_segments = json.loads(json_str)
            else:
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
