#!/usr/bin/env python3
"""
Comprehensive Test Script for All Fixture Actions and DMX Painting

This script tests:
1. All supported direct command types
2. All fixture actions (flash, fade, strobe, set channel, preset, etc.)
3. DMX painting validation for every command
4. Action execution and rendering pipeline
5. All fixtures and their capabilities

Usage:
    python test_all_fixture_actions_dmx_painting.py
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.models.app_state import app_state
from backend.services.ollama.direct_commands_parser import DirectCommandsParser
from backend.services.dmx.actions_parser_service import ActionsParserService
from backend.services.dmx.dmx_canvas import DmxCanvas
from backend.services.actions_service import ActionsService
from backend.models.actions_sheet import ActionsSheet
from backend.config import FIXTURES_FILE


def load_test_fixtures():
    """Load fixtures from fixtures.json for testing"""
    try:
        with open(FIXTURES_FILE, 'r') as f:
            fixtures_data = json.load(f)
        
        # Initialize app_state fixtures (it will auto-create FixturesListModel)
        # Force initialization of fixtures in app_state
        if app_state.fixtures is None:
            _ = app_state.fixtures  # This triggers __post_init__ which creates fixtures
        
        print(f"✅ Loaded {len(fixtures_data)} fixtures: {[f['id'] for f in fixtures_data]}")
        return app_state.fixtures
        
    except Exception as e:
        print(f"❌ Failed to load fixtures: {e}")
        return None


class DMXPaintingValidator:
    """Validates that commands result in proper DMX painting"""
    
    def __init__(self):
        self.initial_state = None
        self.commands_tested = 0
        self.painting_success = 0
        self.painting_failures = []
    
    def capture_initial_state(self):
        """Capture initial DMX canvas state"""
        canvas = DmxCanvas.get_instance()
        self.initial_state = canvas.get_frame(0.0)  # Get frame at time 0
        print(f"📸 Captured initial DMX state: {len([v for v in self.initial_state if v > 0])} active channels")
    
    def validate_dmx_painting(self, command: str, actions_count: int = 0) -> bool:
        """Check if DMX painting occurred after command execution"""
        canvas = DmxCanvas.get_instance()
        current_state = canvas.get_frame(0.0)  # Get frame at time 0
        
        # Check if there are any changes in DMX state
        changes = {}
        for channel, value in enumerate(current_state):
            initial_value = self.initial_state[channel] if self.initial_state else 0
            if initial_value != value:
                changes[channel] = {'before': initial_value, 'after': value}
        
        has_changes = len(changes) > 0
        
        if has_changes:
            self.painting_success += 1
            print(f"   ✅ DMX painting detected: {len(changes)} channels changed")
            if len(changes) <= 10:  # Show details for small changes
                for ch, vals in changes.items():
                    print(f"      CH{ch}: {vals['before']} → {vals['after']}")
            else:
                print(f"      (showing first 5) CH{list(changes.keys())[0]}: {list(changes.values())[0]}, ...")
        else:
            self.painting_failures.append(command)
            print(f"   ❌ No DMX painting detected")
        
        self.commands_tested += 1
        
        # Update initial state for next test
        self.initial_state = current_state
        
        return has_changes
    
    def print_summary(self):
        """Print validation summary"""
        print(f"\n📊 DMX Painting Validation Summary:")
        print(f"   Commands tested: {self.commands_tested}")
        print(f"   Successful painting: {self.painting_success}")
        print(f"   Failed painting: {len(self.painting_failures)}")
        print(f"   Success rate: {(self.painting_success/self.commands_tested*100):.1f}%" if self.commands_tested > 0 else "N/A")
        
        if self.painting_failures:
            print(f"\n❌ Commands that failed DMX painting:")
            for cmd in self.painting_failures:
                print(f"   • {cmd}")


async def test_direct_commands_dmx_painting():
    """Test all direct commands and validate DMX painting"""
    print("\n🎭 Testing Direct Commands DMX Painting...")
    
    # First load a song to satisfy the requirement for direct commands
    try:
        from shared.models.song_metadata import SongMetadata
        song_metadata = SongMetadata("test_song", songs_folder="/home/darkangel/ai-light-show/songs", ignore_existing=True)
        app_state.current_song = song_metadata
        print("✅ Loaded test song for direct commands")
    except Exception as e:
        print(f"⚠️ Could not load test song: {e}")
    
    parser = DirectCommandsParser()
    validator = DMXPaintingValidator()
    validator.capture_initial_state()
    
    # Test commands that should trigger DMX painting
    painting_commands = [
        # Basic action commands
        "#add flash to parcan_l at 1.0s duration 0.5s",
        "#add strobe to parcan_r at 2.0s for 1.0s", 
        "#add fade to parcan_pl at 3.0s duration 2.0s",
        
        # Channel commands
        "#set parcan_l red channel to 0.8 at 4.0s",
        "#set parcan_r dim channel to 1.0 at 4.5s",
        "#set head_el150 color channel to 0.5 at 5.0s",
        
        # Preset commands
        "#preset head_el150 Piano at 6.0s",
        
        # Fade channel commands
        "#fade parcan_l red channel from 0.0 to 1.0 duration 2.0s",
        "#fade parcan_r green channel from 1.0 to 0.2 duration 1.5s",
        
        # Strobe channel commands
        "#strobe parcan_pl white channel rate 10 duration 2.0s",
        "#strobe parcan_pr blue channel rate 5 duration 1.0s",
        
        # Clear fixture commands
        "#clear parcan_l state at 8.0s",
        "#clear parcan_r state at 8.5s",
        
        # Render command (should always paint)
        "#render",
    ]
    
    # Test commands that should NOT trigger DMX painting
    non_painting_commands = [
        "#help",
        "#tasks", 
        "#analyze",
        "#clear all",
        "#clear action test_id",
        "#clear group test_group",
    ]
    
    print(f"\n🎨 Testing {len(painting_commands)} commands that SHOULD trigger DMX painting:")
    for i, command in enumerate(painting_commands, 1):
        print(f"\n{i:2d}. Testing: {command}")
        try:
            success, message, data = await parser.parse_command(command)
            if success:
                print(f"   ✅ Command executed successfully: {message}")
                validator.validate_dmx_painting(command)
            else:
                print(f"   ❌ Command failed: {message}")
                validator.commands_tested += 1
                validator.painting_failures.append(command)
        except Exception as e:
            print(f"   💥 Command error: {e}")
            validator.commands_tested += 1
            validator.painting_failures.append(command)
    
    print(f"\n🚫 Testing {len(non_painting_commands)} commands that should NOT trigger DMX painting:")
    for i, command in enumerate(non_painting_commands, 1):
        print(f"\n{i:2d}. Testing: {command}")
        try:
            success, message, data = await parser.parse_command(command)
            print(f"   ✅ Command executed: {message}")
            # These commands shouldn't paint, so we don't validate painting
            validator.commands_tested += 1
        except Exception as e:
            print(f"   💥 Command error: {e}")
    
    validator.print_summary()
    return validator


def test_actions_parser_all_types():
    """Test all action types through the ActionsParserService"""
    print("\n🎬 Testing Actions Parser Service All Action Types...")
    
    if not app_state.fixtures:
        print("❌ No fixtures loaded, skipping actions parser tests")
        return None, None
    
    parser = ActionsParserService(app_state.fixtures, debug=True)
    validator = DMXPaintingValidator() 
    validator.capture_initial_state()
    
    # Get available fixture IDs
    fixture_ids = list(app_state.fixtures.fixtures.keys())
    print(f"🎯 Available fixtures: {fixture_ids}")
    
    # Test all supported action command patterns
    test_commands = [
        # Flash commands
        f"flash {fixture_ids[0]} red at 1.0s for 1.0s with intensity 0.8",
        f"flash {fixture_ids[1]} blue at 2.0s",
        f"flash all_parcans white at 3.0s for 0.5s",
        
        # Fade commands  
        f"fade {fixture_ids[0]} from red to blue at 4.0s for 2.0s",
        f"fade {fixture_ids[1]} from white to black at 6.0s for 1.5s",
        f"fade all at 8.0s",
        
        # Strobe commands
        f"strobe {fixture_ids[0]} at 10.0s for 2.0s",
        f"strobe all_parcans at 12.0s for 1.0s",
        
        # Set channel commands
        f"set {fixture_ids[0]} red channel to 0.5 at 14.0s",
        f"set {fixture_ids[1]} dim channel to 1.0 at 15.0s",
        
        # Preset commands (if available)
        f"preset {fixture_ids[0]} Piano at 16.0s",
        
        # Fade channel commands
        f"fade {fixture_ids[0]} red channel from 0.0 to 1.0 duration 3.0s",
        f"fade {fixture_ids[1]} green channel from 1.0 to 0.0 duration 2.0s",
        
        # Strobe channel commands
        f"strobe {fixture_ids[0]} red channel rate 10 duration 2.0s",
        f"strobe {fixture_ids[1]} white channel rate 5 duration 1.5s",
        
        # Clear fixture commands
        f"clear {fixture_ids[0]} state at 20.0s",
        
        # Generic commands
        f"full {fixture_ids[0]} intensity=0.7 at 22.0s for 1.0s",
        f"pulse {fixture_ids[1]} at 24.0s",
    ]
    
    actions_sheet = ActionsSheet("test_song")
    actions_service = app_state.get_actions_service()
    
    for i, command in enumerate(test_commands, 1):
        print(f"\n{i:2d}. Parsing: {command}")
        try:
            actions = parser.parse_command(command)
            if actions:
                print(f"   ✅ Parsed {len(actions)} action(s)")
                for action in actions:
                    print(f"      → {action.action} on {action.fixture_id} at {action.start_time}s")
                    actions_sheet.add_action(action)
                
                # Test rendering to DMX canvas
                print(f"   🎨 Rendering actions to DMX canvas...")
                render_result = actions_service.render_actions_to_canvas(actions_sheet)
                print(f"   📊 Render result: {render_result}")
                
                validator.validate_dmx_painting(command, len(actions))
            else:
                print(f"   ❌ No actions parsed")
                validator.commands_tested += 1
                validator.painting_failures.append(command)
                
        except Exception as e:
            print(f"   💥 Parsing error: {e}")
            validator.commands_tested += 1
            validator.painting_failures.append(command)
    
    print(f"\n📈 Actions Parser Test Summary:")
    print(f"   Total actions in sheet: {len(actions_sheet.actions)}")
    print(f"   Action types tested: {len(set(a.action for a in actions_sheet.actions))}")
    print(f"   Fixtures involved: {len(set(a.fixture_id for a in actions_sheet.actions))}")
    
    validator.print_summary()
    return validator, actions_sheet


def test_fixture_capabilities():
    """Test each fixture's capabilities and effects"""
    print("\n🎪 Testing Individual Fixture Capabilities...")
    
    if not app_state.fixtures:
        print("❌ No fixtures loaded, skipping fixture capability tests")
        return None
    
    validator = DMXPaintingValidator()
    validator.capture_initial_state()
    actions_service = app_state.get_actions_service()
    
    for fixture_id, fixture in app_state.fixtures.fixtures.items():
        print(f"\n🎯 Testing fixture: {fixture_id} ({fixture.name})")
        print(f"   Type: {fixture.fixture_type}")
        print(f"   Channels: {list(fixture._config['channels'].keys()) if fixture._config else 'N/A'}")
        print(f"   Effects: {fixture._config.get('effects', []) if fixture._config else 'N/A'}")
        print(f"   Presets: {[p['name'] for p in fixture._config.get('presets', [])] if fixture._config else 'N/A'}")
        
        # Test each effect if available
        effects = fixture._config.get('effects', []) if fixture._config else []
        for effect in effects:
            command = f"{effect} {fixture_id} at 1.0s for 0.5s"
            print(f"   🎭 Testing effect: {command}")
            
            try:
                parser = ActionsParserService(app_state.fixtures, debug=False)
                actions = parser.parse_command(command)
                if actions:
                    actions_sheet = ActionsSheet("test_fixture")
                    for action in actions:
                        actions_sheet.add_action(action)
                    
                    render_result = actions_service.render_actions_to_canvas(actions_sheet)
                    validator.validate_dmx_painting(command)
                else:
                    print(f"      ❌ No actions generated")
                    validator.commands_tested += 1
                    validator.painting_failures.append(command)
            except Exception as e:
                print(f"      💥 Error: {e}")
                validator.commands_tested += 1 
                validator.painting_failures.append(command)
        
        # Test channel controls
        if fixture._config and 'channels' in fixture._config:
            for channel_name in list(fixture._config['channels'].keys())[:3]:  # Test first 3 channels
                command = f"set {fixture_id} {channel_name} channel to 0.8 at 2.0s"
                print(f"   🎛️ Testing channel: {command}")
                
                try:
                    parser = ActionsParserService(app_state.fixtures, debug=False)
                    actions = parser.parse_command(command)
                    if actions:
                        actions_sheet = ActionsSheet("test_channel")
                        for action in actions:
                            actions_sheet.add_action(action)
                        
                        render_result = actions_service.render_actions_to_canvas(actions_sheet)
                        validator.validate_dmx_painting(command)
                    else:
                        print(f"      ❌ No actions generated")
                        validator.commands_tested += 1
                        validator.painting_failures.append(command)
                except Exception as e:
                    print(f"      💥 Error: {e}")
                    validator.commands_tested += 1
                    validator.painting_failures.append(command)
        
        # Test presets
        presets = fixture._config.get('presets', []) if fixture._config else []
        for preset in presets[:2]:  # Test first 2 presets
            preset_name = preset['name'] if isinstance(preset, dict) else str(preset)
            command = f"preset {fixture_id} {preset_name} at 3.0s"
            print(f"   🎚️ Testing preset: {command}")
            
            try:
                parser = ActionsParserService(app_state.fixtures, debug=False)
                actions = parser.parse_command(command)
                if actions:
                    actions_sheet = ActionsSheet("test_preset")
                    for action in actions:
                        actions_sheet.add_action(action)
                    
                    render_result = actions_service.render_actions_to_canvas(actions_sheet)
                    validator.validate_dmx_painting(command)
                else:
                    print(f"      ❌ No actions generated")
                    validator.commands_tested += 1
                    validator.painting_failures.append(command)
            except Exception as e:
                print(f"      💥 Error: {e}")
                validator.commands_tested += 1
                validator.painting_failures.append(command)
    
    validator.print_summary()
    return validator


