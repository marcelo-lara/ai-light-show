"""Timeline execution service for the AI Light Show system."""

import asyncio
import time
from ..models.app_state import app_state
from ..fixture_utils import load_fixtures_config
from ..timeline_engine import execute_timeline


async def timeline_executor() -> None:
    """Main timeline execution loop."""
    # Initialize fixture configuration
    fixture_config, fixture_presets, chasers = load_fixtures_config()
    app_state.fixture_config = fixture_config
    app_state.fixture_presets = fixture_presets
    app_state.chasers = chasers

    while True:
        if app_state.playback.is_playing:
            now = time.monotonic() - app_state.playback.start_monotonic
            execute_timeline(now)
        await asyncio.sleep(0.01)
