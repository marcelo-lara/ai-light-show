"""
Main audio analyzer service that orchestrates all analysis tasks.
"""

from typing import Dict, Any
import logging
from pathlib import Path
from models.song_metadata import SongMetadata
from .load_metadata_hints import (load_arrangement_from_hints, load_key_moments_from_hints, load_chords_from_hints)

from .audio import (
    extract_with_essentia,
    extract_stems,
    get_stem_clusters,
    noise_gate,
    guess_arrangement
)

logger = logging.getLogger(__name__)


class SongAnalyzer:
    """Main song analysis orchestrator."""
    
    def __init__(self):
        """Initialize the analyzer."""
        self.analyze_patterns_using_model = False
        self.infer_drums_using_model = False
        self.noise_gate_stems = True
    
    def analyze(self, song: SongMetadata, reset_file: bool = True, debug: bool = False) -> SongMetadata:
        """
        Analyze a song and extract its metadata, beats, BPM, and patterns.
        This function uses Essentia for core analysis and Demucs for stem extraction.
        
        Args:
            song: SongMetadata object containing the song to analyze.
            reset_file: If True, will re-create entire metadata.
            debug: Enable debug output.
            
        Returns:
            Updated SongMetadata object with analysis results.
        """
        
        logger.info(f"🔍 Analyzing song: {song.title} ({song.mp3_path})")

        if reset_file:
            song = SongMetadata(song.song_name, songs_folder=song.songs_folder, ignore_existing=True)
            song = load_chords_from_hints(song)
            song = load_key_moments_from_hints(song)
            song = load_arrangement_from_hints(song)

        # Core analysis using Essentia
        logger.info("🎧 Extracting beats, volume and basic metadata using Essentia...")
        essentia_core = extract_with_essentia(song.mp3_path)
        
        song.clear_beats()
        song.bpm = essentia_core['bpm']
        song.duration = essentia_core['song_duration']
        
        # Add beats with volumes
        for beat_time, volume in essentia_core['beat_volumes']:
            song.add_beat(beat_time, volume)
        
        logger.info(f"✅ Essentia analysis complete: BPM={song.bpm}, Duration={song.duration:.1f}s, Beats={len(song.beats)}")

        # Split song into stems
        logger.info("🎵 Splitting audio into stems using Demucs...")
        stems_folder = extract_stems(song.mp3_path)
        
        if not stems_folder or 'output_folder' not in stems_folder:
            raise ValueError("Failed to extract stems - no output folder returned")

        # Analyze stems for patterns
        stems_list = ['drums', 'bass']
        song.clear_patterns()

        for stem in stems_list:
            stem_path = f"{stems_folder['output_folder']}/{stem}.wav"
            
            if not Path(stem_path).exists():
                logger.warning(f"⚠️ Stem file not found: {stem_path}")
                continue

            # Apply noise gate to stem
            if self.noise_gate_stems:
                logger.info(f"🔇 Applying noise gate to {stem} stem...")
                noise_gate(input_path=stem_path, threshold_db=-35.0)

            # Get clusters (librosa)
            try:
                logger.info(f"🔍 Analyzing patterns for {stem} stem...")
                stem_clusters = get_stem_clusters(
                    song.get_beats_array(),
                    stem_path,
                    debug=debug
                )
                
                if not stem_clusters:
                    continue
                
                if 'clusters_timeline' in stem_clusters:
                    n_clusters = stem_clusters.get('n_clusters', 0)
                    score = stem_clusters.get('clusterization_score', 0.0)
                    logger.info(f"  Adding {n_clusters} clusters for {stem} → Score: {score:.4f}")
                    song.add_patterns(stem, stem_clusters['clusters_timeline'])
                else:
                    logger.warning(f"⚠️ No clusters timeline found for {stem}")

            except Exception as e:
                logger.error(f"⚠️ Failed to process {stem}: {str(e)}")
                continue

        # Guess arrangement if needed
        if len(song.arrangement) == 0:
            logger.info("🎼 Guessing song arrangement...")
            guess_arrangement(song)

        logger.info(f"✅ Song analysis complete for: {song.song_name}")
        return song