def test_dmx_canvas_direct_painting():
    """Test direct DMX canvas painting operations"""
    print("\n🎨 Testing Direct DMX Canvas Painting...")
    
    validator = DMXPaintingValidator()
    validator.capture_initial_state()
    
    canvas = DmxCanvas.get_instance()
    
    # Test direct canvas operations
    test_operations = [
        ("Set single channel", lambda: canvas.paint_frame(0.0, {16: 255})),
        ("Set multiple channels", lambda: canvas.paint_frame(0.0, {17: 128, 18: 200, 19: 100})),
        ("Paint channel range", lambda: canvas.paint_channel(20, 0.0, 1.0, lambda t: int(255 * t))),
        ("Paint frame range", lambda: canvas.paint_range(1.0, 2.0, lambda t: {22: 255})),
        ("Clear canvas", lambda: canvas.clear_canvas()),
    ]
    
    for i, (name, operation) in enumerate(test_operations, 1):
        print(f"\n{i}. Testing: {name}")
        try:
            operation()
            validator.validate_dmx_painting(name)
        except Exception as e:
            print(f"   💥 Error: {e}")
            validator.commands_tested += 1
            validator.painting_failures.append(name)
    
    validator.print_summary()
    return validator


async def main():
    """Main test runner"""
    print("🧪 Comprehensive Fixture Actions and DMX Painting Test Suite")
    print("=" * 70)
    
    # Load fixtures
    fixtures = load_test_fixtures()
    if not fixtures:
        print("❌ Cannot proceed without fixtures")
        return
    
    # Initialize DMX canvas 
    canvas = DmxCanvas.get_instance()
    canvas.clear_canvas()
    print("🎨 DMX Canvas initialized")
    
    # Test results storage
    all_validators = []
    
    try:
        # Test 1: Direct Commands DMX Painting
        validator1 = await test_direct_commands_dmx_painting()
        all_validators.append(("Direct Commands", validator1))
        
        # Test 2: Actions Parser All Types
        validator2, actions_sheet = test_actions_parser_all_types()
        if validator2:
            all_validators.append(("Actions Parser", validator2))
        
        # Test 3: Fixture Capabilities
        validator3 = test_fixture_capabilities() 
        if validator3:
            all_validators.append(("Fixture Capabilities", validator3))
        
        # Test 4: Direct DMX Canvas Painting
        validator4 = test_dmx_canvas_direct_painting()
        all_validators.append(("Direct Canvas", validator4))
        
    except Exception as e:
        print(f"💥 Test suite error: {e}")
        import traceback
        traceback.print_exc()
    
    # Final Summary
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
    print("=" * 70)
    
    total_commands = 0
    total_success = 0
    total_failures = 0
    
    for test_name, validator in all_validators:
        total_commands += validator.commands_tested
        total_success += validator.painting_success
        total_failures += len(validator.painting_failures)
        
        success_rate = (validator.painting_success / validator.commands_tested * 100) if validator.commands_tested > 0 else 0
        print(f"\n🔬 {test_name}:")
        print(f"   Commands tested: {validator.commands_tested}")
        print(f"   DMX painting success: {validator.painting_success}")
        print(f"   DMX painting failures: {len(validator.painting_failures)}")
        print(f"   Success rate: {success_rate:.1f}%")
    
    overall_success_rate = (total_success / total_commands * 100) if total_commands > 0 else 0
    print(f"\n🏆 OVERALL RESULTS:")
    print(f"   Total commands tested: {total_commands}")
    print(f"   Total DMX painting successes: {total_success}")
    print(f"   Total DMX painting failures: {total_failures}")
    print(f"   Overall success rate: {overall_success_rate:.1f}%")
    
    if overall_success_rate >= 90:
        print("   🎉 EXCELLENT: DMX painting working very well!")
    elif overall_success_rate >= 75:
        print("   ✅ GOOD: DMX painting mostly working")
    elif overall_success_rate >= 50:
        print("   ⚠️ FAIR: DMX painting partially working")
    else:
        print("   ❌ POOR: DMX painting needs attention")
    
    # Show all failures
    all_failures = []
    for test_name, validator in all_validators:
        for failure in validator.painting_failures:
            all_failures.append(f"{test_name}: {failure}")
    
    if all_failures:
        print(f"\n❌ ALL COMMANDS THAT FAILED DMX PAINTING:")
        for failure in all_failures:
            print(f"   • {failure}")
    
    print(f"\n✨ Test suite completed!")


if __name__ == "__main__":
    asyncio.run(main())
