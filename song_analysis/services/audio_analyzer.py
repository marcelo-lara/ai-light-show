"""
Main audio analyzer service that orchestrates all analysis tasks.
"""

import os
from typing import Dict, Any
import logging
from pathlib import Path
from models.song_metadata import SongMetadata
from .load_metadata_hints import (load_arrangement_from_hints, load_key_moments_from_hints, load_chords_from_hints)
from .legacy_analyzer import legacy_analyze

from .audio import (
    extract_with_essentia,
    extract_stems,
    get_stem_clusters,
    noise_gate,
    guess_arrangement,
    extract_song_features    
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

        try:
            # Use the LangGraph pipeline for analysis
            from song_analysis.simple_pipeline import run_pipeline
            
            logger.info("🧩 Running modular LangGraph analysis pipeline...")
            
            # Run the pipeline and get the results
            pipeline_results = run_pipeline(song.mp3_path)
            
            # Check if we have results
            if not pipeline_results:
                logger.warning("⚠️ LangGraph pipeline returned no results, falling back to traditional analysis")
                return legacy_analyze(song, debug, self.noise_gate_stems)
            
            # Extract section data from the pipeline results
            sections = pipeline_results.get('sections', [])
            lighting_hints = pipeline_results.get('lighting_hints', [])
            
            logger.info(f"✅ LangGraph pipeline complete: {len(sections)} sections, {len(lighting_hints)} lighting hints")
            
            # Update the SongMetadata with the results
            if sections:
                # Clear existing arrangement by setting it to an empty list
                song.arrangement = []
                
                # Add sections to arrangement
                arrangement_sections = []
                for section in sections:
                    section_name = section.get('name', 'Unknown')
                    start_time = section.get('start', 0)
                    end_time = section.get('end', 0)
                    
                    logger.info(f"  Adding section: {section_name} ({start_time:.1f}s - {end_time:.1f}s)")
                    # Create a new Section object
                    arrangement_sections.append({
                        "name": section_name,
                        "start": start_time,
                        "end": end_time,
                        "prompt": f"LangGraph identified {section_name}"
                    })
                
                # Set the arrangement with our new sections
                song.arrangement = arrangement_sections
            
            # Add lighting hints as key moments
            if lighting_hints:
                # Create key moments list
                key_moments = []
                for hint in lighting_hints:
                    section_name = hint.get('section_name', 'Unknown')
                    start_time = hint.get('start', 0)
                    suggestion = hint.get('suggestion', '')
                    
                    logger.info(f"  Adding lighting hint for {section_name} at {start_time:.1f}s")
                    key_moments.append({
                        "start": start_time,
                        "end": None,
                        "name": f"Lighting: {section_name}",
                        "description": suggestion
                    })
                
                # Add to existing key moments
                existing_key_moments = song.key_moments
                song.key_moments = existing_key_moments + key_moments
            
            return song
            
        except Exception as e:
            logger.error(f"⚠️ Error in LangGraph pipeline: {str(e)}")
            logger.info("⚙️ Falling back to legacy analysis method")
            return legacy_analyze(song, debug, self.noise_gate_stems)
