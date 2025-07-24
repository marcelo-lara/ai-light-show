#!/usr/bin/env python3
"""
Enhanced Test Script for Fixture Actions and DMX Painting

This script addresses the issues found in the comprehensive test:
1. Extends fixture action handlers to support all actions from fixtures.json
2. Fixes SongMetadata initialization
3. Provides better DMX painting validation
4. Tests both direct commands and action parsing with proper song context

Usage:
    python enhanced_fixture_actions_test.py
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.models.app_state import app_state
from backend.services.direct_commands import DirectCommandsParser
from backend.services.dmx.actions_parser_service import ActionsParserService
from backend.services.dmx.dmx_canvas import DmxCanvas
from backend.models.actions_sheet import ActionsSheet
from backend.config import FIXTURES_FILE


class EnhancedFixtureActionHandler:
    """Helper class to add missing action handlers to fixtures"""
    
    @staticmethod
    def add_missing_handlers(fixture):
        """Add missing action handlers based on effects in fixtures.json"""
        if not fixture._config:
            return
        
        effects = fixture._config.get('effects', [])
        existing_handlers = set(fixture.action_handlers.keys())
        
        # Add strobe handler if missing but in effects
        if 'strobe' in effects and 'strobe' not in existing_handlers:
            fixture.action_handlers['strobe'] = lambda **kwargs: EnhancedFixtureActionHandler._handle_strobe(fixture, **kwargs)
            
        # Add fade handler if missing but in effects  
        if 'fade' in effects and 'fade' not in existing_handlers:
            fixture.action_handlers['fade'] = lambda **kwargs: EnhancedFixtureActionHandler._handle_fade(fixture, **kwargs)
            
        # Add full handler if missing but in effects
        if 'full' in effects and 'full' not in existing_handlers:
            fixture.action_handlers['full'] = lambda **kwargs: EnhancedFixtureActionHandler._handle_full(fixture, **kwargs)
            
        # Add seek handler if missing but in effects
        if 'seek' in effects and 'seek' not in existing_handlers:
            fixture.action_handlers['seek'] = lambda **kwargs: EnhancedFixtureActionHandler._handle_seek(fixture, **kwargs)
            
        # Add set_channel handler (always useful)
        if 'set_channel' not in existing_handlers:
            fixture.action_handlers['set_channel'] = lambda **kwargs: EnhancedFixtureActionHandler._handle_set_channel(fixture, **kwargs)
            
        # Add preset handler if presets exist
        if fixture._config.get('presets', []) and 'preset' not in existing_handlers:
            fixture.action_handlers['preset'] = lambda **kwargs: EnhancedFixtureActionHandler._handle_preset(fixture, **kwargs)
    
    @staticmethod
    def _handle_strobe(fixture, start_time=0.0, duration=1.0, rate=10, **kwargs):
        """Handle strobe effect"""
        print(f"  ⚡ {fixture.name}: Strobe effect at {start_time:.2f}s for {duration:.2f}s at {rate}Hz")
        
        # Find a suitable channel for strobing (prefer dim, then first color channel)
        strobe_channel = None
        if 'dim' in fixture.channel_names:
            strobe_channel = 'dim'
        elif 'strobe' in fixture.channel_names:
            strobe_channel = 'strobe'
        elif 'red' in fixture.channel_names:
            strobe_channel = 'red'
        elif fixture.channel_names:
            strobe_channel = list(fixture.channel_names.keys())[0]
            
        if strobe_channel:
            # Simple strobe implementation - toggle between 0 and 255
            period = 1.0 / rate
            for i in range(int(duration * rate)):
                on_time = start_time + i * period
                off_time = on_time + period * 0.5
                fixture.set_channel_value(strobe_channel, 255, start_time=on_time, duration=0.01)
                fixture.set_channel_value(strobe_channel, 0, start_time=off_time, duration=0.01)
    
    @staticmethod
    def _handle_fade(fixture, start_time=0.0, duration=2.0, from_value=0, to_value=255, **kwargs):
        """Handle fade effect"""
        print(f"  🌈 {fixture.name}: Fade effect at {start_time:.2f}s for {duration:.2f}s")
        
        # Find suitable channels for fading
        fade_channels = []
        if 'dim' in fixture.channel_names:
            fade_channels.append('dim')
        else:
            # Use color channels
            for color in ['red', 'green', 'blue', 'white']:
                if color in fixture.channel_names:
                    fade_channels.append(color)
                    
        for channel in fade_channels:
            fixture.fade_channel(channel, from_value, to_value, start_time=start_time, duration=duration)
    
    @staticmethod
    def _handle_full(fixture, start_time=0.0, duration=1.0, intensity=1.0, **kwargs):
        """Handle full brightness effect"""
        print(f"  💡 {fixture.name}: Full brightness at {start_time:.2f}s for {duration:.2f}s")
        
        dmx_value = int(intensity * 255)
        
        # Set all available channels to full
        for channel_name in fixture.channel_names:
            if channel_name in ['dim', 'red', 'green', 'blue', 'white']:
                fixture.set_channel_value(channel_name, dmx_value, start_time=start_time, duration=duration)
    
    @staticmethod 
    def _handle_seek(fixture, start_time=0.0, duration=1.0, **kwargs):
        """Handle seek effect (for moving heads)"""
        print(f"  🔍 {fixture.name}: Seek effect at {start_time:.2f}s for {duration:.2f}s")
        
        # Simple seek - move pan/tilt if available
        if 'pan_msb' in fixture.channel_names:
            fixture.fade_channel('pan_msb', 0, 255, start_time=start_time, duration=duration)
        if 'tilt_msb' in fixture.channel_names:
            fixture.fade_channel('tilt_msb', 0, 255, start_time=start_time, duration=duration)
    
    @staticmethod
    def _handle_set_channel(fixture, channel=None, value=255, start_time=0.0, **kwargs):
        """Handle set channel effect"""
        if channel and channel in fixture.channel_names:
            print(f"  🎛️ {fixture.name}: Set {channel} to {value} at {start_time:.2f}s")
            fixture.set_channel_value(channel, int(value), start_time=start_time, duration=0.1)
        else:
            print(f"  ⚠️ {fixture.name}: Channel '{channel}' not found")
    
    @staticmethod
    def _handle_preset(fixture, preset_name=None, start_time=0.0, **kwargs):
        """Handle preset effect"""
        presets = fixture._config.get('presets', [])
        preset = None
        
        for p in presets:
            if p.get('name') == preset_name:
                preset = p
                break
                
        if preset:
            print(f"  🎚️ {fixture.name}: Apply preset '{preset_name}' at {start_time:.2f}s")
            values = preset.get('values', {})
            for channel, value in values.items():
                if channel in fixture.channel_names:
                    fixture.set_channel_value(channel, value, start_time=start_time, duration=0.1)
        else:
            print(f"  ⚠️ {fixture.name}: Preset '{preset_name}' not found")


class DMXPaintingValidator:
    """Validates DMX painting by checking canvas state changes"""
    
    def __init__(self):
        self.dmx_canvas = DmxCanvas.get_instance()
        self.initial_state = {}
        self.commands_tested = 0
        self.painting_success = 0
        self.painting_failures = []
    
    def capture_initial_state(self):
        """Capture initial DMX canvas state"""
        frame = self.dmx_canvas.get_frame(0.0)
        self.initial_state = {ch: val for ch, val in enumerate(frame) if val > 0}
        print(f"📸 Captured initial DMX state: {len(self.initial_state)} active channels")
    
    def validate_dmx_painting(self, command):
        """Check if DMX canvas was painted after command"""
        current_frame = self.dmx_canvas.get_frame(0.0)
        current_state = {ch: val for ch, val in enumerate(current_frame) if val > 0}
        
        self.commands_tested += 1
        
        # Check for changes
        changes = {}
        for ch in range(len(current_frame)):
            old_val = self.initial_state.get(ch, 0)
            new_val = current_state.get(ch, 0)
            if old_val != new_val:
                changes[ch] = (old_val, new_val)
        
        if changes:
            self.painting_success += 1
            print(f"   ✅ DMX painting detected: {len(changes)} channels changed")
            for ch, (old, new) in list(changes.items())[:5]:  # Show first 5 changes
                print(f"      CH{ch+1}: {old} → {new}")
        else:
            print(f"   ❌ No DMX painting detected")
            self.painting_failures.append(command)
        
        # Update initial state for next test
        self.initial_state = current_state
    
    def print_summary(self):
        """Print validation summary"""
        print(f"\n📊 DMX Painting Validation Summary:")
        print(f"   Commands tested: {self.commands_tested}")
        print(f"   Successful painting: {self.painting_success}")
        print(f"   Failed painting: {len(self.painting_failures)}")
        success_rate = (self.painting_success/self.commands_tested*100) if self.commands_tested > 0 else 0
        print(f"   Success rate: {success_rate:.1f}%")
        
        if success_rate < 50:
            print(f"   ❌ POOR: DMX painting needs attention")
        elif success_rate < 80:
            print(f"   ⚠️ FAIR: DMX painting could be improved") 
        else:
            print(f"   ✅ GOOD: DMX painting working well")


def load_test_fixtures():
    """Load fixtures and enhance them with missing action handlers"""
    print("🎪 Loading and enhancing test fixtures...")
    
    if not app_state.fixtures:
        print("⚠️ No fixtures in app_state - fixtures need to be loaded externally")
    
    if not app_state.fixtures:
        print("❌ No fixtures loaded")
        return False
    
    # Enhance all fixtures with missing action handlers
    for fixture_id, fixture in app_state.fixtures.fixtures.items():
        print(f"  🔧 Enhancing {fixture.name} with missing action handlers...")
        before_count = len(fixture.action_handlers)
        EnhancedFixtureActionHandler.add_missing_handlers(fixture)
        after_count = len(fixture.action_handlers)
        print(f"      Actions: {before_count} → {after_count} ({list(fixture.action_handlers.keys())})")
    
    return True


def setup_test_environment():
    """Set up test environment with song and services"""
    print("🛠️ Setting up test environment...")
    
    # Load fixtures
    if not load_test_fixtures():
        return False
    
    # Create test song 
    try:
        from shared.models.song_metadata import SongMetadata
        song_metadata = SongMetadata("test_song", songs_folder="/home/darkangel/ai-light-show/songs", ignore_existing=True)
        app_state.current_song = song_metadata
        print("  ✅ Created test song metadata")
    except Exception as e:
        print(f"  ⚠️ Could not create test song: {e}")
    
    # Initialize DMX canvas
    dmx_canvas = DmxCanvas.get_instance()
    dmx_canvas.clear_canvas()
    print("  ✅ DMX canvas initialized and cleared")
    
    return True


async def test_enhanced_direct_commands():
    """Test direct commands with proper setup"""
    print("\n🎭 Testing Enhanced Direct Commands...")
    
    parser = DirectCommandsParser()
    validator = DMXPaintingValidator()
    validator.capture_initial_state()
    
    # Test basic action commands
    commands = [
        "#add flash to parcan_l at 1.0s duration 0.5s",
        "#add flash to head_el150 at 2.0s duration 0.5s",
        "#render"
    ]
    
    for i, command in enumerate(commands, 1):
        print(f"\n{i:2d}. Testing: {command}")
        try:
            success, message, data = await parser.parse_command(command)
            if success:
                print(f"   ✅ Command executed: {message}")
                validator.validate_dmx_painting(command)
            else:
                print(f"   ❌ Command failed: {message}")
                validator.commands_tested += 1
                validator.painting_failures.append(command)
        except Exception as e:
            print(f"   💥 Command error: {e}")
            validator.commands_tested += 1
            validator.painting_failures.append(command)
    
    validator.print_summary()
    return validator


def test_enhanced_actions_parser():
    """Test action parsing with enhanced fixture handlers"""
    print("\n🎪 Testing Enhanced Actions Parser...")
    
    if not app_state.fixtures:
        print("❌ No fixtures loaded")
        return None
    
    validator = DMXPaintingValidator()
    validator.capture_initial_state()
    
    # Get actions service
    actions_service = app_state.get_actions_service()
    if not actions_service:
        print("❌ Could not get actions service")
        return None
    
    # Test enhanced commands
    commands = [
        "flash parcan_l at 1.0s for 0.5s",
        "strobe parcan_l at 2.0s for 1.0s", 
        "fade parcan_l at 3.0s for 2.0s",
        "full parcan_l intensity=0.8 at 4.0s for 1.0s",
        "flash head_el150 at 5.0s for 0.5s",
        "seek head_el150 at 6.0s for 2.0s",
    ]
    
    parser = ActionsParserService(app_state.fixtures, debug=False)
    
    for i, command in enumerate(commands, 1):
        print(f"\n{i:2d}. Testing: {command}")
        try:
            actions = parser.parse_command(command)
            if actions:
                print(f"   ✅ Parsed {len(actions)} action(s)")
                
                # Create actions sheet and render
                actions_sheet = ActionsSheet("test_enhanced")
                for action in actions:
                    actions_sheet.add_action(action)
                
                render_result = actions_service.render_actions_to_canvas(actions_sheet)
                print(f"   📊 Render result: {render_result}")
                validator.validate_dmx_painting(command)
            else:
                print(f"   ❌ No actions generated")
                validator.commands_tested += 1
                validator.painting_failures.append(command)
        except Exception as e:
            print(f"   💥 Error: {e}")
            validator.commands_tested += 1
            validator.painting_failures.append(command)
    
    validator.print_summary()
    return validator


def test_direct_canvas_painting():
    """Test direct DMX canvas painting methods"""
    print("\n🎨 Testing Direct DMX Canvas Painting...")
    
    validator = DMXPaintingValidator()
    validator.capture_initial_state()
    
    dmx_canvas = DmxCanvas.get_instance()
    
    tests = [
        ("Set single channel", lambda: dmx_canvas.paint_frame(0.0, {15: 255})),
        ("Set multiple channels", lambda: dmx_canvas.paint_frame(0.0, {16: 128, 17: 200, 18: 100})),
        ("Clear canvas", lambda: dmx_canvas.clear_canvas()),
    ]
    
    for i, (test_name, test_func) in enumerate(tests, 1):
        print(f"\n{i}. Testing: {test_name}")
        try:
            test_func()
            validator.validate_dmx_painting(test_name)
        except Exception as e:
            print(f"   💥 Error: {e}")
            validator.commands_tested += 1
            validator.painting_failures.append(test_name)
    
    validator.print_summary()
    return validator


async def main():
    """Main test runner"""
    print("🧪 Enhanced Fixture Actions and DMX Painting Test Suite")
    print("=" * 70)
    
    # Setup test environment
    if not setup_test_environment():
        print("❌ Failed to setup test environment")
        return
    
    fixture_count = len(app_state.fixtures.fixtures) if app_state.fixtures else 0
    print(f"✅ Loaded {fixture_count} fixtures")
    
    # Run tests
    validators = []
    
    # Test 1: Enhanced direct commands
    validator1 = await test_enhanced_direct_commands()
    if validator1:
        validators.append(("Direct Commands", validator1))
    
    # Test 2: Enhanced actions parser
    validator2 = test_enhanced_actions_parser()
    if validator2:
        validators.append(("Actions Parser", validator2))
    
    # Test 3: Direct canvas painting
    validator3 = test_direct_canvas_painting()
    if validator3:
        validators.append(("Direct Canvas", validator3))
    
    # Overall summary
    print("\n" + "=" * 70)
    print("📊 ENHANCED TEST RESULTS SUMMARY")
    print("=" * 70)
    
    total_tested = total_success = total_failures = 0
    
    for test_name, validator in validators:
        success_rate = (validator.painting_success/validator.commands_tested*100) if validator.commands_tested > 0 else 0
        print(f"\n🔬 {test_name}:")
        print(f"   Commands tested: {validator.commands_tested}")
        print(f"   DMX painting success: {validator.painting_success}")
        print(f"   DMX painting failures: {len(validator.painting_failures)}")
        print(f"   Success rate: {success_rate:.1f}%")
        
        total_tested += validator.commands_tested
        total_success += validator.painting_success
        total_failures += len(validator.painting_failures)
    
    if total_tested > 0:
        overall_rate = (total_success/total_tested*100)
        print(f"\n🏆 OVERALL RESULTS:")
        print(f"   Total commands tested: {total_tested}")
        print(f"   Total DMX painting successes: {total_success}")
        print(f"   Total DMX painting failures: {total_failures}")
        print(f"   Overall success rate: {overall_rate:.1f}%")
        
        if overall_rate >= 80:
            print(f"   ✅ EXCELLENT: DMX painting working well")
        elif overall_rate >= 60:
            print(f"   ⚠️ GOOD: DMX painting mostly working")
        elif overall_rate >= 40:
            print(f"   ⚠️ FAIR: DMX painting needs improvement")
        else:
            print(f"   ❌ POOR: DMX painting needs major fixes")
    
    print("\n✨ Enhanced test suite completed!")


if __name__ == "__main__":
    asyncio.run(main())
