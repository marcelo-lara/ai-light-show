# Import all fixture classes from the fixtures module for backward compatibility
from .fixtures import FixtureModel, RgbParcan, MovingHead, FixturesModel

# Re-export classes for backward compatibility
__all__ = ['FixtureModel', 'RgbParcan', 'MovingHead', 'FixturesModel']

        