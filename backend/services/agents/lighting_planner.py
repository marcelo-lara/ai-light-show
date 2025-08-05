"""
Lighting Planner Agent

This agent analyzes musical segments and generates concise, natural language context summaries 
for lighting design. The goal is to create a Lighting Plan with timed entries.
"""

from typing import Dict, Any, Optional, List, Callable
from ._agent_model import AgentModel
from ..ollama import query_ollama
from ..song_analysis_client import SongAnalysisClient
from ...models.app_state import app_state
import asyncio
import logging

logger = logging.getLogger(__name__)


class LightingPlannerAgent(AgentModel):
    """
    Lighting Planner Agent that analyzes musical segments and creates lighting plan entries.

    This agent uses the data from the song_analysis service to create lighting scenes for a given segment of the song OR create a light story segregating the song into planned sections (e.g. intro, verse, chorus, etc.).
    The output of this agent is a list of lighting plan entries that stored for later use.
    The agent MUST use precise time (from song arrangement or key moments) to create the plan entries.

    The agent generates plan entries in the format:
    #plan add at [time] "[label]" "[description]"
    
    Example output:
    #plan add at 0.487 "Intro start" "half intensity blue chaser from left to right at 1b intervals"
    #plan add at 1.234 "Intro build" "fade from blue to white from right to left every 1b intervals"
    """

    def __init__(self, agent_name: str = "lighting_planner", model_name: str = "mixtral", agent_aliases: Optional[str] = "planner"):
        super().__init__(agent_name, model_name, agent_aliases)

    async def run_async(self, input_data: Dict[str, Any], callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Run the lighting planner agent asynchronously with streaming support.
        
        Automatically uses the current song from app_state for exact beat analysis.
        
        Args:
            input_data: Dictionary containing:
                - context_summary: Musical context analysis
                - segment: Optional segment information with start, end, duration
                - user_prompt: Optional user-provided prompt
                - song: Optional song metadata (auto-populated from app_state)
                - fixtures: Optional fixture information (auto-populated from app_state)
            callback: Optional callback for streaming responses
                
        Returns:
            Dictionary with:
                - lighting_plan: Generated lighting plan commands
                - exact_beats: Beat times retrieved from song analysis
                - status: Success/error status
                - error: Error message if any
        """
        try:
            self.state.status = "running"
            self.state.progress = 10
            
            # Fetch exact beat times from current song
            exact_beats = None
            if app_state.current_song_file:
                logger.info("Fetching exact beat times from song analysis...")
                exact_beats = await self._fetch_exact_beats_async(input_data.get('segment'))
                if exact_beats:
                    input_data['exact_beats'] = exact_beats
                    logger.info(f"Retrieved {len(exact_beats)} exact beat times")
                else:
                    logger.warning("Could not retrieve exact beat times, proceeding without them")
            else:
                logger.warning("No current song loaded, proceeding without exact beats")
            
            self.state.progress = 30
            
            # Build the prompt using the Jinja2 template
            prompt = self._build_prompt(input_data)
            
            self.state.progress = 50
            
            # Call the LLM with streaming support
            response = await self._call_ollama_async(
                prompt=prompt,
                callback=callback
            )
            
            self.state.progress = 80
            
            # Parse the response
            lighting_plan = self._parse_plan_response(response)
            
            self.state.progress = 100
            self.state.status = "completed"
            self.state.result = {
                "lighting_plan": lighting_plan,
                "raw_response": response,
                "exact_beats": exact_beats
            }
            
            return {
                "lighting_plan": lighting_plan,
                "raw_response": response,
                "exact_beats": exact_beats,
                "status": "success"
            }
            
        except Exception as e:
            self.state.status = "error"
            self.state.error = str(e)
            logger.error(f"Lighting planner error: {str(e)}")
            return {
                "lighting_plan": [],
                "status": "error",
                "error": str(e)
            }

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous wrapper for run_async.
        
        For better performance in UI scenarios, prefer using run_async directly.
        """
        return asyncio.run(self.run_async(input_data))

    def _call_ollama(self, prompt: str) -> str:
        """Call the Ollama API with the given prompt."""
        try:
            response = query_ollama(prompt, model=self.model_name)
            return response
        except Exception as e:
            raise Exception(f"Failed to call Ollama API: {str(e)}")

    def _fetch_exact_beats(self, segment: Optional[Dict[str, Any]] = None) -> Optional[List[float]]:
        """
        Fetch exact beat times from the song analysis service.
        
        Uses the current song from app_state.current_song_file.
        
        Args:
            segment: Optional segment information to filter beats
            
        Returns:
            List of exact beat times in seconds, or None if failed
        """
        return asyncio.run(self._fetch_exact_beats_async(segment))

    async def _fetch_exact_beats_async(self, segment: Optional[Dict[str, Any]] = None) -> Optional[List[float]]:
        """
        Fetch exact beat times from the song analysis service.
        
        Uses the current song from app_state.current_song_file.
        
        Args:
            segment: Optional segment information to filter beats
            
        Returns:
            List of exact beat times in seconds, or None if failed
        """
        try:
            # Use song name from app_state (always available)
            song_name = app_state.current_song_file
            if not song_name:
                logger.error("No current song file in app_state")
                return None
                
            logger.info(f"Extracting beats for current song: {song_name}")
            
            # Use synchronous wrapper for simplicity in this context
            async def _fetch():
                async with SongAnalysisClient() as client:
                    start_time = segment.get('start') if segment else None
                    end_time = segment.get('end') if segment else None
                    
                    result = await client.analyze_beats_rms_flux(
                        song_name=song_name,
                        force=False,  # Use cache if available
                        start_time=start_time,
                        end_time=end_time
                    )
                    
                    if result.get('status') == 'ok' and 'beats' in result:
                        return result['beats']
                    else:
                        logger.error(f"Beat analysis failed: {result.get('message', 'Unknown error')}")
                        return None
            
            return asyncio.run(_fetch())
            
        except Exception as e:
            logger.error(f"Failed to fetch exact beats: {str(e)}")
            return None

    def _parse_plan_response(self, response: str) -> list:
        """
        Parse the LLM response to extract plan commands.
        
        Looks for lines starting with #plan add at and extracts:
        - time: timestamp in seconds
        - label: descriptive label
        - description: effect description
        """
        plan_entries = []
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('#plan add at '):
                try:
                    # Parse: #plan add at 0.0 "Intro start" "half intensity blue chaser..."
                    # Remove the #plan add at prefix
                    remainder = line[13:].strip()
                    
                    # Find the first space to separate time from the rest
                    space_idx = remainder.find(' ')
                    if space_idx == -1:
                        continue
                        
                    time_str = remainder[:space_idx]
                    rest = remainder[space_idx + 1:].strip()
                    
                    # Parse time
                    time = float(time_str)
                    
                    # Parse label and description (both in quotes)
                    if rest.startswith('"'):
                        # Find the closing quote for label
                        end_quote = rest.find('"', 1)
                        if end_quote == -1:
                            continue
                        label = rest[1:end_quote]
                        
                        # Find the description
                        remainder = rest[end_quote + 1:].strip()
                        if remainder.startswith('"') and remainder.endswith('"'):
                            description = remainder[1:-1]
                        else:
                            continue
                    else:
                        continue
                    
                    plan_entries.append({
                        "time": time,
                        "label": label,
                        "description": description
                    })
                    
                except (ValueError, IndexError) as e:
                    # Skip malformed lines
                    continue
        
        return plan_entries

    async def create_plan_for_segment_async(self, segment_data: Dict[str, Any], 
                                          context_summary: str,
                                          callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Async convenience method to create a lighting plan for a specific musical segment.
        
        Uses the current song from app_state for exact beat analysis.
        
        Args:
            segment_data: Segment information (start, end, duration, etc.)
            context_summary: Musical context analysis
            callback: Optional streaming callback
            
        Returns:
            Lighting plan result
        """
        input_data = {
            "segment": segment_data,
            "context_summary": context_summary
        }
        return await self.run_async(input_data, callback)

    def create_plan_for_segment(self, segment_data: Dict[str, Any], context_summary: str) -> Dict[str, Any]:
        """
        Convenience method to create a lighting plan for a specific musical segment.
        
        Uses the current song from app_state for exact beat analysis.
        
        Args:
            segment_data: Segment information (start, end, duration, etc.)
            context_summary: Musical context analysis
            
        Returns:
            Lighting plan result
        """
        input_data = {
            "segment": segment_data,
            "context_summary": context_summary
        }
        return self.run(input_data)

    async def create_plan_from_user_prompt_async(self, user_prompt: str, 
                                               context_summary: str = "",
                                               callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Async convenience method to create a lighting plan from a user prompt.
        
        Uses the current song from app_state for exact beat analysis.
        
        Args:
            user_prompt: User's lighting request
            context_summary: Optional musical context
            callback: Optional streaming callback
            
        Returns:
            Lighting plan result
        """
        input_data = {
            "user_prompt": user_prompt,
            "context_summary": context_summary
        }
        return await self.run_async(input_data, callback)

    def create_plan_from_user_prompt(self, user_prompt: str, context_summary: str = "") -> Dict[str, Any]:
        """
        Convenience method to create a lighting plan from a user prompt.
        
        Uses the current song from app_state for exact beat analysis.
        
        Args:
            user_prompt: User's lighting request
            context_summary: Optional musical context
            
        Returns:
            Lighting plan result
        """
        input_data = {
            "user_prompt": user_prompt,
            "context_summary": context_summary
        }
        return self.run(input_data)

    async def create_plan_for_current_song_async(self, context_summary: str = "",
                                               segment: Optional[Dict[str, Any]] = None,
                                               user_prompt: Optional[str] = None,
                                               callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Create a lighting plan for the currently loaded song using exact beat synchronization (async).
        
        This method automatically uses the current song from app_state and includes
        song metadata and fixture information in the prompt.
        
        Args:
            context_summary: Optional musical context (will use song info if empty)
            segment: Optional segment information
            user_prompt: Optional user prompt
            callback: Optional streaming callback
            
        Returns:
            Lighting plan result with exact beat synchronization
            
        Raises:
            ValueError: If no song is currently loaded
        """
        if not app_state.current_song or not app_state.current_song_file:
            raise ValueError("No song is currently loaded. Use app_state.current_song to set a song first.")
        
        # Use song metadata for context if not provided
        if not context_summary and app_state.current_song:
            song = app_state.current_song
            context_summary = f"Song: {song.title or app_state.current_song_file}, BPM: {song.bpm or 'unknown'}, Duration: {song.duration or 'unknown'}s"
        
        # Prepare input data with all available information
        input_data: Dict[str, Any] = {
            "context_summary": context_summary,
            "song": {
                "title": app_state.current_song.title or app_state.current_song_file,
                "bpm": app_state.current_song.bpm,
                "duration": app_state.current_song.duration,
                "beats": app_state.current_song.beats if hasattr(app_state.current_song, 'beats') else None
            },
            "fixtures": [
                {
                    "id": fixture.id,
                    "type": fixture.fixture_type,
                    "effects": list(fixture.action_handlers.keys()) if hasattr(fixture, 'action_handlers') else []
                }
                for fixture in app_state.fixtures.fixtures.values() if app_state.fixtures
            ] if app_state.fixtures else []
        }
        
        if segment:
            input_data["segment"] = segment
        if user_prompt:
            input_data["user_prompt"] = user_prompt
        
        logger.info(f"Creating lighting plan for current song: {app_state.current_song_file}")
        return await self.run_async(input_data, callback)

    def create_plan_for_current_song(self, context_summary: str = "",
                                   segment: Optional[Dict[str, Any]] = None,
                                   user_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a lighting plan for the currently loaded song using exact beat synchronization.
        
        This method automatically uses the current song from app_state and includes
        song metadata and fixture information in the prompt.
        
        Args:
            context_summary: Optional musical context (will use song info if empty)
            segment: Optional segment information
            user_prompt: Optional user prompt
            
        Returns:
            Lighting plan result with exact beat synchronization
            
        Raises:
            ValueError: If no song is currently loaded
        """
        if not app_state.current_song or not app_state.current_song_file:
            raise ValueError("No song is currently loaded. Use app_state.current_song to set a song first.")
        
        # Use song metadata for context if not provided
        if not context_summary and app_state.current_song:
            song = app_state.current_song
            context_summary = f"Song: {song.title or app_state.current_song_file}, BPM: {song.bpm or 'unknown'}, Duration: {song.duration or 'unknown'}s"
        
        # Prepare input data with all available information
        input_data: Dict[str, Any] = {
            "context_summary": context_summary,
            "song": {
                "title": app_state.current_song.title or app_state.current_song_file,
                "bpm": app_state.current_song.bpm,
                "duration": app_state.current_song.duration,
                "beats": app_state.current_song.beats if hasattr(app_state.current_song, 'beats') else None
            },
            "fixtures": [
                {
                    "id": fixture.id,
                    "type": fixture.fixture_type,
                    "effects": list(fixture.action_handlers.keys()) if hasattr(fixture, 'action_handlers') else []
                }
                for fixture in app_state.fixtures.fixtures.values() if app_state.fixtures
            ] if app_state.fixtures else []
        }
        
        if segment:
            input_data["segment"] = segment
        if user_prompt:
            input_data["user_prompt"] = user_prompt
        
        logger.info(f"Creating lighting plan for current song: {app_state.current_song_file}")
        return self.run(input_data)

    def _build_context(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build the context for the agent model from the input data."""
        context = input_data.copy()
        
        # Add song information from app_state if not provided
        if not context.get('song') and app_state.current_song:
            context['song'] = {
                'title': app_state.current_song.title or app_state.current_song_file,
                'bpm': app_state.current_song.bpm,
                'duration': app_state.current_song.duration
            }
        
        # Add fixture information from app_state if not provided
        if not context.get('fixtures') and app_state.fixtures:
            context['fixtures'] = [
                {
                    "id": fixture.id,
                    "type": fixture.fixture_type,
                    "effects": list(fixture.action_handlers.keys()) if hasattr(fixture, 'action_handlers') else []
                }
                for fixture in app_state.fixtures.fixtures.values()
            ]
        
        return context
