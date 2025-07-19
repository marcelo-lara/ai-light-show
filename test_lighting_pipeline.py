#!/usr/bin/env python3
"""
Test script for the LangGraph Lighting Pipeline
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.langgraph.lighting_pipeline import run_lighting_pipeline

def test_pipeline():
    """Test the lighting pipeline with sample data"""
    
    # Sample segment data
    test_segment = {
        "segment": {
            "name": "Verse 1",
            "start": 10.0,
            "end": 25.0,
            "features": {
                "energy": 0.7,
                "valence": 0.6,
                "tempo": 120,
                "key": "C major",
                "loudness": -8.5,
                "danceability": 0.8
            }
        }
    }
    
    print("🧪 Testing Lighting Pipeline...")
    print(f"Input: {test_segment}")
    print("\n" + "="*50)
    
    try:
        result = run_lighting_pipeline(test_segment)
        
        print("\n" + "="*50)
        print("📊 Pipeline Result:")
        print(f"Context Summary: {result.get('context_summary', 'N/A')}")
        print(f"Actions Count: {len(result.get('actions', []))}")
        print(f"DMX Commands Count: {len(result.get('dmx', []))}")
        
        if result.get('actions'):
            print("\nSample Actions:")
            for i, action in enumerate(result['actions'][:3]):  # Show first 3
                print(f"  {i+1}. {action}")
        
        if result.get('dmx'):
            print("\nSample DMX Commands:")
            for i, dmx in enumerate(result['dmx'][:3]):  # Show first 3
                print(f"  {i+1}. {dmx}")
                
        print("\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pipeline()
    sys.exit(0 if success else 1)
