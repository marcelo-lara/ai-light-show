#!/usr/bin/env python3
"""Test script to verify the light_plan implementation in SongMetadata."""

import os
import tempfile
import shutil
from shared.models.song_metadata import SongMetadata, LightPlanItem

def test_light_plan_functionality():
    """Test all light_plan functionality."""
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a temporary songs folder
        songs_dir = os.path.join(temp_dir, "songs")
        os.makedirs(songs_dir, exist_ok=True)
        
        # Create a SongMetadata instance
        song = SongMetadata("test_song", songs_folder=songs_dir, ignore_existing=True)
        
        print("🧪 Testing light_plan initialization...")
        assert len(song.light_plan) == 0, "Light plan should be empty initially"
        print("✅ Initialization test passed")
        
        print("\n🧪 Testing add_light_plan_item...")
        song.add_light_plan_item(1, 10.0, 20.0, "Intro Lights", "Soft warm lights for intro")
        song.add_light_plan_item(2, 30.0, 45.0, "Drop Lights", "Intense strobing for drop")
        song.add_light_plan_item(3, 60.0, name="Outro Lights", description="Fade out lights")
        
        assert len(song.light_plan) == 3, f"Expected 3 light plan items, got {len(song.light_plan)}"
        assert song.light_plan[0].id == 1, "First item ID should be 1"
        assert song.light_plan[0].start == 10.0, "First item start should be 10.0"
        assert song.light_plan[0].end == 20.0, "First item end should be 20.0"
        assert song.light_plan[0].name == "Intro Lights", "First item name should be 'Intro Lights'"
        assert song.light_plan[2].end is None, "Third item end should be None"
        print("✅ Add light plan item test passed")
        
        print("\n🧪 Testing get_light_plan_at_time...")
        active_at_15 = song.get_light_plan_at_time(15.0)
        assert len(active_at_15) == 1, f"Expected 1 active item at time 15.0, got {len(active_at_15)}"
        assert active_at_15[0].id == 1, "Active item at 15.0 should be item with ID 1"
        
        active_at_35 = song.get_light_plan_at_time(35.0)
        assert len(active_at_35) == 1, f"Expected 1 active item at time 35.0, got {len(active_at_35)}"
        assert active_at_35[0].id == 2, "Active item at 35.0 should be item with ID 2"
        
        active_at_65 = song.get_light_plan_at_time(65.0)
        assert len(active_at_65) == 1, f"Expected 1 active item at time 65.0, got {len(active_at_65)}"
        assert active_at_65[0].id == 3, "Active item at 65.0 should be item with ID 3"
        
        active_at_5 = song.get_light_plan_at_time(5.0)
        assert len(active_at_5) == 0, f"Expected 0 active items at time 5.0, got {len(active_at_5)}"
        print("✅ Get light plan at time test passed")
        
        print("\n🧪 Testing light_plan property setter with dicts...")
        song.light_plan = [
            {"id": 4, "start": 0.0, "end": 10.0, "name": "Pre-intro", "description": "Setup lights"},
            {"id": 5, "start": 50.0, "end": 60.0, "name": "Bridge", "description": "Bridge lighting"}
        ]
        assert len(song.light_plan) == 2, f"Expected 2 light plan items after setter, got {len(song.light_plan)}"
        assert isinstance(song.light_plan[0], LightPlanItem), "Items should be converted to LightPlanItem objects"
        assert song.light_plan[0].id == 4, "First item ID should be 4"
        print("✅ Light plan setter test passed")
        
        print("\n🧪 Testing remove_light_plan_item...")
        removed = song.remove_light_plan_item(4)
        assert removed == True, "Should return True when item is removed"
        assert len(song.light_plan) == 1, f"Expected 1 light plan item after removal, got {len(song.light_plan)}"
        
        removed_missing = song.remove_light_plan_item(999)
        assert removed_missing == False, "Should return False when item is not found"
        print("✅ Remove light plan item test passed")
        
        print("\n🧪 Testing save and load...")
        # Add some items back
        song.add_light_plan_item(6, 70.0, 80.0, "Final Drop", "Epic finale")
        song.save()
        
        # Create new instance and load
        song2 = SongMetadata("test_song", songs_folder=songs_dir)
        assert len(song2.light_plan) == 2, f"Expected 2 light plan items after load, got {len(song2.light_plan)}"
        assert isinstance(song2.light_plan[0], LightPlanItem), "Loaded items should be LightPlanItem objects"
        assert song2.light_plan[1].id == 6, "Second loaded item ID should be 6"
        assert song2.light_plan[1].name == "Final Drop", "Second loaded item name should be 'Final Drop'"
        print("✅ Save and load test passed")
        
        print("\n🧪 Testing clear_light_plan...")
        song2.clear_light_plan()
        assert len(song2.light_plan) == 0, f"Expected 0 light plan items after clear, got {len(song2.light_plan)}"
        print("✅ Clear light plan test passed")
        
        print("\n🧪 Testing to_dict serialization...")
        song.add_light_plan_item(7, 90.0, 100.0, "Test Item", "Test description")
        data = song.to_dict()
        assert "light_plan" in data, "light_plan should be in serialized data"
        assert len(data["light_plan"]) == 3, f"Expected 3 light plan items in serialized data, got {len(data['light_plan'])}"
        assert isinstance(data["light_plan"][0], dict), "Serialized items should be dicts"
        assert data["light_plan"][2]["id"] == 7, "Third serialized item ID should be 7"
        print("✅ Serialization test passed")
        
        print("\n🧪 Testing get_prompt includes light_plan...")
        prompt = song.get_prompt()
        assert "light plan:" in prompt, "Prompt should include light_plan section"
        assert "Bridge (50.00-60.00)" in prompt, "Prompt should include light plan items"
        print("✅ Prompt test passed")
        
        print("\n🧪 Testing __str__ includes light_plan count...")
        str_repr = str(song)
        assert "light_plan=3" in str_repr, f"String representation should include light_plan count, got: {str_repr}"
        print("✅ String representation test passed")
        
    print("\n🎉 All tests passed! Light plan implementation is working correctly.")

if __name__ == "__main__":
    test_light_plan_functionality()
