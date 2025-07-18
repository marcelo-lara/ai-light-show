"""
Test runner for the simplified LangGraph-based song analysis pipeline.
"""

import os
import sys
import json
from pathlib import Path
import argparse

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from song_analysis.simple_pipeline import run_pipeline


def main():
    """Run the pipeline on a test song."""
    parser = argparse.ArgumentParser(description="Run the LangGraph-based song analysis pipeline")
    parser.add_argument("--song", type=str, default="born_slippy.mp3",
                        help="Name of the song file in the songs folder to analyze")
    args = parser.parse_args()
    
    # Get the base directory of the project
    base_dir = Path(__file__).parent.parent
    
    # Build the path to the song file
    song_path = base_dir / "songs" / args.song
    
    if not song_path.exists():
        print(f"Error: Song file '{song_path}' not found.")
        return 1
    
    print(f"Running analysis pipeline on '{song_path}'...")
    
    # Run the pipeline
    result = run_pipeline(str(song_path))
    
    # Write the final result to a file
    output_path = song_path.with_suffix(".analysis.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"Analysis complete. Results written to '{output_path}'")
    
    # Also print a summary to the console
    print("\nAnalysis Summary:")
    print(f"  Sections: {len(result.get('sections', []))}")
    print(f"  Lighting Hints: {len(result.get('lighting_hints', []))}")
    
    # Print the first few sections and hints
    if result.get('sections'):
        print("\nFirst 3 Sections:")
        for i, section in enumerate(result.get('sections', [])[:3]):
            print(f"  {section.get('name')}: {section.get('start'):.2f}s - {section.get('end'):.2f}s")
    
    if result.get('lighting_hints'):
        print("\nFirst 3 Lighting Hints:")
        for i, hint in enumerate(result.get('lighting_hints', [])[:3]):
            print(f"  {hint.get('section_name')}: {hint.get('suggestion')[:60]}...")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
