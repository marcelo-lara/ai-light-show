#!/usr/bin/env python3
"""
Simple integration example showing how to use the improved agents together
for a ChatGPT-like AI lighting assistant.
"""

import asyncio
import json
import logging
from typing import Optional, Callable

# Set up logging
logger = logging.getLogger(__name__)

# Mock imports for demonstration - replace with actual imports
# from backend.services.agents.lighting_planner import LightingPlannerAgent
# from backend.services.agents.effect_translator import EffectTranslatorAgent


class AILightingAssistant:
    """
    ChatGPT-like AI assistant for lighting control that combines both agents.
    """
    
    def __init__(self, model_name: str = "mixtral"):
        self.model_name = model_name
        self.planner = None  # LightingPlannerAgent(model_name=model_name)
        self.translator = None  # EffectTranslatorAgent(model_name=model_name)
        self.conversation_history = []
        
        # Set up logging for this instance
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"🎭 AILightingAssistant initialized with model: {model_name}")
    
    async def chat(self, user_message: str, stream_callback: Optional[Callable] = None) -> dict:
        """
        Main chat interface - processes user message and returns appropriate response.
        
        Args:
            user_message: User's natural language request
            stream_callback: Optional callback for streaming responses
            
        Returns:
            Dictionary with response, actions, and metadata
        """
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        self.logger.info(f"💬 Processing user message: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")
        
        try:
            # Determine intent and route to appropriate agent
            if self._is_planning_request(user_message):
                self.logger.info("🎯 Routing to planning request handler")
                result = await self._handle_planning_request(user_message, stream_callback)
            elif self._is_direct_action_request(user_message):
                self.logger.info("🎯 Routing to direct action request handler")
                result = await self._handle_direct_action_request(user_message, stream_callback)
            else:
                self.logger.info("🎯 Routing to general request handler")
                result = await self._handle_general_request(user_message, stream_callback)
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant", 
                "content": result.get("response", "")
            })
            
            self.logger.info(f"✅ Chat completed successfully. Status: {result.get('status', 'unknown')}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Chat error: {str(e)}", exc_info=True)
            error_result = {
                "response": f"I encountered an error: {str(e)}",
                "actions": [],
                "status": "error",
                "error": str(e)
            }
            
            self.conversation_history.append({
                "role": "assistant",
                "content": error_result["response"]
            })
            
            return error_result
    
    def _is_planning_request(self, message: str) -> bool:
        """Check if message is asking for a lighting plan."""
        planning_keywords = [
            "plan", "create", "design", "make", "build",
            "intro", "verse", "chorus", "bridge", "outro",
            "section", "segment", "whole song"
        ]
        is_planning = any(keyword in message.lower() for keyword in planning_keywords)
        self.logger.debug(f"🔍 Planning request check: {is_planning} (keywords found: {[kw for kw in planning_keywords if kw in message.lower()]})")
        return is_planning
    
    def _is_direct_action_request(self, message: str) -> bool:
        """Check if message is asking for direct actions."""
        action_keywords = [
            "flash", "strobe", "fade", "dim", "bright",
            "red", "blue", "green", "white", "color",
            "now", "immediately", "quick"
        ]
        is_action = any(keyword in message.lower() for keyword in action_keywords)
        self.logger.debug(f"🔍 Direct action check: {is_action} (keywords found: {[kw for kw in action_keywords if kw in message.lower()]})")
        return is_action
    
    async def _handle_planning_request(self, message: str, callback: Optional[Callable]) -> dict:
        """Handle requests for lighting plans."""
        self.logger.info(f"🎛️ Starting planning request handler for: {message[:50]}{'...' if len(message) > 50 else ''}")
        
        if callback:
            callback("🎛️ Creating lighting plan...\n")
        
        try:
            # Log the sub-agent call
            context = self._get_current_context()
            self.logger.info(f"🤖 Calling LightingPlannerAgent.create_plan_from_user_prompt_async")
            self.logger.debug(f"   📝 Input prompt: {message}")
            self.logger.debug(f"   🎵 Context: {context}")
            
            # Use the lighting planner
            plan_result = await self.planner.create_plan_from_user_prompt_async(
                user_prompt=message,
                context_summary=context,
                callback=callback
            )
            
            # Log the planning result
            self.logger.info(f"📊 LightingPlannerAgent result: status={plan_result.get('status', 'unknown')}")
            if plan_result["status"] == "success":
                plan_count = len(plan_result.get("lighting_plan", []))
                self.logger.info(f"   ✅ Generated {plan_count} lighting plan entries")
                for i, entry in enumerate(plan_result.get("lighting_plan", [])[:3]):  # Log first 3
                    self.logger.debug(f"   📋 Entry {i+1}: {entry.get('time', 0)}s - {entry.get('label', 'Unknown')}")
            else:
                error = plan_result.get('error', 'Unknown error')
                self.logger.error(f"   ❌ Planning failed: {error}")
                return {
                    "response": f"I couldn't create a lighting plan: {error}",
                    "actions": [],
                    "status": "error"
                }

            # Translate plan to actions
            if callback:
                callback("\n🎭 Translating to fixture actions...\n")
            
            self.logger.info(f"🤖 Calling EffectTranslatorAgent.run_async")
            self.logger.debug(f"   📝 Input plan entries: {len(plan_result['lighting_plan'])}")
            
            action_result = await self.translator.run_async({
                "lighting_plan": plan_result["lighting_plan"]
            }, callback=callback)
            
            # Log the translation result
            self.logger.info(f"📊 EffectTranslatorAgent result: status={action_result.get('status', 'unknown')}")
            if action_result["status"] == "success":
                action_count = len(action_result.get("actions", []))
                self.logger.info(f"   ✅ Generated {action_count} fixture actions")
                for i, action in enumerate(action_result.get("actions", [])[:3]):  # Log first 3
                    self.logger.debug(f"   🎭 Action {i+1}: {action}")
            else:
                error = action_result.get('error', 'Unknown error')
                self.logger.warning(f"   ⚠️ Translation had issues: {error}")
            
            # Format response
            plan_count = len(plan_result["lighting_plan"])
            action_count = len(action_result.get("actions", []))
            
            response = f"I've created a lighting plan with {plan_count} entries and generated {action_count} fixture actions."
            
            if plan_count > 0:
                response += "\n\nPlan summary:"
                for i, entry in enumerate(plan_result["lighting_plan"][:3]):  # Show first 3
                    response += f"\n• {entry['time']}s: {entry['label']} - {entry['description']}"
                
                if plan_count > 3:
                    response += f"\n... and {plan_count - 3} more entries"
            
            result = {
                "response": response,
                "actions": action_result.get("actions", []),
                "lighting_plan": plan_result["lighting_plan"],
                "status": "success"
            }
            
            self.logger.info(f"✅ Planning request completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Planning request failed: {str(e)}", exc_info=True)
            return {
                "response": f"I encountered an error during planning: {str(e)}",
                "actions": [],
                "status": "error",
                "error": str(e)
            }
    
    async def _handle_direct_action_request(self, message: str, callback: Optional[Callable]) -> dict:
        """Handle requests for immediate actions."""
        self.logger.info(f"⚡ Starting direct action request handler for: {message[:50]}{'...' if len(message) > 50 else ''}")
        
        if callback:
            callback("⚡ Creating immediate lighting effect...\n")
        
        try:
            # Log the sub-agent call
            self.logger.info(f"🤖 Calling EffectTranslatorAgent.translate_single_effect")
            self.logger.debug(f"   📝 Effect description: {message}")
            self.logger.debug(f"   ⏰ Time: 0.0 (immediate)")
            self.logger.debug(f"   ⏱️ Duration: 5.0s (default)")
            
            # Use effect translator directly
            actions = await self.translator.translate_single_effect(
                effect_description=message,
                time=0.0,  # Immediate
                duration=5.0,  # Default 5 seconds
                callback=callback
            )
            
            # Log the translation result
            action_count = len(actions) if actions else 0
            self.logger.info(f"📊 EffectTranslatorAgent.translate_single_effect result: {action_count} actions generated")
            
            if actions:
                for i, action in enumerate(actions[:5]):  # Log first 5 actions
                    self.logger.debug(f"   🎭 Action {i+1}: {action}")
                if len(actions) > 5:
                    self.logger.debug(f"   ... and {len(actions) - 5} more actions")
            else:
                self.logger.warning("   ⚠️ No actions generated from effect translation")
            
            response = f"I've created {len(actions)} immediate lighting actions."
            
            if actions:
                response += "\n\nActions:"
                for action in actions[:3]:  # Show first 3
                    response += f"\n• {action}"
                
                if len(actions) > 3:
                    response += f"\n... and {len(actions) - 3} more actions"
            
            result = {
                "response": response,
                "actions": actions,
                "status": "success"
            }
            
            self.logger.info(f"✅ Direct action request completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Direct action request failed: {str(e)}", exc_info=True)
            return {
                "response": f"I encountered an error creating the effect: {str(e)}",
                "actions": [],
                "status": "error",
                "error": str(e)
            }
    
    async def _handle_general_request(self, message: str, callback: Optional[Callable]) -> dict:
        """Handle general questions or requests."""
        self.logger.info(f"💬 Starting general request handler for: {message[:50]}{'...' if len(message) > 50 else ''}")
        
        # This could use a general chat model or route to specific handlers
        if callback:
            callback("🤔 Let me help you with that...\n")
        
        self.logger.debug("💭 Generating general help response (no sub-agents called)")
        
        response = "I can help you with lighting control! Try asking me to:\n"
        response += "• 'Create a plan for the intro' (for lighting plans)\n"
        response += "• 'Flash all lights red' (for immediate actions)\n"
        response += "• 'Make the lights pulse with the beat' (for beat-synced effects)"
        
        result = {
            "response": response,
            "actions": [],
            "status": "info"
        }
        
        self.logger.info("✅ General request completed - provided help information")
        return result
    
    def _get_current_context(self) -> str:
        """Get current song/context information."""
        # This would normally get info from app_state
        context = "Electronic dance music, BPM: 128, Duration: 240s"
        self.logger.debug(f"🎵 Retrieved context: {context}")
        return context
    
    async def get_suggestions(self) -> list:
        """Get suggested prompts for the user."""
        self.logger.debug("💡 Generating suggestion prompts")
        suggestions = [
            "Create an energetic intro with blue lights",
            "Flash all lights red for 3 seconds", 
            "Make a rainbow chase effect",
            "Create a plan for the whole song",
            "Strobe the moving heads during the drop",
            "Fade to warm white lights"
        ]
        self.logger.debug(f"   📝 Generated {len(suggestions)} suggestions")
        return suggestions
    
    def clear_history(self):
        """Clear conversation history."""
        old_count = len(self.conversation_history)
        self.conversation_history = []
        self.logger.info(f"🗑️ Conversation history cleared ({old_count} messages removed)")
    
    def get_history(self) -> list:
        """Get conversation history."""
        history = self.conversation_history.copy()
        self.logger.debug(f"📚 Retrieved conversation history: {len(history)} messages")
        return history


