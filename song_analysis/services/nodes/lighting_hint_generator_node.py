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
        
        try:
            llm_response = query_ollama(prompt, model="mistral")
            json_start = llm_response.find("[")
            json_end = llm_response.rfind("]") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = llm_response[json_start:json_end]
                lighting_hints = json.loads(json_str)
            else:
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
    
    final_output = {
        "sections": inputs.get("labeled_segments", []),
        "lighting_hints": lighting_hints
    }
    
    log_node_output("lighting_hint_generator", output)
    log_node_output("final_output", final_output)
    
    return output
