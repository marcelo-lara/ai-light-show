
from pathlib import Path
import subprocess
import logging
from typing import Dict, Any
from song_analysis.services.nodes.utils import log_node_output
from ..audio.demucs_split import extract_stems

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def stem_split_node(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Split an audio file into stems using Demucs.
    
    Args:
        inputs: Dictionary containing mp3_path
        
    Returns:
        Dictionary with stem paths
    """
    mp3_path = inputs["mp3_path"]
    song_name = Path(mp3_path).stem
    temp_folder = str(Path(mp3_path).parent / "temp")
    
    # Extract stems using Demucs
    stems_result = extract_stems(
        input_file=mp3_path,
        songs_temp_folder=temp_folder,
        song_prefix=song_name
    )
    
    output = {
        "mp3_path": mp3_path,
        "stems": stems_result["stems"],
        "stems_folder": stems_result["output_folder"]
    }
    
    log_node_output("stem_split", output)
    return output