# Example usage
async def demo_chat_session():
    """Demonstrate the AI assistant in a chat-like interface."""
    # Set up logging for the demo
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('ai_lighting_assistant_demo.log')
        ]
    )
    
    logger.info("🚀 Starting AI Lighting Assistant Demo")
    
    assistant = AILightingAssistant()
    
    print("🎭 AI Lighting Assistant Demo")
    print("=" * 40)
    
    # Streaming callback for demo
    def stream_callback(chunk: str):
        print(chunk, end="", flush=True)
    
    # Test conversations
    test_messages = [
        "Create a plan for an energetic intro",
        "Flash all lights red now",
        "What can you help me with?"
    ]
    
    for message in test_messages:
        print(f"\n👤 User: {message}")
        print("🤖 Assistant: ", end="")
        
        logger.info(f"🎯 Demo processing message: {message}")
        
        result = await assistant.chat(message, stream_callback)
        
        if not result["response"].endswith("\n"):
            print()  # Add newline if not streamed
        
        if result.get("actions"):
            action_count = len(result['actions'])
            print(f"\n🎬 Generated {action_count} actions")
            logger.info(f"📊 Demo result: {action_count} actions, status: {result.get('status')}")
        
        print("-" * 40)
    
    # Show conversation history
    print("\n📝 Conversation History:")
    history = assistant.get_history()
    for i, msg in enumerate(history):
        role = "👤" if msg["role"] == "user" else "🤖"
        content = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
        print(f"{i+1}. {role} {content}")
    
    logger.info(f"🎉 Demo completed successfully with {len(history)} conversation exchanges")


if __name__ == "__main__":
    # Run demo
    print("Note: This is a demo with mock agents. Replace with actual agent imports to test.")
    asyncio.run(demo_chat_session())
