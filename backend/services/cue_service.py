"""Cue management service for the AI Light Show system."""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..config import SONGS_DIR
from ..models.app_state import app_state
from ..timeline_engine import render_timeline


class CueManager:
    """Manages cues for the AI Light Show system."""
    
    def __init__(self):
        self._cue_list: List[Dict[str, Any]] = []
        self._current_song_file: Optional[str] = None
    
    @property
    def cue_list(self) -> List[Dict[str, Any]]:
        """Get the current cue list."""
        return self._cue_list
    
    @property
    def current_song_file(self) -> Optional[str]:
        """Get the current song file."""
        return self._current_song_file
    
    def clear_cues(self) -> None:
        """Clear all cues."""
        self._cue_list.clear()
    
    def add_cue(self, cue: Dict[str, Any]) -> None:
        """Add a cue and sort the list."""
        if 'duration' not in cue:
            if 'parameters' in cue and 'loop_duration' in cue['parameters']:
                cue['duration'] = cue['parameters']['loop_duration']
            else:
                cue['duration'] = cue['parameters'].get('fade_duration', 0)
        
        self._cue_list.append(cue)
        self._cue_list.sort(key=lambda c: (c["fixture"], c["time"]))
    
    def update_cues(self, cues: List[Dict[str, Any]]) -> None:
        """Replace all cues with new list."""
        self._cue_list.clear()
        cues.sort(key=lambda c: (c["time"], c["fixture"]))
        self._cue_list.extend(cues)
    
    def delete_cue_by_chaser_id(self, chaser_id: str) -> None:
        """Delete all cues with the given chaser_id."""
        self._cue_list[:] = [c for c in self._cue_list if c.get("chaser_id") != chaser_id]
    
    def delete_cue(self, fixture: str, time: float) -> None:
        """Delete a specific cue by fixture and time."""
        self._cue_list[:] = [
            c for c in self._cue_list 
            if not (c["fixture"] == fixture and c["time"] == time)
        ]
    
    def load_cues(self, song_file: str) -> None:
        """Load cues for a specific song file."""
        self._current_song_file = song_file
        cue_path = SONGS_DIR / f"{song_file}.cues.json"

        if not cue_path.exists():
            print(f"⚠️ No cues found for {song_file}, creating empty cue list.")
            self.clear_cues()
            return

        try:
            with open(cue_path) as f:
                cues_data = json.load(f)
                self.clear_cues()
                self._cue_list.extend(cues_data)
            print(f"🎵 Loaded cues for {song_file} ({len(self._cue_list)} total)")
        except Exception as e:
            print(f"❌ load_cues error: {e}")

    def save_cues(self, song_file: Optional[str] = None, cues: Optional[List[Dict[str, Any]]] = None) -> None:
        """Save cues for a specific song file."""
        target_song_file = song_file or self._current_song_file
        target_cues = cues or self._cue_list
        
        if not target_song_file:
            print("❌ Cannot save cues: no song file specified")
            return
            
        cue_path = SONGS_DIR / f"{target_song_file}.cues.json"
        try:
            cue_path.write_text(json.dumps(target_cues, indent=2))
            print(f"💾 Saved cues to {cue_path}")
        except Exception as e:
            print(f"❌ save_cues error: {e}")
            return
        
        # Re-render timeline after saving cues
        bpm = app_state.song_metadata.get("bpm", 100)
        if app_state.current_song and hasattr(app_state.current_song, 'bpm'):
            bpm = app_state.current_song.bpm
            
        render_timeline(
            app_state.fixture_config, 
            app_state.fixture_presets, 
            cues=target_cues, 
            current_song=target_song_file, 
            bpm=bpm
        )

    def generate_test_beat_sync_cues(self, song_beats: List[float]) -> List[Dict[str, Any]]:
        """Generate test cues synchronized to song beats."""
        fixtures_id = ["parcan_pl", "parcan_pr", "parcan_l", "parcan_r"]
        cue_template = {
            "time": 0,
            "fixture": "parcan_l",
            "preset": "flash",
            "parameters": {
                "fade_beats": 1
            },
            "duration": 1,
            "chaser": "ai",
            "chaser_id": "ai_generated_000"
        }
        
        # Create flash cues for each beat
        cues = []
        curr_fixture_idx = 0
        for beat in song_beats:
            # Cycle through fixtures
            fixture = fixtures_id[curr_fixture_idx]
            cue = cue_template.copy()
            cue["time"] = beat
            cue["fixture"] = fixture
            cues.append(cue)
            curr_fixture_idx += 1
            if curr_fixture_idx >= len(fixtures_id):
                curr_fixture_idx = 0

        return cues


# Global cue manager instance
cue_manager = CueManager()
