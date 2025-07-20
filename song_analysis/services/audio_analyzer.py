"""
Main audio analyzer service that orchestrates all analysis tasks.
"""

import os
from typing import Dict, Any
import logging
from pathlib import Path
from shared.models.song_metadata import SongMetadata
from song_analysis.services.audio.arrangement_guess import guess_arrangement
from song_analysis.services.audio.audio_process import noise_gate
from song_analysis.services.audio.demucs_split import extract_stems
from song_analysis.services.audio.essentia_analysis import extract_with_essentia
from song_analysis.services.audio.section_features import extract_song_features
from .load_metadata_hints import (load_arrangement_from_hints, load_key_moments_from_hints, load_chords_from_hints)

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
        This function uses a LangGraph-based pipeline for modular, traceable analysis.
        
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

        features_analysis = extract_song_features(
            stems_dir=stems_folder['output_folder'],
            output_json_path=song.analysis_file,
            save_file=debug
        )

        for stem in ['drums', 'bass']:
            logger.info(f"🔍 Analyzing {stem} stem features...")
            stem_path = f"{stems_folder['output_folder']}/{stem}.wav"

            if not Path(stem_path).exists():
                logger.warning(f"⚠️ Stem file not found: {stem_path}")
                continue

            # Apply noise gate to stem
            logger.info(f"🔇 Applying noise gate to {stem} stem...")
            noise_gate(input_path=stem_path, threshold_db=-35.0)


        # Guess arrangement if needed
        if len(song.arrangement) == 0:
            logger.info("🎼 Guessing song arrangement...")
            guess_arrangement(song)

        logger.info(f"✅ Song analysis complete for: {song.song_name}")

        return song
