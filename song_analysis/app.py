"""
Song Analysis Microservice for AI Light Show.
Handles audio analysis: beat detection, stem separation, pattern analysis, etc.
Consumed by the main backend service.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import tempfile
import os
import json
from typing import Dict, Any, Optional, List
import logging

# Import audio analysis modules
from services.audio_analyzer import SongAnalyzer
from services.beats_rms_flux import analyze_beats_rms_flux, create_dataframe, filter_dataframe, dataframe_to_response
from shared.models.song_metadata import SongMetadata
import pandas as pd

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
    song_name: str  # Changed from song_path to song_name
    reset_file: bool = True
    debug: bool = False

class AnalysisResponse(BaseModel):
    status: str
    metadata: Dict[str, Any]
    message: Optional[str] = None

# New models for the beats/RMS/flux endpoint
class BeatsRmsFluxRequest(BaseModel):
    song_name: str
    force: bool = False
    start_time: Optional[float] = None
    end_time: Optional[float] = None

class BeatsRmsFluxResponse(BaseModel):
    status: str
    beats: List[float]
    rms: List[float]
    flux: List[float]
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

@app.post("/analyze", response_model=BeatsRmsFluxResponse)
async def analyze_beats_rms_flux_endpoint(request: BeatsRmsFluxRequest):
    """
    Extracts beats, RMS, and flux from an audio file with caching.

    - Caches analysis results in a .pkl file to speed up subsequent requests.
    - Use `force=true` to bypass the cache.
    - Supports `start_time` and `end_time` to filter the response data.

    Args:
        request: Request model with `song_name` and options.

    Returns:
        Response model with beat times, RMS, and spectral flux arrays.
    """
    try:
        logger.info(f"Requested beats/RMS/flux analysis for: {request.song_name}")
        song_name = request.song_name
        # Validate song path exists
        song_metadata = SongMetadata(song_name)
        song_path = song_metadata.mp3_path
        
        # Use SongMetadata to get the data folder path
        pickle_path = Path(song_metadata.data_folder) / f"{song_name}.pkl"
        
        # Ensure data folder exists
        pickle_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if we should load from cache or force re-analysis
        if not request.force and pickle_path.exists():
            logger.info(f"Loading existing analysis from: {pickle_path}")
            df = pd.read_pickle(pickle_path)
        else:
            logger.info(f"Performing new analysis for: {song_path}")
            # Perform analysis
            analysis_data = analyze_beats_rms_flux(song_path)
            
            # Create DataFrame
            df = create_dataframe(analysis_data)
            
            # Save to pickle
            df.to_pickle(pickle_path)
            logger.info(f"Analysis saved to: {pickle_path}")
        
        # Filter by time range if specified
        df_filtered = filter_dataframe(df, request.start_time, request.end_time)
        
        # Convert to response format
        response_data = dataframe_to_response(df_filtered)
        
        return BeatsRmsFluxResponse(
            status="ok",
            beats=response_data["beats"],
            rms=response_data["rms"],
            flux=response_data["flux"]
        )
        
    except Exception as e:
        logger.error(f"Failed to analyze beats/RMS/flux: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/analyze_song", response_model=AnalysisResponse)
async def analyze_song(request: AnalysisRequest):
    """
    Analyze a song file using song name and return metadata including beats, BPM, patterns, etc.
    
    Args:
        request: Analysis request containing song name and options
        
    Returns:
        Analysis response with song metadata
    """
    try:
        logger.info(f"Requested analysis for song: {request.song_name}")
        
        # Build the full path using the internal volume mapping
        songs_folder = Path("/app/static/songs")
        song_name = request.song_name
        
        # Create SongMetadata object
        try:
            song = SongMetadata(
                song_name=song_name,
                songs_folder=str(songs_folder),
                ignore_existing=request.reset_file
            )
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Song file not found: {song_name} (looked in {songs_folder})")
        
        # Perform analysis
        analyzed_song = analyzer.analyze(
            song=song,
            reset_file=request.reset_file,
            debug=request.debug
        )
        
        # Save results
        analyzed_song.save()
        
        logger.info(f"Analysis completed for song: {request.song_name}")
        
        return AnalysisResponse(
            status="success",
            metadata=analyzed_song.to_dict(),
            message="Song analysis completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Analysis failed for song {request.song_name}: {str(e)}")
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
            # Extract song name from filename
            song_name = Path(file.filename).stem
            
            # Create analysis request using song name
            request = AnalysisRequest(
                song_name=song_name,
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

@app.get("/analyze/batch")
async def analyze_batch(reset_file: bool = True):
    """
    Analyze all MP3 files in the internal songs folder.
    
    Args:
        reset_file: Whether to reset existing analysis
        
    Returns:
        Batch analysis results
    """
    try:
        # Use the internal volume mapped songs folder
        songs_folder = Path("/app/static/songs")
        
        if not songs_folder.exists():
            raise HTTPException(status_code=404, detail=f"Songs folder not found: {songs_folder}")
        
        mp3_files = list(songs_folder.glob("*.mp3"))
        if not mp3_files:
            raise HTTPException(status_code=404, detail="No MP3 files found in songs folder")
        
        results = []
        for mp3_file in sorted(mp3_files):
            try:
                # Use just the song name (without .mp3 extension)
                song_name = mp3_file.stem
                
                request = AnalysisRequest(
                    song_name=song_name,
                    reset_file=reset_file,
                    debug=False
                )
                
                response = await analyze_song(request)
                results.append({
                    "song_name": song_name,
                    "file": mp3_file.name,
                    "status": "success",
                    "metadata": response.metadata
                })
                
            except Exception as e:
                results.append({
                    "song_name": mp3_file.stem,
                    "file": mp3_file.name,
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

@app.get("/songs")
async def list_songs():
    """
    List all available MP3 files in the songs folder.
    
    Returns:
        List of available song names
    """
    try:
        songs_folder = Path("/app/static/songs")
        
        if not songs_folder.exists():
            return {"songs": [], "message": "Songs folder not found"}
        
        mp3_files = list(songs_folder.glob("*.mp3"))
        song_names = [mp3_file.stem for mp3_file in sorted(mp3_files)]
        
        return {
            "songs": song_names,
            "total": len(song_names),
            "folder": str(songs_folder)
        }
        
    except Exception as e:
        logger.error(f"Failed to list songs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list songs: {str(e)}")

@app.get("/status")
async def health_status():
    """
    Get the current status of the service.
    This endpoint can be used get the langchain current running nodes and their status.

    Returns:
        {"status": str, "message": str}
    """
    # TODO: Implement actual status check logic
    return {"status": "ok", "message": "Idle and ready for requests"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
