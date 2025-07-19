"""
Actions Service

This service handles the actions to the current song.
It renders actions from an ActionsSheet to the DMX canvas.
"""
from typing import Optional, Dict, Any
from backend.models.actions_sheet import ActionsSheet, ActionModel
from backend.models.fixtures.fixtures_list_model import FixturesListModel
from backend.services.dmx.dmx_canvas import DmxCanvas


class ActionsService:
    """
    Service for handling and rendering actions to the DMX canvas.
    
    This service bridges ActionsSheet (which stores actions for a song) 
    and FixturesListModel (which can render actions to the DMX canvas).
    """
    
    def __init__(self, fixtures: FixturesListModel, dmx_canvas: DmxCanvas, debug: bool = True):
        """
        Initialize the Actions Service.
        
        Args:
            fixtures (FixturesListModel): The fixtures model containing all fixtures
            dmx_canvas (DmxCanvas): The DMX canvas to render actions to
            debug (bool): Enable debug output
        """
        self.fixtures = fixtures
        self.dmx_canvas = dmx_canvas
        self.debug = debug

    def render_actions_to_canvas(self, actions_sheet: ActionsSheet, clear_first: bool = True) -> bool:
        """
        Render all actions from an ActionsSheet to the DMX canvas.
        
        Args:
            actions_sheet (ActionsSheet): The actions sheet containing actions to render
            clear_first (bool): Whether to clear the canvas before rendering (default: True)
            
        Returns:
            bool: True if actions were rendered successfully, False otherwise
        """
        try:
            # Clear the canvas first if requested
            if clear_first:
                if self.debug:
                    print("🧹 Clearing DMX canvas before rendering actions...")
                self.dmx_canvas.clear_canvas()
            
            if self.debug:
                print(f"🎬 Rendering {len(actions_sheet)} actions to DMX canvas...")
            
            # Sort actions by start time for better organization
            actions_sheet.sort_actions_by_time()
            
            # Render each action
            success_count = 0
            for i, action in enumerate(actions_sheet.actions):
                try:
                    if self._render_single_action(action):
                        success_count += 1
                    if self.debug:
                        print(f"  ✅ Action {i+1}/{len(actions_sheet)}: {action.action} at {action.start_time}s")
                except Exception as e:
                    if self.debug:
                        print(f"  ❌ Action {i+1}/{len(actions_sheet)}: Failed to render {action.action} - {e}")
                    continue
            
            if self.debug:
                from shared.file_utils import save_file
                from backend.models.app_state import app_state
                save_file(f"{app_state.current_song.data_folder}/dmx_canvas.txt", self.dmx_canvas.export_as_txt())

                print(f"🎯 Successfully rendered {success_count}/{len(actions_sheet)} actions")
                
            return success_count > 0
            
        except Exception as e:
            if self.debug:
                print(f"❌ Error rendering actions to canvas: {e}")
            return False
    
    def _render_single_action(self, action: ActionModel) -> bool:
        """
        Render a single action to the DMX canvas.
        
        Args:
            action (ActionModel): The action to render
            
        Returns:
            bool: True if action was rendered successfully, False otherwise
        """
        try:
            # Get the fixture_id from the action (now mandatory)
            fixture_id = action.fixture_id
            if not fixture_id:
                if self.debug:
                    print(f"    ⚠️  Empty fixture_id in action")
                return False
            
            # Find the fixture
            if fixture_id not in self.fixtures.fixtures:
                if self.debug:
                    print(f"    ⚠️  Fixture '{fixture_id}' not found")
                return False
            
            fixture = self.fixtures.fixtures[fixture_id]
            
            # Prepare parameters for the fixture action
            action_params = action.parameters.copy()
            action_params['start_time'] = action.start_time
            action_params['duration'] = action.duration
            
            # Render the action on the fixture
            fixture.render_action(action.action, action_params)
            
            return True
            
        except ValueError as e:
            if self.debug:
                print(f"    ⚠️  Action '{action.action}' failed: {e}")
            return False
        except Exception as e:
            if self.debug:
                print(f"    ❌ Unexpected error rendering action '{action.action}': {e}")
            return False
    
    def render_action_at_time(self, actions_sheet: ActionsSheet, timestamp: float) -> Dict[str, Any]:
        """
        Get all actions that should be active at a specific timestamp and render them.
        
        Args:
            actions_sheet (ActionsSheet): The actions sheet to check
            timestamp (float): The time to check for active actions
            
        Returns:
            Dict[str, Any]: Dictionary with render results and active actions info
        """
        active_actions = actions_sheet.get_actions_at_time(timestamp)
        
        result = {
            'timestamp': timestamp,
            'active_actions_count': len(active_actions),
            'rendered_count': 0,
            'failed_count': 0,
            'actions': []
        }
        
        for action in active_actions:
            action_result = {
                'action': action.action,
                'fixture_id': action.fixture_id,
                'start_time': action.start_time,
                'duration': action.duration,
                'rendered': False
            }
            
            try:
                if self._render_single_action(action):
                    action_result['rendered'] = True
                    result['rendered_count'] += 1
                else:
                    result['failed_count'] += 1
            except Exception as e:
                action_result['error'] = str(e)
                result['failed_count'] += 1
            
            result['actions'].append(action_result)
        
        return result
    
    def validate_actions(self, actions_sheet: ActionsSheet) -> Dict[str, Any]:
        """
        Validate all actions in an ActionsSheet without rendering them.
        
        Args:
            actions_sheet (ActionsSheet): The actions sheet to validate
            
        Returns:
            Dict[str, Any]: Validation results with details about each action
        """
        validation_result = {
            'total_actions': len(actions_sheet),
            'valid_actions': 0,
            'invalid_actions': 0,
            'warnings': [],
            'errors': [],
            'action_details': []
        }
        
        for i, action in enumerate(actions_sheet.actions):
            action_detail = {
                'index': i,
                'action': action.action,
                'start_time': action.start_time,
                'duration': action.duration,
                'valid': True,
                'issues': []
            }
            
            # Check if fixture_id is provided
            fixture_id = action.fixture_id
            if not fixture_id:
                action_detail['valid'] = False
                action_detail['issues'].append("Empty fixture_id")
                validation_result['errors'].append(f"Action {i}: Empty fixture_id")
            
            # Check if fixture exists
            elif fixture_id not in self.fixtures.fixtures:
                action_detail['valid'] = False
                action_detail['issues'].append(f"Fixture '{fixture_id}' not found")
                validation_result['errors'].append(f"Action {i}: Fixture '{fixture_id}' not found")
            
            # Check if action is supported by fixture
            elif fixture_id in self.fixtures.fixtures:
                fixture = self.fixtures.fixtures[fixture_id]
                if action.action not in fixture.actions:
                    action_detail['valid'] = False
                    action_detail['issues'].append(f"Action '{action.action}' not supported by fixture '{fixture_id}'")
                    validation_result['errors'].append(f"Action {i}: '{action.action}' not supported by '{fixture_id}'")
            
            # Check for timing issues
            if action.start_time < 0:
                action_detail['issues'].append("Negative start time")
                validation_result['warnings'].append(f"Action {i}: Negative start time")
            
            if action.duration <= 0:
                action_detail['issues'].append("Non-positive duration")
                validation_result['warnings'].append(f"Action {i}: Non-positive duration")
            
            if action_detail['valid']:
                validation_result['valid_actions'] += 1
            else:
                validation_result['invalid_actions'] += 1
            
            validation_result['action_details'].append(action_detail)
        
        return validation_result
