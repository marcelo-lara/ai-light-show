"""SongMetadata model for the AI Light Show system."""

import json
import os
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

from .key_moment import KeyMoment
from .light_plan_item import LightPlanItem
from .section import Section
from .utils import ensure_json_serializable


class SongMetadata:
    """Main class for managing song metadata including beats, chords, and arrangement."""

    def __init__(self, song_name: Optional[str] = None, songs_folder: Optional[str] = None, ignore_existing: bool = False):

        if song_name is None:
            self._song_name = '_not_loaded_'
            return  # Placeholder for uninitialized song

        # Determine songs folder from different sources
        if not songs_folder:
            self._songs_folder = str(Path("/app/static/songs")) if Path("/app/static/songs").exists() else str(Path(__file__).parent.parent / "songs")
        else:
            self._songs_folder = songs_folder
        if not Path(self._songs_folder).exists():
            raise FileNotFoundError(f"Base directory {self._songs_folder} does not exist.")

        # Initialize metadata attributes
        self._song_name = song_name[:-4] if song_name.endswith(".mp3") else song_name
        self._title = song_name.replace("_", " ")
        self._genre = "unknown"
        self._bpm = 120
        self._beats: List[Dict[str, Any]] = []
        self._chords: List[Dict[str, Any]] = []
        self._patterns: List[Dict[str, Any]] = []
        self._arrangement: List[Section] = []
        self._duration = 2.0 * 60.0 # Default duration of 2 minutes
        self._analysis: List[Dict[str, Any]] = []
        self._key_moments: List[KeyMoment] = []
        self._light_plan: List[LightPlanItem] = []

        self._mp3_path = self._find_mp3_path()
        self._hints_folder = os.path.join(self._songs_folder, "hints")

        if not ignore_existing and self.exists():
            self.load()
        else:
            self.initialize_song_metadata()

    @property
    def data_folder(self) -> str:
        """Get the path to the data folder."""
        return os.path.join(self._songs_folder, "data")

    @property
    def song_name(self) -> str:
        return self._song_name

    @property
    def songs_folder(self) -> str:
        return self._songs_folder

    @property
    def mp3_path(self) -> str:
        return self._mp3_path or 'PATH_NOT_FOUND'

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str):
        self._title = value

    @property
    def analysis(self) -> List[Dict[str, Any]]:
        return self._analysis

    @analysis.setter
    def analysis(self, value: List[Dict[str, Any]]):
        self._analysis = value

    @property
    def genre(self) -> str:
        return self._genre

    @genre.setter
    def genre(self, value: str):
        self._genre = value

    @property
    def patterns(self) -> List[Dict[str, Any]]:
        return self._patterns

    @patterns.setter
    def patterns(self, value: List[Dict[str, Any]]):
        self._patterns = value

    @property
    def duration(self) -> float:
        return self._duration

    @duration.setter
    def duration(self, value: float):
        self._duration = float(value)

    @property
    def bpm(self) -> int:
        return self._bpm

    @bpm.setter
    def bpm(self, value: int):
        self._bpm = value

    @property
    def beats(self) -> List[Dict[str, Any]]:
        return self._beats

    @beats.setter
    def beats(self, value: List[Dict[str, Any]]):
        self._beats = value

    @property
    def light_plan(self) -> List[LightPlanItem]:
        return self._light_plan

    @light_plan.setter
    def light_plan(self, value: List[Any]):
        # Accepts list of LightPlanItem or dicts
        if not isinstance(value, list):
            raise TypeError("light_plan must be a list of LightPlanItem or dict objects.")
        new_list = []
        for v in value:
            if isinstance(v, LightPlanItem):
                new_list.append(v)
            elif isinstance(v, dict):
                new_list.append(LightPlanItem(**v))
            else:
                raise TypeError("Elements of light_plan must be LightPlanItem or dict.")
        self._light_plan = new_list

    @property
    def chords(self) -> List[Dict[str, Any]]:
        return self._chords

    @chords.setter
    def chords(self, value: List[Dict[str, Any]]):
        self._chords = value

    @property
    def analysis_file(self) -> str:
        """Get the path to the analysis file."""
        return os.path.join(self._songs_folder, "data", f"{self._song_name}.analysis.json")

    @property
    def context_file(self) -> str:
        """Get the path to the context file."""
        return os.path.join(self._songs_folder, "data", f"{self._song_name}.context.json")

    @property
    def key_moments(self) -> List[KeyMoment]:
        return self._key_moments

    @key_moments.setter
    def key_moments(self, value: List[Any]):
        # Accepts list of KeyMoment or dicts
        if not isinstance(value, list):
            raise TypeError("key_moments must be a list of KeyMoment or dict objects.")
        new_list = []
        for v in value:
            if isinstance(v, KeyMoment):
                new_list.append(v)
            elif isinstance(v, dict):
                new_list.append(KeyMoment(**v))
            else:
                raise TypeError("Elements of key_moments must be KeyMoment or dict.")
        self._key_moments = new_list

    @property
    def arrangement(self) -> List[Section]:
        return self._arrangement

    @property
    def placeholder_prop(self) -> bool:
        """True when the arrangement is a placeholder."""
        if len(self._arrangement) > 0 and isinstance(self._arrangement[0], Section):
            return "(placeholder)" in self._arrangement[0].prompt
        return len(self._arrangement) == 0

    @arrangement.setter
    def arrangement(self, value: List[Union[Section, Dict[str, Any]]]):
        if not isinstance(value, list):
            raise TypeError("Arrangement must be a list of Section objects.")
        
        # Convert dicts to Section objects if needed
        new_arrangement: List[Section] = []
        for item in value:
            if isinstance(item, Section):
                new_arrangement.append(item)
            elif isinstance(item, dict):
                new_arrangement.append(Section(
                    name=str(item.get("name", "")),
                    start=float(item.get("start", 0.0)),
                    end=float(item.get("end", 0.0)),
                    prompt=str(item.get("prompt", ""))
                ))
            else:
                raise TypeError(f"Unexpected type in arrangement: {type(item)}")
                
        self._arrangement = new_arrangement

    def _find_mp3_path(self) -> Optional[str]:
        """Try to locate the MP3 file for this song."""
        song_file = f"{self._song_name}.mp3" if not self._song_name.endswith(".mp3") else self._song_name

        mp3_path = os.path.join(self._songs_folder, song_file)
        if os.path.isfile(mp3_path):
            return mp3_path
        else:
            print(f"⚠️ Warning: MP3 file not found for '{self._song_name}' at {mp3_path}")
            return None

    def get_metadata_path(self) -> str:
        """Get path where metadata should be saved."""
        data_dir = os.path.join(self._songs_folder, "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, f"{self._song_name}.meta.json")

    def exists(self) -> bool:
        """Check if metadata file exists."""
        return os.path.isfile(self.get_metadata_path())

    def load(self) -> None:
        """Load metadata from JSON file."""
        with open(self.get_metadata_path(), "r") as f:
            data = json.load(f)

        self._title = data.get("title", self.title)
        self._genre = data.get("genre", self.genre)
        self._bpm = data.get("bpm", self.bpm)
        self._beats = data.get("beats", [])
        self._patterns = data.get("patterns", [])
        self._chords = data.get("chords", [])
        self._analysis = data.get("analysis", [])
        self._duration = data.get("duration", 0.0)
        
        # Load arrangement - support both raw dict and Section objects
        arrangement_data = data.get("arrangement", [])
        if arrangement_data:
            self.arrangement = arrangement_data  # Will convert to Section objects if needed
        else:
            self._arrangement = []
            
        # Convert key_moments dicts to KeyMoment objects
        key_moments_data = data.get("key_moments", [])
        self._key_moments = [KeyMoment(**km) if not isinstance(km, KeyMoment) else km for km in key_moments_data]
        
        # Convert light_plan dicts to LightPlanItem objects
        light_plan_data = data.get("light_plan", [])
        self._light_plan = [LightPlanItem(**lp) if not isinstance(lp, LightPlanItem) else lp for lp in light_plan_data]

    def initialize_song_metadata(self) -> None:
        """Initialize song metadata with default values."""
        self.beats = []
        self.arrangement = []
        self.key_moments = []
        self.light_plan = []

    def add_beat(self, time: float, volume: float = 0.0, energy: float = 1.0) -> None:
        """Add a beat to the song metadata."""
        self.beats.append({"time": time, "volume": volume, "energy": energy})

    def clear_beats(self) -> None:
        """Clear all beats."""
        self.beats = []

    def get_beats_array(self) -> List[float]:
        """Get array of beat times."""
        return [beat["time"] for beat in self.beats]

    def set_beats_volume(self, beat_volume: List[Tuple[float, float]]) -> None:
        """Set volume for beats."""
        if len(beat_volume) != len(self.beats):
            print(f"⚠️ Warning: Volume list length {len(beat_volume)} does not match number of beats {len(self.beats)}.")
            return
        for i, (time, volume) in enumerate(beat_volume):
            if abs(self.beats[i]["time"] - time) > 1e-6:
                print(f"⚠️ Warning: Beat time mismatch at index {i}: expected {self.beats[i]['time']}, got {time}")
            self.beats[i]["volume"] = float(volume)

    def set_beats_energy(self, beat_energy: List[Tuple[float, float]]) -> None:
        """Set energy for beats."""
        if len(beat_energy) != len(self.beats):
            print(f"⚠️ Warning: Energy list length {len(beat_energy)} does not match number of beats {len(self.beats)}.")
            return
        for i, (time, energy) in enumerate(beat_energy):
            if abs(self.beats[i]["time"] - time) > 1e-6:
                print(f"⚠️ Warning: Beat time mismatch at index {i}: expected {self.beats[i]['time']}, got {time}")
            self.beats[i]["energy"] = float(energy)

    def clear_patterns(self) -> None:
        """Clears all patterns from the song metadata."""
        self._patterns = []

    def add_patterns(self, stem_name: str, patterns: List[Dict[str, Any]]) -> None:
        """Adds patterns for a given stem to the song metadata."""
        if not hasattr(self, "_patterns"):
            self._patterns = []
        self._patterns.append({"stem": stem_name, "clusters": patterns})

    def clear_light_plan(self) -> None:
        """Clear all light plan items."""
        self.light_plan = []

    def add_light_plan_item(self, id: int, start: float, end: Optional[float] = None, name: str = '', description: Optional[str] = None) -> None:
        """Add a light plan item to the song metadata."""
        light_plan_item = LightPlanItem(id=id, start=start, end=end, name=name, description=description)
        self._light_plan.append(light_plan_item)

    def remove_light_plan_item(self, id: int) -> bool:
        """Remove a light plan item by ID. Returns True if removed, False if not found."""
        for i, item in enumerate(self._light_plan):
            if item.id == id:
                self._light_plan.pop(i)
                return True
        return False

    def get_light_plan_at_time(self, time: float) -> List[LightPlanItem]:
        """Get all light plan items that are active at a given time."""
        active_items = []
        for item in self._light_plan:
            if item.start <= time and (item.end is None or time <= item.end):
                active_items.append(item)
        return active_items

    def get_prompt(self) -> str:
        """Generate a prompt for the song metadata."""
        song = self
        if song.arrangement:
            _song_sections_line = '\n'.join([f"  - {s.name} ({s.start:.2f}-{s.end:.2f})" for s in song.arrangement])
        else:
            _song_sections_line = "  - None"

        return f"""
Song: {song.title}
Genre: {song.genre}
- duration: {song.duration} seconds
- bpm: {song.bpm}
- beats time: {', '.join(f'{b["time"]:.2f}' for b in song.beats) if song.beats else 'None'}
- key moments: {', '.join(f"{km.name} ({km.start:.2f}-{km.end:.2f})" for km in song.key_moments) if song.key_moments else 'None'}
- light plan: {', '.join(f"{lp.name} ({lp.start:.2f}-{lp.end:.2f})" for lp in song.light_plan) if song.light_plan else 'None'}
- song sections: 
{_song_sections_line}
"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary format."""
        data: Dict[str, Any] = {
            "title": self.title,
            "genre": self.genre,
            "duration": self.duration,
            "bpm": self.bpm,
            "chords": self.chords,
            "beats": self.beats,
            "analysis": self.analysis,
            "patterns": self._patterns,
            # Serialize arrangement as list of dicts
            "arrangement": [s.to_dict() if isinstance(s, Section) else s for s in self.arrangement],
            "key_moments": [km.to_dict() if isinstance(km, KeyMoment) else km for km in self.key_moments],
            "light_plan": [lp.to_dict() if isinstance(lp, LightPlanItem) else lp for lp in self.light_plan],
        }
        # Ensure all data is JSON serializable
        result = ensure_json_serializable(data)
        assert isinstance(result, dict), "ensure_json_serializable should return a dict"
        return result

    def to_json(self) -> str:
        """Convert metadata to JSON string."""
        return json.dumps(self.to_dict())

    def save(self) -> None:
        """Save metadata to JSON file."""
        os.makedirs(os.path.dirname(self.get_metadata_path()), exist_ok=True)
        with open(self.get_metadata_path(), "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"ℹ️ Metadata saved for '{self._song_name}' at {self.get_metadata_path()}")

    def __str__(self) -> str:
        return f"SongMetadata(song_name={self._song_name}, title={self.title}, genre={self.genre}, bpm={self.bpm}, duration={self.duration}, beats={len(self.beats)}, arrangement={len(self.arrangement)}, light_plan={len(self.light_plan)})"
