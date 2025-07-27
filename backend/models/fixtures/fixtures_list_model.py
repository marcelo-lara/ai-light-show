from pathlib import Path
import json
from typing import Dict, Optional
from .fixture_model import FixtureModel
from .rgb_parcan import RgbParcan
from .moving_head import MovingHead
from backend.services.dmx.dmx_canvas import DmxCanvas


class FixturesListModel:
    def __init__(self, fixtures_config_file:Path, dmx_canvas: DmxCanvas, debug=False):
        """
        Initialize the FixturesModel with an empty fixture list.
        """
        self._fixtures = {}
        self._dmx_canvas = dmx_canvas
        self.debug = debug
        self.load_fixtures(fixtures_config_file)

    @property
    def dmx_canvas(self) -> DmxCanvas:
        """
        Get the DMX canvas associated with the fixtures.
        Returns:
            DmxCanvas: The DMX canvas instance.
        """
        return self._dmx_canvas
    
    @dmx_canvas.setter
    def dmx_canvas(self, canvas: DmxCanvas) -> None:
        """
        Set the DMX canvas for the fixtures.
        Args:
            canvas (DmxCanvas): The DMX canvas instance to set.
        """
        self._dmx_canvas = canvas
        for fixture in self._fixtures.values():
            fixture.dmx_canvas = canvas

    @property
    def fixtures(self) -> Dict[str, FixtureModel]:
        """
        Get the fixtures dictionary.
        Returns:
            dict: Dictionary of fixtures with fixture ID as key.
        """
        return self._fixtures

    def add_fixture(self, fixture: FixtureModel) -> None:
        """
        Add a fixture to the model.
        Args:
            fixture (FixtureModel): The fixture to add.
        """
        # Set the DMX canvas for the fixture
        fixture.dmx_canvas = self._dmx_canvas
        self._fixtures[fixture.id] = fixture

    def get_fixture(self, id: str) -> Optional[FixtureModel]:
        """
        Get a fixture by its ID.
        Args:
            id (str): Unique identifier of the fixture.
        Returns:
            Optional[FixtureModel]: The requested fixture, or None if not found.
        """
        return self._fixtures.get(id)
    
    def get_fixtures_by_position_label(self, label: str) -> list[FixtureModel]:
        """
        Get all fixtures at a specific position label.
        Args:
            label (str): Position label to search for (e.g., 'stage_left', 'center_stage').
        Returns:
            list[FixtureModel]: List of fixtures at the specified position.
        """
        fixtures_at_position = []
        for fixture in self._fixtures.values():
            if fixture.position and fixture.position.label == label:
                fixtures_at_position.append(fixture)
        return fixtures_at_position
    
    def get_fixtures_in_area(self, min_x: float = 0.0, max_x: float = 1.0, 
                           min_y: float = 0.0, max_y: float = 1.0) -> list[FixtureModel]:
        """
        Get all fixtures within a specified rectangular area.
        Args:
            min_x (float): Minimum x coordinate (0.0-1.0).
            max_x (float): Maximum x coordinate (0.0-1.0).
            min_y (float): Minimum y coordinate (0.0-1.0).
            max_y (float): Maximum y coordinate (0.0-1.0).
        Returns:
            list[FixtureModel]: List of fixtures within the area.
        """
        fixtures_in_area = []
        for fixture in self._fixtures.values():
            if fixture.position:
                pos = fixture.position
                if (min_x <= pos.x <= max_x and min_y <= pos.y <= max_y):
                    fixtures_in_area.append(fixture)
        return fixtures_in_area
    
    def load_fixtures(self, fixtures_config_file:Path, debug=None) -> None:
        """
        Load fixtures from the fixtures.json file.
        This method initializes fixtures based on the provided data.
        Args:
            fixtures_data (list): List of fixture data dictionaries.
        """
        if debug is None:
            debug = self.debug

        if not fixtures_config_file.exists():
            raise FileNotFoundError(f"Fixtures configuration file {fixtures_config_file} not found.")
        
        with open(fixtures_config_file, 'r') as f:
            fixtures_data = json.load(f)

        # load fixtures based on their type
        for fixture_data in fixtures_data:
            if fixture_data['type'] == 'rgb':
                fixture = RgbParcan(
                    id=fixture_data['id'], 
                    name=fixture_data['name'], 
                    dmx_canvas=self._dmx_canvas, 
                    config=fixture_data
                )
            elif fixture_data['type'] == 'moving_head':
                fixture = MovingHead(
                    id=fixture_data['id'], 
                    name=fixture_data['name'], 
                    dmx_canvas=self._dmx_canvas, 
                    config=fixture_data
                )
            else:
                print(f"⚠️ Unknown fixture type: {fixture_data['type']}. Skipping fixture with ID {fixture_data['id']}.")
                continue
            
            # Actions are now automatically derived from action_handlers
            # No need to set them from config
            self.add_fixture(fixture)

        if debug:
            print(f"Loaded {len(self._fixtures)} fixtures:")
            for fixture in self._fixtures.values():
                position = fixture.position
                position_str = f" at {position.label} ({position.x}, {position.y}, {position.z})" if position else " (no position)"
                print(f"  - {fixture}{position_str}")

    def __iter__(self):
        """
        Iterate over the fixtures in the model.
        Returns:
            Iterator[FixtureModel]: Iterator over the fixtures.
        """
        return iter(self._fixtures.values())
