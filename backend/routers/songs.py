"""Songs management router for the AI Light Show system."""

import json
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException
from ..config import SONGS_DIR

router = APIRouter(prefix="/songs", tags=["songs"])


@router.post("/save")
async def save_song_data(request: Request) -> Dict[str, str]:
    """Save song data to file."""
    try:
        payload = await request.json()
        file = payload.get("fileName")
        data = payload.get("data")

        if not file or not data:
            print("ERROR: Missing file or data in request payload")
            print(f"    fileName: {file}")
            print(f"    data: {data}")
            raise HTTPException(
                status_code=400, 
                detail="Missing file or data"
            )

        file_path = SONGS_DIR / file
        file_path.write_text(json.dumps(data, indent=2))
        
        return {"status": "ok", "message": f"{file} saved."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
