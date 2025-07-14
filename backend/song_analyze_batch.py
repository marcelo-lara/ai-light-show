from backend.models.song_metadata import SongMetadata, Section
from backend.services.audio.song_analyze import song_analyze
if __name__ == "__main__":

    songs_folder="/home/darkangel/ai-light-show/songs"

    # get a list of mp3 files in the songs folder
    import os
    from glob import glob
    mp3_files = glob(os.path.join(songs_folder, "*.mp3"))
    if not mp3_files:
        print("No MP3 files found in the songs folder.")
        exit(1)

    #remove temp folder if it exists
    temp_folder = os.path.join(songs_folder, "temp/htdemucs/*")
    if os.path.exists(temp_folder):
        print(f"Removing existing temp folder: {temp_folder}")
        try:
            os.rmdir(temp_folder)
        except Exception as e:
            print(f"Failed to remove temp folder: {e}")
            exit(1)

    # remove all files that are not mp3 files
    failed_to_remove = []
    for file in os.listdir(songs_folder):
        file_path = os.path.join(songs_folder, file)
        if os.path.isdir(file_path):
            continue  # Skip directories
        if os.path.isdir(file_path) or not file.endswith(".mp3"):
            try:
                os.remove(file_path)
            except Exception as e:
                failed_to_remove.append(file_path)

    if failed_to_remove:
        print("Failed to remove the following files:")
        for file in failed_to_remove:
            print(f"  {file}")
        exit(1)

    batch_results = []
    
    for mp3_file in sorted(mp3_files):
        print("\n-----------------------------------------------------------------------")
        song_name = os.path.splitext(os.path.basename(mp3_file))[0]
        print(f"Analyzing song: {song_name} ({mp3_file})")
        
        # Create a SongMetadata instance
        song = SongMetadata(song_name, songs_folder=songs_folder, ignore_existing=True)
        
        # Analyze the song
        try:
            song = song_analyze(song, debug=True)
            
            # Save the song metadata
            song.save()
            
            # Check if patterns were found
            drum_patterns = [p for p in song.patterns if p.get('stem') == 'drums']
            batch_results.append({
                'song_name': song_name,
                'success': True,
                'n_segments': len(drum_patterns),
                'n_clusters': len(set(p['cluster'] for p in drum_patterns)) if drum_patterns else 0,
                'duration': sum(p['end'] - p['start'] for p in drum_patterns) if drum_patterns else 0
            })
            
            print(f"✅ {song_name}: {len(drum_patterns)} segments, {len(set(p['cluster'] for p in drum_patterns)) if drum_patterns else 0} clusters")
            
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
    
    print(f"✅ Successful: {len(successful)}/{len(batch_results)} songs")
    print(f"❌ Failed: {len(failed)}/{len(batch_results)} songs")
    
    if successful:
        print(f"\n📊 Pattern Detection Results:")
        for result in successful:
            print(f"   {result['song_name']:30} {result['n_segments']:3} segments, {result['n_clusters']:2} clusters")
    
    if failed:
        print(f"\n⚠️  Failed Songs:")
        for result in failed:
            print(f"   {result['song_name']:30} {result['error']}")
    
    print(f"\n💾 Debug files saved in: {songs_folder}/temp/htdemucs/[song_name]/stem_clusters_best.json")
