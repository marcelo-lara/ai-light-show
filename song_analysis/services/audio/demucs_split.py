"""
Audio stem separation using Demucs.
"""

from pathlib import Path
import subprocess
import logging

logger = logging.getLogger(__name__)


def extract_stems(input_file: str, songs_temp_folder: str = '', song_prefix: str = '', stems: str = 'all', model: str = ''):
    """
    Extract stems from an audio file using Demucs.
    
    Args:
        input_file: Path to the input audio file.
        songs_temp_folder: Folder to store temporary output files.
        song_prefix: Prefix for the output files.
        stems: Type of stems to extract ('vocals', 'drums', 'bass', 'other', or 'all').
        model: Model to use for separation (optional: 'htdemucs_ft', 'mdx_extra').
        
    Returns:
        Dictionary with output paths.
        
    Raises:
        RuntimeError: If Demucs fails to run.
    """
    # Set default values if not provided
    if song_prefix == '':
        song_prefix = Path(input_file).stem
    if songs_temp_folder == '':
        songs_temp_folder = str(Path(input_file).parent / 'temp')

    # Prepare command
    command = [
        "python", "-m", "demucs.separate", 
        "-o", songs_temp_folder,
        *(["--two-stems=" + stems] if stems != 'all' else []),
        *(["-n=" + model] if model else []),
        input_file        
    ]
    
    # Execute command
    logger.info("🎵 Extracting stems from the song...")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        if result.returncode != 0:
            logger.error(f"Error running Demucs: {result.stderr}")
            raise RuntimeError(f"Demucs failed with error: {result.stderr}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Command: {' '.join(command)}")
        logger.error(f"Error running Demucs: {e.stderr}")
        raise RuntimeError(f"Demucs failed with error: {e.stderr}")

    # Return output paths
    output_folder = f"{songs_temp_folder}/htdemucs/{song_prefix}"

    stems_dict = {}
    if stems == 'all' or stems == 'vocals':
        stems_dict['vocals'] = f"{output_folder}/vocals.wav"
    if stems == 'all' or stems == 'drums':
        stems_dict['drums'] = f"{output_folder}/drums.wav"
    if stems == 'all' or stems == 'bass':
        stems_dict['bass'] = f"{output_folder}/bass.wav"
    if stems == 'all' or stems == 'other':
        stems_dict['other'] = f"{output_folder}/other.wav"

    return {
        "output_folder": output_folder,
        "stems": stems_dict
    }