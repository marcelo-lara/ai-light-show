#!/usr/bin/env python3
"""
Health check script for verifying Song Analysis Service connectivity.
"""

import asyncio
import sys
from backend.services.song_analysis_client import SongAnalysisClient


async def check_song_analysis_service():
    """Check if the Song Analysis Service is accessible and healthy."""
    
    print("🔍 Checking Song Analysis Service connectivity...")
    
    try:
        async with SongAnalysisClient() as client:
            # Perform health check
            health = await client.health_check()
            
            if health.get("status") == "healthy":
                print("✅ Song Analysis Service is healthy!")
                print(f"   Service: {health.get('service', 'unknown')}")
                print(f"   Version: {health.get('version', 'unknown')}")
                
                dependencies = health.get('dependencies', {})
                print("   Dependencies:")
                for dep, status in dependencies.items():
                    print(f"     - {dep}: {status}")
                
                return True
            else:
                print(f"❌ Song Analysis Service is not healthy: {health.get('status')}")
                if 'error' in health:
                    print(f"   Error: {health['error']}")
                return False
                
    except Exception as e:
        print(f"❌ Failed to connect to Song Analysis Service: {str(e)}")
        print("💡 Make sure the service is running:")
        print("   - docker-compose up song-analysis")
        print("   - Or check the SONG_ANALYSIS_SERVICE_URL environment variable")
        return False


if __name__ == "__main__":
    success = asyncio.run(check_song_analysis_service())
    sys.exit(0 if success else 1)
