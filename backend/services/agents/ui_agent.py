"""
UI Agent - Intelligent Router

This agent acts as an intelligent router that analyzes user requests and determines 
which specialized agent to call or which direct command to execute. It uses LLM 
to understand user intent and route accordingly.
"""

from typing import Optional, Dict, Any, Callable
from datetime import datetime
from ._agent_model import AgentModel
from .lighting_planner import LightingPlannerAgent
from .effect_translator import EffectTranslatorAgent
import logging

logger = logging.getLogger(__name__)

class UIAgent(AgentModel):
    """
    UI Agent that acts as an intelligent router for user requests.
    
    This agent analyzes user intentions using LLM and routes requests to:
    1. Direct Commands (for precise lighting actions)
    2. Lighting Planner Agent (for planning lighting sequences) 
    3. Effect Translator Agent (for translating effects to actions)
    4. Conversational responses (for general questions/help)
    
    The agent uses LLM for ALL routing decisions - no hardcoded logic.
    """

    def __init__(self, agent_name: str = "ui_agent", model_name: str = "gemma3n:e4b", agent_aliases: Optional[str] = "ui", debug: bool = True):
        super().__init__(agent_name, model_name, agent_aliases, debug)
        
        # Initialize specialized agents
        self.lighting_planner = LightingPlannerAgent(model_name=model_name)
        self.effect_translator = EffectTranslatorAgent(model_name=model_name)
        
        # Track conversation state
        self.conversation_history = []

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the UI agent asynchronously with intelligent routing."""
        try:
            self.state.status = "running"
            self.state.started_at = datetime.now()
            
            # Extract user prompt and optional callback for streaming
            user_prompt = input_data.get("prompt", "")
            callback = input_data.get("callback")
            conversation_history = input_data.get("conversation_history", [])
            
            if not user_prompt:
                raise ValueError("No prompt provided in input_data")
            
            logger.info(f"🤖 UI Agent processing: {user_prompt}")
            
            # Step 1: Use LLM to analyze user intent and determine routing
            routing_decision = await self._analyze_user_intent(user_prompt, callback)
            
            logger.info(f"🎯 Routing decision: {routing_decision}")
            
            # Step 2: Route to appropriate handler based on LLM decision
            if routing_decision["type"] == "direct_command":
                response = await self._handle_direct_command(
                    routing_decision["command"],
                    user_prompt,
                    callback
                )
            elif routing_decision["type"] == "lighting_plan":
                response = await self._handle_lighting_plan_request(
                    routing_decision,
                    user_prompt,
                    callback
                )
            elif routing_decision["type"] == "effect_translation":
                response = await self._handle_effect_translation_request(
                    routing_decision,
                    user_prompt,
                    callback
                )
            elif routing_decision["type"] == "conversation":
                response = await self._handle_conversational_request(
                    user_prompt,
                    callback,
                    conversation_history
                )
            else:
                # Fallback to conversational if routing is unclear
                response = await self._handle_conversational_request(
                    user_prompt,
                    callback,
                    conversation_history
                )
            
            self.state.status = "completed"
            self.state.completed_at = datetime.now()
            self.state.result = response
            
            return {
                "success": True,
                "response": response.get("response", ""),
                "agent": self.agent_name,
                "routing": routing_decision,
                "actions": response.get("actions", []),
                "lighting_plan": response.get("lighting_plan", [])
            }
            
        except Exception as e:
            self.state.status = "error"
            self.state.error = str(e)
            self.state.completed_at = datetime.now()
            logger.error(f"❌ UI Agent error: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "agent": self.agent_name
            }

    async def _analyze_user_intent(self, user_prompt: str, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Use LLM to analyze user intent and determine routing strategy.
        
        Returns a routing decision with type and parameters.
        """
        
        # Build routing analysis prompt
        routing_prompt = f"""
You are an intelligent router for a DMX lighting control system. Analyze the user's request and determine the best routing strategy.

User Request: "{user_prompt}"

Available Routing Options:
1. **direct_command** - For precise lighting actions that should be executed immediately
   - Examples: "flash red lights", "strobe moving head", "fade to blue", "clear all actions"
   - Returns specific command to execute

2. **lighting_plan** - For creating structured lighting plans/sequences  
   - Examples: "create intro lighting", "plan the chorus section", "design lights for the whole song"
   - Needs musical context and timing

3. **effect_translation** - For converting lighting descriptions to precise actions
   - Examples: "translate this effect to fixtures", "make this effect work with our lights"
   - Has existing lighting plan that needs translation

4. **conversation** - For general questions, help, or unclear requests
   - Examples: "what can you do?", "how does this work?", unclear requests

Analyze the request and respond with ONLY a JSON object:
{{
  "type": "direct_command|lighting_plan|effect_translation|conversation",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation of why this routing was chosen",
  "parameters": {{
    "command": "for direct_command: the specific command to execute",
    "context": "for lighting_plan: musical context needed", 
    "effect_description": "for effect_translation: effect to translate",
    "topic": "for conversation: general topic/question"
  }}
}}

JSON Response:"""
        
        try:
            if callback:
                callback("🎯 Analyzing request intent...\n")
            
            # Call LLM for routing decision
            routing_response = await self._call_ollama_async(
                prompt=routing_prompt,
                callback=None  # Don't stream routing analysis
            )
            
            # Parse JSON response
            import json
            routing_decision = json.loads(routing_response.strip())
            
            logger.info(f"🧠 Intent analysis: {routing_decision['type']} (confidence: {routing_decision.get('confidence', 0)})")
            
            return routing_decision
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"⚠️ Failed to parse routing decision, defaulting to conversation: {e}")
            return {
                "type": "conversation",
                "confidence": 0.3,
                "reasoning": "Failed to parse routing decision",
                "parameters": {"topic": "general"}
            }

    async def _handle_direct_command(self, command: str, user_prompt: str, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Handle direct command execution."""
        try:
            if callback:
                callback("⚡ Executing direct command...\n")
            
            logger.info(f"🎭 Executing direct command: {command}")
            
            # Import here to avoid circular imports
            from ..direct_commands import DirectCommandsParser
            
            # Create direct commands parser and execute
            direct_commands_parser = DirectCommandsParser()
            success, message, additional_data = await direct_commands_parser.parse_command(command)
            
            if success:
                # Process any response actions and broadcast updates
                await self._process_response_actions(command)
                
                return {
                    "response": f"✅ Command executed successfully: {message}",
                    "actions": additional_data.get("actions", []) if additional_data else [],
                    "success": True
                }
            else:
                return {
                    "response": f"❌ Command failed: {message}",
                    "actions": [],
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"❌ Direct command error: {e}")
            return {
                "response": f"❌ Error executing command: {str(e)}",
                "actions": [],
                "success": False
            }

    async def _handle_lighting_plan_request(self, routing_decision: Dict[str, Any], user_prompt: str, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Handle lighting plan creation requests."""
        try:
            if callback:
                callback("🎛️ Creating lighting plan...\n")
            
            logger.info("🎛️ Routing to Lighting Planner Agent")
            
            # Prepare input for lighting planner
            planner_input = {
                "user_prompt": user_prompt,
                "context_summary": routing_decision.get("parameters", {}).get("context", ""),
            }
            
            # Call lighting planner with streaming
            plan_result = await self.lighting_planner.run_async(planner_input, callback)
            
            if plan_result["status"] == "success":
                plan_count = len(plan_result["lighting_plan"])
                
                response_text = f"✅ Created lighting plan with {plan_count} entries.\n\n"
                
                # Show summary of plan entries
                for i, entry in enumerate(plan_result["lighting_plan"][:3]):  # Show first 3
                    response_text += f"• {entry['time']}s: {entry['label']} - {entry['description']}\n"
                
                if plan_count > 3:
                    response_text += f"... and {plan_count - 3} more entries\n"
                
                response_text += f"\nUse 'translate to actions' to convert this plan to executable lighting actions."
                
                return {
                    "response": response_text,
                    "lighting_plan": plan_result["lighting_plan"],
                    "exact_beats": plan_result.get("exact_beats", []),
                    "success": True
                }
            else:
                return {
                    "response": f"❌ Failed to create lighting plan: {plan_result.get('error', 'Unknown error')}",
                    "lighting_plan": [],
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"❌ Lighting plan error: {e}")
            return {
                "response": f"❌ Error creating lighting plan: {str(e)}",
                "lighting_plan": [],
                "success": False
            }

    async def _handle_effect_translation_request(self, routing_decision: Dict[str, Any], user_prompt: str, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Handle effect translation requests."""
        try:
            if callback:
                callback("🎭 Translating effects to actions...\n")
            
            logger.info("🎭 Routing to Effect Translator Agent")
            
            # Check if we have a lighting plan to translate
            # This could come from previous conversation or be inferred from the request
            effect_description = routing_decision.get("parameters", {}).get("effect_description", user_prompt)
            
            # Create a simple lighting plan entry for translation
            simple_plan = [{
                "time": 0.0,  # Immediate
                "label": "User Effect",
                "description": effect_description
            }]
            
            # Call effect translator
            translator_input = {
                "lighting_plan": simple_plan
            }
            
            translation_result = await self.effect_translator.run_async(translator_input, callback)
            
            if translation_result["status"] == "success":
                actions = translation_result["actions"]
                action_count = len(actions)
                
                response_text = f"✅ Translated effect into {action_count} lighting actions.\n\n"
                
                # Show sample actions
                for i, action in enumerate(actions[:5]):  # Show first 5
                    response_text += f"• {action}\n"
                
                if action_count > 5:
                    response_text += f"... and {action_count - 5} more actions\n"
                
                # Auto-execute actions by processing them as direct commands
                await self._process_response_actions("\n".join([f"#action {action}" for action in actions]))
                
                return {
                    "response": response_text,
                    "actions": actions,
                    "success": True
                }
            else:
                return {
                    "response": f"❌ Failed to translate effect: {translation_result.get('error', 'Unknown error')}",
                    "actions": [],
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"❌ Effect translation error: {e}")
            return {
                "response": f"❌ Error translating effect: {str(e)}",
                "actions": [],
                "success": False
            }

    async def _handle_conversational_request(self, user_prompt: str, callback: Optional[Callable] = None, conversation_history: Optional[list] = None) -> Dict[str, Any]:
        """Handle general conversational requests."""
        try:
            if callback:
                callback("💬 Thinking about your question...\n")
            
            logger.info("💬 Handling conversational request")
            
            # Build context for conversational response
            context_data = self._build_context({})
            
            # Use the router template for conversational responses
            from pathlib import Path
            from jinja2 import Environment, FileSystemLoader
            
            prompts_dir = Path(__file__).parent / "prompts"
            jinja_env = Environment(
                loader=FileSystemLoader(prompts_dir),
                trim_blocks=True,
                lstrip_blocks=True
            )
            router_template = jinja_env.get_template("ui_agent_router.j2")
            system_context = router_template.render(context_data)
            
            # Call Ollama for conversational response
            response = await self._call_ollama_async(
                prompt=user_prompt,
                context=system_context,
                callback=callback,
                conversation_history=conversation_history or [],
                auto_execute_commands=False
            )
            
            # Check if response contains any action commands that should be processed
            if "#" in response and any(word in response for word in ['action', 'flash', 'strobe', 'fade']):
                await self._process_response_actions(response)
            
            return {
                "response": response,
                "actions": [],
                "success": True
            }
            
        except Exception as e:
            logger.error(f"❌ Conversational error: {e}")
            return {
                "response": f"❌ I encountered an error: {str(e)}",
                "actions": [],
                "success": False
            }

    def get_conversation_history(self) -> list:
        """Get the current conversation history."""
        return self.conversation_history.copy()

    def add_to_conversation(self, role: str, content: str):
        """Add a message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
        logger.info("🗑️ Conversation history cleared")

    async def quick_response(self, user_prompt: str, callback: Optional[Callable] = None) -> str:
        """
        Quick response method for simple conversational interactions.
        
        Returns just the response text without full routing analysis.
        """
        try:
            result = await self.run({
                "prompt": user_prompt,
                "callback": callback
            })
            
            return result.get("response", "I couldn't process that request.")
            
        except Exception as e:
            logger.error(f"❌ Quick response error: {e}")
            return f"I encountered an error: {str(e)}"

    def _build_context(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build the context for the UI agent from the input data."""
        from ...models.app_state import app_state
        
        # Prepare song data
        song = app_state.current_song
        song_data = {}
        
        # Handle case when no song is loaded
        if song is None:
            raise ValueError("No song is currently loaded. Please load a song to build the UI context.")

        # Extract song data for template with safe attribute access
        try:
            song_data = {
                "title": getattr(song, 'song_name', 'Unknown'),
                "bpm": getattr(song, 'bpm', 120),
                "duration": getattr(song, 'duration', 0),
                "arrangement": getattr(song, 'arrangement', []),
                "beats": [],  # Don't send full beats array, agent will request sections as needed
                "key_moments": getattr(song, 'key_moments', [])
            }
        except AttributeError as e:
            # Handle partially initialized song objects
            print(f"⚠️ Warning: Song object missing attributes: {e}")
            song_data = {
                "title": "Unknown Song",
                "bpm": 120,
                "duration": 0,
                "arrangement": [],
                "beats": [],  # Don't send full beats array
                "key_moments": []
            }
        
        # Prepare fixtures data
        fixtures = []
        if app_state.fixtures and hasattr(app_state.fixtures, 'fixtures'):
            fixtures_dict = app_state.fixtures.fixtures
            for fixture_id, fixture in fixtures_dict.items():
                fixtures.append({
                    "id": fixture.id,
                    "type": fixture.fixture_type,
                    "effects": [action for action in fixture.actions if action != 'arm']  # omit 'arm' action
                })
        
        return {
            "song": song_data,
            "fixtures": fixtures
        }

    async def _process_response_actions(self, response: str) -> None:
        """
        Process the AI response to detect and save any action commands, 
        then broadcast the updated actions to the frontend.
        
        Args:
            response (str): The complete AI response text
        """
        try:
            # Extract action commands from the response (lines starting with #action or #)
            action_lines = []
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith('#action') or (line.startswith('#') and any(word in line for word in ['flash', 'strobe', 'fade', 'seek', 'arm'])):
                    action_lines.append(line)
            
            if not action_lines:
                print("📝 No action commands found in AI response")
                return
            
            print(f"🎭 Found {len(action_lines)} action commands in AI response")
            
            # Import here to avoid circular imports
            from ..direct_commands import DirectCommandsParser
            from ...models.app_state import app_state
            from ..utils.broadcast import broadcast_to_all
            
            # Create direct commands parser
            direct_commands_parser = DirectCommandsParser()
            
            # Process each action command
            actions_added = 0
            for action_line in action_lines:
                try:
                    # Parse and execute the action command
                    success, message, additional_data = await direct_commands_parser.parse_command(action_line)
                    if success:
                        actions_added += 1
                        print(f"✅ Action executed: {action_line}")
                    else:
                        print(f"❌ Action failed: {action_line} -> {message}")
                except Exception as e:
                    print(f"❌ Error processing action '{action_line}': {e}")
            
            # If actions were added successfully, broadcast the updated actions to frontend
            if actions_added > 0 and app_state.current_song_file:
                from pathlib import Path
                from ...models.actions_sheet import ActionsSheet
                
                # Get current actions
                song_name = Path(app_state.current_song_file).stem
                actions_sheet = ActionsSheet(song_name)
                actions_sheet.load_actions()
                
                # Log the actions update
                action_count = len(actions_sheet.actions)
                print(f"📊 Broadcasting actions update: {action_count} total actions for song '{song_name}' (added {actions_added} new)")
                
                # IMPORTANT: Render actions to canvas so they appear on the main canvas
                try:
                    # Automatically render actions to canvas after adding them
                    render_success, render_message, render_data = await direct_commands_parser.parse_command("#render")
                    if render_success:
                        print(f"✅ Actions rendered to canvas: {render_message}")
                    else:
                        print(f"⚠️ Failed to render actions to canvas: {render_message}")
                except Exception as render_error:
                    print(f"❌ Error rendering actions to canvas: {render_error}")
                
                # Broadcast actions update to all clients
                await broadcast_to_all({
                    "type": "actionsUpdate",
                    "actions": [action.to_dict() for action in actions_sheet.actions]
                })

            
        except Exception as e:
            print(f"❌ Error in _process_response_actions: {e}")
