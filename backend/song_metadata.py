# song_analyzer.py

import json
import os

class Section:
    def __init__(self, start, end, prompt):
        self.start = start
        self.end = end
        self.prompt = prompt

    def to_dict(self):
        return {
            "start": self.start,
            "end": self.end,
            "prompt": self.prompt
        }

    @staticmethod
    def from_dict(data):
        return Section(data["start"], data["end"], data["prompt"])


class SongMetadata:

    def __init__(self, song_name, songs_folder=None, ignore_existing=False):
        self._song_name = song_name
        self._title = song_name.replace("_", " ")
        self._genre = "unknown"
        self._bpm = 120
        self._beats = []
        self._arrangement = {}
        self._duration = 0.0
        if not songs_folder:
            from backend.config import SONGS_DIR
            self._songs_folder = SONGS_DIR
        else:
            self._songs_folder = songs_folder

        self._mp3_path = self._find_mp3_path()

        if not ignore_existing and self.exists():
            self.load()
        else:
            self.generate_placeholders()

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
    def arrangement(self):
        return self._arrangement

    @arrangement.setter
    def arrangement(self, value):
        self._arrangement = value

    def _find_mp3_path(self):
        """Try to locate the MP3 file for this song."""
        if not self._song_name.endswith(".mp3"):
            self._song_name += ".mp3"

        mp3_path = os.path.join(self._songs_folder, self._song_name)
        if os.path.isfile(mp3_path):
            return mp3_path
        else:
            print(f"⚠️ Warning: MP3 file not found for '{self._song_name}' at {mp3_path}")
            return None

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
        self.arrangement = {k: Section.from_dict(v) for k, v in data.get("arrangement", {}).items()}

    def generate_placeholders(self):
        self.beats = [
            {"time": 0.5, "volume": 0.2, "energy": 0.3},
            {"time": 1.0, "volume": 0.4, "energy": 0.5},
            {"time": 1.5, "volume": 0.6, "energy": 0.7},
            {"time": 2.0, "volume": 0.5, "energy": 0.6},
            {"time": 2.5, "volume": 0.3, "energy": 0.4},
        ]

        self.arrangement = {
            "intro": Section(0.0, 0.5, "Intro section with ambient sounds."),
            "verse": Section(0.5, 1.5, "Verse with minimal instrumentation and vocals."),
            "chorus": Section(1.5, 2.0, "Chorus with full energy and instrumentation."),
            "bridge": Section(2.0, 2.5, "Bridge section with rhythmic variation."),
            "outro": Section(2.5, 3.0, "Outro with fade-out or reduced energy.")
        }

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
            "beats": self.beats,
            "arrangement": {k: v.to_dict() for k, v in self.arrangement.items()},
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def save(self):
        os.makedirs(self._songs_folder, exist_ok=True)
        with open(self.get_metadata_path(), "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"ℹ️ Metadata saved for '{self._song_name}' at {self.get_metadata_path()}")


# Example usage
if __name__ == "__main__":
    song = SongMetadata("born_slippy", songs_folder="/home/darkangel/ai-light-show/songs", ignore_existing=True)
    song.save()
    print(f"Metadata saved to {song.get_metadata_path()}")
    if song.mp3_path:
        print(f"MP3 file located at: {song.mp3_path}")
