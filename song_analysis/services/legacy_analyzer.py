"""
Legacy song analysis implementation.

This module contains the traditional procedural approach to audio analysis,
used as a fallback if the LangGraph-based pipeline fails.
"""

import logging
from pathlib import Path

from models.song_metadata import SongMetadata
from .audio import (
    extract_with_essentia,
    extract_stems,
    get_stem_clusters,
    noise_gate,
    guess_arrangement,
    extract_song_features
)

logger = logging.getLogger(__name__)


def legacy_analyze(song: SongMetadata, debug: bool = False, noise_gate_stems: bool = True) -> SongMetadata:
    """
    Legacy analysis method using the procedural approach.
    Used as a fallback if the LangGraph pipeline fails.
    
    Args:
        song: SongMetadata object containing the song to analyze.
        debug: Enable debug output.
        noise_gate_stems: Whether to apply noise gate to stems.
        
    Returns:
        Updated SongMetadata object with analysis results.
    """
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

    stems_list = ['drums', 'bass']
    for stem in stems_list:
        stem_path = f"{stems_folder['output_folder']}/{stem}.wav"

        if not Path(stem_path).exists():
            logger.warning(f"⚠️ Stem file not found: {stem_path}")
            continue

        # Apply noise gate to stem
        if noise_gate_stems:
            logger.info(f"🔇 Applying noise gate to {stem} stem...")
            noise_gate(input_path=stem_path, threshold_db=-35.0)

    # Analyze stems for patterns
    extract_patterns(song, stems_list, stems_folder, debug)

    # Guess arrangement if needed
    if len(song.arrangement) == 0:
        logger.info("🎼 Guessing song arrangement...")
        guess_arrangement(song)

    logger.info(f"✅ Song analysis complete for: {song.song_name}")
    return song


def extract_patterns(song: SongMetadata, stems_list: list, stems_folder: dict, debug: bool = False):
    """
    Extract patterns from stems and add them to the song metadata.
    
    Args:
        song: SongMetadata object to update with patterns
        stems_list: List of stems to analyze
        stems_folder: Dictionary containing stem extraction results
        debug: Enable debug output
    """
    song.clear_patterns()
    for stem in stems_list:
        stem_path = f"{stems_folder['output_folder']}/{stem}.wav"

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
