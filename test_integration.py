#!/usr/bin/env python3
"""
Test script to verify the song analysis service integration
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.song_analysis_client import SongAnalysisClient

# Override the service URL for localhost testing
import os
os.environ['SONG_ANALYSIS_SERVICE_URL'] = 'http://localhost:8001'

async def test_song_analysis_integration():
    """Test the complete integration"""
    print("🧪 Testing Song Analysis Service Integration")
    print("=" * 60)
    
    async with SongAnalysisClient() as client:
        # Test 1: Health check
        print("1. Health Check...")
        try:
            health = await client.health_check()
            print(f"   ✅ Service Health: {health.get('status', 'unknown')}")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            return False
        
        # Test 2: List available songs
        print("\n2. List Available Songs...")
        try:
            songs_info = await client.list_songs()
            songs = songs_info.get("songs", [])
            total = songs_info.get("total", 0)
            print(f"   📁 Found {total} songs")
            if songs:
                print(f"   📄 First 5 songs: {songs[:5]}")
        except Exception as e:
            print(f"   ❌ Failed to list songs: {e}")
            return False
        
        # Test 3: Analyze a song
        if songs:
            test_song = songs[0]  # Use the first available song
            print(f"\n3. Analyzing Song: '{test_song}'...")
            try:
                result = await client.analyze_song(
                    song_name=test_song,
                    reset_file=False,  # Use existing analysis if available
                    debug=False
                )
                
                if result.get("status") == "success":
                    metadata = result.get("metadata", {})
                    print(f"   ✅ Analysis successful!")
                    print(f"   🎵 BPM: {metadata.get('bpm', 'unknown')}")
                    print(f"   ⏱️  Duration: {metadata.get('duration', 'unknown'):.1f}s")
                    print(f"   🥁 Beats: {len(metadata.get('beats', []))}")
                    
                    patterns = metadata.get("patterns", [])
                    drum_patterns = [p for p in patterns if p.get('stem') == 'drums']
                    if drum_patterns:
                        segments = len(drum_patterns[0].get('clusters', []))
                        print(f"   🎼 Drum segments: {segments}")
                    
                    arrangement = metadata.get("arrangement", [])
                    print(f"   🎯 Arrangement sections: {len(arrangement)}")
                    
                    return True
                else:
                    print(f"   ❌ Analysis failed: {result.get('message', 'Unknown error')}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Analysis failed: {e}")
                return False
        else:
            print("\n3. No songs available to test analysis")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_song_analysis_integration())
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Integration test PASSED! Song Analysis Service is working correctly.")
        exit(0)
    else:
        print("❌ Integration test FAILED! Please check the service configuration.")
        exit(1)
