#!/usr/bin/env python3
"""Test script to check the dynamic fixture list context"""

import sys
import asyncio
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.models.app_state import app_state
from backend.services.websocket_handlers.ai_handler import build_ui_context

async def test_context():
    """Test the dynamic context building"""
    print("Testing dynamic fixture list context...")
    print("=" * 50)
    
    try:
        # Build the context
        context = build_ui_context()
        
        print("Generated context:")
        print(context)
        print("=" * 50)
        
        # Show fixture details
        if app_state.fixtures and hasattr(app_state.fixtures, 'fixtures'):
            fixtures_dict = app_state.fixtures.fixtures
            print(f"Found {len(fixtures_dict)} fixtures:")
            for fixture_id, fixture in fixtures_dict.items():
                print(f"  - {fixture_id}: {fixture.fixture_type} ({fixture.name})")
                print(f"    Actions: {fixture.actions}")
        else:
            print("No fixtures found in app_state")
            print(f"app_state.fixtures = {app_state.fixtures}")
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_context())
