# song_analyzer.py

import json
import os

class Section:
    def to_dict(self):
        return {
            "name": self.name,
            "start": self.start,
            "end": self.end,
            "prompt": self.prompt,
        }
    
    def __init__(self, name, start, end, prompt):
        self.name = name
        self.start = start
        self.end = end
        self.prompt = prompt

class SongMetadata:

    def __init__(self, song_name, songs_folder=None, ignore_existing=False):
        self._song_name = song_name[:-4] if song_name.endswith(".mp3") else song_name
        self._title = song_name.replace("_", " ")
        self._genre = "unknown"
        self._bpm = 120
        self._beats = []
        self._chords = []
        self._arrangement = []
        self._duration = 0.0
        self._drums = []
        if not songs_folder:
            from backend.config import SONGS_DIR
            self._songs_folder = SONGS_DIR
        else:
            self._songs_folder = songs_folder

        self._mp3_path = self._find_mp3_path()
        self._hints_folder = os.path.join(self._songs_folder, "hints")

        if not ignore_existing and self.exists():
            self.load()
        else:
            self.initialize_song_metadata()

    @property
    def song_name(self):
        return self._song_name

    @property
    def songs_folder(self):
        return self._songs_folder

    @property
    def mp3_path(self) -> str:
        return self._mp3_path or 'PATH_NOT_FOUND'

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def drums(self):
        return self._drums

    @drums.setter
    def drums(self, value):
        self._drums = value
        
    @property
    def genre(self):
        return self._genre

    @genre.setter
    def genre(self, value):
        self._genre = value

    @property
    def duration(self) -> float:
        return self._duration

    @duration.setter
    def duration(self, value: float):
        self._duration = float(value)

    @property
    def bpm(self):
        return self._bpm

    @bpm.setter
    def bpm(self, value):
        self._bpm = value

    @property
    def beats(self):
        return self._beats

    @beats.setter
    def beats(self, value):
        self._beats = value

    @property
    def chords(self):
        return self._chords

    @chords.setter
    def chords(self, value):
        self._chords = value

    @property
    def arrangement(self) -> list[Section]:
        return self._arrangement

    @arrangement.setter
    def arrangement(self, value):
        if not isinstance(value, list):
            raise TypeError("Arrangement must be a list of Section objects.")
        if not all(isinstance(v, Section) for v in value):
            raise TypeError("All elements of arrangement must be Section objects.")
        self._arrangement = value

    def _find_mp3_path(self):
        """Try to locate the MP3 file for this song."""
        song_file = f"{self._song_name}.mp3" if not self._song_name.endswith(".mp3") else self._song_name

        mp3_path = os.path.join(self._songs_folder, song_file)
        if os.path.isfile(mp3_path):
            return mp3_path
        else:
            print(f"⚠️ Warning: MP3 file not found for '{self._song_name}' at {mp3_path}")
            return None

    def load_chords_from_hints(self):
        """Load chords from hints files if available."""
        hints_folder = os.path.join(self._songs_folder, "hints")
        chords_file = os.path.join(hints_folder, f"{self._song_name}.chords.json")

        if os.path.isfile(chords_file):
            with open(chords_file, "r") as f:
                self._chords = json.load(f)
            print(f" -> Chords loaded from {chords_file}")
        else:
            print(f"⚠️ Warning: Chords file not found for '{self._song_name}' at {chords_file}")

    def load_arrangement_from_hints(self):
        """Load arrangement from hints files if available."""
        hints_folder = os.path.join(self._songs_folder, "hints")
        segments_file = os.path.join(hints_folder, f"{self._song_name}.segments.json")
        if not os.path.isfile(segments_file):
            return False
        with open(segments_file, "r") as f:
            segments_data = json.load(f)
        print(f" -> Segments loaded from {segments_file}")

        # convert segments to arrangement (list of Section)
        self.arrangement = [
            Section(
                name=segment.get("label") or segment.get("name", ""),
                start=segment["start"],
                end=segment["end"],
                prompt=segment.get("prompt", "")
            ) for segment in segments_data
        ]
        print(f"    .. {len(self._arrangement)} sections created")
        return True

    def _load_hints_files(self):
        """Try to locate the hints files for this song."""
        hints_folder = os.path.join(self._songs_folder, "hints")
        if not os.path.isdir(hints_folder):
            print(f"⚠️ Warning: Hints folder not found for '{self._song_name}' at {hints_folder}")
            return None

        ## chords file
        self.load_chords_from_hints()

        # lyrics file
        lyrics_file = os.path.join(hints_folder, f"{self._song_name}.lyrics.json")
        if os.path.isfile(lyrics_file):
            with open(lyrics_file, "r") as f:
                lyrics_data = json.load(f)
            print(f" -> Lyrics loaded from {lyrics_file}")

        # segments file
        self.load_arrangement_from_hints()

    def get_metadata_path(self):
        return os.path.join(self._songs_folder, f"{self._song_name}.meta.json")

    def exists(self):
        return os.path.isfile(self.get_metadata_path())

    def load(self):
        with open(self.get_metadata_path(), "r") as f:
            data = json.load(f)

        self.title = data.get("title", self.title)
        self.genre = data.get("genre", self.genre)
        self.bpm = data.get("bpm", self.bpm)
        self.beats = data.get("beats", [])
        self.chords = data.get("chords", [])
        self._arrangement = data.get("arrangement", [])

        # attempt to load hints files if not already done
        if len(self.beats) == 0:
            self.load_chords_from_hints()
        if len(self._arrangement) == 0:
            self.load_arrangement_from_hints()

    def initialize_song_metadata(self):

        # look for hints files
        self._load_hints_files()
        
        self.beats = [
            {"time": 0.5, "volume": 0.2, "energy": 0.3},
            {"time": 1.0, "volume": 0.4, "energy": 0.5},
            {"time": 1.5, "volume": 0.6, "energy": 0.7},
            {"time": 2.0, "volume": 0.5, "energy": 0.6},
            {"time": 2.5, "volume": 0.3, "energy": 0.4},
        ]

        if len(self._arrangement) == 0:
            self.arrangement = [
                Section("intro", 0.0, 0.5, "Intro section with ambient sounds. (placeholder)"),
                Section("verse", 0.5, 1.5, "Verse with minimal instrumentation and vocals."),
                Section("chorus", 1.5, 2.0, "Chorus with full energy and instrumentation."),
                Section("bridge", 2.0, 2.5, "Bridge section with rhythmic variation."),
                Section("outro", 2.5, 3.0, "Outro with fade-out or reduced energy.")
            ]

    def add_beat(self, time, volume=0.0, energy=1.0):
        self.beats.append({"time": time, "volume": volume, "energy": energy})

    def clear_beats(self):
        self.beats = []

    def get_beats_array(self):
        return [beat["time"] for beat in self.beats]

    def set_beats_volume(self, beat_volume: list[tuple[float, float]]):
        if len(beat_volume) != len(self.beats):
            print(f"⚠️ Warning: Volume list length {len(beat_volume)} does not match number of beats {len(self.beats)}.")
            return
        for i, (time, volume) in enumerate(beat_volume):
            if abs(self.beats[i]["time"] - time) > 1e-6:
                print(f"⚠️ Warning: Beat time mismatch at index {i}: expected {self.beats[i]['time']}, got {time}")
            self.beats[i]["volume"] = float(volume)

    def set_beats_energy(self, beat_energy: list[tuple[float, float]]):
        if len(beat_energy) != len(self.beats):
            print(f"⚠️ Warning: Energy list length {len(beat_energy)} does not match number of beats {len(self.beats)}.")
            return
        for i, (time, energy) in enumerate(beat_energy):
            if abs(self.beats[i]["time"] - time) > 1e-6:
                print(f"⚠️ Warning: Beat time mismatch at index {i}: expected {self.beats[i]['time']}, got {time}")
            self.beats[i]["energy"] = float(energy)

    def update_beat(self, time, volume=None, energy=None):
        for beat in self.beats:
            if beat["time"] == time:
                if volume is not None:
                    beat["volume"] = volume
                if energy is not None:
                    beat["energy"] = energy
                return
        print(f"⚠️ Beat at time {time} not found.")

    def to_dict(self):
        return {
            "title": self.title,
            "genre": self.genre,
            "bpm": self.bpm,
            "chords": self.chords,
            "beats": self.beats,
            # Serialize arrangement as list of dicts
            "arrangement": [s.to_dict() if isinstance(s, Section) else s for s in self.arrangement],
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def save(self):
        os.makedirs(self._songs_folder, exist_ok=True)
        with open(self.get_metadata_path(), "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"ℹ️ Metadata saved for '{self._song_name}' at {self.get_metadata_path()}")

    def __str__(self):
        return f"SongMetadata(song_name={self._song_name}, title={self.title}, genre={self.genre}, bpm={self.bpm}, duration={self.duration}, beats={len(self.beats)}, arrangement={len(self.arrangement)})"


# Example usage
if __name__ == "__main__":
    song = SongMetadata("born_slippy", songs_folder="/home/darkangel/ai-light-show/songs", ignore_existing=True)
    song.save()
    print(f"Metadata saved to {song.get_metadata_path()}")
    if song.mp3_path:
        print(f"MP3 file located at: {song.mp3_path}")
