"""
Standalone Song Analysis Service for AI Light Show

This service handles audio analysis tasks including:
- Song structure analysis using Essentia
- Beat detection and BPM analysis
- Stem separation using Demucs
- Pattern detection and clustering
- Audio feature extraction

Built to be consumed by the main AI Light Show backend service.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import tempfile
import os
import json
from typing import Dict, Any, Optional
import logging

# Import audio analysis modules
from services.audio_analyzer import SongAnalyzer
from models.song_metadata import SongMetadata

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Song Analysis Service",
    description="Standalone audio analysis service for AI Light Show",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the analyzer
analyzer = SongAnalyzer()

# Request/Response models
class AnalysisRequest(BaseModel):
    song_path: str
    reset_file: bool = True
    debug: bool = False

class AnalysisResponse(BaseModel):
    status: str
    metadata: Dict[str, Any]
    message: Optional[str] = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Song Analysis Service is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "song-analysis",
        "version": "1.0.0",
        "dependencies": {
            "essentia": "available",
            "librosa": "available", 
            "demucs": "available",
            "torch": "available"
        }
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_song(request: AnalysisRequest):
    """
    Analyze a song file and return metadata including beats, BPM, patterns, etc.
    
    Args:
        request: Analysis request containing song path and options
        
    Returns:
        Analysis response with song metadata
    """
    try:
        logger.info(f"Starting analysis for: {request.song_path}")
        
        # Validate input file exists
        song_path = Path(request.song_path)
        if not song_path.exists():
            raise HTTPException(status_code=404, detail=f"Song file not found: {request.song_path}")
        
        # Create SongMetadata object
        song = SongMetadata(
            song_name=song_path.stem,
            songs_folder=str(song_path.parent),
            ignore_existing=request.reset_file
        )
        
        # Perform analysis
        analyzed_song = analyzer.analyze(
            song=song,
            reset_file=request.reset_file,
            debug=request.debug
        )
        
        # Save results
        analyzed_song.save()
        
        logger.info(f"Analysis completed for: {request.song_path}")
        
        return AnalysisResponse(
            status="success",
            metadata=analyzed_song.to_dict(),
            message="Song analysis completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Analysis failed for {request.song_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/analyze/upload", response_model=AnalysisResponse)
async def analyze_uploaded_song(
    file: UploadFile = File(...),
    reset_file: bool = True,
    debug: bool = False
):
    """
    Upload and analyze a song file.
    
    Args:
        file: Audio file to analyze
        reset_file: Whether to reset existing analysis
        debug: Enable debug output
        
    Returns:
        Analysis response with song metadata
    """
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith(('.mp3', '.wav', '.flac', '.m4a')):
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Create analysis request
            request = AnalysisRequest(
                song_path=temp_path,
                reset_file=reset_file,
                debug=debug
            )
            
            # Analyze the file
            response = await analyze_song(request)
            
            # Update response with original filename
            response.metadata['original_filename'] = file.filename
            
            return response
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Upload analysis failed for {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload analysis failed: {str(e)}")

@app.get("/analyze/batch/{songs_folder:path}")
async def analyze_batch(songs_folder: str, reset_file: bool = True):
    """
    Analyze all MP3 files in a folder.
    
    Args:
        songs_folder: Path to folder containing MP3 files
        reset_file: Whether to reset existing analysis
        
    Returns:
        Batch analysis results
    """
    try:
        folder_path = Path(songs_folder)
        if not folder_path.exists():
            raise HTTPException(status_code=404, detail=f"Folder not found: {songs_folder}")
        
        mp3_files = list(folder_path.glob("*.mp3"))
        if not mp3_files:
            raise HTTPException(status_code=404, detail="No MP3 files found in folder")
        
        results = []
        for mp3_file in sorted(mp3_files):
            try:
                request = AnalysisRequest(
                    song_path=str(mp3_file),
                    reset_file=reset_file,
                    debug=False
                )
                
                response = await analyze_song(request)
                results.append({
                    "file": str(mp3_file),
                    "status": "success",
                    "metadata": response.metadata
                })
                
            except Exception as e:
                results.append({
                    "file": str(mp3_file),
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "status": "completed",
            "total_files": len(mp3_files),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Batch analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
