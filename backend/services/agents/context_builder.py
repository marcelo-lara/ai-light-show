"""
Context Builder Agent

This agent analyzes musical segments and generates context summaries
for lighting design.
"""
import json
import re
from typing import Dict, Any, Optional, List
from typing_extensions import TypedDict
from pathlib import Path
from shared.models.song_metadata_new import SongMetadata

from ..ollama.ollama_api import query_ollama


class PipelineState(TypedDict):
    segment: Dict[str, Any]
    context_summary: str
    actions: list
    dmx: list


def save_node_output(node_name: str, data: Dict[str, Any]) -> None:
    """Save node output to logs for debugging"""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    output_file = logs_dir / f"{node_name}.json"
    try:
        data_dict = dict(data) if hasattr(data, 'keys') else data
        with open(output_file, 'w') as f:
            json.dump(data_dict, f, indent=2)
        print(f"💾 Saved {node_name} output to {output_file}")
    except Exception as e:
        print(f"⚠️ Failed to save {node_name} output: {e}")


class SongContextAssembler:
    """Helper class for assembling lighting context from multiple chunks"""
    
    def __init__(self):
        self.timeline = []

    def add_chunk_response(self, chunk_start: float, chunk_end: float, lighting: list, response: str):
        for action in lighting:
            action_start = action.get("start", chunk_start)
            if chunk_start <= action_start <= chunk_end:
                self.timeline.append(action)

        # Save the response to file
        self.response = response
        print(f"Response for chunk {chunk_start:.2f}s - {chunk_end:.2f}s saved.")
        print(response[:200] + "..." if len(response) > 200 else response)

    def finalize(self) -> list:
        # Sort and optionally deduplicate or smooth
        self.timeline.sort(key=lambda x: x.get("start", 0.0))
        return self.timeline


