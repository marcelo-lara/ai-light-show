#!/usr/bin/env python3
"""
Batch song analysis using the standalone Song Analysis Service.
This replaces the original song_analyze_batch.py to use the microservice.
"""

import asyncio
import os
import sys
from pathlib import Path
from backend.services.song_analysis_client import SongAnalysisClient


async def analyze_batch_with_service(songs_folder: str = "/home/darkangel/ai-light-show/songs"):
    """
    Analyze all MP3 files in the songs folder using the Song Analysis Service.
    
    Args:
        songs_folder: Path to folder containing MP3 files
    """
    print(f"🎵 Starting batch analysis of songs in: {songs_folder}")
    
    # Get list of MP3 files
    folder_path = Path(songs_folder)
    if not folder_path.exists():
        print(f"❌ Songs folder not found: {songs_folder}")
        return
    
    mp3_files = list(folder_path.glob("*.mp3"))
    if not mp3_files:
        print("❌ No MP3 files found in the songs folder.")
        return
    
    print(f"📁 Found {len(mp3_files)} MP3 files to analyze")
    
    # Clean up any existing temp files
    temp_folder = folder_path / "temp"
    if temp_folder.exists():
        print(f"🧹 Cleaning up existing temp folder: {temp_folder}")
        try:
            import shutil
            shutil.rmtree(temp_folder)
        except Exception as e:
            print(f"⚠️ Warning: Could not remove temp folder: {e}")
    
    # Remove any non-MP3 files (cleanup)
    failed_to_remove = []
    for file_path in folder_path.iterdir():
        if file_path.is_file() and not file_path.name.endswith(".mp3") and file_path.name != ".gitkeep":
            if file_path.is_dir():
                continue  # Skip directories
            try:
                file_path.unlink()  # Remove file
            except Exception as e:
                failed_to_remove.append(str(file_path))
    
    if failed_to_remove:
        print("⚠️ Failed to remove the following files:")
        for file in failed_to_remove:
            print(f"  {file}")
    
    # Analyze songs using the service
    async with SongAnalysisClient() as client:
        # Check service health first
        print("🔍 Checking Song Analysis Service health...")
        health = await client.health_check()
        if health.get("status") != "healthy":
            print(f"❌ Song Analysis Service is not healthy: {health.get('error', 'Unknown error')}")
            print("💡 Make sure the service is running: docker-compose up song-analysis")
            return
        
        print("✅ Song Analysis Service is healthy")
        
        # Process each song
        batch_results = []
        
        for i, mp3_file in enumerate(sorted(mp3_files), 1):
            print(f"\n{'='*70}")
            song_name = mp3_file.stem
            print(f"[{i}/{len(mp3_files)}] Analyzing song: {song_name}")
            print(f"File: {mp3_file}")
            
            try:
                # Analyze the song
                result = await client.analyze_song(
                    song_path=str(mp3_file),
                    reset_file=True,
                    debug=True
                )
                
                if result.get("status") == "success":
                    metadata = result.get("metadata", {})
                    
                    # Extract pattern information
                    patterns = metadata.get("patterns", [])
                    drum_patterns = [p for p in patterns if p.get('stem') == 'drums']
                    
                    batch_results.append({
                        'song_name': song_name,
                        'success': True,
                        'n_segments': len(drum_patterns[0].get('clusters', [])) if drum_patterns else 0,
                        'n_clusters': len(set(c.get('cluster', 0) for p in drum_patterns for c in p.get('clusters', []))) if drum_patterns else 0,
                        'duration': metadata.get('duration', 0),
                        'bpm': metadata.get('bpm', 0),
                        'beats': len(metadata.get('beats', []))
                    })
                    
                    n_segments = batch_results[-1]['n_segments']
                    n_clusters = batch_results[-1]['n_clusters']
                    duration = batch_results[-1]['duration']
                    bpm = batch_results[-1]['bpm']
                    beats = batch_results[-1]['beats']
                    
                    print(f"✅ {song_name}: {n_segments} segments, {n_clusters} clusters")
                    print(f"   Duration: {duration:.1f}s, BPM: {bpm}, Beats: {beats}")
                    
                else:
                    error_message = result.get("message", "Unknown error")
                    print(f"❌ Failed to analyze {song_name}: {error_message}")
                    batch_results.append({
                        'song_name': song_name,
                        'success': False,
                        'error': error_message
                    })
                    
            except Exception as e:
                print(f"❌ Failed to analyze {song_name}: {str(e)}")
                batch_results.append({
                    'song_name': song_name,
                    'success': False,
                    'error': str(e)
                })
    
    # Print batch summary
    print("\n" + "="*70)
    print("BATCH ANALYSIS SUMMARY")
    print("="*70)
    
    successful = [r for r in batch_results if r['success']]
    failed = [r for r in batch_results if not r['success']]
    
    print(f"📊 Total songs: {len(batch_results)}")
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    if successful:
        avg_duration = sum(r['duration'] for r in successful) / len(successful)
        avg_bpm = sum(r['bpm'] for r in successful) / len(successful)
        total_beats = sum(r['beats'] for r in successful)
        total_segments = sum(r['n_segments'] for r in successful)
        
        print(f"📈 Average duration: {avg_duration:.1f}s")
        print(f"📈 Average BPM: {avg_bpm:.1f}")
        print(f"📈 Total beats analyzed: {total_beats}")
        print(f"📈 Total pattern segments: {total_segments}")
    
    if failed:
        print(f"\n❌ Failed songs:")
        for result in failed:
            print(f"  - {result['song_name']}: {result['error']}")
    
    print("\n🎉 Batch analysis completed!")


if __name__ == "__main__":
    songs_folder = sys.argv[1] if len(sys.argv) > 1 else "/home/darkangel/ai-light-show/songs"
    asyncio.run(analyze_batch_with_service(songs_folder))
