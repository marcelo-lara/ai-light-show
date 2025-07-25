"""API router for AI-powered lighting control."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from ..services.ollama import query_ollama_with_actions, execute_confirmed_action
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

@router.post("/chat", response_model=ChatResponse)
async def ai_chat(request: ChatRequest):
    """Chat with AI assistant for lighting design."""
    
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
