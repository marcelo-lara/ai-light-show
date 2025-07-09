"""API router for AI-powered lighting control."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from ..ai.ollama_client import query_ollama_with_actions, execute_confirmed_action
from ..ai.cue_interpreter import CueInterpreter
from ..services.cue_service import CueManager
from ..models.app_state import app_state

router = APIRouter(prefix="/ai", tags=["AI Lighting"])

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    response: str
    action_proposals: List[Dict[str, Any]]
    success: bool

class ActionConfirmationRequest(BaseModel):
    action_id: str
    proposals: List[Dict[str, Any]]
    session_id: Optional[str] = "default"

class CueCommand(BaseModel):
    command: str
    session_id: Optional[str] = "default"

@router.post("/chat", response_model=ChatResponse)
async def ai_chat(request: ChatRequest):
    """Chat with AI assistant for lighting design and cue management."""
    
    try:
        # Get AI response and action proposals for confirmation
        ai_response, action_proposals = await query_ollama_with_actions(
            request.message, 
            request.session_id or "default"
        )
        
        return ChatResponse(
            response=ai_response,
            action_proposals=action_proposals,
            success=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI chat error: {str(e)}")

@router.post("/execute-cue", response_model=Dict[str, Any])
async def execute_cue_command(request: CueCommand):
    """Execute a natural language cue command directly."""
    
    try:
        # Validate current song
        if not app_state.current_song:
            raise HTTPException(status_code=400, detail="No song currently loaded")
        
        # Get system context
        from ..ai.ollama_client import load_fixture_config
        fixtures, presets, chasers = load_fixture_config()
        
        if not fixtures:
            raise HTTPException(status_code=400, detail="No fixtures configured")
        
        if not presets:
            raise HTTPException(status_code=400, detail="No presets configured")
        
        # Execute command
        cue_manager = CueManager()
        interpreter = CueInterpreter(cue_manager)
        
        success, message = interpreter.execute_command(
            request.command,
            app_state.current_song,
            fixtures,
            presets
        )
        
        # Get interpretation details for feedback
        interpretation = interpreter.interpret_command(
            request.command,
            app_state.current_song,
            fixtures,
            presets
        )
        
        return {
            "success": success,
            "message": message,
            "command": request.command,
            "interpretation": interpretation,
            "confidence": interpretation.get('confidence', 0.0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Command execution error: {str(e)}")

@router.get("/current-context")
async def get_current_context():
    """Get current AI context (song, fixtures, presets)."""
    
    try:
        from ..ai.ollama_client import get_current_song, get_current_fixtures, get_current_presets
        
        return {
            "song": get_current_song(),
            "fixtures": len(get_current_fixtures()),
            "presets": len(get_current_presets()),
            "has_song": app_state.current_song is not None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context retrieval error: {str(e)}")

@router.post("/suggestions")
async def get_lighting_suggestions(song_section: Optional[str] = None):
    """Get AI-generated lighting suggestions for current song or specific section."""
    
    try:
        if not app_state.current_song:
            raise HTTPException(status_code=400, detail="No song currently loaded")
        
        # Construct prompt for suggestions
        if song_section:
            prompt = f"Suggest lighting effects for the {song_section} section of this song"
        else:
            prompt = "Suggest a complete lighting design for this song"
        
        # Get AI suggestions
        from ..ai.ollama_client import query_ollama_mistral
        suggestions = query_ollama_mistral(prompt, "suggestions")
        
        return {
            "suggestions": suggestions,
            "song_title": app_state.current_song.title,
            "section": song_section,
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestions error: {str(e)}")

@router.delete("/clear-conversation/{session_id}")
async def clear_ai_conversation(session_id: str):
    """Clear AI conversation history for a session."""
    
    try:
        from ..ai.ollama_client import clear_conversation
        clear_conversation(session_id)
        
        return {"success": True, "message": f"Conversation cleared for session {session_id}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear conversation error: {str(e)}")

@router.post("/confirm-action")
async def confirm_and_execute_action(request: ActionConfirmationRequest):
    """Confirm and execute a proposed lighting action."""
    
    try:
        from ..ai.ollama_client import execute_confirmed_action
        
        success, message = execute_confirmed_action(
            request.action_id,
            request.proposals
        )
        
        return {
            "success": success,
            "message": message,
            "action_id": request.action_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Action execution error: {str(e)}")
