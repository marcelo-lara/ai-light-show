from pathlib import Path
from shared.models.song_metadata import SongMetadata
from song_analysis.services.audio_analyzer import SongAnalyzer
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# variables
songs_folder = Path("/home/darkangel/ai-light-show/songs")
song_name = "born_slippy"

# Initialize the analyzer
analyzer = SongAnalyzer()

# Create SongMetadata object
song = SongMetadata(
    song_name=song_name,
    songs_folder=str(songs_folder),
    ignore_existing=True
)
logger.info(f"!!!!!!!! Starting analysis for song: {song_name}")
# Perform analysis
analyzed_song = analyzer.analyze(
    song=song,
    reset_file=True,
    debug=True
)
