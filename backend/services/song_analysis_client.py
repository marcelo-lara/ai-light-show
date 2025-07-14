"""
Client for communicating with the Song Analysis Service.
"""

import aiohttp
import asyncio
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SongAnalysisClient:
    """Client for communicating with the standalone Song Analysis Service."""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the song analysis service
        """
        self.base_url = base_url or os.getenv('SONG_ANALYSIS_SERVICE_URL', 'http://song-analysis:8001')
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the song analysis service is healthy.
        
        Returns:
            Health status response
        """
        try:
            if not self.session:
                return {"status": "unreachable", "error": "No session available"}
                
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {"status": "unreachable", "error": str(e)}
    
    async def analyze_song(self, song_name: str, reset_file: bool = True, debug: bool = False) -> Dict[str, Any]:
        """
        Analyze a song file by name.
        
        Args:
            song_name: Name of the song (without .mp3 extension)
            reset_file: Whether to reset existing analysis
            debug: Enable debug output
            
        Returns:
            Analysis results
        """
        try:
            if not self.session:
                raise Exception("No session available")
                
            data = {
                "song_name": song_name,
                "reset_file": reset_file,
                "debug": debug
            }
            
            async with self.session.post(f"{self.base_url}/analyze", json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Analysis failed with HTTP {response.status}: {error_text}")
                    
        except Exception as e:
            logger.error(f"Song analysis failed: {str(e)}")
            raise
    
    async def analyze_batch(self, reset_file: bool = True) -> Dict[str, Any]:
        """
        Analyze all songs in the songs folder.
        
        Args:
            reset_file: Whether to reset existing analysis
            
        Returns:
            Batch analysis results
        """
        try:
            if not self.session:
                raise Exception("No session available")
                
            params = {"reset_file": reset_file}
            
            async with self.session.get(f"{self.base_url}/analyze/batch", params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Batch analysis failed with HTTP {response.status}: {error_text}")
                    
        except Exception as e:
            logger.error(f"Batch analysis failed: {str(e)}")
            raise
    
    async def list_songs(self) -> Dict[str, Any]:
        """
        List all available songs.
        
        Returns:
            List of available song names
        """
        try:
            if not self.session:
                raise Exception("No session available")
                
            async with self.session.get(f"{self.base_url}/songs") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to list songs with HTTP {response.status}: {error_text}")
                    
        except Exception as e:
            logger.error(f"Failed to list songs: {str(e)}")
            raise


# Convenience function for synchronous usage
def analyze_song_sync(song_name: str, reset_file: bool = True, debug: bool = False) -> Dict[str, Any]:
    """
    Synchronous wrapper for song analysis.
    
    Args:
        song_name: Name of the song (without .mp3 extension)
        reset_file: Whether to reset existing analysis
        debug: Enable debug output
        
    Returns:
        Analysis results
    """
    async def _analyze():
        async with SongAnalysisClient() as client:
            return await client.analyze_song(song_name, reset_file, debug)
    
    return asyncio.run(_analyze())
