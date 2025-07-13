from pathlib import Path
import json
from typing import Optional
from .fixture_model import FixtureModel
from .rgb_parcan import RgbParcan
from .moving_head import MovingHead


class FixturesModel:
    def __init__(self, fixtures_config_file:Path, debug=False):
        """
        Initialize the FixturesModel with an empty fixture list.
        """
        self.fixtures = {}
        self.load_fixtures(fixtures_config_file, debug)

    def add_fixture(self, fixture: FixtureModel) -> None:
        """
        Add a fixture to the model.
        Args:
            fixture (FixtureModel): The fixture to add.
        """
        self.fixtures[fixture.id] = fixture

    def get_fixture(self, id: str) -> Optional[FixtureModel]:
        """
        Get a fixture by its ID.
        Args:
            id (str): Unique identifier of the fixture.
        Returns:
            Optional[FixtureModel]: The requested fixture, or None if not found.
        """
        return self.fixtures.get(id)
    
    def load_fixtures(self, fixtures_config_file:Path, debug=False) -> None:
        """
        Load fixtures from the fixtures.json file.
        This method initializes fixtures based on the provided data.
        Args:
            fixtures_data (list): List of fixture data dictionaries.
        """
        if not fixtures_config_file.exists():
            raise FileNotFoundError(f"Fixtures configuration file {fixtures_config_file} not found.")
        
        with open(fixtures_config_file, 'r') as f:
            fixtures_data = json.load(f)

        # load fixtures based on their type
        for fixture_data in fixtures_data:
            if fixture_data['type'] == 'rgb':
                fixture = RgbParcan(fixture_data['id'], fixture_data['name'])
            elif fixture_data['type'] == 'moving_head':
                fixture = MovingHead(fixture_data['id'], fixture_data['name'])
            else:
                print(f"⚠️ Unknown fixture type: {fixture_data['type']}. Skipping fixture with ID {fixture_data['id']}.")
                continue
            
            # Actions are now automatically derived from action_handlers
            # No need to set them from config
            self.add_fixture(fixture)

        if debug:
            print(f"Loaded {len(self.fixtures)} fixtures:")
            for fixture in self.fixtures.values():
                print(f"  - {fixture}")
