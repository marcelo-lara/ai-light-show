"""
Agent for interacting with the 'song_context' LLM model.
"""
from .ollama_api import query_ollama

class SongContextAssembler:
    def __init__(self):
        self.timeline = []

    def add_chunk_response(self, chunk_start: float, chunk_end: float, lighting: list):
        for action in lighting:
            action_start = action.get("start", chunk_start)
            if chunk_start <= action_start <= chunk_end:
                self.timeline.append(action)

    def finalize(self) -> list:
        # Sort and optionally deduplicate or smooth
        self.timeline.sort(key=lambda x: x.get("start", 0.0))
        return self.timeline

class SongContextAgent:
    def __init__(self):
        # Initialize with model name or config if needed
        self.model = 'mistral'  # Using mistral as it's available on the server

    def get_context(self, prompt: str, **kwargs):
        # Call the LLM server for song context
        response = query_ollama(prompt, model=self.model, **kwargs)
        return self.parse_response(response)

    def parse_response(self, response):
        # Implement model-specific parsing logic here
        return response
        
    def extract_lighting_actions(self, response: str, start_time: float, end_time: float) -> list:
        """
        Extract lighting actions from the model response.
        Attempts to parse structured data from LLM response.
        
        Args:
            response: Raw text response from the LLM
            start_time: Start time of the chunk in seconds
            end_time: End time of the chunk in seconds
            
        Returns:
            List of lighting action dictionaries
        """
        import json
        import re
        
        # Initialize empty list for actions
        actions = []
        
        # Try to find JSON in the response
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
        if json_match:
            try:
                json_data = json.loads(json_match.group(1))
                
                # If it's a dict with lighting key, extract that
                if isinstance(json_data, dict) and 'lighting' in json_data:
                    actions = json_data['lighting']
                # If it's a list, assume it's already the lighting actions
                elif isinstance(json_data, list):
                    actions = json_data
                
                return actions
            except json.JSONDecodeError:
                # Failed to parse JSON, continue with text parsing
                pass
        
        # Fallback: Create a simple lighting action based on description
        # Extract any description from the response
        description_match = re.search(r'description["\']?\s*:\s*["\']([^"\']+)["\']', response, re.IGNORECASE)
        description = description_match.group(1) if description_match else "Automatic lighting"
        
        # Create a generic lighting action for the entire chunk
        default_action = {
            "start": start_time,
            "end": end_time,
            "type": "lighting",
            "description": description,
            "intensity": 0.8,  # Default intensity
            "color": "auto"    # Let system choose appropriate color
        }
        
        actions.append(default_action)
        return actions

    def analyze_song_context(self):
        """
        Analyze the song data to generate context for light show design.
        Expects song_data to contain chunks with 'start', 'end', and 'stems'.
        """
                # get the current song from app_state

        from shared.models.song_metadata import SongMetadata
        from ...models.app_state import app_state
        
        if not app_state.current_song:
            raise ValueError("No song is currently loaded")

        song: SongMetadata = app_state.current_song
        print(f"-> 🎬 Analyzing song: {song.title}")
        
        # read the song.analysis file
        import json
        from pathlib import Path
        
        song_name = song.song_name
        analysis_path = Path(song.analysis_file)
        
        if not analysis_path.exists():
            raise FileNotFoundError(f"Analysis file not found: {analysis_path}")
            
        with open(analysis_path, 'r') as f:
            song_data = json.load(f)
        
        # build prompts for each chunk and process them
        assembler = SongContextAssembler()
        
        print(f"🎵 Analyzing song context for {song_name}")
        print(f"Found {len(song_data)} chunks in analysis data")
        
        for i, chunk in enumerate(song_data):
            print(f"Processing chunk {i+1}/{len(song_data)}: {chunk['start']:.2f}s - {chunk['end']:.2f}s")
            
            # build the prompt for this chunk
            prompt = self.build_prompt_from_stem_chunk(chunk)
            
            # send the prompt to the LLM
            response = self.get_context(prompt)
            
            try:
                # Extract the lighting instructions from the response
                lighting_actions = self.extract_lighting_actions(response, chunk['start'], chunk['end'])
                
                # collect responses and build the timeline using SongContextAssembler
                assembler.add_chunk_response(chunk['start'], chunk['end'], lighting_actions)
                
            except Exception as e:
                print(f"Error processing chunk {i}: {e}")
                print(f"Response: {response[:200]}...")
        
        # Finalize the timeline
        timeline = assembler.finalize()
        
        # save the results to a file for debugging or further processing
        with open(song.context_file, 'w') as f:
            json.dump(timeline, f, indent=2)
        print(f"✅ Saved context results to {song.context_file}")
            
        return timeline
        

    def build_prompt_from_stem_chunk(self, chunk) -> str:
        start = chunk["start"]
        end = chunk["end"]
        stems = chunk["stems"]

        prompt_lines = [
            f"You are a light show designer.",
            f"This music segment runs from {start:.2f}s to {end:.2f}s.",
            f"Below are time-aligned audio features, extracted per stem.",
            ""
        ]

        for stem_name, features in stems.items():
            prompt_lines.append(f"🎚 Stem: {stem_name}")
            prompt_lines.append(f"Timestamps: {features.get('timestamps')[:10]} ...")
            prompt_lines.append(f"RMS: {features.get('rms')[:10]} ...")
            prompt_lines.append(f"Flux: {features.get('flux')[:10]} ...")
            mfcc_keys = [k for k in features if k.startswith("mfcc_")]
            for k in mfcc_keys[:2]:  # include just first two MFCCs to keep it clean
                prompt_lines.append(f"{k}: {features[k][:10]} ...")
            prompt_lines.append("")  # spacing

        prompt_lines.append("Describe the musical behavior, and how it should be expressed through light.")
        prompt_lines.append("Return:")
        prompt_lines.append("- 'description': a summary of the segment's musical mood or structure")

        return "\n".join(prompt_lines)
