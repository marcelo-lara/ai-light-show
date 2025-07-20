"""
Song arrangement guessing based on patterns and beats.
"""

from shared.models.song_metadata import SongMetadata, Section
import logging

logger = logging.getLogger(__name__)


def guess_arrangement_using_drum_patterns(song: SongMetadata) -> SongMetadata:
    """
    Guess the arrangement of the song based on its drum patterns.
    This function will analyze the song's drum patterns to determine sections.
    
    Args:
        song: SongMetadata object containing the song to analyze.
        
    Returns:
        Updated SongMetadata object with guessed arrangement.
    """
    return song


def guess_arrangement(song: SongMetadata, ignore_current_data: bool=False) -> SongMetadata:
    """
    Guess the arrangement of the song based on its beats and patterns.
    This function will analyze the song's beats and patterns to determine sections.
    
    Args:
        song: SongMetadata object containing the song to analyze.
        
    Returns:
        Updated SongMetadata object with guessed arrangement.
    """
    # Placeholder for arrangement guessing logic
    # This could be based on beat patterns, volume changes, etc.
    # For now, we will just create a simple arrangement based on beats
    if not song.beats:
        logger.warning("No beats found in the song, cannot guess arrangement")
        return song

    if len(song.arrangement)>0 or not ignore_current_data:
        logger.info("Arrangement already exists, skipping guessing")
        return song

    # TODO: This is a placeholder logic and should be replaced with actual arrangement logic
    # -- placeholder start here --
    section_length = 32 #assuming a typical song of 4/4 time with 32 beats per section
    arrangement = []
    
    for i in range(0, len(song.beats), section_length):
        section_beats = song.beats[i:i + section_length]
        if section_beats:
            section_start = section_beats[0]['time']
            section_end = section_beats[-1]['time']
            section_volume = sum(beat['volume'] for beat in section_beats) / len(section_beats)
           
            # Create a new section with the calculated properties
            section = Section(
                f"Section {len(arrangement) + 1}", 
                section_start, 
                section_end, 
                f"{section_length} beats | volume: {section_volume:.3f}"
            )
            arrangement.append(section)
    # -- placeholder ends here --

    song.arrangement = arrangement            
    return song
