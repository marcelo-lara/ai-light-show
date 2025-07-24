"""
Tasks command handler for listing background tasks.
"""
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

from .base_command import BaseCommandHandler


class TasksCommandHandler(BaseCommandHandler):
    """Handler for the 'tasks' command."""
    
    def matches(self, command: str) -> bool:
        """Check if this is a tasks command."""
        return command.lower() == "tasks"
    
    async def handle(self, command: str, websocket=None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Handle the tasks command."""
        from ...models.app_state import app_state
        
        if not app_state.background_tasks:
            return True, "No background tasks found.", None
        
        task_list = []
        task_list.append("Background Tasks:")
        task_list.append("-" * 50)
        
        for task_id, task_state in app_state.background_tasks.items():
            status_emoji = "🔄" if task_state.status == "running" else "✅" if task_state.status == "completed" else "❌"
            elapsed = (datetime.now() - task_state.started_at).total_seconds()
            
            task_list.append(f"{status_emoji} {task_id}")
            task_list.append(f"   Song: {task_state.song_name}")
            task_list.append(f"   Operation: {task_state.operation}")
            task_list.append(f"   Status: {task_state.status}")
            task_list.append(f"   Progress: {task_state.progress}% ({task_state.current}/{task_state.total})")
            task_list.append(f"   Started: {elapsed:.1f}s ago")
            if task_state.message:
                task_list.append(f"   Message: {task_state.message}")
            if task_state.error:
                task_list.append(f"   Error: {task_state.error}")
            task_list.append("")
        
        return True, "\n".join(task_list), None