class ContextBuilderAgent:
    """
    Context Builder Agent
    
    Interprets musical segments and generates context summaries for lighting design.
    Also supports full song analysis for direct lighting action extraction.
    """
    
    def __init__(self, model: str = "mixtral"):
        self.model = model
    
    def run(self, state: PipelineState) -> PipelineState:
        """Execute the context building process for the lighting pipeline"""
        print("🎵 Running Context Builder...")
        
        segment = state.get("segment", {})
        
        # Extract segment information
        name = segment.get("name", "Unknown")
        start_time = segment.get("start", 0.0)
        end_time = segment.get("end", 0.0)
        features = segment.get("features", {})
        
        # Build prompt for context interpretation
        prompt = self._build_prompt(name, start_time, end_time, features)
        
        try:
            # Call model via Ollama
            response = query_ollama(prompt, model=self.model)
            
            # Extract context summary from response
            context_summary = response.strip().strip('"')
            
            # Update state
            result_state = state.copy()
            result_state["context_summary"] = context_summary
            
            # Save output for debugging
            save_node_output("context_builder", {
                "input": segment,
                "context_summary": context_summary,
                "model_response": response
            })
            
            print(f"✅ Context: {context_summary}")
            return result_state
            
        except Exception as e:
            print(f"❌ Context Builder failed: {e}")
            result_state = state.copy()
            result_state["context_summary"] = f"Error processing segment: {str(e)}"
            return result_state
    
    def _build_prompt(self, name: str, start_time: float, end_time: float, features: Dict[str, Any]) -> str:
        """Build the prompt for context interpretation"""
        from jinja2 import Environment, FileSystemLoader

        # Set up Jinja environment
        env = Environment(loader=FileSystemLoader('backend/services/agents/prompts'))
        template = env.get_template('context_builder.j2')

        # Exclude the full beats array from the prompt to save tokens
        features_without_beats = features.copy()
        if 'beats' in features_without_beats:
            del features_without_beats['beats']

        # Render the template with the provided variables
        return template.render(
            name=name,
            start_time=start_time,
            end_time=end_time,
            features=json.dumps(features_without_beats)
        )

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

    async def analyze_song_context(self, websocket=None, task_id: Optional[str] = None):
        """
        Generate lighting context by analyzing song data with AI.
        Supports persistent background execution with task tracking and checkpoint resume.
        
        Args:
            websocket: WebSocket connection for progress updates (optional)
            task_id: Unique task identifier for tracking (optional)
            
        Returns:
            List of lighting actions
        """
        # Get the current song (SongMetadata) from app state
        from ...models.app_state import app_state
        
        if not app_state.current_song:
            raise ValueError("No song is currently loaded")
        song: SongMetadata = app_state.current_song

        print(f"-> 🎬 Analyzing song: {song.title}")
        
        # Generate task_id if not provided
        if not task_id:
            import uuid
            task_id = f"analyze_context_{song.song_name}_{uuid.uuid4().hex[:8]}"
        
        # read the song.analysis file
        from datetime import datetime
        
        song_name = song.song_name
        analysis_path = Path(song.analysis_file)
        context_file_path = Path(song.context_file)
        
        if not analysis_path.exists():
            raise FileNotFoundError(f"Analysis file not found: {analysis_path}")
            
        with open(analysis_path, 'r') as f:
            song_data = json.load(f)
        
        # Check for existing partial context results to resume from
        existing_timeline = []
        last_processed_chunk = -1
        
        if context_file_path.exists():
            try:
                with open(context_file_path, 'r') as f:
                    existing_data = json.load(f)
                    
                # Handle both old format (list) and new format (dict with metadata)
                if isinstance(existing_data, list):
                    existing_timeline = existing_data
                elif isinstance(existing_data, dict):
                    existing_timeline = existing_data.get('timeline', [])
                    last_processed_chunk = existing_data.get('last_processed_chunk', -1)
                
                if last_processed_chunk >= 0:
                    print(f"🔄 Resuming analysis from chunk {last_processed_chunk + 1}/{len(song_data)}")
                else:
                    print(f"🔄 Found {len(existing_timeline)} existing actions, determining resume point...")
                    # Determine last processed chunk from existing timeline
                    if existing_timeline:
                        max_end_time = max(action.get('end', action.get('start', 0)) for action in existing_timeline)
                        for i, chunk in enumerate(song_data):
                            if chunk['end'] <= max_end_time:
                                last_processed_chunk = i
                        print(f"🔄 Resuming from chunk {last_processed_chunk + 1}/{len(song_data)}")
                        
            except (json.JSONDecodeError, FileNotFoundError):
                print("⚠️ Could not read existing context file, starting fresh")
                last_processed_chunk = -1
        
        # Create or update task state
        start_chunk = last_processed_chunk + 1
        remaining_chunks = len(song_data) - start_chunk
        
        task_state = app_state.create_background_task(
            task_id=task_id,
            song_name=song_name,
            operation="analyzeContext",
            total=len(song_data)
        )
        
        # Update task state with current progress if resuming
        if start_chunk > 0:
            app_state.update_task_progress(
                task_id, 
                progress=int((start_chunk / len(song_data)) * 100),
                current=start_chunk,
                message=f"Resuming from chunk {start_chunk + 1}/{len(song_data)}"
            )
        
        # build prompts for each chunk and process them
        assembler = SongContextAssembler()
        
        # Add existing timeline to assembler
        for action in existing_timeline:
            assembler.timeline.append(action)
        
        print(f"🎵 Analyzing song context for {song_name}")
        print(f"Found {len(song_data)} chunks in analysis data")
        if start_chunk > 0:
            print(f"📍 Resuming from chunk {start_chunk + 1}, {remaining_chunks} chunks remaining")
        
        # Helper function to send progress updates
        def send_progress(progress: int, current: int, message: str, error: bool = False):
            # Update task state
            app_state.update_task_progress(task_id, progress, current, message, error)
            
            # Broadcast to all connected clients (resilient to disconnections)
            progress_message = {
                "type": "backendProgress",
                "operation": "analyzeContext",
                "task_id": task_id,
                "progress": progress,
                "current": current,
                "total": len(song_data),
                "message": message,
                "song_name": song_name
            }
            if error:
                progress_message["error"] = True
                
            app_state.broadcast_to_clients(progress_message)
        
        # Helper function to save partial results
        def save_partial_results(current_chunk_index: int, timeline: list):
            try:
                partial_data = {
                    "timeline": timeline,
                    "last_processed_chunk": current_chunk_index,
                    "total_chunks": len(song_data),
                    "song_name": song_name,
                    "analysis_progress": {
                        "completed_chunks": current_chunk_index + 1,
                        "total_chunks": len(song_data),
                        "progress_percent": int(((current_chunk_index + 1) / len(song_data)) * 100)
                    }
                }
                
                with open(context_file_path, 'w') as f:
                    json.dump(partial_data, f, indent=2)
                    
                print(f"💾 Saved partial results: {current_chunk_index + 1}/{len(song_data)} chunks processed")
                
            except Exception as e:
                print(f"⚠️ Failed to save partial results: {e}")
        
        # Send initial progress
        if start_chunk == 0:
            send_progress(0, 0, f"Starting analysis of {len(song_data)} chunks...")
        else:
            current_progress = int((start_chunk / len(song_data)) * 100)
            send_progress(current_progress, start_chunk, f"Resuming analysis from chunk {start_chunk + 1}/{len(song_data)}...")
        
        try:
            # Process chunks starting from the resume point
            for i in range(start_chunk, len(song_data)):
                chunk = song_data[i]
                print(f"Processing chunk {i+1}/{len(song_data)}: {chunk['start']:.2f}s - {chunk['end']:.2f}s")
                
                # Send progress update before processing chunk
                send_progress(
                    int((i / len(song_data)) * 100),
                    i,
                    f"Processing chunk {i+1}/{len(song_data)} ({chunk['start']:.2f}s - {chunk['end']:.2f}s)"
                )
                
                try:
                    # build the prompt for this chunk
                    prompt = self.build_prompt_from_stem_chunk(chunk)
                    
                    # Include song metadata in the prompt
                    song_info = f"\nSong: {song.title}\nBPM: {song.bpm}\nGenre/Style context: "
                    
                    # add song arrangement context if available
                    if song.arrangement:
                        for section in song.arrangement:
                            if section.start <= chunk['start'] <= section.end:
                                song_info += f"Currently in section '{section.name}' ({section.start:.1f}s-{section.end:.1f}s)"
                                if hasattr(section, 'prompt') and section.prompt:
                                    song_info += f" - {section.prompt}"
                                break
                    
                    full_prompt = song_info + "\n" + prompt

                    # query the LLM directly
                    response = query_ollama(full_prompt, model=self.model)
                    
                    # extract lighting actions from the response
                    lighting_actions = self.extract_lighting_actions(response, chunk['start'], chunk['end'])
                    
                    # collect responses and build the timeline using SongContextAssembler
                    assembler.add_chunk_response(chunk['start'], chunk['end'], lighting_actions, response)

                    # Save partial results every 5 chunks or if it's the last chunk
                    if (i + 1) % 5 == 0 or i == len(song_data) - 1:
                        save_partial_results(i, assembler.timeline)
                    
                except Exception as e:
                    print(f"Error processing chunk {i}: {e}")
                    print(f"Response: {response[:200]}..." if 'response' in locals() else "No response received")
                    
                    # Save partial results even on error
                    save_partial_results(i - 1, assembler.timeline)  # Save up to last successful chunk
                    
                    # Send error progress update
                    send_progress(
                        int(((i+1) / len(song_data)) * 100),
                        i+1,
                        f"Error in chunk {i+1}: {str(e)[:50]}...",
                        error=True
                    )
            
            # Send completion progress
            send_progress(100, len(song_data), "Finalizing timeline...")
            
            # Finalize the timeline
            timeline = assembler.finalize()
            
            # Save final results with completion metadata
            final_data = {
                "timeline": timeline,
                "last_processed_chunk": len(song_data) - 1,
                "total_chunks": len(song_data),
                "song_name": song_name,
                "analysis_progress": {
                    "completed_chunks": len(song_data),
                    "total_chunks": len(song_data),
                    "progress_percent": 100,
                    "status": "completed"
                },
                "completion_timestamp": json.dumps(datetime.now(), default=str)
            }
            
            with open(context_file_path, 'w') as f:
                json.dump(final_data, f, indent=2)
            print(f"✅ Saved final context results to {context_file_path}")
            
            # Mark task as completed
            app_state.complete_task(task_id, result=timeline)
            
            return timeline
            
        except Exception as e:
            # Save partial results on any exception
            if 'assembler' in locals():
                try:
                    save_partial_results(i if 'i' in locals() else start_chunk - 1, assembler.timeline)
                except:
                    pass
            
            # Mark task as failed
            app_state.complete_task(task_id, error=str(e))
            raise

    def build_prompt_from_stem_chunk(self, chunk) -> str:
        """Build a prompt from stem analysis chunk data"""
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


# Helper function for backward compatibility
def run_context_builder(state: PipelineState) -> PipelineState:
    """Run context builder on a pipeline state"""
    agent = ContextBuilderAgent()
    return agent.run(state)
