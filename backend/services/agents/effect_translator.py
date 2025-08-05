"""
Effect Translator Agent

This agent translates lighting plan entries into precise fixture actions with exact timing.
It converts natural language lighting descriptions into specific DMX commands that can be
executed by the lighting system.
"""

from typing import Dict, Any, Optional, List, Callable
import json
import logging
import asyncio
from ._agent_model import AgentModel
from ..song_analysis_client import SongAnalysisClient
from ...models.app_state import app_state

logger = logging.getLogger(__name__)


class EffectTranslatorAgent(AgentModel):
    """
    Effect Translator Agent that converts lighting plan entries into executable actions.

    This agent takes natural language lighting descriptions and translates them into
    specific fixture actions with precise timing, considering the available fixtures
    and their capabilities.

    The agent generates action commands in the format:
    #fade parcan_pl blue at 0.2 intensity 0.5 for 0.32s
    #strobe moving_head_1 at 90.5 for 4.0s intensity 0.9 frequency 8.0
    """

    def __init__(self, agent_name: str = "effect_translator", model_name: str = "mixtral", agent_aliases: Optional[str] = "translator"):
        super().__init__(agent_name, model_name, agent_aliases)

    async def run_async(self, input_data: Dict[str, Any], callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Run the effect translator agent asynchronously with streaming support.
        
        Args:
            input_data: Dictionary containing:
                - lighting_plan: List of plan entries to translate
                - segment: Optional segment information
                - fixtures: Optional fixture information (auto-populated from app_state)
                - beat_times: Optional beat times for precise timing
                
            callback: Optional callback for streaming responses
                
        Returns:
            Dictionary with:
                - actions: Generated action commands
                - translated_count: Number of plan entries translated
                - status: Success/error status
                - error: Error message if any
        """
        try:
            self.state.status = "running"
            self.state.progress = 10
            
            # Get lighting plan from input
            lighting_plan = input_data.get('lighting_plan', [])
            if not lighting_plan:
                return {
                    "actions": [],
                    "translated_count": 0,
                    "status": "success",
                    "message": "No lighting plan entries to translate"
                }
            
            # Fetch beat times if needed
            beat_times = input_data.get('beat_times')
            if not beat_times and app_state.current_song_file:
                logger.info("Fetching beat times for precise timing...")
                beat_times = await self._fetch_beat_times(input_data.get('segment'))
                if beat_times:
                    input_data['beat_times'] = beat_times
                    logger.info(f"Retrieved {len(beat_times)} beat times")
            
            self.state.progress = 30
            
            # Build context with fixture and timing information
            context = self._build_context(input_data)
            
            # Process plan entries in batches for efficiency
            all_actions = []
            batch_size = 5  # Process 5 plan entries at a time
            
            for i in range(0, len(lighting_plan), batch_size):
                batch = lighting_plan[i:i + batch_size]
                
                # Build prompt for this batch
                batch_context = context.copy()
                batch_context['lighting_plan_batch'] = batch
                batch_context['batch_info'] = {
                    'current': i // batch_size + 1,
                    'total': (len(lighting_plan) + batch_size - 1) // batch_size,
                    'entries': len(batch)
                }
                
                prompt = self._build_prompt(batch_context)
                
                self.state.progress = 30 + (50 * i // len(lighting_plan))
                
                # Call LLM with streaming support
                response = await self._call_ollama_async(
                    prompt=prompt,
                    callback=callback
                )
                
                # Parse actions from response
                batch_actions = self._parse_action_response(response)
                all_actions.extend(batch_actions)
                
                logger.info(f"Translated batch {i//batch_size + 1}: {len(batch_actions)} actions generated")
            
            self.state.progress = 90
            
            # Validate and optimize actions
            validated_actions = self._validate_actions(all_actions)
            
            self.state.progress = 100
            self.state.status = "completed"
            self.state.result = {
                "actions": validated_actions,
                "translated_count": len(lighting_plan),
                "raw_responses": all_actions  # Keep raw for debugging
            }
            
            return {
                "actions": validated_actions,
                "translated_count": len(lighting_plan),
                "status": "success"
            }
            
        except Exception as e:
            self.state.status = "error"
            self.state.error = str(e)
            logger.error(f"Effect translator error: {str(e)}")
            return {
                "actions": [],
                "translated_count": 0,
                "status": "error",
                "error": str(e)
            }

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous wrapper for run_async.
        
        For better performance in UI scenarios, prefer using run_async directly.
        """
        return asyncio.run(self.run_async(input_data))

    async def translate_single_effect(self, effect_description: str, 
                                    time: float, 
                                    duration: Optional[float] = None,
                                    callback: Optional[Callable] = None) -> List[str]:
        """
        Translate a single lighting effect description into actions.
        
        Args:
            effect_description: Natural language description of the effect
            time: Start time in seconds
            duration: Optional duration in seconds
            callback: Optional streaming callback
            
        Returns:
            List of action command strings
        """
        input_data = {
            'lighting_plan': [{
                'time': time,
                'label': f"Effect at {time}s",
                'description': effect_description,
                'duration': duration
            }]
        }
        
        result = await self.run_async(input_data, callback)
        return result.get('actions', [])

    def _build_context(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build context for the LLM prompt."""
        context = {
            'lighting_plan': input_data.get('lighting_plan', []),
            'beat_times': input_data.get('beat_times', []),
            'segment': input_data.get('segment', {}),
        }
        
        # Add fixture information from app_state
        if app_state.fixtures:
            fixtures_info = {}
            available_fixtures = []
            
            for fixture_id, fixture in app_state.fixtures.fixtures.items():
                fixtures_info[fixture_id] = {
                    'type': fixture.fixture_type,
                    'actions': list(fixture.action_handlers.keys()) if hasattr(fixture, 'action_handlers') else [],
                    'channels': getattr(fixture, 'channels', {})
                }
                available_fixtures.append(fixture_id)
            
            context['fixtures_details'] = fixtures_info
            context['fixture_ids'] = available_fixtures
            context['available_actions'] = self._get_available_actions()
        else:
            context['fixtures_details'] = {}
            context['fixture_ids'] = []
            context['available_actions'] = []
        
        # Add song information if available
        if app_state.current_song:
            context['song'] = {
                'title': app_state.current_song.title,
                'bpm': app_state.current_song.bpm,
                'duration': app_state.current_song.duration
            }
        
        return context

    def _get_available_actions(self) -> List[str]:
        """Get list of all available action types across fixtures."""
        available_actions = set()
        
        if app_state.fixtures:
            for fixture in app_state.fixtures.fixtures.values():
                if hasattr(fixture, 'action_handlers'):
                    available_actions.update(fixture.action_handlers.keys())
        
        return list(available_actions)

    async def _fetch_beat_times(self, segment: Optional[Dict[str, Any]] = None) -> Optional[List[float]]:
        """
        Fetch exact beat times from the song analysis service.
        
        Args:
            segment: Optional segment information to filter beats
            
        Returns:
            List of exact beat times in seconds, or None if failed
        """
        try:
            song_name = app_state.current_song_file
            if not song_name:
                logger.error("No current song file in app_state")
                return None
                
            logger.info(f"Fetching beat times for current song: {song_name}")
            
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
            
        except Exception as e:
            logger.error(f"Failed to fetch beat times: {str(e)}")
            return None

    def _parse_action_response(self, response: str) -> List[str]:
        """
        Parse the LLM response to extract action commands.
        
        Looks for lines that appear to be action commands and validates them.
        """
        actions = []
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#') and not self._is_action_command(line):
                continue
            
            # Try to parse as JSON array first (if response is JSON)
            if line.startswith('[') and line.endswith(']'):
                try:
                    json_actions = json.loads(line)
                    if isinstance(json_actions, list):
                        actions.extend([str(action) for action in json_actions])
                        continue
                except json.JSONDecodeError:
                    pass
            
            # Check if line looks like an action command
            if self._is_action_command(line):
                # Remove leading # if present
                action = line.lstrip('#').strip()
                actions.append(action)
        
        return actions

    def _is_action_command(self, line: str) -> bool:
        """Check if a line looks like an action command."""
        line = line.strip().lstrip('#').strip()
        
        # Common action keywords
        action_keywords = [
            'fade', 'flash', 'strobe', 'seek', 'center_sweep', 
            'searchlight', 'flyby', 'full', 'dim', 'color'
        ]
        
        # Check if line starts with an action keyword and contains timing
        words = line.split()
        if len(words) >= 3:  # Minimum: action fixture timing
            first_word = words[0].lower()
            has_timing = any(word.startswith('at') or word.startswith('for') for word in words)
            return first_word in action_keywords and has_timing
        
        return False

    def _validate_actions(self, actions: List[str]) -> List[str]:
        """
        Validate and clean up action commands.
        
        Removes invalid actions and ensures proper formatting.
        """
        validated = []
        
        for action in actions:
            action = action.strip()
            if not action:
                continue
            
            # Basic validation - action should have fixture, timing, etc.
            parts = action.split()
            if len(parts) < 3:
                logger.warning(f"Skipping invalid action (too short): {action}")
                continue
            
            # Check for required timing parameters
            has_at = any('at' in part for part in parts)
            has_for = any('for' in part for part in parts)
            
            if not (has_at or has_for):
                logger.warning(f"Skipping action without timing: {action}")
                continue
            
            validated.append(action)
        
        return validated

    async def translate_plan_entry(self, plan_entry: Dict[str, Any], 
                                 beat_times: Optional[List[float]] = None,
                                 callback: Optional[Callable] = None) -> List[str]:
        """
        Convenience method to translate a single plan entry.
        
        Args:
            plan_entry: Single lighting plan entry
            beat_times: Optional beat times for timing
            callback: Optional streaming callback
            
        Returns:
            List of action commands
        """
        input_data = {
            'lighting_plan': [plan_entry],
            'beat_times': beat_times or []
        }
        
        result = await self.run_async(input_data, callback)
        return result.get('actions', [])
