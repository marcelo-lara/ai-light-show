"""
List of actions for a song.
"""
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from backend.config import SONGS_DIR
from backend.models.song_metadata import SongMetadata


@dataclass
class ActionModel:
    """
    Represents a single action in the actions sheet.
    
    Attributes:
        action (str): The name of the action.
        fixture_id (str): Fixture ID for the action (mandatory).
        parameters (dict): Parameters for the action.
        start_time (float): Start time of the action in seconds.
        duration (float): Duration of the action in seconds.
    """
    action: str
    fixture_id: str  # Fixture ID for the action (mandatory)
    parameters: dict = field(default_factory=dict)
    start_time: float = 0.0
    duration: float = 0.0
    action_id: str = ""  # Unique identifier for the action
    group_id: str = ""  # Optional group ID for grouping actions

    def to_dict(self) -> dict:
        """Convert the action to a dictionary for JSON serialization."""
        return {
            "action": self.action,
            "fixture_id": self.fixture_id,
            "parameters": self.parameters,
            "start_time": self.start_time,
            "duration": self.duration,
            "action_id": self.action_id,
            "group_id": self.group_id
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ActionModel":
        """Create an ActionModel from a dictionary."""
        return cls(
            action=data.get("action", ""),
            fixture_id=data.get("fixture_id", ""),
            parameters=data.get("parameters", {}),
            start_time=data.get("start_time", 0.0),
            duration=data.get("duration", 0.0),
            action_id=data.get("action_id", ""),
            group_id=data.get("group_id", "")
        )


class ActionsSheet:
    """
    Class to manage a list of actions for a song.
    
    The actions are loaded from/saved to a JSON file from (SONGS_DIR / data / <song_name>.actions.json).
    Includes methods to load actions when the song is loaded and contains methods to add, remove, and modify actions.
    """
    
    def __init__(self, song_name: str):
        """
        Initialize the ActionsSheet for a specific song.
        
        Args:
            song_name (str): The name of the song (without extension)
        """
        self.song_name = song_name
        self.actions: List[ActionModel] = []
        self._actions_file = SONGS_DIR / "data" / f"{song_name}.actions.json"
        
    @property
    def actions_file_path(self) -> Path:
        """Get the path to the actions file."""
        return self._actions_file
    
    def load_actions(self) -> bool:
        """
        Load actions from the JSON file when the song is loaded.
        Reset all inner variables and initialize an empty file with default values if it doesn't exist.
        
        Returns:
            bool: True if actions were loaded successfully, False otherwise
        """
        # Reset all inner variables when song is loaded
        self.actions = []
        
        try:
            if self._actions_file.exists():
                with open(self._actions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.actions = [ActionModel.from_dict(action_data) for action_data in data.get("actions", [])]
                return True
            else:
                # Initialize empty file with default values if it doesn't exist
                self._initialize_empty_actions_file()
                return True
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            print(f"Error loading actions for {self.song_name}: {e}")
            # Reset to empty state and create default file
            self.actions = []
            self._initialize_empty_actions_file()
            return False
    
    def _initialize_empty_actions_file(self) -> None:
        """
        Initialize an empty actions file with default values.
        """
        try:
            # Ensure the data directory exists
            self._actions_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create default empty actions structure
            default_data = {
                "song_name": self.song_name,
                "actions": []
            }
            
            with open(self._actions_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2)
        except Exception as e:
            print(f"Error initializing empty actions file for {self.song_name}: {e}")
    
    def save_actions(self) -> bool:
        """
        Save actions to the JSON file.
        
        Returns:
            bool: True if actions were saved successfully, False otherwise
        """
        try:
            # Ensure the data directory exists
            self._actions_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "song_name": self.song_name,
                "actions": [action.to_dict() for action in self.actions]
            }
            
            with open(self._actions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving actions for {self.song_name}: {e}")
            return False
    
    def add_action(self, action: ActionModel) -> None:
        """
        Add an action to the actions list.
        
        Args:
            action (ActionModel): The action to add
        """
        if not action.action_id:
            action.action_id = str(uuid.uuid4())
        else:
            if any(a.action_id == action.action_id for a in self.actions):
                raise ValueError(f"Action ID {action.action_id} already exists")
        
        self.actions.append(action)
    
    def remove_action(self, index: int) -> bool:
        """
        Remove an action from the actions list by index.
        
        Args:
            index (int): The index of the action to remove
            
        Returns:
            bool: True if action was removed successfully, False otherwise
        """
        try:
            if 0 <= index < len(self.actions):
                self.actions.pop(index)
                return True
            return False
        except IndexError:
            return False
    
    def remove_action_by_time(self, start_time: float) -> bool:
        """
        Remove an action from the actions list by start time.
        
        Args:
            start_time (float): The start time of the action to remove
            
        Returns:
            bool: True if action was removed successfully, False otherwise
        """
        for i, action in enumerate(self.actions):
            if action.start_time == start_time:
                self.actions.pop(i)
                return True
        return False
    
    def modify_action(self, index: int, updated_action: ActionModel) -> bool:
        """
        Modify an action in the actions list.
        
        Args:
            index (int): The index of the action to modify
            updated_action (ActionModel): The updated action
            
        Returns:
            bool: True if action was modified successfully, False otherwise
        """
        try:
            if 0 <= index < len(self.actions):
                self.actions[index] = updated_action
                return True
            return False
        except IndexError:
            return False
    
    def remove_all_actions(self) -> None:
        """Remove all actions from the actions list."""
        self.actions.clear()
    
    def get_actions_at_time(self, time: float) -> List[ActionModel]:
        """
        Get all actions that are active at a specific time.
        
        Args:
            time (float): The time to check for active actions
            
        Returns:
            List[ActionModel]: List of actions active at the specified time
        """
        active_actions = []
        for action in self.actions:
            if action.start_time <= time <= (action.start_time + action.duration):
                active_actions.append(action)
        return active_actions
    
    def get_actions_by_name(self, action_name: str) -> List[ActionModel]:
        """
        Get all actions with a specific name.
        
        Args:
            action_name (str): The name of the action to search for
            
        Returns:
            List[ActionModel]: List of actions with the specified name
        """
        return [action for action in self.actions if action.action == action_name]
    
    def sort_actions_by_time(self) -> None:
        """Sort actions by start time."""
        self.actions.sort(key=lambda x: x.start_time)
    
    def __len__(self) -> int:
        """Return the number of actions."""
        return len(self.actions)
    
    def __getitem__(self, index: int) -> ActionModel:
        """Get an action by index."""
        return self.actions[index]
    
    def __iter__(self):
        """Iterate over actions."""
        return iter(self.actions)
