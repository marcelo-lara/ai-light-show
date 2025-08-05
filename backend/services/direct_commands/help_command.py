"""
Help command handler for displaying available commands.
"""
from typing import Dict, Any, Tuple, Optional

from .base_command import BaseCommandHandler


class HelpCommandHandler(BaseCommandHandler):
    """Handler for the 'help' command."""
    
    def matches(self, command: str) -> bool:
        """Check if this is a help command."""
        return command.lower() in ["help", "h", "?"]
    
    async def handle(self, command: str, websocket=None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Handle the help command."""
        help_text = []
        help_text.append("AI Light Show - Direct Commands Help")
        help_text.append("=" * 40)
        help_text.append("")
        help_text.append("Available Commands (use # prefix):")
        help_text.append("")
        
        # Analysis Commands
        help_text.append("📊 ANALYSIS COMMANDS:")
        help_text.append("  #analyze                    - Analyze current song (requires WebSocket)")
        help_text.append("  #analyze context           - Generate lighting context for current song")
        help_text.append("  #analyze context reset     - Clear and regenerate lighting context")
        help_text.append("  #analyze beats <start> <end> - Get beat times for specific time range")
        help_text.append("                              - Example: #analyze beats 0 30")
        help_text.append("")
        
        # Agent Commands
        help_text.append("🤖 AGENT COMMANDS:")
        help_text.append("  #call lightingPlanner       - Execute lighting planner agent directly")
        help_text.append("")
        
        # Task Management
        help_text.append("⚙️  TASK MANAGEMENT:")
        help_text.append("  #tasks                      - List all background tasks")
        help_text.append("")
        
        # Light Plan Management
        help_text.append("💡 LIGHT PLAN MANAGEMENT:")
        help_text.append("  #create plan <name> at <time> [to <end_time>] [description <desc>]")
        help_text.append("     Example: #create plan 'Intro Flash' at 1m30s to 1m35s description 'Opening sequence'")
        help_text.append("  #delete plan <id|name>      - Delete light plan by ID or name")
        help_text.append("  #reset plans               - Delete all light plans")
        help_text.append("  #list plans                - Show all light plans")
        help_text.append("")
        
        # Action Management
        help_text.append("🎭 ACTION MANAGEMENT:")
        help_text.append("  #render                     - Render all actions to DMX canvas")
        help_text.append("  #clear all                  - Clear all actions AND lighting plans")
        help_text.append("  #clear all plans            - Clear all lighting plans only")
        help_text.append("  #clear all actions          - Clear all actions only")
        help_text.append("  #clear id <action_id>       - Clear specific action by ID")
        help_text.append("  #clear group <group_id>     - Clear all actions in a group")
        help_text.append("")
        
        # Adding Actions
        help_text.append("➕ ADDING ACTIONS:")
        help_text.append("  #add <action> to <fixture> at <time> [duration <duration>]")
        help_text.append("     Example: #add flash to parcan_l at 1m30s duration 2b")
        help_text.append("     Time formats: 1m30s, 45.5, 2b (beats)")
        help_text.append("")
        
        # Direct Action Commands
        help_text.append("⚡ DIRECT ACTION COMMANDS:")
        help_text.append("  #<action> <fixture> at <time> [for <duration>]")
        help_text.append("     Examples:")
        help_text.append("       #flash parcan_l at 135.78s")
        help_text.append("       #strobe all at 2m15s for 4b")
        help_text.append("       #fade wash_r at 1m30s for 2s")
        help_text.append("")
        
        # Available Fixtures (if fixtures are loaded)
        try:
            from ...models.app_state import app_state
            if hasattr(app_state, 'fixtures') and app_state.fixtures:
                help_text.append("🔧 AVAILABLE FIXTURES:")
                fixture_list = []
                for fixture_id, fixture in app_state.fixtures.fixtures.items():
                    actions = ", ".join(fixture.actions)
                    fixture_list.append(f"  {fixture_id}: {actions}")
                help_text.extend(sorted(fixture_list))
                help_text.append("")
        except Exception:
            pass
        
        # Time Formats
        help_text.append("⏱️  TIME FORMATS:")
        help_text.append("  1m30s                       - 1 minute 30 seconds")
        help_text.append("  45.5                        - 45.5 seconds")
        help_text.append("  2b                          - 2 beats (depends on song BPM)")
        help_text.append("  0.5b                        - Half a beat")
        help_text.append("")
        
        # Help
        help_text.append("❓ HELP:")
        help_text.append("  #help, #h, #?               - Show this help message")
        help_text.append("")
        
        # Notes
        help_text.append("📝 NOTES:")
        help_text.append("  • Commands are case-insensitive")
        help_text.append("  • Some commands require a song to be loaded")
        help_text.append("  • Analysis commands require WebSocket connection")
        help_text.append("  • Use #tasks to monitor background operations")
        help_text.append("  • Actions are automatically saved to the current song")
        
        return True, "\n".join(help_text), None
