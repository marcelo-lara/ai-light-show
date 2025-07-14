#!/usr/bin/env python3
"""
Test script for the Song Analysis Service.
"""

import asyncio
import aiohttp
import sys
import json
from pathlib import Path


async def test_song_analysis_service(base_url="http://localhost:8001"):
    """Test the song analysis service."""
    
    print(f"🧪 Testing Song Analysis Service at {base_url}")
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Health check
        print("\n1. Testing health check...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health = await response.json()
                    print(f"✅ Health check passed: {health['status']}")
                    print(f"   Dependencies: {health['dependencies']}")
                else:
                    print(f"❌ Health check failed: HTTP {response.status}")
                    return
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return
        
        # Test 2: Root endpoint
        print("\n2. Testing root endpoint...")
        try:
            async with session.get(f"{base_url}/") as response:
                if response.status == 200:
                    root = await response.json()
                    print(f"✅ Root endpoint: {root['message']}")
                else:
                    print(f"❌ Root endpoint failed: HTTP {response.status}")
        except Exception as e:
            print(f"❌ Root endpoint failed: {e}")
        
        # Test 3: Song analysis (if test file exists)
        test_song_path = "/app/songs/born_slippy.mp3"  # Docker path
        local_test_song = "./test_song.mp3"  # Local test file
        
        print(f"\n3. Testing song analysis...")
        
        # Check if we have a test song
        song_path = None
        if Path(local_test_song).exists():
            song_path = local_test_song
        else:
            print(f"   No test song found at {local_test_song}")
            print(f"   To test song analysis, place an MP3 file at {local_test_song}")
            return
        
        try:
            data = {
                "song_path": song_path,
                "reset_file": True,
                "debug": True
            }
            
            async with session.post(f"{base_url}/analyze", json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Song analysis completed: {result['status']}")
                    metadata = result.get('metadata', {})
                    print(f"   BPM: {metadata.get('bpm', 'N/A')}")
                    print(f"   Duration: {metadata.get('duration', 'N/A'):.1f}s")
                    print(f"   Beats: {len(metadata.get('beats', []))}")
                    print(f"   Patterns: {len(metadata.get('patterns', []))}")
                else:
                    error_text = await response.text()
                    print(f"❌ Song analysis failed: HTTP {response.status}")
                    print(f"   Error: {error_text}")
        except Exception as e:
            print(f"❌ Song analysis failed: {e}")
    
    print("\n🎉 Testing completed!")


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8001"
    asyncio.run(test_song_analysis_service(base_url))
