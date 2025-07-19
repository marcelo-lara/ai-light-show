"""
Integration example showing how to use the LangGraph Pipeline
in the main backend application
"""
import json
from backend.services.langgraph.lighting_pipeline import run_lighting_pipeline

def integrate_with_song_analysis():
    """
    Example of how the pipeline integrates with the song analysis workflow
    """
    
    # Example: This would come from the song analysis service
    song_segments = [
        {
            "segment": {
                "name": "Intro",
                "start": 0.0,
                "end": 8.0,
                "features": {
                    "energy": 0.3,
                    "valence": 0.4,
                    "tempo": 90,
                    "key": "Am",
                    "loudness": -12.0,
                    "danceability": 0.3
                }
            }
        },
        {
            "segment": {
                "name": "Verse",
                "start": 8.0,
                "end": 24.0,
                "features": {
                    "energy": 0.6,
                    "valence": 0.7,
                    "tempo": 120,
                    "key": "C",
                    "loudness": -8.0,
                    "danceability": 0.7
                }
            }
        },
        {
            "segment": {
                "name": "Chorus",
                "start": 24.0,
                "end": 40.0,
                "features": {
                    "energy": 0.9,
                    "valence": 0.8,
                    "tempo": 120,
                    "key": "C",
                    "loudness": -5.0,
                    "danceability": 0.9
                }
            }
        }
    ]
    
    print("🎵 Processing song segments through AI Lighting Pipeline...")
    
    all_results = []
    
    for i, segment_data in enumerate(song_segments):
        print(f"\n📍 Processing segment {i+1}: {segment_data['segment']['name']}")
        
        # Run the 3-agent pipeline
        result = run_lighting_pipeline(segment_data)
        
        # Store result with timing info
        enriched_result = {
            "segment_index": i,
            "segment_name": segment_data['segment']['name'],
            "start_time": segment_data['segment']['start'],
            "end_time": segment_data['segment']['end'],
            "pipeline_result": result
        }
        
        all_results.append(enriched_result)
        
        print(f"   ✓ Generated {len(result.get('actions', []))} lighting actions")
        print(f"   ✓ Generated {len(result.get('dmx', []))} DMX commands")
    
    # Save combined results
    output_file = "logs/full_song_lighting_design.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Saved complete lighting design to {output_file}")
    print(f"🎉 Processed {len(all_results)} segments successfully!")
    
    return all_results

# Example usage in a FastAPI endpoint:
def example_fastapi_integration():
    """
    This shows how you could integrate the pipeline into a FastAPI endpoint
    """
    print("\n🌐 Example FastAPI Integration:")
    print("""
# In your FastAPI router (e.g., backend/routers/ai_router.py):

@router.post("/generate-lighting-design")
async def generate_lighting_design(song_analysis: dict):
    '''Generate lighting design from song analysis using AI pipeline'''
    
    try:
        segments = song_analysis.get('segments', [])
        lighting_results = []
        
        for segment in segments:
            # Format segment for pipeline
            segment_input = {
                "segment": {
                    "name": segment.get('label', 'Unknown'),
                    "start": segment.get('start', 0.0),
                    "end": segment.get('end', 0.0),
                    "features": segment.get('features', {})
                }
            }
            
            # Run the 3-agent LangGraph pipeline
            result = run_lighting_pipeline(segment_input)
            lighting_results.append(result)
        
        return {
            "status": "success",
            "segments_processed": len(segments),
            "lighting_design": lighting_results
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    """)

if __name__ == "__main__":
    # Run the integration example
    results = integrate_with_song_analysis()
    example_fastapi_integration()
